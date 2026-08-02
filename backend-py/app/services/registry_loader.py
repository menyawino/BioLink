from __future__ import annotations

import csv
import hashlib
import logging
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
import sys

_candidate_paths = [
    Path(__file__).resolve().parents[3] / "db" / "test",
    Path("/app/db/test"),
    Path.cwd() / "db" / "test",
]
for _candidate in _candidate_paths:
    if (_candidate / "src" / "pipeline").exists():
        _p = str(_candidate)
        if _p not in sys.path:
            sys.path.insert(0, _p)
        break

from src.pipeline.step_6_fuzzy_match_v2 import find_best_nationality_match
from psycopg2 import sql
from psycopg2.extras import Json, execute_values
from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

REGISTRY_VERIFY_TIMEOUT_S = int(os.getenv("REGISTRY_VERIFY_TIMEOUT_S", "180"))
REGISTRY_VERIFY_POLL_INTERVAL_S = float(
    os.getenv("REGISTRY_VERIFY_POLL_INTERVAL_S", "5")
)

_DATASET_TABLE_CONFIG = {
    "bhs": {
        "table": "bhs_participants",
        "cohort": "D1",
        "source_dataset": "bhs",
    },
    "ehvol": {
        "table": "ehvol_participants",
        "cohort": "D2",
        "source_dataset": "ehvol",
    },
}
_REGISTRY_TABLES = ["unified_registry", "bhs_participants", "ehvol_participants"]
_PG_IDENTIFIER_LIMIT = 63


def _workspace_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _default_snapshot_candidates() -> list[Path]:
    env_path = os.getenv("REGISTRY_SNAPSHOT_PATH")
    if env_path:
        return [Path(env_path)]

    return [
        Path("/app/outputs/unified_registry.csv"),
        _workspace_root() / "outputs" / "unified_registry.csv",
        Path.cwd() / "outputs" / "unified_registry.csv",
    ]


def resolve_registry_snapshot_path(snapshot_path: str | Path | None = None) -> Path:
    if snapshot_path is not None:
        return Path(snapshot_path)

    candidates = _default_snapshot_candidates()
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


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


def get_registry_counts(engine: Engine) -> dict[str, int]:
    counts: dict[str, int] = {}
    with engine.connect() as conn:
        for table_name in _REGISTRY_TABLES:
            if not _table_exists(conn, table_name):
                counts[table_name] = 0
                continue
            counts[table_name] = int(
                conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"')).scalar() or 0
            )
    return counts


def get_latest_registry_run_id(engine: Engine) -> int | None:
    with engine.connect() as conn:
        if not _table_exists(conn, "registry_etl_runs"):
            return None
        value = conn.execute(text("SELECT MAX(run_id) FROM registry_etl_runs")).scalar()
    return int(value) if value is not None else None


def get_registry_run_event(
    engine: Engine,
    *,
    trigger_token: str,
    source: str | None = None,
) -> dict[str, object] | None:
    if not trigger_token:
        return None

    with engine.connect() as conn:
        if not _table_exists(conn, "registry_etl_runs"):
            return None

        row = conn.execute(
            text(
                """
                SELECT run_id, finished_at, manifest
                FROM registry_etl_runs
                WHERE manifest ->> 'trigger_token' = :trigger_token
                  AND (:source IS NULL OR manifest ->> 'source' = :source)
                ORDER BY run_id DESC
                LIMIT 1
                """
            ),
            {"trigger_token": trigger_token, "source": source},
        ).mappings().first()

    if not row:
        return None

    manifest = row["manifest"]
    return {
        "run_id": int(row["run_id"]),
        "finished_at": row["finished_at"],
        "manifest": manifest if isinstance(manifest, dict) else {},
    }


