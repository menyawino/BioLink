from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger("biolink.audit")


def audit_event(event_type: str, payload: Dict[str, Any], request_id: Optional[str] = None) -> None:
    redacted_payload = redact_payload(payload)
    record = {
        "event": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": request_id,
        "payload": redacted_payload,
    }
    logger.info(json.dumps(record, ensure_ascii=False))


def redact_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    redacted = dict(payload)
    for key in ["dna_id", "mrn", "name", "email", "phone"]:
        if key in redacted and redacted[key] is not None:
            redacted[key] = "[REDACTED]"
    return redacted