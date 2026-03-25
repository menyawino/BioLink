from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import text

logger = logging.getLogger("biolink.audit")


def _get_db_engine():
    """Lazily import the engine to avoid circular imports."""
    try:
        from app.database import engine
        return engine
    except Exception:
        return None


def audit_event(
    event_type: str,
    payload: Dict[str, Any],
    request_id: Optional[str] = None,
    username: Optional[str] = None,
) -> None:
    redacted_payload = redact_payload(payload)
    record = {
        "event": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": request_id,
        "username": username,
        "payload": redacted_payload,
    }
    logger.info(json.dumps(record, ensure_ascii=False))

    # Persist to audit_log table (best-effort; never break the caller)
    engine = _get_db_engine()
    if engine is not None:
        try:
            with engine.begin() as conn:
                conn.execute(
                    text(
                        "INSERT INTO audit_log (event_type, username, request_id, payload) "
                        "VALUES (:event_type, :username, :request_id, :payload)"
                    ),
                    {
                        "event_type": event_type,
                        "username": username,
                        "request_id": request_id,
                        "payload": json.dumps(redacted_payload, ensure_ascii=False),
                    },
                )
        except Exception:
            logger.debug("audit_log DB write skipped (table may not exist yet)")


def redact_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    redacted = dict(payload)
    for key in ["dna_id", "mrn", "name", "email", "phone"]:
        if key in redacted and redacted[key] is not None:
            redacted[key] = "[REDACTED]"
    return redacted