def _insertable_columns(raw_conn, table_name: str) -> list[tuple[str, str]]:
    with raw_conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position
            """,
            (table_name,),
        )
        return [
            (row[0], row[1])
            for row in cursor.fetchall()
            if row[0] != "_ingest_id"
        ]


def _parse_dateish(text_value: str):
    normalized = text_value.strip()
    if not normalized:
        return None

    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(normalized, fmt).date()
        except ValueError:
            continue

    iso_candidate = normalized.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(iso_candidate).date()
    except ValueError:
        return None


def _parse_timestampish(text_value: str):
    normalized = text_value.strip()
    if not normalized:
        return None

    iso_candidate = normalized.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(iso_candidate)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        pass

    for fmt in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y"):
        try:
            return datetime.strptime(normalized, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue

    return None


def _clean_cell(value: str | None, data_type: str):
    if value is None:
        return None

    text_value = str(value).strip()
    if text_value == "":
        return None

    lowered = text_value.lower()
    if data_type == "boolean":
        if lowered in {"true", "t", "1", "yes", "y", "on", "checked"}:
            return True
        if lowered in {"false", "f", "0", "no", "n", "off", "unchecked"}:
            return False
        return None

    if data_type == "date":
        return _parse_dateish(text_value)
    if data_type.startswith("timestamp"):
        return _parse_timestampish(text_value)
    if data_type in {"smallint", "integer", "bigint"}:
        try:
            return int(text_value)
        except ValueError:
            return None
    if data_type in {"real", "double precision", "numeric", "decimal"}:
        try:
            return float(text_value)
        except ValueError:
            return None

    return text_value


def _safe_pg_identifier(name: str, used_names: set[str]) -> str:
    normalized = re.sub(r"[^0-9a-zA-Z_]+", "_", str(name).strip()).strip("_").lower()
    if not normalized:
        normalized = "column"
    if normalized[0].isdigit():
        normalized = f"col_{normalized}"

    candidate = normalized[:_PG_IDENTIFIER_LIMIT]
    if candidate not in used_names and len(normalized) <= _PG_IDENTIFIER_LIMIT:
        used_names.add(candidate)
        return candidate

    digest = hashlib.sha1(str(name).encode("utf-8")).hexdigest()[:8]
    stem_limit = _PG_IDENTIFIER_LIMIT - len(digest) - 1
    candidate = f"{normalized[:stem_limit].rstrip('_')}_{digest}"
    counter = 1
    while candidate in used_names:
        suffix = f"_{digest}{counter}"
        stem_limit = _PG_IDENTIFIER_LIMIT - len(suffix)
        candidate = f"{normalized[:stem_limit].rstrip('_')}{suffix}"
        counter += 1
    used_names.add(candidate)
    return candidate


def _load_unified_registry(raw_conn, csv_path: Path, table_name: str) -> int:
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        columns = reader.fieldnames or []

    if not columns:
        raise ValueError(f"Registry snapshot '{csv_path}' has no header row")

    used_names: set[str] = set()
    column_map = {column: _safe_pg_identifier(column, used_names) for column in columns}
    payload = [
        tuple((row.get(column) or "").strip() or None for column in columns)
        for row in rows
    ]

    with raw_conn.cursor() as cursor:
        cursor.execute(
            sql.SQL("DROP TABLE IF EXISTS {} CASCADE").format(
                sql.Identifier(table_name)
            )
        )
        cursor.execute(
            sql.SQL("CREATE TABLE {} ({})").format(
                sql.Identifier(table_name),
                sql.SQL(", ").join(
                    sql.SQL("{} TEXT").format(sql.Identifier(column_map[column]))
                    for column in columns
                ),
            )
        )
        if payload:
            insert_sql = sql.SQL("INSERT INTO {} ({}) VALUES %s").format(
                sql.Identifier(table_name),
                sql.SQL(", ").join(
                    sql.Identifier(column_map[column]) for column in columns
                ),
            )
            execute_values(
                cursor,
                insert_sql.as_string(cursor),
                payload,
                page_size=20,
            )
    return len(rows)


def normalize_nationality(val: str | None) -> str | None:
    if not val:
        return None
    val_str = str(val).strip()
    if not val_str or val_str.lower() in {"na", "n/a", "none", "null", "unknown", "—"}:
        return None

    match = find_best_nationality_match(val_str)
    if match and match[0]:
        return match[0].title()
    return val_str.title()


def _load_dataset_participants(
    raw_conn,
    csv_path: Path,
    table_name: str,
    cohort_name: str,
    source_dataset: str,
) -> int:
    columns = _insertable_columns(raw_conn, table_name)
    if not columns:
        raise ValueError(f"Target table '{table_name}' does not exist or has no columns")

    loaded_at = datetime.now(timezone.utc)
    payload: list[tuple] = []
    key_column = next(
        (
            column_name
            for column_name, _ in columns
            if column_name in {"participant_id", "dna_id", "record_id"}
        ),
        None,
    )
    deduped_rows: dict[object, tuple] = {}

    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if (row.get("cohort") or "").strip() != cohort_name:
                continue

            values = []
            for column_name, data_type in columns:
                if column_name == "_source_dataset":
                    values.append(source_dataset)
                elif column_name == "_ingested_at":
                    values.append(loaded_at)
                elif column_name == "_source_raw_json":
                    values.append(Json(row))
                else:
                    raw_val = row.get(column_name)
                    if raw_val is None or str(raw_val).strip() == "":
                        if column_name in {"dna_id", "record_id", "participant_id"}:
                            raw_val = row.get("participant_id") or row.get("dna_id") or row.get("record_id")
                        elif column_name == "nationality":
                            raw_val = row.get("ethnicity_related_nationality_data_finding_demographics")
                    if column_name == "nationality":
                        raw_val = normalize_nationality(raw_val)
                    values.append(_clean_cell(raw_val, data_type))

            if key_column:
                key_index = next(
                    index
                    for index, (column_name, _) in enumerate(columns)
                    if column_name == key_column
                )
                key_value = values[key_index]
                if key_value is not None:
                    deduped_rows[key_value] = tuple(values)
                    continue

            payload.append(tuple(values))

    if deduped_rows:
        payload.extend(deduped_rows.values())

    with raw_conn.cursor() as cursor:
        cursor.execute(
            sql.SQL("TRUNCATE TABLE {} RESTART IDENTITY").format(
                sql.Identifier(table_name)
            )
        )
        if payload:
            insert_sql = sql.SQL("INSERT INTO {} ({}) VALUES %s").format(
                sql.Identifier(table_name),
                sql.SQL(", ").join(
                    sql.Identifier(column_name) for column_name, _ in columns
                ),
            )
            execute_values(cursor, insert_sql.as_string(cursor), payload, page_size=25)

    return len(payload)


def _store_run_manifest(raw_conn, manifest: dict) -> int:
    with raw_conn.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS registry_etl_runs (
                run_id BIGSERIAL PRIMARY KEY,
                finished_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                manifest JSONB NOT NULL
            )
            """
        )
        cursor.execute(
            "INSERT INTO registry_etl_runs (manifest) VALUES (%s) RETURNING run_id",
            (Json(manifest),),
        )
        row = cursor.fetchone()
    return int(row[0])


