import logging
import os
import shutil
import time
import uuid
from pathlib import Path

import requests
from pydantic import BaseModel, ConfigDict, Field
from app.database import engine
from app.services import registry_loader

logger = logging.getLogger(__name__)

NIFI_API_URL = os.getenv(
    "ETL_SERVICE_URL", os.getenv("NIFI_API_URL", "https://nifi:8443/nifi-api")
).rstrip("/")
NIFI_USERNAME = os.getenv(
    "NIFI_USERNAME", os.getenv("SINGLE_USER_CREDENTIALS_USERNAME", "admin")
)
NIFI_PASSWORD = os.getenv(
    "NIFI_PASSWORD",
    os.getenv("SINGLE_USER_CREDENTIALS_PASSWORD", "biolink_nifi_secret_123"),
)
NIFI_REQUEST_TIMEOUT = int(os.getenv("NIFI_REQUEST_TIMEOUT", "60"))
NIFI_SCRIPTED_PIPELINE_PROCESSOR_ID = os.getenv(
    "NIFI_SCRIPTED_PIPELINE_PROCESSOR_ID", "proc-registry-scripted-pipeline"
)
NIFI_VERIFY_SSL = os.getenv("NIFI_VERIFY_SSL", "false").lower() in {
    "1",
    "true",
    "yes",
    "on",
}
NIFI_STAGE_DIR = Path(os.getenv("NIFI_STAGE_DIR", "/app/db"))
NIFI_TRIGGER_RUN_TOKEN_PROPERTY = os.getenv(
    "NIFI_TRIGGER_RUN_TOKEN_PROPERTY", "Trigger Run Token"
)
NIFI_TRIGGER_DATASETS_PROPERTY = os.getenv(
    "NIFI_TRIGGER_DATASETS_PROPERTY", "Triggered Datasets"
)

BHS_CANONICAL_FILENAME = "BHS_Full.csv"
EHVOL_CANONICAL_FILENAME = "EHVol_Full.csv"


