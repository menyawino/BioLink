#!/usr/bin/env python3
"""
BioLink NiFi ETL Pipeline Setup
================================
Creates the complete NiFi flow for BHS + EHVol dataset ingestion via REST API.
Uses NiFi 2.x REST API to:
1. Create DBCP controller service
2. Create BHS pipeline processors + connections
3. Create EHVol pipeline processors + connections
4. Enable controller services
5. Start all processors

Usage:
    python3 nifi/scripts/setup_nifi_pipeline.py [--nifi-url http://localhost:8443]
"""
import argparse
import json
import sys
import time
import requests
from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

NIFI_URL = "https://localhost:8443"
AUTH_TOKEN = None

NIFI_USERNAME = "admin"
NIFI_PASSWORD = "biolink_nifi_secret_123"


def authenticate():
    """Obtain a Bearer token from NiFi single-user auth."""
    global AUTH_TOKEN
    url = f"{NIFI_URL}/nifi-api/access/token"
    resp = requests.post(
        url,
        data={"username": NIFI_USERNAME, "password": NIFI_PASSWORD},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        verify=False,
        timeout=15,
    )
    if resp.status_code == 201:
        AUTH_TOKEN = resp.text.strip()
        print(f"  Authenticated as {NIFI_USERNAME}")
        return True
    print(f"  ERROR: Auth failed ({resp.status_code}): {resp.text[:200]}")
    return False


def api(method, path, body=None, params=None):
    """Make a NiFi REST API call."""
    url = f"{NIFI_URL}/nifi-api{path}"
    kwargs = {"verify": False, "timeout": 30}
    headers = {}
    if AUTH_TOKEN:
        headers["Authorization"] = f"Bearer {AUTH_TOKEN}"
    if body:
        kwargs["json"] = body
        headers["Content-Type"] = "application/json"
    if headers:
        kwargs["headers"] = headers
    if params:
        kwargs["params"] = params
    resp = getattr(requests, method)(url, **kwargs)
    if resp.status_code >= 400:
        print(f"  ERROR {resp.status_code}: {method.upper()} {path}")
        print(f"  Response: {resp.text[:500]}")
        return None
    try:
        return resp.json()
    except Exception:
        return resp.text


def wait_for_nifi(max_wait=300):
    """Wait for NiFi to be ready and authenticate."""
    print("Waiting for NiFi to start...")
    start = time.time()
    while time.time() - start < max_wait:
        try:
            r = requests.get(f"{NIFI_URL}/nifi-api/system-diagnostics", verify=False, timeout=5)
            if r.status_code in (200, 401, 403):
                print("  NiFi is responding!")
                if authenticate():
                    # Verify access
                    r2 = requests.get(
                        f"{NIFI_URL}/nifi-api/system-diagnostics",
                        headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
                        verify=False, timeout=5,
                    )
                    if r2.status_code == 200:
                        print("  NiFi is ready and authenticated!")
                        return True
                    print(f"  Auth verification returned {r2.status_code}, retrying...")
        except Exception:
            pass
        time.sleep(5)
        elapsed = int(time.time() - start)
        print(f"  Waiting... ({elapsed}s / {max_wait}s)")
    print("  ERROR: NiFi did not become ready in time.")
    return False


def get_root_pg_id():
    """Get the root process group ID."""
    data = api("get", "/flow/process-groups/root")
    if data:
        return data["processGroupFlow"]["id"]
    return None


def get_root_revision():
    """Get the root PG revision."""
    data = api("get", "/process-groups/root")
    if data:
        return data["revision"]
    return {"version": 0}


def create_controller_service(pg_id, name, svc_type, bundle, properties):
    """Create a controller service in a process group."""
    body = {
        "revision": {"version": 0},
        "component": {
            "name": name,
            "type": svc_type,
            "bundle": bundle,
            "properties": properties,
        },
    }
    result = api("post", f"/process-groups/{pg_id}/controller-services", body)
    if result:
        cs_id = result["id"]
        print(f"  Created controller service: {name} ({cs_id})")
        return cs_id
    return None


def enable_controller_service(cs_id):
    """Enable a controller service."""
    # Get current revision
    cs = api("get", f"/controller-services/{cs_id}")
    if not cs:
        return False
    rev = cs["revision"]
    body = {
        "revision": rev,
        "state": "ENABLED",
    }
    result = api("put", f"/controller-services/{cs_id}/run-status", body)
    if result:
        print(f"  Enabled controller service: {cs_id}")
        return True
    return False


