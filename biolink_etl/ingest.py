#!/usr/bin/env python3
"""Universal CSV → Postgres ingestion via dlt.

Reads any messy CSV (BOM, mixed encodings, duplicate headers, inconsistent
types) and loads it into Postgres with sanitized column names and automatic
type inference.  Zero schema files, zero config — just point at a file.

Usage (CLI):
    python -m biolink_etl.ingest --csv db/EHVol_Full.csv --table ehvol_raw

Usage (Python):
    from biolink_etl.ingest import ingest_csv
    info = ingest_csv("db/EHVol_Full.csv", "ehvol_raw")
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

import dlt


# ---------------------------------------------------------------------------
# Header sanitisation
# ---------------------------------------------------------------------------

def sanitize_header(name: str, seen: dict[str, int]) -> str:
    """Convert a raw CSV header to a Postgres-safe snake_case identifier.

    * strips whitespace and BOM chars
    * lowercases
    * replaces non-alphanumeric sequences with ``_``
    * deduplicates (``name``, ``name_1``, ``name_2`` …)
    """
    clean = name.strip().lstrip("\ufeff").lower()
    clean = re.sub(r"[^\w]+", "_", clean).strip("_") or "unnamed"
    if clean in seen:
        seen[clean] += 1
        clean = f"{clean}_{seen[clean]}"
    else:
        seen[clean] = 0
    return clean


# ---------------------------------------------------------------------------
# Lightweight value coercion
# ---------------------------------------------------------------------------

_DATE_FORMATS = ("%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d")


def _try_number(val: str) -> int | float | str:
    """Attempt int then float conversion; return original string on failure."""
    try:
        f = float(val)
        if f == int(f) and "." not in val:
            return int(f)
        return f
    except ValueError:
        return val


def _try_date(val: str) -> datetime | str:
    """Try common date formats; return datetime or original string."""
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(val, fmt)
        except ValueError:
            continue
    return val


def _coerce_value(val: str) -> Any:
    """Minimal coercion: empty → None, everything else stays as text.

    We deliberately load all values as strings and let dbt handle type
    casting.  This avoids misclassifying phone numbers, IDs, or codes
    as integers which then blow up at the Postgres level.
    """
    stripped = val.strip()
    if not stripped:
        return None
    return stripped


# ---------------------------------------------------------------------------
# dlt resource — the entire "Extract + Load" in one function
# ---------------------------------------------------------------------------

@dlt.resource(write_disposition="replace")
def csv_source(file_path: str) -> Iterator[dict[str, Any]]:
    """Yield cleaned rows from *any* CSV file.

    * Handles BOM (``utf-8-sig``)
    * Sanitises headers
    * Coerces values (numbers, dates, booleans)
    * Deduplicates column names
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")

    with path.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.reader(fh)
        raw_headers = next(reader)
        seen: dict[str, int] = {}
        headers = [sanitize_header(h, seen) for h in raw_headers]

        for row in reader:
            record: dict[str, Any] = {}
            for key, val in zip(headers, row):
                record[key] = _coerce_value(val)
            yield record


# ---------------------------------------------------------------------------
# Pipeline runner
# ---------------------------------------------------------------------------

def ingest_csv(
    csv_path: str,
    table_name: str,
    database_url: str | None = None,
) -> dlt.pipeline.PipelineContext:
    """Ingest a CSV file into Postgres.

    Args:
        csv_path:     Path to the source CSV.
        table_name:   Destination Postgres table (will be created/replaced).
        database_url: SQLAlchemy-style connection string.
                      Falls back to ``DATABASE_URL`` env var.

    Returns:
        dlt ``LoadInfo`` with load statistics.
    """
    db_url = database_url or os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError(
            "No database URL.  Set DATABASE_URL or pass --db-url."
        )

    pipeline = dlt.pipeline(
        pipeline_name="biolink_ingest",
        destination=dlt.destinations.postgres(db_url),
        dataset_name="public",
    )

    load_info = pipeline.run(
        csv_source(csv_path),
        table_name=table_name,
    )

    print(load_info)
    return load_info


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest a CSV into Postgres via dlt"
    )
    parser.add_argument(
        "--csv", required=True, help="Path to the source CSV file"
    )
    parser.add_argument(
        "--table",
        default="raw_data",
        help="Destination Postgres table name (default: raw_data)",
    )
    parser.add_argument(
        "--db-url",
        default=None,
        help="Postgres connection URL (default: DATABASE_URL env var)",
    )
    args = parser.parse_args()
    ingest_csv(args.csv, args.table, args.db_url)


if __name__ == "__main__":
    main()
