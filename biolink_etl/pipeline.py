#!/usr/bin/env python3
"""NiFi/dbt/OpenMetadata orchestrator + governed protocol handler.

NiFi handles ingestion visually. This service runs dbt, refreshes Superset,
and emits lineage to OpenMetadata.
"""
from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


THIS_DIR = Path(__file__).resolve().parent
ROOT = THIS_DIR.parent
BACKEND = ROOT / "backend-py"

PROTOCOL_VERSION = "1.0"


@dataclass
class PipelineOptions:
    table: str
    schema: str
    csv: str | None = None
    dataset_name: str | None = None
    skip_superset: bool = False
    skip_refresh: bool = False
    dbt_select: str | None = None
    dbt_full_refresh: bool = False
    dbt_vars: dict[str, Any] | None = None


def _add_backend_to_path():
    if str(BACKEND) not in sys.path:
        sys.path.insert(0, str(BACKEND))


def load_settings():
    _add_backend_to_path()
    try:
        from app.config import settings  # type: ignore
        return settings
    except Exception:
        cfg_path = BACKEND / "app" / "config.py"
        spec = importlib.util.spec_from_file_location("app_config", cfg_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore
        return getattr(module, "settings")


def _get_superset_client():
    _add_backend_to_path()
    from app.services.superset_client import SupersetClient  # type: ignore
    return SupersetClient.from_settings()


def _get_superset_db_settings() -> tuple[str, str]:
    env_name = os.getenv("SUPERSET_DATABASE_NAME")
    env_uri = os.getenv("SUPERSET_DATABASE_URI")
    if env_name and env_uri:
        return env_name, env_uri
    settings = load_settings()
    return settings.superset_database_name, settings.superset_database_uri


def _dbt_run(select: str | None, full_refresh: bool, dbt_vars: dict[str, Any] | None) -> dict[str, Any]:
    project_dir = os.getenv("DBT_PROJECT_DIR", str(THIS_DIR / "dbt"))
    profiles_dir = os.getenv("DBT_PROFILES_DIR", project_dir)

    dbt_bin = os.getenv("DBT_BIN")
    if dbt_bin:
        dbt_cmd = [dbt_bin]
    else:
        which_dbt = shutil.which("dbt")
        if which_dbt:
            dbt_cmd = [which_dbt]
        else:
            venv_dbt = ROOT / "venv" / "bin" / "dbt"
            if venv_dbt.exists():
                dbt_cmd = [str(venv_dbt)]
            else:
                venv_python = ROOT / "venv" / "bin" / "python"
                if venv_python.exists():
                    dbt_cmd = [str(venv_python), "-m", "dbt"]
                else:
                    raise FileNotFoundError(
                        "Could not find dbt executable. Install dbt in your environment, activate the venv, or set DBT_BIN."
                    )

    cmd = [*dbt_cmd, "run", "--project-dir", project_dir, "--profiles-dir", profiles_dir]
    if select:
        cmd += ["--select", select]
    if full_refresh:
        cmd.append("--full-refresh")
    if dbt_vars:
        cmd += ["--vars", json.dumps(dbt_vars)]

    env = os.environ.copy()
    if not env.get("DB_HOST"):
        try:
            settings = load_settings()
            parsed = urlparse(settings.database_url)
        except Exception:
            parsed = urlparse(os.getenv("DATABASE_URL", ""))

        if parsed.hostname:
            env.setdefault("DB_HOST", parsed.hostname)
        if parsed.port:
            env.setdefault("DB_PORT", str(parsed.port))
        if parsed.username:
            env.setdefault("DB_USER", parsed.username)
        if parsed.password:
            env.setdefault("DB_PASSWORD", parsed.password)
        if parsed.path and parsed.path.strip("/"):
            env.setdefault("DB_NAME", parsed.path.strip("/"))

    proc = subprocess.run(cmd, text=True, capture_output=True, env=env)
    if proc.returncode != 0:
        raise RuntimeError(f"dbt run failed: {proc.stderr.strip()}")
    return {"stdout": proc.stdout.strip()}


def _sanitize_dataset_name(value: str) -> str:
    cleaned = "".join(ch.lower() if (ch.isalnum() or ch == "_") else "_" for ch in value.strip())
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    cleaned = cleaned.strip("_")
    if not cleaned:
        cleaned = "dataset"
    if cleaned[0].isdigit():
        cleaned = f"d_{cleaned}"
    return cleaned


def _openmetadata_emit(event: dict[str, Any]) -> dict[str, Any]:
    import requests

    base_url = os.getenv("OPENMETADATA_URL")
    token = os.getenv("OPENMETADATA_JWT")
    custom_endpoint = os.getenv("OPENMETADATA_LINEAGE_ENDPOINT")

    if not base_url:
        return {"status": "skipped", "reason": "OPENMETADATA_URL not set"}

    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    endpoint = custom_endpoint or (base_url.rstrip("/") + "/api/v1/lineage")
    resp = requests.post(endpoint, json=event, headers=headers, timeout=30)
    if resp.status_code >= 400:
        return {"status": "error", "code": resp.status_code, "body": resp.text[:400]}
    return {"status": "ok", "response": resp.json() if resp.content else {}}


async def register_superset_alias(table: str, schema: str, alias: str) -> int | None:
    client = _get_superset_client()
    import aiohttp

    async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar(unsafe=True)) as session:
        tokens = await client.bootstrap()
        access_token = tokens["access_token"]
        csrf_token = tokens["csrf_token"]

        db_name, db_uri = _get_superset_db_settings()
        db_id = await client.get_or_create_database(session, access_token, csrf_token, db_name, db_uri)

        # If the alias dataset already exists, return it so callers can refresh it.
        datasets = await client._list_resource(session, access_token, "dataset")
        for d in datasets:
            if d.get("schema") == schema and d.get("table_name") == alias:
                try:
                    dataset_id = int(d["id"])
                except Exception:
                    break

                # If the dataset is virtual but we're trying to publish a real table/view
                # with the same name, recreate it as a physical dataset so Superset can
                # introspect columns correctly.
                try:
                    details = await client._request(
                        session,
                        "GET",
                        f"/api/v1/dataset/{dataset_id}",
                        access_token,
                        csrf_token,
                    )
                    kind = (details.get("result") or {}).get("kind") if isinstance(details, dict) else None
                except Exception:
                    kind = None

                if kind == "virtual" and alias == table:
                    try:
                        await client._request(
                            session,
                            "DELETE",
                            f"/api/v1/dataset/{dataset_id}",
                            access_token,
                            csrf_token,
                        )
                    except Exception:
                        # If we can't delete, fall back to updating SQL and returning the existing dataset.
                        kind = "virtual"
                    else:
                        try:
                            created = await client._request(
                                session,
                                "POST",
                                "/api/v1/dataset/",
                                access_token,
                                csrf_token,
                                json_body={"database": db_id, "schema": schema, "table_name": alias},
                            )
                            new_id = client._extract_id(created)
                            if new_id is not None:
                                return int(new_id)
                        except Exception:
                            pass

                # If a dataset with this name already exists, ensure it points at the intended
                # underlying table/view. This handles the common case where an earlier run
                # created a virtual dataset with stale SQL.
                try:
                    put_path = f"/api/v1/dataset/{dataset_id}"
                    await client._request(
                        session,
                        "PUT",
                        put_path,
                        access_token,
                        csrf_token,
                        json_body={"sql": f"SELECT * FROM {schema}.{table}"},
                    )
                except Exception:
                    pass

                return dataset_id

        variants = [
            {"database": db_id, "schema": schema, "table_name": table, "dataset_name": alias},
            {"database": db_id, "schema": schema, "table_name": table, "name": alias},
            {"database": db_id, "schema": schema, "table_name": alias},
            {"database": db_id, "schema": None, "table_name": alias, "sql": f"SELECT * FROM {schema}.{table}"},
        ]

        for payload in variants:
            try:
                created = await client._request(session, "POST", "/api/v1/dataset/", access_token, csrf_token, json_body=payload)
                dataset_id = client._extract_id(created)
                if dataset_id is not None:
                    return dataset_id
            except Exception:
                continue

    return None


