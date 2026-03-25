#!/usr/bin/env python3
"""
Harmonization transforms: value normalization functions and dispatch.

These functions are used by apply_schema.py to enforce terminology
normalization at transform time (not just structural column selection).
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

from variable_rules import (
    BOOLEAN_FALSE,
    BOOLEAN_TRUE,
    GENDER_MAP,
    MARITAL_STATUS_MAP,
    RHYTHM_MAP,
    SEVERITY_MAP,
    SMOKING_STATUS_MAP,
)


def _safe_str(value) -> Optional[str]:
    """Safely convert to stripped string, return None for empty/NaN."""
    if value is None:
        return None
    s = str(value).strip()
    if s in ("", "nan", "NaN", "None", "NA", "N/A", "none", "."):
        return None
    return s


# ── Date ──────────────────────────────────────────────────────────────

def parse_date(value, **_kw) -> Optional[str]:
    if not (s := _safe_str(value)):
        return None
    s = re.split(r"[T ]", s, maxsplit=1)[0].strip()
    s = re.sub(r"[.]0+$", "", s)
    s = s.replace("\\", "/")
    formats = [
        "%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%d-%m-%Y",
        "%d.%m.%Y", "%m/%d/%Y", "%m-%d-%Y", "%m.%d.%Y",
        "%d/%m/%y", "%d-%m-%y", "%m/%d/%y", "%m-%d-%y",
    ]
    parsed = None
    for fmt in formats:
        try:
            parsed = datetime.strptime(s, fmt)
            break
        except ValueError:
            continue
    if parsed is None:
        return None
    min_year, max_year = 1900, datetime.utcnow().year + 1
    if parsed.year < min_year or parsed.year > max_year:
        return None
    return parsed.strftime("%Y-%m-%d")


# ── Numeric ───────────────────────────────────────────────────────────

def parse_numeric(value, **_kw) -> Optional[float]:
    if not (s := _safe_str(value)):
        return None
    s = s.replace(",", "").replace(" ", "")
    # strip units that sometimes trail the number
    s = re.sub(r"\s*(mg|ml|mmhg|mm hg|%|kg|cm|bpm|ms|g/dl|u/l|mmol/l|fL|pg)$",
               "", s, flags=re.IGNORECASE).strip()
    # handle range "120-130" by averaging
    m = re.match(r"^(-?\d+\.?\d*)\s*[-–]\s*(-?\d+\.?\d*)$", s)
    if m:
        try:
            return (float(m.group(1)) + float(m.group(2))) / 2
        except ValueError:
            pass
    try:
        return float(s)
    except ValueError:
        return None


def parse_integer(value, **_kw) -> Optional[int]:
    num = parse_numeric(value)
    return int(num) if num is not None else None


# ── Categorical normalizers ───────────────────────────────────────────

def normalize_gender(value, **_kw) -> Optional[str]:
    if not (s := _safe_str(value)):
        return None
    mapped = GENDER_MAP.get(s.lower())
    return mapped  # None if not in map


def normalize_boolean(value, **_kw):
    if not (s := _safe_str(value)):
        return None
    low = s.lower().strip()
    if low in BOOLEAN_TRUE:
        return True
    if low in BOOLEAN_FALSE:
        return False
    return None


def normalize_smoking_status(value, **_kw) -> Optional[str]:
    if not (s := _safe_str(value)):
        return None
    mapped = SMOKING_STATUS_MAP.get(s.lower())
    return mapped


def normalize_smoking_type(value, **_kw) -> Optional[str]:
    if not (s := _safe_str(value)):
        return None
    low = s.lower()
    if "both" in low:
        return "both"
    if "shisha" in low or "hookah" in low:
        return "shisha"
    if "cigarette" in low:
        return "cigarettes"
    if low in BOOLEAN_FALSE:
        return "none"
    return s


def normalize_marital_status(value, **_kw) -> Optional[str]:
    if not (s := _safe_str(value)):
        return None
    mapped = MARITAL_STATUS_MAP.get(s.lower())
    return mapped if mapped else s.title()


def normalize_severity(value, **_kw) -> Optional[str]:
    if not (s := _safe_str(value)):
        return None
    low = s.lower().strip()
    # Handle compound like "Mild-Moderate"
    for k, v in SEVERITY_MAP.items():
        if k in low:
            return v
    return low


def normalize_rhythm(value, **_kw) -> Optional[str]:
    if not (s := _safe_str(value)):
        return None
    low = s.lower().strip()
    for k, v in RHYTHM_MAP.items():
        if k in low:
            return v
    return low


def extract_bp(value, **_kw) -> Optional[str]:
    """Return BP as 'systolic/diastolic' or None."""
    if not (s := _safe_str(value)):
        return None
    s = re.sub(r"\s*(mmhg|mm hg)\s*", "", s, flags=re.IGNORECASE)
    if "/" in s:
        parts = s.split("/")
        if len(parts) == 2:
            sys_v = parse_numeric(parts[0])
            dia_v = parse_numeric(parts[1])
            if sys_v is not None and dia_v is not None:
                return f"{int(sys_v)}/{int(dia_v)}"
    return s


def passthrough(value, **_kw):
    return _safe_str(value)


# ── Dispatch table ────────────────────────────────────────────────────

TRANSFORM_DISPATCH = {
    "parse_date": parse_date,
    "parse_numeric": parse_numeric,
    "parse_integer": parse_integer,
    "normalize_gender": normalize_gender,
    "normalize_boolean": normalize_boolean,
    "normalize_smoking_status": normalize_smoking_status,
    "normalize_smoking_type": normalize_smoking_type,
    "normalize_marital_status": normalize_marital_status,
    "normalize_severity": normalize_severity,
    "normalize_rhythm": normalize_rhythm,
    "extract_bp": extract_bp,
    "passthrough": passthrough,
}


def apply_transform(value, transform_name: str | None):
    """Apply a named transform function. Returns transformed value or original."""
    if transform_name is None:
        return _safe_str(value)
    fn = TRANSFORM_DISPATCH.get(transform_name)
    if fn is None:
        return _safe_str(value)
    return fn(value)


def validate_range(value, rng: tuple | None) -> tuple[bool, Optional[str]]:
    """
    Check if a numeric value falls within the allowable range.
    Returns (is_valid, reason_if_invalid).
    """
    if value is None or rng is None:
        return True, None
    try:
        v = float(value)
    except (ValueError, TypeError):
        return True, None  # non-numeric; range check doesn't apply
    lo, hi = rng
    if v < lo or v > hi:
        return False, f"out_of_range({lo}-{hi}): {v}"
    return True, None


def validate_allowable(value, allowed: list | None) -> tuple[bool, Optional[str]]:
    """
    Check if a categorical value is in the allowable set.
    Returns (is_valid, reason_if_invalid).
    """
    if value is None or allowed is None:
        return True, None
    sval = str(value)
    if sval in allowed:
        return True, None
    # case-insensitive check
    low_allowed = {a.lower() for a in allowed}
    if sval.lower() in low_allowed:
        return True, None
    return False, f"not_in_allowed({allowed}): {sval}"
