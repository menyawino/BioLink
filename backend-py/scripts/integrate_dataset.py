#!/usr/bin/env python3
"""Integrate a clinical CSV into the BioLink DB and register it in Superset.

Usage:
  python integrate_dataset.py --csv /path/to/file.csv --table EHVOL --schema public --replace

This script:
 - loads a CSV
 - runs the cleaning pipeline from db/clean_clinical_data.py
 - writes the cleaned dataframe into the Superset/Postgres database
 - calls the Superset API to get-or-create the database and dataset
"""
from pathlib import Path
import argparse
import asyncio
import importlib.util
import sys
import pandas as pd
from sqlalchemy import create_engine
import re

# Ensure backend-py directory is on path so we can import app.config
THIS_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = THIS_DIR.parent
sys.path.insert(0, str(BACKEND_ROOT))

from app.config import settings as backend_settings  # type: ignore
from app.services.superset_client import SupersetClient  # type: ignore


def load_cleaning_module():
    # Load db/clean_clinical_data.py dynamically from repository root db/
    cleaning_path = BACKEND_ROOT.parent / "db" / "clean_clinical_data.py"
    spec = importlib.util.spec_from_file_location("clean_clinical_data", cleaning_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore
    return module


def write_dataframe_to_db(df: pd.DataFrame, table: str, schema: str, uri: str, replace: bool = False):
    engine = create_engine(uri)
    if_exists = "replace" if replace else "append"
    print(f"Writing {len(df)} rows to {schema}.{table} (if_exists={if_exists})")
    df.to_sql(table, engine, schema=schema, if_exists=if_exists, index=False, method="multi", chunksize=1000)
    print("Write complete.")


def sanitize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Sanitize and deduplicate column names to avoid SQL errors."""
    # Create SQL-safe, short, unique column names that respect PostgreSQL's
    # 63-character identifier limit. We produce lowercase snake_case names.
    MAX_IDENT = 63
    new_cols = []
    seen: dict[str, int] = {}
    originals = list(df.columns)
    for i, col in enumerate(originals):
        c = str(col).strip()
        c = c.replace('\n', ' ').replace('\r', ' ')
        c = re.sub(r'\s+', ' ', c)
        # Make SQL-safe token
        token = re.sub(r'[^0-9A-Za-z_]', '_', c).strip('_').lower()
        if token == '':
            token = f'col_{i+1}'
        # Truncate base to leave room for suffixes
        base_max = MAX_IDENT - 5
        if len(token) > base_max:
            token = token[:base_max]
        base = token
        if base in seen:
            seen[base] += 1
            suffix = f"_{seen[base]}"
            # Ensure final token <= MAX_IDENT
            token = (base[: MAX_IDENT - len(suffix)]) + suffix
        else:
            seen[base] = 0
        new_cols.append(token)

    # Save a mapping for reference (original -> sanitized)
    mapping_path = THIS_DIR / f"column_map_integrate_dataset.csv"
    try:
        pd.DataFrame({"original": originals, "sanitized": new_cols}).to_csv(mapping_path, index=False)
        print(f"Saved column mapping to {mapping_path}")
    except Exception:
        pass

    df.columns = new_cols
    return df


async def register_in_superset(table: str, schema: str):
    client = SupersetClient.from_settings()
    # bootstrap returns tokens
    tokens = await client.bootstrap()
    access_token = tokens.get("access_token")
    csrf_token = tokens.get("csrf_token")

    import aiohttp

    async with aiohttp.ClientSession() as session:
        # Ensure the Superset DB record exists (points to the DB URI used by Superset)
        db_id = await client.get_or_create_database(
            session, access_token, csrf_token,
            name=backend_settings.superset_database_name,
            uri=backend_settings.superset_database_uri,
        )

        dataset_id = await client.get_or_create_dataset(
            session, access_token, csrf_token,
            database_id=db_id,
            schema=schema,
            table_name=table,
        )

    print(f"Superset dataset ID: {dataset_id}")
    return dataset_id


def main():
    parser = argparse.ArgumentParser(description="Integrate and register clinical CSVs")
    parser.add_argument("--csv", required=True, help="Path to the CSV file to integrate")
    parser.add_argument("--table", required=False, default=backend_settings.superset_default_table, help="Destination table name")
    parser.add_argument("--schema", required=False, default=backend_settings.superset_default_schema, help="Destination schema")
    parser.add_argument("--replace", action="store_true", help="Replace the table instead of appending")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"CSV file not found: {csv_path}")
        raise SystemExit(1)

    print(f"Loading CSV: {csv_path}")
    df_raw = pd.read_csv(csv_path)

    cleaning = load_cleaning_module()
    print("Cleaning data using db/clean_clinical_data.apply_all_cleaning...")
    df_cleaned = cleaning.apply_all_cleaning(df_raw.copy())

    # Sanitize column names to avoid SQL duplicate column errors
    print("Sanitizing column names...")
    df_cleaned = sanitize_column_names(df_cleaned)

    # Write cleaned dataframe into Superset/Postgres DB
    write_dataframe_to_db(df_cleaned, args.table, args.schema, backend_settings.superset_database_uri, replace=args.replace)

    # Register/refresh dataset in Superset
    print("Registering dataset in Superset...")
    try:
        asyncio.run(register_in_superset(args.table, args.schema))
    except Exception as e:
        print(f"Warning: failed to register dataset in Superset: {e}")

    print("Integration complete.")


if __name__ == "__main__":
    main()
