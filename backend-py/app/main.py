from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from contextlib import asynccontextmanager
from app.config import settings
from app.database import test_connection
from app.database import engine
from app.db_bootstrap import ensure_schema
from app.services.registry_loader import ensure_registry_snapshot_loaded
from app.routes import (
    chat,
    cohort,
    patients,
    analytics,
    charts,
    tools,
    rag,
    superset,
    etl,
    auth,
    harmonization,
)
from app.api import health as health_router
from app.core import limiter, setup_rate_limiting, RateLimits
from app.core.middleware import RequestIdMiddleware, request_id_var
import logging
from datetime import datetime

from app.core.logging_config import setup_logging, get_logger

# Configure structured logging
setup_logging()
logger = get_logger(__name__)

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token", auto_error=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting BioLink API Server")
    try:
        ensure_schema(engine)
    except Exception as e:
        logger.error(f"Database schema bootstrap failed: {e}")

    try:
        reload_result = ensure_registry_snapshot_loaded(engine, reason="startup")
        if reload_result.get("loaded"):
            logger.info("✓ Registry snapshot restored during startup")
    except Exception as e:
        logger.warning(f"Registry snapshot startup reload failed: {e}")


    # Bootstrap auth tables + seed default users
    try:
        from app.auth_bootstrap import bootstrap_auth

        bootstrap_auth()
        logger.info("✓ Auth tables bootstrapped")
    except Exception as e:
        logger.warning(f"Auth bootstrap failed: {e}")

    # Create database indexes for performance
    try:
        from app.db_indexes import create_indexes, analyze_tables

        create_indexes()
        analyze_tables()
        logger.info("✓ Database indexes created")
    except Exception as e:
        logger.warning(f"Database index creation failed: {e}")

    db_connected = test_connection()
    logger.info(
        f"Database connection: {'✓ connected' if db_connected else '✗ disconnected'}"
    )

    # Test Redis connection
    try:
        from app.core.cache import get_redis_client

        redis_client = get_redis_client()
        if redis_client:
            logger.info("✓ Redis cache connected")
        else:
            logger.warning("✗ Redis cache not available")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")

    yield
    # Shutdown
    logger.info("Shutting down BioLink API Server")


app = FastAPI(
    title="BioLink API",
    description="AI-powered cardiovascular patient registry API with authentication and rate limiting",
    version="1.2.0",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.environment == "development" else None,
    redoc_url="/api/redoc" if settings.environment == "development" else None,
)

# Setup rate limiting
setup_rate_limiting(app)

# Request ID + timing middleware (outermost — runs first on every request)
app.add_middleware(RequestIdMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Length", "X-Request-ID", "X-Response-Time-Ms"],
    max_age=86400,
)


# Health check endpoints
@app.get("/")
async def root():
    return {
        "status": "ok",
        "name": "BioLink API",
        "version": "1.2.0",
    }


@app.get("/health")
@limiter.limit(RateLimits.READ_ONLY)
async def health(request: Request):
    """Health check with dependency status."""
    import time

    db_ok = test_connection()

    redis_ok = False
    try:
        from app.core.cache import get_redis_client
        rc = get_redis_client()
        if rc:
            rc.ping()
            redis_ok = True
    except Exception:
        pass

    services = {
        "database": "connected" if db_ok else "disconnected",
        "redis": "connected" if redis_ok else "disconnected",
        "api": "healthy",
    }

    all_healthy = db_ok and redis_ok

    return {
        "status": "healthy" if all_healthy else "degraded",
        "version": "1.2.0",
        "environment": settings.environment,
        "services": services,
        "timestamp": datetime.now().isoformat(),
    }


def _check_db() -> dict:
    """Probe PostgreSQL and return status + latency."""
    import time
    info: dict = {"status": "unknown", "latency_ms": None}
    try:
        start = time.perf_counter()
        ok = test_connection()
        info["latency_ms"] = round((time.perf_counter() - start) * 1000, 2)
        info["status"] = "connected" if ok else "disconnected"
    except Exception as exc:
        info["status"] = "error"
        info["error"] = str(exc)
    return info