class ETLParams(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    table: str = "ehvol_full"
    schema_name: str = Field(default="public", alias="schema")
    csv: str | None = None
    dataset_name: str | None = None
    datasets: list[str] | None = None
    dbt_select: str | None = None
    skip_superset: bool = False


def _nifi_base_url() -> str:
    return NIFI_API_URL[:-9] if NIFI_API_URL.endswith("/nifi-api") else NIFI_API_URL


def _infer_dataset(params: ETLParams) -> str:
    candidates = [
        params.dataset_name,
        params.table,
        params.csv,
    ]
    haystack = " ".join([item for item in candidates if item]).lower()
    if "bhs" in haystack or "biobank" in haystack:
        return "bhs"
    return "ehvol"


def _requested_datasets(params: ETLParams) -> list[str]:
    normalized: list[str] = []
    for item in params.datasets or []:
        dataset = str(item).strip().lower()
        if dataset in {"bhs", "ehvol"} and dataset not in normalized:
            normalized.append(dataset)

    if normalized:
        return normalized

    inferred = _infer_dataset(params)
    return [inferred] if params.dataset_name else ["ehvol", "bhs"]


def _stage_csv_for_nifi(csv_path: str | None, dataset: str) -> str | None:
    if not csv_path:
        return None

    source = Path(csv_path)
    if not source.exists() or not source.is_file():
        logger.warning("CSV path does not exist or is not a file: %s", csv_path)
        return csv_path

    NIFI_STAGE_DIR.mkdir(parents=True, exist_ok=True)
    target_name = (
        BHS_CANONICAL_FILENAME if dataset == "bhs" else EHVOL_CANONICAL_FILENAME
    )
    staged_path = NIFI_STAGE_DIR / target_name
    shutil.copy2(source, staged_path)
    return str(staged_path)


def _get_auth_headers() -> dict[str, str]:
    # Use the configured API base so token endpoint is correct (e.g. /nifi-api/access/token)
    token_url = f"{NIFI_API_URL}/access/token"
    try:
        response = requests.post(
            token_url,
            data={"username": NIFI_USERNAME, "password": NIFI_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=NIFI_REQUEST_TIMEOUT,
            verify=NIFI_VERIFY_SSL,
        )
        response.raise_for_status()
        token = response.text.strip()
        if token:
            return {"Authorization": f"Bearer {token}"}
    except Exception as exc:
        logger.warning(
            "NiFi token request failed; trying unauthenticated API call: %s", exc
        )
    return {}


def _discover_processor_in_group(group_id: str, headers: dict[str, str]) -> str | None:
    response = requests.get(
        f"{NIFI_API_URL}/flow/process-groups/{group_id}",
        headers=headers,
        timeout=NIFI_REQUEST_TIMEOUT,
        verify=NIFI_VERIFY_SSL,
    )
    response.raise_for_status()
    flow = response.json().get("processGroupFlow", {}).get("flow", {})

    for proc in flow.get("processors", []):
        component = proc.get("component", {})
        name = (component.get("name") or "").lower()
        if "scripted registry pipeline" in name or "run scripted registry pipeline" in name:
            proc_id = component.get("id")
            if proc_id:
                return proc_id

    for child in flow.get("processGroups", []):
        child_id = child.get("component", {}).get("id")
        if not child_id:
            continue
        discovered = _discover_processor_in_group(child_id, headers)
        if discovered:
            return discovered

    return None


def _resolve_pipeline_processor_id(headers: dict[str, str]) -> str:
    env_default = NIFI_SCRIPTED_PIPELINE_PROCESSOR_ID
    if env_default and not env_default.startswith("proc-"):
        return env_default

    try:
        discovered = _discover_processor_in_group("root", headers)
        if discovered:
            return discovered
    except Exception as exc:
        logger.warning(
            "Failed to auto-discover NiFi scripted pipeline processor: %s", exc
        )

    return env_default


def _run_once_processor(processor_id: str, headers: dict[str, str]) -> dict:
    processor_response = requests.get(
        f"{NIFI_API_URL}/processors/{processor_id}",
        headers=headers,
        timeout=NIFI_REQUEST_TIMEOUT,
        verify=NIFI_VERIFY_SSL,
    )
    if processor_response.status_code != 200:
        return {
            "ok": False,
            "error": f"HTTP {processor_response.status_code}: {processor_response.text}",
        }

    revision_version = (
        processor_response.json().get("revision", {}).get("version", 0)
    )

    url = f"{NIFI_API_URL}/processors/{processor_id}/run-status"
    payload = {
        "revision": {"version": revision_version, "clientId": str(uuid.uuid4())},
        "state": "RUN_ONCE",
        "disconnectedNodeAcknowledged": True,
    }
    response = requests.put(
        url,
        json=payload,
        headers=headers,
        timeout=NIFI_REQUEST_TIMEOUT,
        verify=NIFI_VERIFY_SSL,
    )
    if response.status_code == 409 and "Current state is RUNNING" in response.text:
        return {"ok": True, "status_code": response.status_code, "already_running": True}
    if response.status_code not in (200, 202):
        return {"ok": False, "error": f"HTTP {response.status_code}: {response.text}"}
    return {"ok": True, "status_code": response.status_code}


def _configure_processor_run_context(
    processor_id: str,
    headers: dict[str, str],
    *,
    trigger_token: str,
    requested_datasets: list[str],
) -> dict:
    processor_response = requests.get(
        f"{NIFI_API_URL}/processors/{processor_id}",
        headers=headers,
        timeout=NIFI_REQUEST_TIMEOUT,
        verify=NIFI_VERIFY_SSL,
    )
    if processor_response.status_code != 200:
        return {
            "ok": False,
            "error": f"HTTP {processor_response.status_code}: {processor_response.text}",
        }

    entity = processor_response.json()
    revision_version = entity.get("revision", {}).get("version", 0)
    component = entity.get("component", {})
    config = component.get("config", {}) or {}
    properties = dict(config.get("properties") or {})
    properties[NIFI_TRIGGER_RUN_TOKEN_PROPERTY] = trigger_token
    properties[NIFI_TRIGGER_DATASETS_PROPERTY] = ",".join(requested_datasets)

    update_payload = {
        "revision": {"version": revision_version, "clientId": str(uuid.uuid4())},
        "component": {
            "id": processor_id,
            "config": {
                "properties": properties,
            },
        },
        "disconnectedNodeAcknowledged": True,
    }
    update_response = requests.put(
        f"{NIFI_API_URL}/processors/{processor_id}",
        json=update_payload,
        headers=headers,
        timeout=NIFI_REQUEST_TIMEOUT,
        verify=NIFI_VERIFY_SSL,
    )
    if update_response.status_code not in (200, 201):
        return {
            "ok": False,
            "error": f"HTTP {update_response.status_code}: {update_response.text}",
        }
    return {"ok": True, "trigger_token": trigger_token}


def trigger_etl_pipeline(params: ETLParams) -> dict:
    dataset = _infer_dataset(params)
    requested_datasets = _requested_datasets(params)
    expected_tables = ["unified_registry"] + [
        f"{item}_participants" for item in requested_datasets
    ]
    staged_csv = _stage_csv_for_nifi(params.csv, dataset)
    headers = _get_auth_headers()
    processor_id = _resolve_pipeline_processor_id(headers)
    baseline_counts = registry_loader.get_registry_counts(engine)
    baseline_run_id = registry_loader.get_latest_registry_run_id(engine)
    trigger_token = str(uuid.uuid4())

    logger.info(
        "Triggering NiFi script-aligned ETL pipeline dataset=%s processor=%s nifi_api=%s",
        dataset,
        processor_id,
        NIFI_API_URL,
    )

    try:
        configure_result = _configure_processor_run_context(
            processor_id,
            headers,
            trigger_token=trigger_token,
            requested_datasets=requested_datasets,
        )
        if not configure_result.get("ok"):
            return configure_result

        run_result = _run_once_processor(processor_id, headers)
        if not run_result.get("ok"):
            return run_result

        verification = registry_loader.wait_for_registry_repopulation(
            engine,
            expected_tables=expected_tables,
            baseline_counts=baseline_counts,
            baseline_run_id=baseline_run_id,
            trigger_token=trigger_token,
        )
        if verification.get("verified"):
            return {
                "ok": True,
                "engine": "nifi",
                "mode": "script-aligned",
                "dataset": dataset,
                "datasets_requested": requested_datasets,
                "processor_id": processor_id,
                "trigger_token": trigger_token,
                "staged_csv": staged_csv,
                "verified": True,
                "verification_method": "nifi",
                "counts": verification.get("counts"),
                "run_id": verification.get("run_id"),
                "message": "NiFi script-aligned registry pipeline triggered and verified",
            }

        fallback = registry_loader.ensure_registry_snapshot_loaded(
            engine,
            reason="etl-fallback",
            force=True,
        )
        fallback_counts = fallback.get("counts") or {}
        if fallback.get("ok") and all(
            int(fallback_counts.get(table_name, 0)) > 0 for table_name in expected_tables
        ):
            return {
                "ok": True,
                "engine": "nifi",
                "mode": "script-aligned",
                "dataset": dataset,
                "datasets_requested": requested_datasets,
                "processor_id": processor_id,
                "trigger_token": trigger_token,
                "staged_csv": staged_csv,
                "verified": True,
                "verification_method": "snapshot-fallback",
                "counts": fallback_counts,
                "run_id": fallback.get("run_id"),
                "message": "NiFi trigger accepted; backend snapshot fallback restored registry tables",
            }

        return {
            "ok": False,
            "engine": "nifi",
            "mode": "script-aligned",
            "dataset": dataset,
            "datasets_requested": requested_datasets,
            "processor_id": processor_id,
            "trigger_token": trigger_token,
            "staged_csv": staged_csv,
            "verified": False,
            "counts": verification.get("counts"),
            "error": verification.get("error") or "NiFi accepted RUN_ONCE but registry tables were not repopulated and snapshot fallback failed",
        }
    except Exception as exc:
        logger.error("Failed to trigger NiFi ETL pipeline: %s", exc)
        return {"ok": False, "error": str(exc)}
