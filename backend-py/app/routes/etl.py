from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel, Field
import logging
from datetime import UTC, datetime
from threading import Lock
from uuid import uuid4
from typing import Any, Optional
from pathlib import Path
import os
from app.services.etl_service import trigger_etl_pipeline, ETLParams

router = APIRouter()
logger = logging.getLogger(__name__)
_jobs_lock = Lock()
_jobs: dict[str, dict] = {}

ETL_UPLOAD_WRITE_DIR = os.getenv(
    "ETL_UPLOAD_WRITE_DIR", os.getenv("ETL_UPLOAD_DIR", "/tmp/biolink_uploaded_csvs")
)
ETL_UPLOAD_READ_DIR = os.getenv(
    "ETL_UPLOAD_READ_DIR", os.getenv("ETL_SERVICE_UPLOAD_DIR", ETL_UPLOAD_WRITE_DIR)
)


class ETLRequest(BaseModel):
    table: str = "ehvol_full"
    schema: str = "public"
    csv: str | None = None
    datasets: list[str] = Field(default_factory=lambda: ["ehvol", "bhs"])
    dataset_name: str | None = None
    dbt_select: str | None = None
    skip_superset: bool = False


class WebhookPayload(BaseModel):
    """A simple webhook payload to trigger ETL runs from external systems."""

    runId: Optional[str] = None
    request: Optional[dict[str, Any]] = None


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _update_job(job_id: str, **updates):
    with _jobs_lock:
        if job_id in _jobs:
            _jobs[job_id].update(updates)


def _is_inline_csv(value: str | None) -> bool:
    return bool(value and ("\n" in value or "\r" in value))


def _materialize_csv_for_etl(csv_value: str | None) -> tuple[str | None, str | None]:
    """Return ETL-visible CSV path and optional backend-local written path.

    - If csv_value is inline CSV content, write it under ETL_UPLOAD_WRITE_DIR and
      return mapped ETL path under ETL_UPLOAD_READ_DIR.
    - If csv_value is already a path/URI-like string, pass it through unchanged.
    """
    if not csv_value:
        return None, None

    if not _is_inline_csv(csv_value):
        return csv_value, None

    write_dir = Path(ETL_UPLOAD_WRITE_DIR)
    write_dir.mkdir(parents=True, exist_ok=True)

    filename = f"uploaded_{uuid4().hex}.csv"
    local_path = write_dir / filename
    local_path.write_text(csv_value, encoding="utf-8")

    etl_path = str(Path(ETL_UPLOAD_READ_DIR) / filename)
    return etl_path, str(local_path)


def _run_wrapper(job_id: str, req: ETLRequest):
    _update_job(job_id, status="running", startedAt=_utcnow())
    etl_csv_path, local_written_csv = _materialize_csv_for_etl(req.csv)

    requested_datasets: list[str] = []
    for item in req.datasets or []:
        normalized = str(item).strip().lower()
        if normalized in {"ehvol", "bhs"} and normalized not in requested_datasets:
            requested_datasets.append(normalized)
    if not requested_datasets:
        requested_datasets = ["ehvol", "bhs"]

    try:
        run_results: list[dict[str, Any]] = []
        for dataset in requested_datasets:
            params = ETLParams(
                table="bhs_full" if dataset == "bhs" else "ehvol_full",
                schema=req.schema,
                csv=etl_csv_path,
                dataset_name=dataset,
                dbt_select=req.dbt_select,
                skip_superset=req.skip_superset,
            )
            result = trigger_etl_pipeline(params)
            run_results.append(result)

        ok = all(bool(item.get("ok", False)) for item in run_results)
        result: dict[str, Any] = {
            "ok": ok,
            "engine": "nifi",
            "datasets_requested": requested_datasets,
            "results": run_results,
            "message": (
                "NiFi ETL trigger executed for all datasets"
                if ok
                else "One or more dataset ETL triggers failed"
            ),
        }

        first_error = next(
            (item.get("error") for item in run_results if not item.get("ok")),
            None,
        )
        _update_job(
            job_id,
            status="succeeded" if ok else "failed",
            finishedAt=_utcnow(),
            result=result,
            error=None if ok else first_error,
            csvPath=etl_csv_path,
            localCsvPath=local_written_csv,
        )
        logger.info("ETL Result (%s): %s", job_id, result)
    except Exception as exc:
        logger.exception("ETL job failed: %s", job_id)
        _update_job(
            job_id,
            status="failed",
            finishedAt=_utcnow(),
            error=str(exc),
        )


@router.post("/webhook/trigger")
async def webhook_trigger(payload: WebhookPayload, background_tasks: BackgroundTasks):
    """Receive a generic webhook from external systems and enqueue an ETL run.

    The payload may include an external `runId` (for lineage tracking)
    and an optional `request` object compatible with `ETLRequest` shape.
    """
    # Build an ETLRequest from provided payload.request or use defaults
    req_data = payload.request or {}
    try:
        req = ETLRequest(**req_data)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid request payload: {exc}")

    job_id = str(uuid4())
    with _jobs_lock:
        _jobs[job_id] = {
            "jobId": job_id,
            "status": "queued",
            "requestedAt": _utcnow(),
            "startedAt": None,
            "finishedAt": None,
            "request": req.model_dump(),
            "result": None,
            "error": None,
            "externalRunId": payload.runId,
        }

    background_tasks.add_task(_run_wrapper, job_id, req)

    return {
        "success": True,
        "data": {
            "jobId": job_id,
            "externalRunId": payload.runId,
            "status": "queued",
            "message": "ETL job enqueued via webhook",
        },
    }


@router.post("/run")
async def trigger_etl(req: ETLRequest, background_tasks: BackgroundTasks):
    """Trigger the ETL pipeline in background."""
    job_id = str(uuid4())
    with _jobs_lock:
        _jobs[job_id] = {
            "jobId": job_id,
            "status": "queued",
            "requestedAt": _utcnow(),
            "startedAt": None,
            "finishedAt": None,
            "request": req.model_dump(),
            "result": None,
            "error": None,
        }

    background_tasks.add_task(_run_wrapper, job_id, req)
    return {
        "success": True,
        "data": {
            "jobId": job_id,
            "status": "queued",
            "message": "ETL job started in background",
        },
    }


@router.get("/status/{job_id}")
async def get_etl_status(job_id: str):
    with _jobs_lock:
        job = _jobs.get(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="ETL job not found")

    return {"success": True, "data": job}


@router.get("/status")
async def list_etl_status(limit: int = Query(default=20, ge=1, le=200)):
    with _jobs_lock:
        jobs = sorted(
            _jobs.values(),
            key=lambda item: item.get("requestedAt") or "",
            reverse=True,
        )[:limit]

    return {"success": True, "data": jobs}
