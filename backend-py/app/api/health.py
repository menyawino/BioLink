"""Health check endpoints for BioLink platform."""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.core.cache import redis_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["health"])


class HealthStatus(BaseModel):
    status: str
    timestamp: str
    version: str
    uptime_seconds: float
    checks: dict[str, Any]


class ReadinessStatus(BaseModel):
    status: str
    checks: dict[str, str]


# Process start time for uptime calculation
_START_TIME = time.time()


async def _check_database(db: Session) -> tuple[bool, float]:
    """Check database connectivity and latency."""
    try:
        start = time.perf_counter()
        db.execute(text("SELECT 1"))
        latency = time.perf_counter() - start
        return True, round(latency * 1000, 2)
    except Exception as exc:
        logger.warning(f"Database health check failed: {exc}")
        return False, 0.0


async def _check_redis() -> tuple[bool, float]:
    """Check Redis connectivity and latency."""
    try:
        start = time.perf_counter()
        if redis_client:
            await redis_client.ping()
        latency = time.perf_counter() - start
        return True, round(latency * 1000, 2)
    except Exception as exc:
        logger.warning(f"Redis health check failed: {exc}")
        return False, 0.0


async def _check_ollama() -> tuple[bool, float]:
    """Check Ollama connectivity (optional)."""
    try:
        import aiohttp

        start = time.perf_counter()
        timeout = aiohttp.ClientTimeout(total=2.0)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(f"{settings.ollama_base_url}/api/tags") as resp:
                latency = time.perf_counter() - start
                return resp.status == 200, round(latency * 1000, 2)
    except Exception:
        return False, 0.0


@router.get(
    "/",
    response_model=HealthStatus,
    summary="Platform health check",
    description="Returns overall platform health with component status.",
)
async def health_check(db: Session = Depends(get_db)) -> HealthStatus:
    """Comprehensive health check for all platform components."""
    db_ok, db_latency = await _check_database(db)
    redis_ok, redis_latency = await _check_redis()
    ollama_ok, ollama_latency = await _check_ollama()

    checks = {
        "database": {"status": "healthy" if db_ok else "unhealthy", "latency_ms": db_latency},
        "redis": {"status": "healthy" if redis_ok else "unhealthy", "latency_ms": redis_latency},
        "ollama": {"status": "healthy" if ollama_ok else "unavailable", "latency_ms": ollama_latency},
    }

    all_healthy = db_ok and redis_ok
    status_str = "healthy" if all_healthy else "degraded"

    return HealthStatus(
        status=status_str,
        timestamp=datetime.now(UTC).isoformat(),
        version="1.2.0",
        uptime_seconds=round(time.time() - _START_TIME, 2),
        checks=checks,
    )


@router.get(
    "/ready",
    response_model=ReadinessStatus,
    summary="Readiness probe",
    description="Kubernetes-style readiness probe. Returns 503 if critical dependencies are down.",
    status_code=status.HTTP_200_OK,
)
async def readiness_check(db: Session = Depends(get_db)) -> ReadinessStatus:
    """Readiness probe for orchestrators (K8s, ACA)."""
    db_ok, _ = await _check_database(db)
    redis_ok, _ = await _check_redis()

    checks: dict[str, str] = {
        "database": "ready" if db_ok else "not_ready",
        "redis": "ready" if redis_ok else "not_ready",
    }

    all_ready = db_ok and redis_ok
    status_str = "ready" if all_ready else "not_ready"

    if not all_ready:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=ReadinessStatus(status=status_str, checks=checks).model_dump(),
        )

    return ReadinessStatus(status=status_str, checks=checks)


@router.get(
    "/live",
    summary="Liveness probe",
    description="Kubernetes-style liveness probe. Always returns 200 if process is running.",
)
async def liveness_check() -> dict[str, str]:
    """Liveness probe — lightweight, no external dependencies."""
    return {"status": "alive"}
