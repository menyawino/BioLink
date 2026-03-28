#!/usr/bin/env python3
"""
Bootstrap BioLink NiFi graph via NiFi REST API (idempotent).

Creates and starts:
  Step 1: Master schema generation
    GenerateFlowFile -> BiolinkMasterSchemaProcessor -> LogMessage

  Step 2a: BHS harmonisation
    GetFile -> BiolinkCsvToJsonProcessor -> BiolinkHarmoniseProcessor
    -> BiolinkJsonToSqlProcessor -> PutSQL (bhs_harmonised)

  Step 2b: EHVol harmonisation
    GetFile -> BiolinkCsvToJsonProcessor -> BiolinkHarmoniseProcessor
    -> BiolinkJsonToSqlProcessor -> PutSQL (ehvol_harmonised)

Also ensures a shared root DBCP controller service exists + is enabled.

Safe to run repeatedly; existing components are re-used by name.
"""

from __future__ import annotations

import argparse
import json
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional


STANDARD_BUNDLE = {
    "group": "org.apache.nifi",
    "artifact": "nifi-standard-nar",
    "version": "2.8.0",
}

PYTHON_BUNDLE = {
    "group": "org.apache.nifi",
    "artifact": "python-extensions",
    "version": "1.0.0",
}

DBCP_BUNDLE = {
    "group": "org.apache.nifi",
    "artifact": "nifi-dbcp-service-nar",
    "version": "2.8.0",
}