def load_registry_snapshot(
    engine: Engine,
    snapshot_path: str | Path | None = None,
    *,
    reason: str,
) -> dict[str, object]:
    resolved_path = resolve_registry_snapshot_path(snapshot_path)
    if not resolved_path.exists():
        raise FileNotFoundError(f"Registry snapshot not found at {resolved_path}")

    raw_conn = engine.raw_connection()
    try:
        counts = {
            "unified_registry": _load_unified_registry(
                raw_conn, resolved_path, "unified_registry"
            )
        }
        for config in _DATASET_TABLE_CONFIG.values():
            counts[config["table"]] = _load_dataset_participants(
                raw_conn,
                resolved_path,
                config["table"],
                config["cohort"],
                config["source_dataset"],
            )

        manifest = {
            "source": "backend-registry-loader",
            "reason": reason,
            "snapshot_path": str(resolved_path),
            "counts": counts,
            "finished_at": datetime.now(timezone.utc).isoformat(),
        }
        run_id = _store_run_manifest(raw_conn, manifest)
        raw_conn.commit()
    except Exception:
        raw_conn.rollback()
        raise
    finally:
        raw_conn.close()

    return {
        "snapshot_path": str(resolved_path),
        "counts": counts,
        "run_id": run_id,
    }


def ensure_registry_snapshot_loaded(
    engine: Engine,
    snapshot_path: str | Path | None = None,
    *,
    reason: str,
    force: bool = False,
) -> dict[str, object]:
    existing_counts = get_registry_counts(engine)
    resolved_path = resolve_registry_snapshot_path(snapshot_path)
    needs_reload = force or any(
        existing_counts.get(table_name, 0) == 0 for table_name in _REGISTRY_TABLES
    )

    if not needs_reload:
        return {
            "ok": True,
            "loaded": False,
            "reason": "already-populated",
            "snapshot_path": str(resolved_path),
            "counts": existing_counts,
        }

    if not resolved_path.exists():
        logger.warning(
            "Registry snapshot reload skipped (%s): snapshot not found at %s",
            reason,
            resolved_path,
        )
        return {
            "ok": False,
            "loaded": False,
            "reason": "snapshot-missing",
            "snapshot_path": str(resolved_path),
            "counts": existing_counts,
        }

    loaded = load_registry_snapshot(engine, resolved_path, reason=reason)
    logger.info(
        "Registry snapshot loaded (%s): unified=%s bhs=%s ehvol=%s",
        reason,
        loaded["counts"]["unified_registry"],
        loaded["counts"]["bhs_participants"],
        loaded["counts"]["ehvol_participants"],
    )
    return {
        "ok": True,
        "loaded": True,
        "reason": reason,
        **loaded,
    }