async def refresh_superset_dataset(table: str, schema: str, alias: str | None = None) -> list[int]:
    client = _get_superset_client()
    import aiohttp

    refreshed = []
    async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar(unsafe=True)) as session:
        tokens = await client.bootstrap()
        access_token = tokens["access_token"]
        csrf_token = tokens.get("csrf_token")

        datasets = await client._list_resource(session, access_token, "dataset")
        matches = []
        for d in datasets:
            if alias and d.get("table_name") == alias:
                matches.append(d)
            elif d.get("table_name") == table and d.get("schema") == schema:
                matches.append(d)

        for d in matches:
            dataset_id = int(d["id"])
            try:
                path = f"/api/v1/dataset/{dataset_id}/refresh"
                await client._request(session, "POST", path, access_token, csrf_token, json_body={})
                refreshed.append(dataset_id)
                continue
            except Exception:
                pass

            try:
                put_path = f"/api/v1/dataset/{dataset_id}"
                existing_sql = d.get("sql")
                payload = {"sql": existing_sql or f"SELECT * FROM {schema}.{table}"}
                await client._request(session, "PUT", put_path, access_token, csrf_token, json_body=payload)
                refreshed.append(dataset_id)
            except Exception:
                continue

    return refreshed


def run_pipeline(opts: PipelineOptions) -> dict[str, Any]:
    out: dict[str, Any] = {}

    dataset_name = opts.dataset_name
    if not dataset_name and opts.csv:
        dataset_name = _sanitize_dataset_name(Path(opts.csv).name.rsplit(".", 1)[0])
    dataset_name = dataset_name or opts.table

    if opts.dbt_select:
        out["dbt"] = _dbt_run(opts.dbt_select, opts.dbt_full_refresh, opts.dbt_vars)

    if not opts.skip_superset:
        dataset_id = asyncio.run(register_superset_alias(opts.table, opts.schema, dataset_name))
        out["superset_dataset_id"] = dataset_id

    if not opts.skip_refresh and not opts.skip_superset:
        refreshed = asyncio.run(refresh_superset_dataset(opts.table, opts.schema, dataset_name))
        out["superset_refreshed_ids"] = refreshed

    om_event = {
        "pipeline": "biolink_etl",
        "table": f"{opts.schema}.{opts.table}",
        "result": out,
    }
    out["openmetadata"] = _openmetadata_emit(om_event)

    return out


