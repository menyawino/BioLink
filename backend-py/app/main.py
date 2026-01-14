from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.database import test_connection
from app.routes import foundry, chat, patients, analytics, charts
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting BioLink API Server")
    db_connected = test_connection()
    logger.info(f"Database connection: {'✓ connected' if db_connected else '✗ disconnected'}")
    yield
    # Shutdown
    logger.info("Shutting down BioLink API Server")

app = FastAPI(
    title="BioLink API",
    description="AI-powered cardiovascular patient registry API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Length"],
    max_age=86400
)

# Health check endpoints
@app.get("/")
async def root():
    return {
        "status": "ok",
        "name": "BioLink API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health():
    db_connected = test_connection()
    return {
        "status": "healthy" if db_connected else "unhealthy",
        "database": "connected" if db_connected else "disconnected",
        "timestamp": datetime.now().isoformat()
    }

# Include routers
app.include_router(foundry.router, prefix="/api/foundry", tags=["foundry"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(patients.router, prefix="/api/patients", tags=["patients"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(charts.router, prefix="/api/charts", tags=["charts"])

# Error handlers
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled error: {exc}")
    return {
        "success": False,
        "error": "Internal server error",
        "message": str(exc) if settings.environment == "development" else None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development"
    )
