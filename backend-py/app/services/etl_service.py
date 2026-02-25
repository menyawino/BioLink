import logging
import os
import shutil
import uuid
from pathlib import Path

import requests
from pydantic import BaseModel

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
NIFI_BHS_PROCESSOR_ID = os.getenv("NIFI_BHS_GETFILE_PROCESSOR_ID", "proc-bhs-getfile")
NIFI_EHVOL_PROCESSOR_ID = os.getenv(
    "NIFI_EHVOL_GETFILE_PROCESSOR_ID", "proc-ehvol-getfile"
)
NIFI_VERIFY_SSL = os.getenv("NIFI_VERIFY_SSL", "false").lower() in {
    "1",
    "true",
    "yes",
    "on",
}
NIFI_STAGE_DIR = Path(os.getenv("NIFI_STAGE_DIR", "/app/db"))

BHS_CANONICAL_FILENAME = "BHS_Full.csv"
EHVOL_CANONICAL_FILENAME = "EHVol_Full.csv"


class ETLParams(BaseModel):
    table: str = "ehvol_full"
    schema: str = "public"
    csv: str | None = None
    dataset_name: str | None = None
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


def _resolve_getfile_processor_id(dataset: str, headers: dict[str, str]) -> str:
    env_default = NIFI_BHS_PROCESSOR_ID if dataset == "bhs" else NIFI_EHVOL_PROCESSOR_ID
    if env_default and not env_default.startswith("proc-"):
        return env_default

    try:
        response = requests.get(
            f"{NIFI_API_URL}/flow/process-groups/root",
            headers=headers,
            timeout=NIFI_REQUEST_TIMEOUT,
            verify=NIFI_VERIFY_SSL,
        )
        response.raise_for_status()
        flow = response.json().get("processGroupFlow", {}).get("flow", {})
        processors = flow.get("processors", [])
        dataset_token = "bhs" if dataset == "bhs" else "ehvol"
        for proc in processors:
            component = proc.get("component", {})
            name = (component.get("name") or "").lower()
            if "getfile" in name and dataset_token in name:
                proc_id = component.get("id")
                if proc_id:
                    return proc_id
    except Exception as exc:
        logger.warning(
            "Failed to auto-discover NiFi processor ID for %s: %s", dataset, exc
        )

    return env_default


def _run_once_getfile(processor_id: str, headers: dict[str, str]) -> dict:
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


def trigger_etl_pipeline(params: ETLParams) -> dict:
    dataset = _infer_dataset(params)
    staged_csv = _stage_csv_for_nifi(params.csv, dataset)
    headers = _get_auth_headers()
    processor_id = _resolve_getfile_processor_id(dataset, headers)

    logger.info(
        "Triggering NiFi ETL pipeline dataset=%s processor=%s nifi_api=%s",
        dataset,
        processor_id,
        NIFI_API_URL,
    )

    try:
        run_result = _run_once_getfile(processor_id, headers)
        if not run_result.get("ok"):
            return run_result

        return {
            "ok": True,
            "engine": "nifi",
            "dataset": dataset,
            "processor_id": processor_id,
            "staged_csv": staged_csv,
            "message": "NiFi GetFile processor triggered (RUN_ONCE)",
        }
    except Exception as exc:
        logger.error("Failed to trigger NiFi ETL pipeline: %s", exc)
        return {"ok": False, "error": str(exc)}