def create_processor(pg_id, name, proc_type, bundle, properties, position, auto_terminate=None, scheduling_period="0 sec"):
    """Create a processor in a process group."""
    config = {
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
            "position": position,
        },
    }
    result = api("post", f"/process-groups/{pg_id}/processors", body)
    if result:
        proc_id = result["id"]
        print(f"  Created processor: {name} ({proc_id})")
        return proc_id
    return None


def create_connection(pg_id, source_id, dest_id, relationships, name=""):
    """Create a connection between two processors."""
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
    result = api("post", f"/process-groups/{pg_id}/connections", body)
    if result:
        conn_id = result["id"]
        print(f"  Created connection: {name or 'unnamed'} ({conn_id})")
        return conn_id
    return None


def create_funnel(pg_id, position):
    """Create a funnel for dead letter routing."""
    body = {
        "revision": {"version": 0},
        "component": {
            "position": position,
        },
    }
    result = api("post", f"/process-groups/{pg_id}/funnels", body)
    if result:
        return result["id"]
    return None


def start_processor(proc_id):
    """Start a processor."""
    proc = api("get", f"/processors/{proc_id}")
    if not proc:
        return False
    rev = proc["revision"]
    body = {
        "revision": rev,
        "state": "RUNNING",
    }
    result = api("put", f"/processors/{proc_id}/run-status", body)
    return result is not None


def create_process_group(parent_id, name, position):
    """Create a process group."""
    body = {
        "revision": {"version": 0},
        "component": {
            "name": name,
            "position": position,
        },
    }
    result = api("post", f"/process-groups/{parent_id}/process-groups", body)
    if result:
        pg_id = result["id"]
        print(f"  Created process group: {name} ({pg_id})")
        return pg_id
    return None


# ======================================================================
# Bundle references
# ======================================================================
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


def build_dataset_pipeline(pg_id, dataset, dbcp_id, x_offset=0):
    """Build a complete ETL pipeline for one dataset (BHS or EHVol)."""
    ds = dataset.upper()
    file_filter = f"{ds}_Full_chunk_.*\\.csv" if dataset == "bhs" else "EHVol_Full_chunk_.*\\.csv"
    table_name = f"{dataset}_participants"
    conflict_column = "record_id" if dataset == "bhs" else "dna_id"

    print(f"\n--- Building {ds} Pipeline ---")

    # 1. GetFile
    getfile_id = create_processor(
        pg_id,
        f"GetFile - {ds} CSV",
        "org.apache.nifi.processors.standard.GetFile",
        STANDARD_BUNDLE,
        {
            "Input Directory": "/opt/nifi/data-input",
            "File Filter": file_filter,
            "Keep Source File": "false",
            "Recurse Subdirectories": "false",
        },
        {"x": x_offset, "y": 0},
        scheduling_period="60 sec",
    )

    # 2. CSV to JSON (Python processor)
    csv2json_id = create_processor(
        pg_id,
        f"CSV to JSON ({ds})",
        "BiolinkCsvToJsonProcessor",
        PYTHON_BUNDLE,
        {
            "Dataset Type": dataset,
            "Batch Size": "100",
        },
        {"x": x_offset, "y": 220},
        auto_terminate=["failure"],
    )

    # 3. Full-width schema standardizer (Python processor)
    standardizer_id = create_processor(
        pg_id,
        f"SchemaStandardizer ({ds})",
        "BiolinkSchemaStandardizerProcessor",
        PYTHON_BUNDLE,
        {
            "Dataset Type": dataset,
            "Include Raw JSON": "false",
        },
        {"x": x_offset, "y": 440},
        auto_terminate=["failure"],
    )

    # 4. Data Quality (Python processor)
    quality_id = create_processor(
        pg_id,
        f"Quality Check ({ds})",
        "BiolinkDataQualityProcessor",
        PYTHON_BUNDLE,
        {"Minimum Quality Score": "0.3"},
        {"x": x_offset, "y": 660},
        auto_terminate=["failure"],
    )

    # 5. JSON to SQL (Python processor)
    json2sql_id = create_processor(
        pg_id,
        f"JSON to SQL ({ds})",
        "BiolinkJsonToSqlProcessor",
        PYTHON_BUNDLE,
        {
            "Table Name": table_name,
            "Upsert Mode": "true",
            "Conflict Column": conflict_column,
        },
        {"x": x_offset, "y": 880},
        auto_terminate=["failure"],
    )

    # 6. PutSQL
    putsql_id = create_processor(
        pg_id,
        f"PutSQL ({ds} → Postgres)",
        "org.apache.nifi.processors.standard.PutSQL",
        STANDARD_BUNDLE,
        {
            "JDBC Connection Pool": dbcp_id,
            "Support Fragmented Transactions": "false",
        },
        {"x": x_offset, "y": 1100},
        auto_terminate=["success", "retry", "failure"],
    )

    # Wire connections
    if getfile_id and csv2json_id:
        create_connection(pg_id, getfile_id, csv2json_id, ["success"], f"GetFile → CSV2JSON ({ds})")
    if csv2json_id and standardizer_id:
        create_connection(pg_id, csv2json_id, standardizer_id, ["success"], f"CSV2JSON → Standardizer ({ds})")
    if standardizer_id and quality_id:
        create_connection(pg_id, standardizer_id, quality_id, ["success"], f"Standardizer → Quality ({ds})")
    if quality_id and json2sql_id:
        create_connection(pg_id, quality_id, json2sql_id, ["success"], f"Quality → JSON2SQL ({ds})")
    if json2sql_id and putsql_id:
        create_connection(pg_id, json2sql_id, putsql_id, ["success"], f"JSON2SQL → PutSQL ({ds})")

    processor_ids = [p for p in [getfile_id, csv2json_id, standardizer_id, quality_id, json2sql_id, putsql_id] if p]
    return processor_ids


