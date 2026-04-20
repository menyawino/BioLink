"""Rate limiting configuration using slowapi."""

from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings


class RateLimits:
    """Predefined rate limits for different endpoint types."""

    AUTH = "5 per minute"
    STANDARD = "60 per minute"
    READ_ONLY = "120 per minute"
    WRITE = "30 per minute"
    ADMIN = "10 per minute"
    CHAT = "30 per minute"
    EXPORT = "5 per minute"


limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[RateLimits.STANDARD],
    storage_uri=getattr(settings, "redis_url", "memory://"),
)


def setup_rate_limiting(app: FastAPI) -> None:
    """Configure rate limiting for the FastAPI application."""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
