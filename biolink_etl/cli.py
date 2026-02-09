"""Command-line wrapper for biolink_etl.run"""
from pathlib import Path
import sys
import argparse
from .etl import run_etl

# Ensure backend-py is on path so `app.config` can be imported when running as module
ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend-py"
sys.path.insert(0, str(BACKEND))
from app.config import settings


def main():
    parser = argparse.ArgumentParser(description="biolink ETL: homogenize and load a CSV")
    parser.add_argument("--csv", required=True, help="CSV to load")
    parser.add_argument("--table", default=settings.superset_default_table, help="Destination table name")
    parser.add_argument("--schema", default=settings.superset_default_schema, help="Destination schema")
    parser.add_argument("--replace", action="store_true", help="Replace table instead of append")
    args = parser.parse_args()

    count = run_etl(args.csv, args.table, args.schema, settings.superset_database_uri, replace=args.replace)
    print(f"ETL complete: {count} rows written to {args.schema}.{args.table}")


if __name__ == '__main__':
    main()