def main():
    parser = argparse.ArgumentParser(description="Setup BioLink NiFi ETL Pipeline")
    parser.add_argument("--nifi-url", default="https://localhost:8443", help="NiFi base URL")
    parser.add_argument("--skip-wait", action="store_true", help="Skip waiting for NiFi startup")
    parser.add_argument("--start", action="store_true", default=True, help="Start processors after creation")
    parser.add_argument("--no-start", action="store_true", help="Do not start processors")
    args = parser.parse_args()

    global NIFI_URL
    NIFI_URL = args.nifi_url

    if not args.skip_wait:
        if not wait_for_nifi():
            sys.exit(1)

    # Get root process group
    root_id = get_root_pg_id()
    if not root_id:
        print("ERROR: Cannot get root process group ID")
        sys.exit(1)
    print(f"Root process group: {root_id}")

    # Create DBCP controller service at root level
    print("\n=== Creating Controller Services ===")
    dbcp_id = create_controller_service(
        root_id,
        "BioLink PostgreSQL DBCP",
        "org.apache.nifi.dbcp.DBCPConnectionPool",
        DBCP_BUNDLE,
        {
            "Database Connection URL": "jdbc:postgresql://postgres:5432/biolink",
            "Database Driver Class Name": "org.postgresql.Driver",
            "Database Driver Locations": "/opt/nifi/jdbc/postgresql-42.7.3.jar",
            "Database User": "biolink",
            "Password": "biolink_secret",
            "Max Wait Time": "500 millis",
            "Max Total Connections": "8",
        },
    )

    if not dbcp_id:
        print("ERROR: Failed to create DBCP controller service")
        sys.exit(1)

    # Enable DBCP
    time.sleep(2)
    enable_controller_service(dbcp_id)
    time.sleep(3)

    # Build BHS pipeline
    print("\n=== Building BHS Pipeline ===")
    bhs_processors = build_dataset_pipeline(root_id, "bhs", dbcp_id, x_offset=0)

    # Build EHVol pipeline
    print("\n=== Building EHVol Pipeline ===")
    ehvol_processors = build_dataset_pipeline(root_id, "ehvol", dbcp_id, x_offset=600)

    all_processors = bhs_processors + ehvol_processors

    # Start processors
    if not args.no_start:
        print("\n=== Starting Processors ===")
        # Start in reverse order (downstream first) to avoid backpressure issues
        for proc_id in reversed(all_processors):
            if start_processor(proc_id):
                print(f"  Started: {proc_id}")
            else:
                print(f"  WARN: Could not start {proc_id}")
            time.sleep(1)

    print("\n=== NiFi ETL Pipeline Setup Complete ===")
    print(f"  BHS processors: {len(bhs_processors)}")
    print(f"  EHVol processors: {len(ehvol_processors)}")
    print(f"  NiFi UI: {NIFI_URL}/nifi/")
    print(f"  DBCP service ID: {dbcp_id}")


if __name__ == "__main__":
    main()