def wait_for_registry_repopulation(
    engine: Engine,
    *,
    expected_tables: list[str],
    baseline_counts: dict[str, int] | None = None,
    baseline_run_id: int | None = None,
    trigger_token: str | None = None,
    timeout_s: int = REGISTRY_VERIFY_TIMEOUT_S,
    poll_interval_s: float = REGISTRY_VERIFY_POLL_INTERVAL_S,
) -> dict[str, object]:
    baseline_counts = baseline_counts or get_registry_counts(engine)
    deadline = time.monotonic() + timeout_s
    latest_counts = baseline_counts
    latest_run_id = baseline_run_id
    latest_run_event: dict[str, object] | None = None

    while time.monotonic() < deadline:
        latest_counts = get_registry_counts(engine)
        latest_run_id = get_latest_registry_run_id(engine)
        if trigger_token:
            latest_run_event = get_registry_run_event(
                engine,
                trigger_token=trigger_token,
                source="nifi-processor",
            )
        counts_ready = all(latest_counts.get(table_name, 0) > 0 for table_name in expected_tables)
        run_advanced = (
            baseline_run_id is not None
            and latest_run_id is not None
            and latest_run_id > baseline_run_id
        )
        counts_changed = any(
            latest_counts.get(table_name, 0) > baseline_counts.get(table_name, 0)
            for table_name in expected_tables
        )
        manifest = (latest_run_event or {}).get("manifest") or {}
        manifest_status = str(manifest.get("status") or "").lower()

        if trigger_token and manifest_status == "failed":
            return {
                "verified": False,
                "counts": latest_counts,
                "run_id": (latest_run_event or {}).get("run_id"),
                "manifest": manifest,
                "error": manifest.get("error") or "NiFi processor reported a failed load stage",
            }

        if trigger_token and manifest_status == "succeeded" and counts_ready:
            return {
                "verified": True,
                "counts": latest_counts,
                "run_id": (latest_run_event or {}).get("run_id"),
                "manifest": manifest,
            }

        if counts_ready and (run_advanced or counts_changed):
            return {
                "verified": True,
                "counts": latest_counts,
                "run_id": latest_run_id,
                "manifest": manifest,
            }

        time.sleep(poll_interval_s)

    return {
        "verified": False,
        "counts": latest_counts,
        "run_id": latest_run_id,
        "manifest": (latest_run_event or {}).get("manifest") if latest_run_event else None,
    }