def _check_redis() -> dict:
    """Probe Redis and return status + latency."""
    import time
    info: dict = {"status": "unknown", "latency_ms": None}
    try:
        from app.core.cache import get_redis_client
        start = time.perf_counter()
        rc = get_redis_client()
        if rc:
            rc.ping()
            info["latency_ms"] = round((time.perf_counter() - start) * 1000, 2)
            info["status"] = "connected"
        else:
            info["status"] = "disconnected"
    except Exception as exc:
        info["status"] = "error"
        info["error"] = str(exc)
    return info


def _check_pgvector() -> dict:
    """Probe pgvector database and return status + latency."""
    import time
    from sqlalchemy import create_engine as _ce, text as _t
    info: dict = {"status": "unknown", "latency_ms": None}
    try:
        start = time.perf_counter()
        _eng = _ce(settings.rag_pg_url, pool_pre_ping=True)
        with _eng.connect() as conn:
            conn.execute(_t("SELECT 1"))
        info["latency_ms"] = round((time.perf_counter() - start) * 1000, 2)
        info["status"] = "connected"
        _eng.dispose()
    except Exception as exc:
        info["status"] = "unavailable"
        info["error"] = str(exc)
    return info


@app.get("/api/health/detailed")
@limiter.limit(RateLimits.READ_ONLY)
async def health_detailed(request: Request):
    """Detailed health check with all dependencies."""

    checks = {
        "database": _check_db(),
        "redis": _check_redis(),
        "pgvector": _check_pgvector(),
        "api": {"status": "healthy", "version": "1.2.0"},
    }

    critical_ok = checks["database"]["status"] == "connected"
    all_ok = all(
        v.get("status") in ("connected", "healthy")
        for v in checks.values()
    )

    if not critical_ok:
        status = "unhealthy"
    elif not all_ok:
        status = "degraded"
    else:
        status = "healthy"

    return {
        "status": status,
        "checks": checks,
        "timestamp": datetime.now().isoformat(),
    }


# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(
    chat.router,
    prefix="/api/chat",
    tags=["chat"],
    dependencies=[Depends(auth.require_scopes("read"))],
)
app.include_router(
    rag.router,
    prefix="/api/rag",
    tags=["rag"],
    dependencies=[Depends(auth.require_scopes("read"))],
)
app.include_router(
    patients.router,
    prefix="/api/patients",
    tags=["patients"],
    dependencies=[Depends(auth.require_scopes("read"))],
)
app.include_router(
    analytics.router,
    prefix="/api/analytics",
    tags=["analytics"],
    dependencies=[Depends(auth.require_scopes("read"))],
)
app.include_router(
    charts.router,
    prefix="/api/charts",
    tags=["charts"],
    dependencies=[Depends(auth.require_scopes("write"))],
)
app.include_router(
    tools.router,
    prefix="/api/tools",
    tags=["tools"],
    dependencies=[Depends(auth.require_scopes("write"))],
)
app.include_router(
    superset.router,
    prefix="/api/superset",
    tags=["superset"],
    dependencies=[Depends(auth.require_scopes("read"))],
)
app.include_router(
    etl.router,
    prefix="/api/etl",
    tags=["etl"],
    dependencies=[Depends(auth.require_role("admin"))],
)
app.include_router(
    harmonization.router,
    prefix="/api/harmonization",
    tags=["harmonization"],
    dependencies=[Depends(auth.require_scopes("read"))],
)
app.include_router(health_router.router)

app.include_router(
    cohort.router,
    prefix="/api/cohort",
    tags=["cohort"],
    dependencies=[Depends(auth.require_scopes("read"))],
)


# Error handlers
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc):
    rid = getattr(request.state, "request_id", None) or request_id_var.get("")
    logger.error("Unhandled error rid=%s: %s", rid, exc, exc_info=True)
    body = {
        "success": False,
        "error": "Internal server error",
        "request_id": rid or None,
    }
    if settings.environment == "development":
        body["detail"] = str(exc)
    return JSONResponse(status_code=500, content=body)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development",
    )
