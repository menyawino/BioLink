"""
Structured logging configuration for BioLink API.
Supports JSON format, correlation IDs, and centralized aggregation.
"""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.config import settings


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add correlation ID if available
        if hasattr(record, "correlation_id") and record.correlation_id:
            log_obj["correlation_id"] = record.correlation_id

        # Add request info if available
        if hasattr(record, "request_id") and record.request_id:
            log_obj["request_id"] = record.request_id

        # Add extra fields
        if hasattr(record, "extra") and record.extra:
            log_obj.update(record.extra)

        # Add exception info
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj, default=str)


class CorrelationIdFilter(logging.Filter):
    """Add correlation ID to log records from context variable."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            from app.core.middleware import request_id_var
            record.correlation_id = request_id_var.get(None)
        except Exception:
            record.correlation_id = None
        return True


def setup_logging(
    level: Optional[str] = None,
    json_format: Optional[bool] = None,
) -> None:
    """Configure structured logging for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR). Defaults to settings.log_level.
        json_format: Whether to use JSON formatting. Defaults to settings.log_json_format.
    """
    log_level = (level or settings.log_level or "INFO").upper()
    use_json = json_format if json_format is not None else getattr(settings, "log_json_format", False)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level))

    if use_json:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(correlation_id)s - %(name)s - %(levelname)s - %(message)s"
        )

    console_handler.setFormatter(formatter)
    console_handler.addFilter(CorrelationIdFilter())
    root_logger.addHandler(console_handler)

    # Set specific module levels
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    logging.getLogger(__name__).info(
        "Logging configured",
        extra={"extra": {"level": log_level, "json_format": use_json}},
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger with correlation ID support."""
    logger = logging.getLogger(name)
    return logger