class NiFiClient:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.token: Optional[str] = None
        self.ssl_ctx = ssl._create_unverified_context()

    def _request(
        self,
        method: str,
        path: str,
        body: Optional[dict] = None,
        form: Optional[dict] = None,
        expected: tuple[int, ...] = (200, 201, 202),
    ) -> Any:
        url = f"{self.base_url}/nifi-api{path}"
        headers = {}
        data = None

        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        if form is not None:
            data = urllib.parse.urlencode(form).encode("utf-8")
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        elif body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
        try:
            with urllib.request.urlopen(req, context=self.ssl_ctx, timeout=30) as resp:
                raw = resp.read()
                if resp.status not in expected:
                    raise RuntimeError(f"{method} {path} -> unexpected status {resp.status}")
                if not raw:
                    return None
                content_type = resp.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    return json.loads(raw.decode("utf-8"))
                return raw.decode("utf-8")
        except urllib.error.HTTPError as e:
            text = e.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"{method} {path} -> HTTP {e.code}: {text[:500]}") from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"{method} {path} -> URL error: {e}") from e

    def authenticate(self) -> None:
        token = self._request(
            "POST",
            "/access/token",
            form={"username": self.username, "password": self.password},
            expected=(200, 201),
        )
        if not isinstance(token, str) or not token.strip():
            raise RuntimeError("Failed to obtain NiFi auth token")
        self.token = token.strip()

    def wait_ready(self, timeout_sec: int = 300) -> None:
        started = time.time()
        while time.time() - started < timeout_sec:
            try:
                self.authenticate()
                self._request("GET", "/system-diagnostics", expected=(200,))
                return
            except Exception:
                time.sleep(3)
        raise RuntimeError(f"NiFi not ready after {timeout_sec} seconds")

    def root_pg_id(self) -> str:
        payload = self._request("GET", "/flow/process-groups/root")
        return payload["processGroupFlow"]["id"]

    def get_pg_flow(self, pg_id: str) -> dict:
        return self._request("GET", f"/flow/process-groups/{pg_id}")

    def find_process_group(self, parent_pg_id: str, name: str) -> Optional[str]:
        flow = self.get_pg_flow(parent_pg_id)
        for entry in flow.get("processGroupFlow", {}).get("flow", {}).get("processGroups", []):
            c = entry.get("component", {})
            if c.get("name") == name:
                return c.get("id")
        return None

    def create_process_group(self, parent_pg_id: str, name: str, x: float, y: float) -> str:
        body = {
            "revision": {"version": 0},
            "component": {"name": name, "position": {"x": x, "y": y}},
        }
        resp = self._request("POST", f"/process-groups/{parent_pg_id}/process-groups", body=body)
        return resp["id"]

    def ensure_process_group(self, parent_pg_id: str, name: str, x: float, y: float) -> str:
        existing = self.find_process_group(parent_pg_id, name)
        if existing:
            return existing
        return self.create_process_group(parent_pg_id, name, x, y)

    def find_controller_service(self, pg_id: str, name: str) -> Optional[str]:
        data = self._request("GET", f"/flow/process-groups/{pg_id}/controller-services")
        for entry in data.get("controllerServices", []):
            c = entry.get("component", {})
            if c.get("name") == name:
                return c.get("id")
        return None

    def ensure_dbcp(self, root_pg_id: str, name: str) -> str:
        existing = self.find_controller_service(root_pg_id, name)
        if existing:
            return existing

        body = {
            "revision": {"version": 0},
            "component": {
                "name": name,
                "type": "org.apache.nifi.dbcp.DBCPConnectionPool",
                "bundle": DBCP_BUNDLE,
                "properties": {
                    "Database Connection URL": "jdbc:postgresql://postgres:5432/biolink",
                    "Database Driver Class Name": "org.postgresql.Driver",
                    "Database Driver Location(s)": "/opt/nifi/jdbc/postgresql-42.7.3.jar",
                    "Database User": "biolink",
                    "Password": "biolink_secret",
                    "Max Wait Time": "500 millis",
                    "Max Total Connections": "20",
                    "Validation query": "SELECT 1",
                },
            },
        }
        resp = self._request("POST", f"/process-groups/{root_pg_id}/controller-services", body=body)
        return resp["id"]

    def enable_controller_service(self, cs_id: str) -> None:
        cs = self._request("GET", f"/controller-services/{cs_id}")
        state = cs.get("component", {}).get("state")
        if state == "ENABLED":
            return
        body = {"revision": cs["revision"], "state": "ENABLED"}
        self._request("PUT", f"/controller-services/{cs_id}/run-status", body=body)

    def list_processors(self, pg_id: str) -> List[dict]:
        flow = self.get_pg_flow(pg_id)
        return flow.get("processGroupFlow", {}).get("flow", {}).get("processors", [])

    def find_processor(self, pg_id: str, name: str) -> Optional[str]:
        for entry in self.list_processors(pg_id):
            c = entry.get("component", {})
            if c.get("name") == name:
                return c.get("id")
        return None

    def create_processor(
        self,
        pg_id: str,
        name: str,
        proc_type: str,
        bundle: dict,
        properties: dict,
        x: float,
        y: float,
        auto_terminate: Optional[List[str]] = None,
        scheduling_period: str = "0 sec",
    ) -> str:
        config: Dict[str, Any] = {
            "properties": properties,
            "schedulingStrategy": "TIMER_DRIVEN",
            "schedulingPeriod": scheduling_period,
            "penaltyDuration": "30 sec",
            "yieldDuration": "1 sec",
            "bulletinLevel": "WARN",
            "concurrentlySchedulableTaskCount": 1,
        }
        if auto_terminate:
            config["autoTerminatedRelationships"] = auto_terminate

        body = {
            "revision": {"version": 0},
            "component": {
                "name": name,
                "type": proc_type,
                "bundle": bundle,
                "config": config,
                "position": {"x": x, "y": y},
            },
        }
        resp = self._request("POST", f"/process-groups/{pg_id}/processors", body=body)
        return resp["id"]

    def ensure_processor(
        self,
        pg_id: str,
        name: str,
        proc_type: str,
        bundle: dict,
        properties: dict,
        x: float,
        y: float,
        auto_terminate: Optional[List[str]] = None,
        scheduling_period: str = "0 sec",
    ) -> str:
        existing = self.find_processor(pg_id, name)
        if existing:
            return existing
        return self.create_processor(
            pg_id, name, proc_type, bundle, properties, x, y, auto_terminate, scheduling_period
        )

    def list_connections(self, pg_id: str) -> List[dict]:
        flow = self.get_pg_flow(pg_id)
        return flow.get("processGroupFlow", {}).get("flow", {}).get("connections", [])

    def ensure_connection(
        self,
        pg_id: str,
        source_id: str,
        dest_id: str,
        relationships: List[str],
        name: str,
    ) -> str:
        target_rels = sorted(relationships)
        for entry in self.list_connections(pg_id):
            c = entry.get("component", {})
            src = c.get("source", {}).get("id")
            dst = c.get("destination", {}).get("id")
            rels = sorted(c.get("selectedRelationships", []))
            if src == source_id and dst == dest_id and rels == target_rels:
                return c.get("id")

        body = {
            "revision": {"version": 0},
            "component": {
                "name": name,
                "source": {"id": source_id, "type": "PROCESSOR", "groupId": pg_id},
                "destination": {"id": dest_id, "type": "PROCESSOR", "groupId": pg_id},
                "selectedRelationships": relationships,
                "backPressureObjectThreshold": 10000,
                "backPressureDataSizeThreshold": "1 GB",
            },
        }
        resp = self._request("POST", f"/process-groups/{pg_id}/connections", body=body)
        return resp["id"]

    def start_processor(self, proc_id: str) -> None:
        data = self._request("GET", f"/processors/{proc_id}")
        state = data.get("component", {}).get("state")
        if state in ("RUNNING", "STARTING"):
            return
        body = {"revision": data["revision"], "state": "RUNNING"}
        try:
            self._request("PUT", f"/processors/{proc_id}/run-status", body=body)
        except RuntimeError as exc:
            msg = str(exc)
            if "HTTP 409" in msg and ("Current state is STARTING" in msg or "Current state is RUNNING" in msg):
                return
            raise


