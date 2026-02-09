"""ETL helpers: load, homogenize (via db/clean_clinical_data), write to DB, register in Superset."""
from pathlib import Path
import importlib.util
import sys
import re
import pandas as pd
from sqlalchemy import create_engine
import asyncio


THIS_DIR = Path(__file__).resolve().parent
ROOT = THIS_DIR.parent


def load_cleaning_module():
    cleaning_path = ROOT / "db" / "clean_clinical_data.py"
    spec = importlib.util.spec_from_file_location("clean_clinical_data", cleaning_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore
    return module


def sanitize_column_names(df: pd.DataFrame, mapping_name: str = "column_map_etl.csv") -> pd.DataFrame:
    MAX_IDENT = 63
    originals = list(df.columns)
    new_cols = []
    seen: dict[str, int] = {}
    for i, col in enumerate(originals):
        c = str(col).strip()
        c = c.replace('\n', ' ').replace('\r', ' ')
        c = re.sub(r'\s+', ' ', c)
        token = re.sub(r'[^0-9A-Za-z_]', '_', c).strip('_').lower()
        if token == '':
            token = f'col_{i+1}'
        base_max = MAX_IDENT - 5
        if len(token) > base_max:
            token = token[:base_max]
        base = token
        if base in seen:
            seen[base] += 1
            suffix = f"_{seen[base]}"
            token = (base[: MAX_IDENT - len(suffix)]) + suffix
        else:
            seen[base] = 0
        new_cols.append(token)

    mapping_path = THIS_DIR / mapping_name
    try:
        pd.DataFrame({"original": originals, "sanitized": new_cols}).to_csv(mapping_path, index=False)
    except Exception:
        pass

    df.columns = new_cols
    return df


def write_dataframe_to_db(df: pd.DataFrame, table: str, schema: str, uri: str, replace: bool = False):
    engine = create_engine(uri)
    if_exists = "replace" if replace else "append"
    df.to_sql(table, engine, schema=schema, if_exists=if_exists, index=False, method="multi", chunksize=1000)


async def register_in_superset(table: str, schema: str, client):
    tokens = await client.bootstrap()
    access_token = tokens.get("access_token")
    csrf_token = tokens.get("csrf_token")
    import aiohttp
    async with aiohttp.ClientSession() as session:
        db_id = await client.get_or_create_database(
            session, access_token, csrf_token, name=client.base_url, uri=client.base_url
        )
        dataset_id = await client.get_or_create_dataset(
            session, access_token, csrf_token, database_id=db_id, schema=schema, table_name=table
        )
    return dataset_id


def run_etl(csv_path: str, table: str, schema: str, db_uri: str, replace: bool = False):
    csv = Path(csv_path)
    if not csv.exists():
        raise FileNotFoundError(f"CSV not found: {csv}")

    df_raw = pd.read_csv(csv)
    cleaning = load_cleaning_module()
    df_clean = cleaning.apply_all_cleaning(df_raw.copy())
    df_clean = sanitize_column_names(df_clean)
    write_dataframe_to_db(df_clean, table, schema, db_uri, replace=replace)
    return len(df_clean)