def _protocol_error(request_id: str | None, message: str) -> dict[str, Any]:
    return {
        "version": PROTOCOL_VERSION,
        "request_id": request_id,
        "ok": False,
        "error": {"message": message},
    }


def handle_protocol_request(payload: dict[str, Any]) -> dict[str, Any]:
    version = payload.get("version")
    action = payload.get("action")
    request_id = payload.get("request_id")

    if version != PROTOCOL_VERSION:
        return _protocol_error(request_id, f"Unsupported protocol version: {version}")

    if action == "health":
        return {"version": PROTOCOL_VERSION, "request_id": request_id, "ok": True, "result": {"status": "ok"}}

    if action != "run_pipeline":
        return _protocol_error(request_id, f"Unsupported action: {action}")

    params = payload.get("payload") or {}
    try:
        opts = PipelineOptions(
            table=params["table"],
            schema=params.get("schema", "public"),
            skip_superset=bool(params.get("skip_superset", False)),
            skip_refresh=bool(params.get("skip_refresh", False)),
            dbt_select=params.get("dbt_select"),
            dbt_full_refresh=bool(params.get("dbt_full_refresh", False)),
            dbt_vars=params.get("dbt_vars"),
        )
    except KeyError as e:
        return _protocol_error(request_id, f"Missing required field: {e}")

    try:
        result = run_pipeline(opts)
        return {"version": PROTOCOL_VERSION, "request_id": request_id, "ok": True, "result": result}
    except Exception as e:
        return _protocol_error(request_id, str(e))


def run_protocol_stdio(loop: bool = False):
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        line = line.strip()
        if not line:
            if loop:
                continue
            break
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as e:
            response = _protocol_error(None, f"Invalid JSON: {e}")
            print(json.dumps(response))
            if not loop:
                break
            continue

        response = handle_protocol_request(payload)
        print(json.dumps(response))
        if not loop:
            break


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="BioLink ETL orchestrator")
    parser.add_argument("--table", help="Destination table name")
    parser.add_argument("--schema", default="public", help="Destination schema")
    parser.add_argument("--csv", help="Source CSV path; used to derive the published dataset name")
    parser.add_argument("--dataset-name", help="Override the published dataset name (defaults to CSV stem or --table)")
    parser.add_argument("--skip-superset", action="store_true", help="Skip Superset registration/refresh")
    parser.add_argument("--skip-refresh", action="store_true", help="Skip Superset metadata refresh")
    parser.add_argument("--dbt-select", help="dbt select string (models/tags)")
    parser.add_argument("--dbt-full-refresh", action="store_true", help="Run dbt with --full-refresh")
    parser.add_argument("--dbt-vars", help="JSON string of dbt vars")
    parser.add_argument("--protocol-stdio", action="store_true", help="Read one request from stdin and respond on stdout")
    parser.add_argument("--protocol-loop", action="store_true", help="Read requests in a loop from stdin")
    parser.add_argument("--protocol-http", action="store_true", help="Serve protocol requests over HTTP")
    parser.add_argument("--host", default="0.0.0.0", help="HTTP host for --protocol-http")
    parser.add_argument("--port", type=int, default=8090, help="HTTP port for --protocol-http")
    return parser.parse_args()


def main():
    args = parse_args()

    if args.protocol_http:
        run_protocol_http(args.host, args.port)
        return

    if args.protocol_stdio or args.protocol_loop:
        run_protocol_stdio(loop=args.protocol_loop)
        return

    if not args.table:
        print("Error: --table is required unless using --protocol-stdio")
        sys.exit(2)

    if not args.dbt_select:
        print("Warning: --dbt-select not provided; skipping dbt run.")

    opts = PipelineOptions(
        table=args.table,
        schema=args.schema,
        csv=args.csv,
        dataset_name=args.dataset_name,
        skip_superset=args.skip_superset,
        skip_refresh=args.skip_refresh,
        dbt_select=args.dbt_select,
        dbt_full_refresh=args.dbt_full_refresh,
        dbt_vars=json.loads(args.dbt_vars) if args.dbt_vars else None,
    )

    result = run_pipeline(opts)
    print(json.dumps({"ok": True, "result": result}, indent=2))


def run_protocol_http(host: str, port: int):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, code: int, payload: dict[str, Any]):
            body = json.dumps(payload).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == "/health":
                self._send(200, {"ok": True})
                return
            self._send(404, {"ok": False, "error": "not_found"})

        def do_POST(self):
            if self.path != "/protocol":
                self._send(404, {"ok": False, "error": "not_found"})
                return
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8")
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError as e:
                self._send(400, _protocol_error(None, f"Invalid JSON: {e}"))
                return
            response = handle_protocol_request(payload)
            self._send(200, response)

    server = HTTPServer((host, port), Handler)
    print(f"ETL protocol HTTP server listening on {host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
