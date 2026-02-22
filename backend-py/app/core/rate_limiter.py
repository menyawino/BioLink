"""
Rate limiting configuration using slowapi.
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, FastAPI
from app.config import settings

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["60 per minute"],
    storage_uri=getattr(settings, 'redis_url', 'memory://')
)


def setup_rate_limiting(app: FastAPI) -> None:
    """Configure rate limiting for the FastAPI application."""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Custom limit decorators for different endpoints
class RateLimits:
    """Predefined rate limits for different endpoint types."""
    
    # Strict limits for authentication endpoints
    AUTH = ["5 per minute"]
    
    # Standard limits for API endpoints
    STANDARD = ["60 per minute"]
    
    # Relaxed limits for read-only endpoints
    READ_ONLY = ["120 per minute"]
    
    # Strict limits for write operations
    WRITE = ["30 per minute"]
    
    # Very strict limits for admin operations
    ADMIN = ["10 per minute"]
    
    # Limits for chat/AI endpoints (can be resource intensive)
    CHAT = ["30 per minute"]
    
    # Limits for export operations
    EXPORT = ["5 per minute"]
