#!/usr/bin/env python3
"""Run ETL for three EHVol datasets and register them in Superset.

Datasets (CSV -> table):
- db/reduced_ehvol_50.csv -> public.ehvol_50
- db/100925_Cleaned_EHVol_Data_STANDARDIZED.csv -> public.ehvol_cleaned
- db/EHVol_Full.csv -> public.ehvol_full

The script runs the ETL (replace) so geocoding is applied, then creates/gets
Superset datasets for each table.
"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[2]
# Add backend and repo root so imports work when running from project root
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(REPO_ROOT))
# ensure biolink_etl package is importable
sys.path.insert(0, str(REPO_ROOT / 'biolink_etl'))

from biolink_etl.etl import run_etl
import asyncio
import aiohttp
from app.services.superset_client import SupersetClient
from app.config import settings


def _infer_table_name(path: str) -> str:
    p = Path(path)
    name = p.stem
    name = name.lower()
    # sanitize to basic identifier
    import re
    name = re.sub(r"[^0-9a-z_]+", "_", name)
    name = name.strip("_")
    return name


def run_all_etl(inputs: list[str], replace: bool = True):
    """Run ETL for a list of csv paths or csv:table mappings.

    Each item may be either:
      - path/to/file.csv
      - path/to/file.csv:table_name

    Returns list of (table, count, error)
    """
    results = []
    for item in inputs:
        if ":" in item and item.count(":") == 1 and not item.startswith("http"):
            csv_path, table = item.split(":", 1)
        else:
            csv_path = item
            table = _infer_table_name(item)

        csvs = str(Path(csv_path))
        print(f"Running ETL for {csvs} -> public.{table} (replace={replace})")
        try:
            count = run_etl(csvs, table, 'public', settings.superset_database_uri, replace=replace)
            print(f"Wrote {count} rows to public.{table}")
            results.append((table, count, None))
        except Exception as e:
            print(f"ETL failed for {csvs}: {e}")
            results.append((table, 0, e))
    return results


async def register_all_in_superset(tables: list[str]):
    client = SupersetClient.from_settings()
    async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar(unsafe=True)) as session:
        tokens = await client.bootstrap()
        at = tokens['access_token']; csrf = tokens.get('csrf_token')
        db_id = await client.get_or_create_database(session, at, csrf, settings.superset_database_name, settings.superset_database_uri)
        created = {}
        for t in tables:
            try:
                ds_id = await client.get_or_create_dataset(session, at, csrf, database_id=db_id, schema='public', table_name=t)
                print(f"Superset dataset for public.{t} -> id={ds_id}")
                created[t] = ds_id
            except Exception as e:
                print(f"Failed to create/register dataset for {t}: {e}")
                created[t] = None
        return created


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run ETL on provided CSVs and optionally register in Superset")
    parser.add_argument('inputs', nargs='+', help='CSV paths or csv:table mappings')
    parser.add_argument('--no-register', action='store_true', help='Do not register datasets in Superset')
    parser.add_argument('--replace', action='store_true', default=True, help='Replace destination tables (default)')
    parser.add_argument('--append', action='store_true', help='Append to destination tables instead of replace')
    args = parser.parse_args()

    replace = True
    if args.append:
        replace = False

    etl_results = run_all_etl(args.inputs, replace=replace)
    tables = [r[0] for r in etl_results if r[1] > 0]
    if not tables:
        print("No tables written; aborting Superset registration")
        return 2

    if args.no_register:
        print("ETL finished; registration skipped (--no-register)")
        return 0

    print("Registering tables in Superset:", tables)
    created = asyncio.run(register_all_in_superset(tables))
    print("Superset registration results:")
    for t, dsid in created.items():
        print(f"  {t}: {dsid}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
