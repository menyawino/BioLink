"""Clone an existing EHVOL table and add a `governorate_iso` column.

Creates a new table `ehvol_full_iso` in the same schema by default.
The ISO-like code is generated as `EG-` + uppercased slug of the governorate
name (spaces -> '-') so it's predictable and searchable.
"""
from pathlib import Path
import re
import sys
import argparse

import pandas as pd
from sqlalchemy import create_engine

# Ensure the backend package root is on sys.path so `app` can be imported when
# running this script directly from repo root.
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config import settings


def find_city_column(columns: list[str]) -> str | None:
    names = [c.lower() for c in columns]
    candidates = [
        'current_city_of_residence',
        'current_city',
        'current_city_of_residence',
        'current_city_category',
        'current_city',
        'city_of_residence',
        'current_city_name',
    ]
    for cand in candidates:
        if cand in names:
            return columns[names.index(cand)]
    # fallback: any column containing 'current' and 'city' or just 'city'
    for i, c in enumerate(names):
        if 'current' in c and 'city' in c:
            return columns[i]
    for i, c in enumerate(names):
        if 'city' == c or 'city' in c:
            return columns[i]
    return None


def make_iso_code(name: str) -> str | None:
    if name is None:
        return None
    s = str(name).strip()
    if s == '' or s.lower() in ('nan', 'none'):
        return None
    # normalize: keep letters, numbers and spaces, convert to hyphen separated, uppercase
    s = s.replace("/", "-").replace("_", " ")
    s = re.sub(r"[^0-9A-Za-z\-\s]", "", s)
    s = re.sub(r"\s+", "-", s.strip())
    code = f"EG-{s.upper()}"
    return code


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--src-table', default='ehvol_full')
    p.add_argument('--dst-table', default='ehvol_full_iso')
    p.add_argument('--schema', default='public')
    args = p.parse_args()

    db_uri = settings.database_url
    engine = create_engine(db_uri)

    src = args.src_table
    dst = args.dst_table
    schema = args.schema

    print(f"Connecting to DB and reading {schema}.{src}...")
    sql = f'SELECT * FROM "{schema}"."{src}"'
    try:
        df = pd.read_sql_query(sql, con=engine)
    except Exception as e:
        print(f"Error reading source table: {e}")
        sys.exit(2)

    city_col = find_city_column(list(df.columns))
    if city_col is None:
        print("Could not find a city/governorate column in the source table; aborting.")
        sys.exit(3)

    print(f"Using city column: {city_col}")
    df['governorate_iso'] = df[city_col].apply(make_iso_code)

    # write to new table
    print(f"Writing {len(df)} rows to {schema}.{dst} (replace existing)...")
    try:
        df.to_sql(dst, engine, schema=schema, if_exists='replace', index=False, method='multi')
    except Exception as e:
        print(f"Error writing destination table: {e}")
        sys.exit(4)

    print("Done.")


if __name__ == '__main__':
    main()