def build_step1_group(client: NiFiClient, root_id: str) -> None:
    pg_id = client.ensure_process_group(root_id, "Schema Generation Pipeline (Step 1)", 100, 1200)

    trigger_id = client.ensure_processor(
        pg_id,
        "GenerateFlowFile - Trigger Schema Gen",
        "org.apache.nifi.processors.standard.GenerateFlowFile",
        STANDARD_BUNDLE,
        {
            "File Size": "0B",
            "Batch Size": "1",
            "Data Format": "Text",
            "Unique FlowFiles": "false",
        },
        0,
        0,
        scheduling_period="24 hours",
    )

    master_id = client.ensure_processor(
        pg_id,
        "MasterSchema - Generate Schema",
        "BiolinkMasterSchemaProcessor",
        PYTHON_BUNDLE,
        {
            "Repository Root": "/opt/nifi/biolink_repo",
            "BHS CSV Path": "/opt/nifi/db/BHS_Full.csv",
            "EHVol CSV Path": "/opt/nifi/db/EHVol_Full.csv",
            "Schema Output Path": "/opt/nifi/outputs/master_schema.csv",
            "Match Threshold": "0.35",
            "Top K": "5",
            "Min Final Score": "0.50",
            "Lexicon Path": "/opt/nifi/biolink_scripts/clinical_lexicon.csv",
        },
        320,
        0,
    )

    log_id = client.ensure_processor(
        pg_id,
        "LogMessage - Schema Generated",
        "org.apache.nifi.processors.standard.LogMessage",
        STANDARD_BUNDLE,
        {
            "Log Level": "info",
            "Log Message": "master_schema.csv generated: ${biolink.schema.total_matched} matched columns (${biolink.schema.pii_columns} PII, ${biolink.schema.clinical_columns} clinical)",
        },
        640,
        0,
        auto_terminate=["success"],
    )

    client.ensure_connection(pg_id, trigger_id, master_id, ["success"], "Trigger -> MasterSchema")
    client.ensure_connection(pg_id, master_id, log_id, ["success"], "MasterSchema -> Log")
    client.ensure_connection(pg_id, master_id, master_id, ["failure"], "MasterSchema failure loop")

    for proc_id in [log_id, master_id, trigger_id]:
        client.start_processor(proc_id)


def build_registry_pipeline_group(client: NiFiClient, root_id: str) -> None:
    pg_id = client.ensure_process_group(root_id, "Registry Pipeline (Steps 2-4)", 100, 1800)

    trigger_id = client.ensure_processor(
        pg_id,
        "GenerateFlowFile - Trigger Registry Pipeline",
        "org.apache.nifi.processors.standard.GenerateFlowFile",
        STANDARD_BUNDLE,
        {
            "File Size": "0B",
            "Batch Size": "1",
            "Data Format": "Text",
            "Unique FlowFiles": "false",
        },
        0,
        0,
        scheduling_period="24 hours",
    )

    pipeline_id = client.ensure_processor(
        pg_id,
        "Run Scripted Registry Pipeline",
        "BiolinkRegistryPipelineProcessor",
        PYTHON_BUNDLE,
        {
            "Repository Root": "/opt/nifi/biolink_repo",
            "Schema Relative Path": "outputs/master_schema.csv",
            "Unified Output Relative Path": "outputs/unified_registry.csv",
            "OMOP Output Relative Directory": "outputs/omop_cdm",
            "Quality Report Relative Path": "outputs/data_quality_report.html",
            "Characterization Relative Path": "outputs/cohort_characterization.csv",
            "Load To PostgreSQL": "true",
            "Database Host": "postgres",
            "Database Port": "5432",
            "Database Name": "biolink",
            "Database User": "biolink",
            "Database Password": "biolink_secret",
            "Unified Registry Table": "unified_registry",
        },
        340,
        0,
    )

    log_id = client.ensure_processor(
        pg_id,
        "LogMessage - Registry Pipeline Complete",
        "org.apache.nifi.processors.standard.LogMessage",
        STANDARD_BUNDLE,
        {
            "Log Level": "info",
            "Log Message": "Registry pipeline complete: ${biolink.registry.rows} rows, ${biolink.registry.columns} columns",
        },
        700,
        0,
        auto_terminate=["success"],
    )

    client.ensure_connection(pg_id, trigger_id, pipeline_id, ["success"], "Trigger -> Scripted Pipeline")
    client.ensure_connection(pg_id, pipeline_id, log_id, ["success"], "Scripted Pipeline -> Log")
    client.ensure_connection(pg_id, pipeline_id, pipeline_id, ["failure"], "Scripted Pipeline failure loop")

    for proc_id in [log_id, pipeline_id, trigger_id]:
        client.start_processor(proc_id)


