from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from contextlib import asynccontextmanager
from app.config import settings
from app.database import test_connection
from app.database import engine
from app.db_bootstrap import ensure_schema
from app.routes import (
    chat,
    patients,
    analytics,
    charts,
    tools,
    rag,
    superset,
    etl,
    auth,
)
from app.core import limiter, setup_rate_limiting, RateLimits
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

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
    version="1.1.0",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.environment == "development" else None,
    redoc_url="/api/redoc" if settings.environment == "development" else None,
)

# Setup rate limiting
setup_rate_limiting(app)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Length"],
    max_age=86400,
)


# Health check endpoints
@app.get("/")
async def root():
    return {
        "status": "ok",
        "name": "BioLink API",
        "version": "1.1.0",
    }


@app.get("/health")
@limiter.limit(RateLimits.READ_ONLY)
async def health(request: Request):
    """Enhanced health check with dependency status."""
    db_connected = test_connection()

    # Check additional services
    services = {
        "database": "connected" if db_connected else "disconnected",
        "api": "healthy",
    }

    # Overall status
    all_healthy = all(s == "connected" or s == "healthy" for s in services.values())

    return {
        "status": "healthy" if all_healthy else "degraded",
        "version": "1.1.0",
        "environment": settings.environment,
        "services": services,
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/health/detailed")
@limiter.limit(RateLimits.READ_ONLY)
async def health_detailed(request: Request):
    """Detailed health check with all dependencies."""

    checks = {
        "database": {"status": "unknown", "latency_ms": None},
        "api": {"status": "healthy", "version": "1.1.0"},
    }

    # Database check with timing
    try:
        import time

        start = time.time()
        db_connected = test_connection()
        latency = (time.time() - start) * 1000
        checks["database"]["status"] = "connected" if db_connected else "disconnected"
        checks["database"]["latency_ms"] = round(latency, 2)
    except Exception as e:
        checks["database"]["status"] = "error"
        checks["database"]["error"] = str(e)

    all_healthy = checks["database"]["status"] == "connected"

    return {
        "status": "healthy" if all_healthy else "degraded",
        "checks": checks,
        "timestamp": datetime.now().isoformat(),
    }


# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(rag.router, prefix="/api/rag", tags=["rag"])
app.include_router(patients.router, prefix="/api/patients", tags=["patients"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(charts.router, prefix="/api/charts", tags=["charts"])
app.include_router(tools.router, prefix="/api/tools", tags=["tools"])
app.include_router(superset.router, prefix="/api/superset", tags=["superset"])
app.include_router(etl.router, prefix="/api/etl", tags=["etl"])


# Error handlers
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled error: {exc}")
    return {
        "success": False,
        "error": "Internal server error",
        "message": str(exc) if settings.environment == "development" else None,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development",
    )
