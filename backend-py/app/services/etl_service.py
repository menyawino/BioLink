import logging
import os
import shutil
import time
import uuid
import asyncio
from collections.abc import Callable
from pathlib import Path

import aiohttp
import requests
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import text
from app.database import engine
from app.config import settings
from app.services import registry_loader
from app.services.superset_client import SupersetClient

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
LINEAGE_STAGE_ORDER = ["ingest", "profile", "unify", "quality", "publish"]
SUPERSET_MANAGED_PIPELINE_TABLES = ("unified_registry", "comparability_report")
SUPERSET_MANAGED_PARTICIPANT_DATASETS = ("ehvol", "bhs")


class ETLParams(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    table: str = "ehvol_full"
    schema_name: str = Field(default="public", alias="schema")
    csv: str | None = None
    dataset_name: str | None = None
    datasets: list[str] | None = None
    dbt_select: str | None = None
    skip_superset: bool = False


def _utcnow_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z", time.gmtime())


def _workspace_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _artifact_exists(relative_path: str) -> bool:
    candidates = [
        Path("/app") / relative_path,
        _workspace_root() / relative_path,
        Path.cwd() / relative_path,
    ]
    return any(candidate.exists() for candidate in candidates)


def _build_stage_manifest(
    key: str,
    status: str,
    source: str,
    message: str,
    *,
    details: dict[str, object] | None = None,
) -> dict[str, object]:
    manifest: dict[str, object] = {
        "key": key,
        "status": status,
        "source": source,
        "message": message,
        "observedAt": _utcnow_iso(),
    }
    if details:
        manifest["details"] = details
    return manifest


def _upsert_lineage_stage(
    lineage: list[dict[str, object]],
    stage: dict[str, object],
) -> list[dict[str, object]]:
    by_key = {
        str(item.get("key")): item
        for item in lineage
        if isinstance(item, dict) and item.get("key")
    }
    by_key[str(stage.get("key"))] = stage
    return [by_key[key] for key in LINEAGE_STAGE_ORDER if key in by_key]


def _normalized_identifier(value: object | None) -> str:
    return str(value or "").strip().lower()


def _ordered_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if not value:
            continue
        normalized = _normalized_identifier(value)
        if normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(value)
    return ordered


def _coerce_int(value: object | None) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.isdigit():
            return int(stripped)
    return None


def _superset_managed_database_names() -> set[str]:
    names = {_normalized_identifier(settings.superset_database_name)}
    for raw_name in str(getattr(settings, "superset_legacy_database_names", "")).split(","):
        normalized = _normalized_identifier(raw_name)
        if normalized:
            names.add(normalized)
    return names


def _superset_target_tables(requested_datasets: list[str]) -> list[str]:
    targets = [settings.superset_default_table, *SUPERSET_MANAGED_PIPELINE_TABLES]
    targets.extend(
        f"{dataset}_participants"
        for dataset in [*requested_datasets, *SUPERSET_MANAGED_PARTICIPANT_DATASETS]
        if dataset
    )

    return _ordered_unique(targets)


def _existing_superset_target_tables(
    schema_name: str,
    table_names: list[str],
) -> list[str]:
    if not table_names:
        return []

    with engine.connect() as conn:
        existing_table_names = {
            str(name)
            for name in conn.execute(
                text(
                    """
                    SELECT LOWER(table_name)
                    FROM information_schema.tables
                    WHERE table_schema = :schema_name
                    """
                ),
                {"schema_name": schema_name},
            ).scalars()
            if name
        }

    return [
        table_name
        for table_name in table_names
        if _normalized_identifier(table_name) in existing_table_names
    ]


def _superset_dataset_matches_database(
    item: dict[str, object],
    *,
    database_id: int,
    database_names: set[str],
) -> bool:
    candidate_ids: set[int] = set()
    candidate_names: set[str] = set()

    raw_database = item.get("database")
    if isinstance(raw_database, dict):
        for key in ("id", "value", "database_id"):
            candidate_id = _coerce_int(raw_database.get(key))
            if candidate_id is not None:
                candidate_ids.add(candidate_id)
        for key in ("database_name", "name"):
            value = raw_database.get(key)
            if value:
                candidate_names.add(_normalized_identifier(value))
    else:
        candidate_id = _coerce_int(raw_database)
        if candidate_id is not None:
            candidate_ids.add(candidate_id)
        elif raw_database:
            candidate_names.add(_normalized_identifier(raw_database))

    candidate_id = _coerce_int(item.get("database_id"))
    if candidate_id is not None:
        candidate_ids.add(candidate_id)

    for key in ("database_name", "database_name_text"):
        value = item.get(key)
        if value:
            candidate_names.add(_normalized_identifier(value))

    if database_id in candidate_ids:
        return True
    if candidate_names and candidate_names.intersection(database_names):
        return True
    return False


def _superset_dataset_in_scope(
    item: dict[str, object],
    *,
    database_id: int,
    database_names: set[str],
    schema_name: str,
) -> bool:
    schema_value = item.get("schema")
    if schema_value and _normalized_identifier(schema_value) != _normalized_identifier(schema_name):
        return False

    return _superset_dataset_matches_database(
        item,
        database_id=database_id,
        database_names=database_names,
    )

async def _refresh_superset_registry_datasets_async(
    requested_datasets: list[str],
) -> dict[str, object]:
    client = SupersetClient.from_settings()
    schema_name = settings.superset_default_schema
    candidate_table_names = _superset_target_tables(requested_datasets)
    table_names = _existing_superset_target_tables(schema_name, candidate_table_names)
    synced_table_names = {_normalized_identifier(table_name) for table_name in table_names}
    skipped_tables = [
        table_name
        for table_name in candidate_table_names
        if _normalized_identifier(table_name) not in synced_table_names
    ]

    if not table_names:
        raise RuntimeError(
            f"No BioLink tables were detected in schema {schema_name!r} for Superset publishing"
        )

    async with aiohttp.ClientSession(
        cookie_jar=aiohttp.CookieJar(unsafe=True)
    ) as session:
        tokens = await client.bootstrap()
        access_token = tokens["access_token"]
        csrf_token = tokens["csrf_token"]

        database_id = await client.get_or_create_database(
            session,
            access_token,
            csrf_token,
            settings.superset_database_name,
            settings.superset_database_uri,
        )
        managed_database_names = _superset_managed_database_names()

        existing_datasets = await client.list_datasets(session, access_token)
        managed_datasets = [
            item
            for item in existing_datasets
            if _superset_dataset_in_scope(
                item,
                database_id=database_id,
                database_names=managed_database_names,
                schema_name=schema_name,
            )
        ]

        datasets: list[dict[str, object]] = []
        desired_dataset_ids: dict[str, int] = {}
        for table_name in table_names:
            dataset_id = await client.get_or_create_dataset(
                session,
                access_token,
                csrf_token,
                database_id,
                schema_name,
                table_name,
            )
            desired_dataset_ids[_normalized_identifier(table_name)] = dataset_id
            refresh_result = await client.refresh_dataset(
                session,
                access_token,
                csrf_token,
                dataset_id,
            )
            datasets.append(
                {
                    "table_name": table_name,
                    "dataset_id": dataset_id,
                    "refresh": refresh_result,
                }
            )

        deleted_datasets: list[dict[str, object]] = []
        for item in managed_datasets:
            dataset_id = _coerce_int(item.get("id"))
            if dataset_id is None:
                continue

            table_key = _normalized_identifier(item.get("table_name"))
            expected_dataset_id = desired_dataset_ids.get(table_key)
            if expected_dataset_id is not None and dataset_id == expected_dataset_id:
                continue

            await client.delete_dataset(
                session,
                access_token,
                csrf_token,
                dataset_id,
            )
            deleted_datasets.append(
                {
                    "table_name": item.get("table_name"),
                    "dataset_id": dataset_id,
                }
            )

    return {
        "ok": True,
        "database_name": settings.superset_database_name,
        "schema": schema_name,
        "datasets": datasets,
        "deleted_datasets": deleted_datasets,
        "managed_tables": table_names,
        "skipped_tables": skipped_tables,
    }


def _sync_superset_registry_datasets(
    requested_datasets: list[str],
    *,
    skip_superset: bool,
) -> dict[str, object]:
    if skip_superset:
        return {
            "ok": True,
            "skipped": True,
            "reason": "skip-superset-requested",
        }

    try:
        return asyncio.run(
            _refresh_superset_registry_datasets_async(requested_datasets)
        )
    except Exception as exc:
        logger.warning("Superset dataset refresh failed after ETL: %s", exc)
        return {
            "ok": False,
            "skipped": False,
            "error": str(exc),
        }


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
    if response.status_code == 409 and "Current state is STOPPING" in response.text:
        # NiFi can briefly report STOPPING while transitioning between runs.
        for _ in range(30):
            time.sleep(2)
            latest = requests.get(
                f"{NIFI_API_URL}/processors/{processor_id}",
                headers=headers,
                timeout=NIFI_REQUEST_TIMEOUT,
                verify=NIFI_VERIFY_SSL,
            )
            if latest.status_code != 200:
                continue
            latest_entity = latest.json()
            latest_state = latest_entity.get("component", {}).get("state")
            latest_version = latest_entity.get("revision", {}).get("version", revision_version)
            if latest_state != "STOPPED":
                continue

            retry_payload = {
                "revision": {"version": latest_version, "clientId": str(uuid.uuid4())},
                "state": "RUN_ONCE",
                "disconnectedNodeAcknowledged": True,
            }
            retry = requests.put(
                url,
                json=retry_payload,
                headers=headers,
                timeout=NIFI_REQUEST_TIMEOUT,
                verify=NIFI_VERIFY_SSL,
            )
            if retry.status_code in (200, 202):
                return {"ok": True, "status_code": retry.status_code, "retried_from_stopping": True}
            if retry.status_code == 409 and "Current state is RUNNING" in retry.text:
                return {"ok": True, "status_code": retry.status_code, "already_running": True}
            if retry.status_code == 409 and "Current state is STOPPING" in retry.text:
                continue
            return {"ok": False, "error": f"HTTP {retry.status_code}: {retry.text}"}

        return {
            "ok": False,
            "error": "Processor remained in STOPPING state and could not be started",
        }
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
    if (
        update_response.status_code == 400
        and "while the Processor is running" in update_response.text
    ):
        logger.info(
            "Skipping NiFi processor context update because processor is already running"
        )
        return {
            "ok": True,
            "trigger_token": trigger_token,
            "context_update_skipped": "processor-running",
        }
    if update_response.status_code not in (200, 201):
        return {
            "ok": False,
            "error": f"HTTP {update_response.status_code}: {update_response.text}",
        }
    return {"ok": True, "trigger_token": trigger_token}


def trigger_etl_pipeline(
    params: ETLParams,
    *,
    progress_callback: Callable[[dict[str, object]], None] | None = None,
) -> dict:
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
    lineage: list[dict[str, object]] = []

    def emit_stage(stage: dict[str, object]) -> None:
        nonlocal lineage
        lineage = _upsert_lineage_stage(lineage, stage)
        if progress_callback is not None:
            progress_callback(stage)

    logger.info(
        "Triggering NiFi script-aligned ETL pipeline dataset=%s processor=%s nifi_api=%s",
        dataset,
        processor_id,
        NIFI_API_URL,
    )

    try:
        emit_stage(
            _build_stage_manifest(
                "profile",
                "running",
                "backend-nifi-trigger",
                "Configuring the replacement db/test NiFi processor context.",
                details={
                    "processor_id": processor_id,
                    "trigger_token": trigger_token,
                    "datasets": requested_datasets,
                },
            )
        )
        configure_result = _configure_processor_run_context(
            processor_id,
            headers,
            trigger_token=trigger_token,
            requested_datasets=requested_datasets,
        )
        if not configure_result.get("ok"):
            emit_stage(
                _build_stage_manifest(
                    "profile",
                    "failed",
                    "backend-nifi-trigger",
                    "Failed to configure the replacement db/test NiFi processor context.",
                    details={"error": configure_result.get("error")},
                )
            )
            return {**configure_result, "lineage": lineage}

        emit_stage(
            _build_stage_manifest(
                "profile",
                "complete",
                "backend-nifi-trigger",
                "Replacement db/test NiFi processor context configured and ready to run.",
                details={
                    "processor_id": processor_id,
                    "trigger_token": trigger_token,
                    "datasets": requested_datasets,
                },
            )
        )
        emit_stage(
            _build_stage_manifest(
                "unify",
                "running",
                "nifi-processor",
                "NiFi accepted the replacement registry run and verification is in progress.",
                details={"processor_id": processor_id, "trigger_token": trigger_token},
            )
        )

        run_result = _run_once_processor(processor_id, headers)
        if not run_result.get("ok"):
            emit_stage(
                _build_stage_manifest(
                    "unify",
                    "failed",
                    "nifi-processor",
                    "NiFi rejected the replacement registry run.",
                    details={"error": run_result.get("error")},
                )
            )
            return {**run_result, "lineage": lineage}

        emit_stage(
            _build_stage_manifest(
                "unify",
                "running",
                "nifi-processor",
                "Waiting for the unified registry tables and manifest events to confirm the load stage.",
                details={
                    "status_code": run_result.get("status_code"),
                    "trigger_token": trigger_token,
                },
            )
        )

        verification = registry_loader.wait_for_registry_repopulation(
            engine,
            expected_tables=expected_tables,
            baseline_counts=baseline_counts,
            baseline_run_id=baseline_run_id,
            trigger_token=trigger_token,
        )
        if verification.get("verified"):
            verification_manifest = verification.get("manifest") or {}
            verification_source = (
                str(verification_manifest.get("source") or "nifi-processor")
                if isinstance(verification_manifest, dict)
                else "nifi-processor"
            )
            emit_stage(
                _build_stage_manifest(
                    "unify",
                    "complete",
                    verification_source,
                    "Registry tables were repopulated and verified.",
                    details={
                        "counts": verification.get("counts"),
                        "run_id": verification.get("run_id"),
                        "manifest": verification_manifest,
                    },
                )
            )

            quality_report_available = _artifact_exists("outputs/data_quality_report.html")
            comparability_available = _artifact_exists("outputs/comparability_report.json")
            emit_stage(
                _build_stage_manifest(
                    "quality",
                    "complete" if (quality_report_available or comparability_available) else "idle",
                    "artifact-observer",
                    "Replacement pipeline artifacts detected." if (quality_report_available or comparability_available) else "Replacement pipeline artifacts were not observed during this run.",
                    details={
                        "comparability_report": comparability_available,
                        "quality_report": quality_report_available,
                    },
                )
            )

            if params.skip_superset:
                emit_stage(
                    _build_stage_manifest(
                        "publish",
                        "optional",
                        "superset-sync",
                        "Superset refresh was skipped for this ETL run.",
                    )
                )
            else:
                emit_stage(
                    _build_stage_manifest(
                        "publish",
                        "running",
                        "superset-sync",
                        "Refreshing Superset-facing datasets.",
                    )
                )

            superset_sync = _sync_superset_registry_datasets(
                requested_datasets,
                skip_superset=params.skip_superset,
            )
            emit_stage(
                _build_stage_manifest(
                    "publish",
                    "optional" if superset_sync.get("skipped") else "complete" if superset_sync.get("ok") else "failed",
                    "superset-sync",
                    "Superset datasets refreshed." if superset_sync.get("ok") and not superset_sync.get("skipped") else "Superset refresh skipped for this run." if superset_sync.get("skipped") else "Superset dataset refresh failed.",
                    details=superset_sync,
                )
            )
            return {
                "ok": True,
                "engine": "nifi",
                "mode": "script-aligned",
                "pipeline": "db/test",
                "dataset": dataset,
                "datasets_requested": requested_datasets,
                "processor_id": processor_id,
                "trigger_token": trigger_token,
                "staged_csv": staged_csv,
                "verified": True,
                "verification_method": "nifi",
                "counts": verification.get("counts"),
                "run_id": verification.get("run_id"),
                "manifest": verification_manifest if isinstance(verification_manifest, dict) else None,
                "superset_sync": superset_sync,
                "lineage": lineage,
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
            emit_stage(
                _build_stage_manifest(
                    "unify",
                    "complete",
                    "snapshot-fallback",
                    "NiFi trigger accepted, then backend snapshot fallback restored registry tables.",
                    details={"counts": fallback_counts, "run_id": fallback.get("run_id")},
                )
            )
            quality_report_available = _artifact_exists("outputs/data_quality_report.html")
            comparability_available = _artifact_exists("outputs/comparability_report.json")
            emit_stage(
                _build_stage_manifest(
                    "quality",
                    "complete" if (quality_report_available or comparability_available) else "idle",
                    "artifact-observer",
                    "Replacement pipeline artifacts detected." if (quality_report_available or comparability_available) else "Replacement pipeline artifacts were not observed during this run.",
                    details={
                        "comparability_report": comparability_available,
                        "quality_report": quality_report_available,
                    },
                )
            )
            if params.skip_superset:
                emit_stage(
                    _build_stage_manifest(
                        "publish",
                        "optional",
                        "superset-sync",
                        "Superset refresh was skipped for this ETL run.",
                    )
                )
            else:
                emit_stage(
                    _build_stage_manifest(
                        "publish",
                        "running",
                        "superset-sync",
                        "Refreshing Superset-facing datasets.",
                    )
                )

            superset_sync = _sync_superset_registry_datasets(
                requested_datasets,
                skip_superset=params.skip_superset,
            )
            emit_stage(
                _build_stage_manifest(
                    "publish",
                    "optional" if superset_sync.get("skipped") else "complete" if superset_sync.get("ok") else "failed",
                    "superset-sync",
                    "Superset datasets refreshed." if superset_sync.get("ok") and not superset_sync.get("skipped") else "Superset refresh skipped for this run." if superset_sync.get("skipped") else "Superset dataset refresh failed.",
                    details=superset_sync,
                )
            )
            return {
                "ok": True,
                "engine": "nifi",
                "mode": "script-aligned",
                "pipeline": "db/test",
                "dataset": dataset,
                "datasets_requested": requested_datasets,
                "processor_id": processor_id,
                "trigger_token": trigger_token,
                "staged_csv": staged_csv,
                "verified": True,
                "verification_method": "snapshot-fallback",
                "counts": fallback_counts,
                "run_id": fallback.get("run_id"),
                "superset_sync": superset_sync,
                "lineage": lineage,
                "message": "NiFi trigger accepted; backend snapshot fallback restored registry tables",
            }

        verification_manifest = verification.get("manifest") or {}
        emit_stage(
            _build_stage_manifest(
                "unify",
                "failed",
                str(verification_manifest.get("source") or "nifi-processor") if isinstance(verification_manifest, dict) else "nifi-processor",
                "Registry tables were not repopulated successfully.",
                details={
                    "counts": verification.get("counts"),
                    "run_id": verification.get("run_id"),
                    "manifest": verification_manifest,
                    "error": verification.get("error"),
                },
            )
        )
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
            "manifest": verification_manifest if isinstance(verification_manifest, dict) else None,
            "lineage": lineage,
            "error": verification.get("error") or "NiFi accepted RUN_ONCE but registry tables were not repopulated and snapshot fallback failed",
        }
    except Exception as exc:
        logger.error("Failed to trigger NiFi ETL pipeline: %s", exc)
        emit_stage(
            _build_stage_manifest(
                "harmonize",
                "failed",
                "backend-nifi-trigger",
                "Unexpected ETL exception while coordinating NiFi and registry verification.",
                details={"error": str(exc)},
            )
        )
        return {"ok": False, "error": str(exc), "lineage": lineage}
