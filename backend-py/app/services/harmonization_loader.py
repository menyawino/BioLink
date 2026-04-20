from __future__ import annotations

import csv
import json
import logging
import math
import os
from datetime import datetime, timezone
from pathlib import Path

from psycopg2 import sql
from psycopg2.extras import Json, execute_values
from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

_ARTIFACT_TABLES = {
    "harmonization_tiers": "_loaded_at",
    "harmonization_provenance": "_loaded_at",
    "comparability_report": "created_at",
}


def _workspace_root() -> Path:
    explicit_root = os.getenv("BIOLINK_WORKSPACE_ROOT")
    if explicit_root:
        return Path(explicit_root)

    candidates = [
        Path("/app"),
        Path(__file__).resolve().parents[3],
        Path.cwd(),
    ]
    for candidate in candidates:
        if (candidate / "outputs").exists():
            return candidate
    return candidates[0]


def _resolve_artifact_path(env_var_name: str, filename: str) -> Path:
    explicit_path = os.getenv(env_var_name)
    if explicit_path:
        return Path(explicit_path)

    candidates = [
        Path("/app/outputs") / filename,
        _workspace_root() / "outputs" / filename,
        Path.cwd() / "outputs" / filename,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def resolve_harmonization_artifact_paths() -> dict[str, Path]:
    return {
        "tiers": _resolve_artifact_path(
            "HARMONIZATION_TIERS_PATH",
            "harmonization_tiers.csv",
        ),
        "provenance": _resolve_artifact_path(
            "HARMONIZATION_PROVENANCE_PATH",
            "provenance.csv",
        ),
        "comparability": _resolve_artifact_path(
            "COMPARABILITY_REPORT_PATH",
            "comparability_report.json",
        ),
    }


def _table_exists(conn, table_name: str) -> bool:
    return bool(
        conn.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = :table_name
                )
                """
            ),
            {"table_name": table_name},
        ).scalar()
    )


def _table_count(conn, table_name: str) -> int:
    if not _table_exists(conn, table_name):
        return 0
    return int(conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"')).scalar() or 0)


def _latest_loaded_at(conn, table_name: str, timestamp_column: str) -> datetime | None:
    if not _table_exists(conn, table_name):
        return None
    value = conn.execute(
        text(f'SELECT MAX("{timestamp_column}") FROM "{table_name}"')
    ).scalar()
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _artifact_mtime(paths: dict[str, Path]) -> datetime | None:
    existing = [path for path in paths.values() if path.exists()]
    if not existing:
        return None
    latest_mtime = max(path.stat().st_mtime for path in existing)
    return datetime.fromtimestamp(latest_mtime, tz=timezone.utc)


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _clean_float(value: str | None) -> float | None:
    cleaned = _clean_text(value)
    if cleaned is None:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _clean_int(value: str | None) -> int | None:
    cleaned = _clean_text(value)
    if cleaned is None:
        return None
    try:
        return int(cleaned)
    except ValueError:
        return None


def _clean_bool(value: str | None) -> bool | None:
    cleaned = _clean_text(value)
    if cleaned is None:
        return None
    lowered = cleaned.lower()
    if lowered in {"true", "1", "yes", "y"}:
        return True
    if lowered in {"false", "0", "no", "n"}:
        return False
    return None


def _sanitize_json(value):
    if isinstance(value, dict):
        return {key: _sanitize_json(inner) for key, inner in value.items()}
    if isinstance(value, list):
        return [_sanitize_json(item) for item in value]
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return value


def _load_harmonization_tiers(raw_conn, csv_path: Path, loaded_at: datetime) -> int:
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        payload = [
            (
                _clean_text(row.get("master_col")),
                _clean_text(row.get("tier")),
                _clean_text(row.get("data_type")),
                _clean_text(row.get("unit")),
                _clean_text(row.get("transform")),
                _clean_text(row.get("loinc")),
                _clean_text(row.get("snomed")),
                _clean_text(row.get("phenotype_definition")),
                _clean_text(row.get("timing_window")),
                _clean_text(row.get("allowable_range")),
                _clean_float(row.get("fill_rate")),
                loaded_at,
            )
            for row in reader
            if _clean_text(row.get("master_col"))
        ]

    with raw_conn.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS harmonization_tiers (
                master_col TEXT PRIMARY KEY,
                tier TEXT,
                data_type TEXT,
                unit TEXT,
                transform TEXT,
                loinc TEXT,
                snomed TEXT,
                phenotype_definition TEXT,
                timing_window TEXT,
                allowable_range TEXT,
                fill_rate DOUBLE PRECISION,
                _loaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        cursor.execute("TRUNCATE TABLE harmonization_tiers")
        if payload:
            execute_values(
                cursor,
                """
                INSERT INTO harmonization_tiers (
                    master_col, tier, data_type, unit, transform, loinc, snomed,
                    phenotype_definition, timing_window, allowable_range, fill_rate, _loaded_at
                ) VALUES %s
                """,
                payload,
                page_size=500,
            )
    return len(payload)


def _load_harmonization_provenance(raw_conn, csv_path: Path, loaded_at: datetime) -> int:
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        payload = [
            (
                _clean_int(row.get("row_index")),
                _clean_text(row.get("cohort")),
                _clean_text(row.get("master_col")),
                _clean_text(row.get("source_cols")),
                _clean_text(row.get("source_value")),
                _clean_text(row.get("transform")),
                _clean_text(row.get("harmonized_value")),
                _clean_text(row.get("validation_status")),
                _clean_text(row.get("validation_reason")),
                _clean_text(row.get("tier")),
                _clean_text(row.get("unit")),
                _clean_text(row.get("confidence")),
                _clean_bool(row.get("reviewer_approved")),
                loaded_at,
            )
            for row in reader
            if _clean_text(row.get("master_col"))
        ]

    with raw_conn.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS harmonization_provenance (
                id BIGSERIAL PRIMARY KEY,
                row_index BIGINT,
                cohort TEXT,
                master_col TEXT,
                source_cols TEXT,
                source_value TEXT,
                transform TEXT,
                harmonized_value TEXT,
                validation_status TEXT,
                validation_reason TEXT,
                tier TEXT,
                unit TEXT,
                confidence TEXT,
                reviewer_approved BOOLEAN,
                _loaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        cursor.execute("TRUNCATE TABLE harmonization_provenance RESTART IDENTITY")
        if payload:
            execute_values(
                cursor,
                """
                INSERT INTO harmonization_provenance (
                    row_index, cohort, master_col, source_cols, source_value, transform,
                    harmonized_value, validation_status, validation_reason, tier, unit,
                    confidence, reviewer_approved, _loaded_at
                ) VALUES %s
                """,
                payload,
                page_size=1000,
            )
    return len(payload)


def _load_comparability_report(raw_conn, report_path: Path) -> int:
    with report_path.open(encoding="utf-8") as handle:
        report = _sanitize_json(json.load(handle))

    with raw_conn.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS comparability_report (
                id BIGSERIAL PRIMARY KEY,
                report JSONB NOT NULL,
                source_path TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        cursor.execute("TRUNCATE TABLE comparability_report RESTART IDENTITY")
        cursor.execute(
            "INSERT INTO comparability_report (report, source_path) VALUES (%s, %s)",
            (Json(report), str(report_path)),
        )
    return 1


def load_harmonization_artifacts(engine: Engine) -> dict[str, object]:
    paths = resolve_harmonization_artifact_paths()
    missing = [name for name, path in paths.items() if not path.exists()]
    if missing:
        raise FileNotFoundError(
            f"Missing harmonization artifacts: {', '.join(sorted(missing))}"
        )

    loaded_at = datetime.now(timezone.utc)
    raw_conn = engine.raw_connection()
    try:
        counts = {
            "harmonization_tiers": _load_harmonization_tiers(raw_conn, paths["tiers"], loaded_at),
            "harmonization_provenance": _load_harmonization_provenance(
                raw_conn,
                paths["provenance"],
                loaded_at,
            ),
            "comparability_report": _load_comparability_report(raw_conn, paths["comparability"]),
        }
        raw_conn.commit()
    except Exception:
        raw_conn.rollback()
        raise
    finally:
        raw_conn.close()

    return {
        "counts": counts,
        "paths": {name: str(path) for name, path in paths.items()},
        "loaded_at": loaded_at.isoformat(),
    }


def ensure_harmonization_artifacts_loaded(
    engine: Engine,
    *,
    force: bool = False,
) -> dict[str, object]:
    paths = resolve_harmonization_artifact_paths()
    missing = [name for name, path in paths.items() if not path.exists()]
    if missing:
        logger.warning(
            "Harmonization artifact sync skipped: missing %s",
            ", ".join(sorted(missing)),
        )
        return {
            "ok": False,
            "loaded": False,
            "reason": "artifacts-missing",
            "missing": sorted(missing),
        }

    artifact_mtime = _artifact_mtime(paths)
    with engine.connect() as conn:
        counts = {table_name: _table_count(conn, table_name) for table_name in _ARTIFACT_TABLES}
        latest_loaded = {
            table_name: _latest_loaded_at(conn, table_name, timestamp_column)
            for table_name, timestamp_column in _ARTIFACT_TABLES.items()
        }

    needs_reload = force or any(count == 0 for count in counts.values())
    if not needs_reload and artifact_mtime is not None:
        for loaded_at in latest_loaded.values():
            if loaded_at is None or artifact_mtime > loaded_at:
                needs_reload = True
                break

    if not needs_reload:
        return {
            "ok": True,
            "loaded": False,
            "reason": "already-current",
            "counts": counts,
            "paths": {name: str(path) for name, path in paths.items()},
        }

    loaded = load_harmonization_artifacts(engine)
    logger.info(
        "Harmonization artifacts loaded: tiers=%s provenance=%s comparability=%s",
        loaded["counts"]["harmonization_tiers"],
        loaded["counts"]["harmonization_provenance"],
        loaded["counts"]["comparability_report"],
    )
    return {
        "ok": True,
        "loaded": True,
        "reason": "startup-sync",
        **loaded,
    }