def build_step2_group(client: NiFiClient, root_id: str, dataset: str, x: float, y: float, dbcp_id: str) -> None:
    ds_label = "BHS" if dataset == "bhs" else "EHVol"
    table_name = f"{dataset}_harmonised"
    pg_name = f"{ds_label} Harmonise Pipeline (Step 2)"

    pg_id = client.ensure_process_group(root_id, pg_name, x, y)

    file_filter = "BHS_Full_chunk_.*\\.csv" if dataset == "bhs" else "EHVol_Full_chunk_.*\\.csv"
    batch_size = "50" if dataset == "bhs" else "100"

    getfile_id = client.ensure_processor(
        pg_id,
        f"GetFile - {ds_label} Harmonise Input",
        "org.apache.nifi.processors.standard.GetFile",
        STANDARD_BUNDLE,
        {
            "Input Directory": "/opt/nifi/data-input",
            "File Filter": file_filter,
            "Recurse Subdirectories": "false",
            "Keep Source File": "false",
        },
        0,
        0,
        scheduling_period="60 sec",
    )

    csv2json_id = client.ensure_processor(
        pg_id,
        f"CsvToJson - {ds_label} Harmonise",
        "BiolinkCsvToJsonProcessor",
        PYTHON_BUNDLE,
        {
            "Dataset Type": dataset,
            "Batch Size": batch_size,
        },
        280,
        0,
    )

    harmonise_id = client.ensure_processor(
        pg_id,
        f"Harmonise - {ds_label}",
        "BiolinkHarmoniseProcessor",
        PYTHON_BUNDLE,
        {
            "Dataset Type": dataset,
            "Schema Path": "/opt/nifi/outputs/master_schema.csv",
        },
        560,
        0,
    )

    json2sql_id = client.ensure_processor(
        pg_id,
        f"JsonToSql - {table_name}",
        "BiolinkJsonToSqlProcessor",
        PYTHON_BUNDLE,
        {
            "Table Name": table_name,
            "Upsert Mode": "false",
            "Conflict Column": "",
        },
        840,
        0,
    )

    putsql_id = client.ensure_processor(
        pg_id,
        f"PutSQL - {table_name}",
        "org.apache.nifi.processors.standard.PutSQL",
        STANDARD_BUNDLE,
        {
            "JDBC Connection Pool": dbcp_id,
            "Auto-Commit": "true",
        },
        1120,
        0,
        auto_terminate=["success", "failure", "retry"],
    )

    client.ensure_connection(pg_id, getfile_id, csv2json_id, ["success"], "GetFile -> CsvToJson")
    client.ensure_connection(pg_id, csv2json_id, harmonise_id, ["success"], "CsvToJson -> Harmonise")
    client.ensure_connection(pg_id, harmonise_id, json2sql_id, ["success"], "Harmonise -> JsonToSql")
    client.ensure_connection(pg_id, json2sql_id, putsql_id, ["success"], "JsonToSql -> PutSQL")

    client.ensure_connection(pg_id, csv2json_id, csv2json_id, ["failure"], "CsvToJson failure loop")
    client.ensure_connection(pg_id, harmonise_id, harmonise_id, ["failure"], "Harmonise failure loop")
    client.ensure_connection(pg_id, json2sql_id, json2sql_id, ["failure"], "JsonToSql failure loop")

    for proc_id in [putsql_id, json2sql_id, harmonise_id, csv2json_id, getfile_id]:
        client.start_processor(proc_id)


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap BioLink Step1+Step2 NiFi graph via REST")
    parser.add_argument("--nifi-url", default="https://nifi:8443", help="NiFi base URL")
    parser.add_argument("--username", default="admin", help="NiFi single-user username")
    parser.add_argument("--password", default="biolink_nifi_secret_123", help="NiFi single-user password")
    parser.add_argument("--wait-timeout", type=int, default=300, help="Max seconds to wait for NiFi readiness")
    args = parser.parse_args()

    client = NiFiClient(args.nifi_url, args.username, args.password)

    try:
        print("[bootstrap] waiting for NiFi...")
        client.wait_ready(timeout_sec=args.wait_timeout)

        root_id = client.root_pg_id()
        print(f"[bootstrap] root pg id: {root_id}")

        dbcp_id = client.ensure_dbcp(root_id, "BioLink PostgreSQL DBCP")
        client.enable_controller_service(dbcp_id)
        print(f"[bootstrap] DBCP ready: {dbcp_id}")

        build_step1_group(client, root_id)
        build_registry_pipeline_group(client, root_id)

        print("[bootstrap] NiFi graph bootstrap complete")
        return 0
    except Exception as exc:
        print(f"[bootstrap] ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
