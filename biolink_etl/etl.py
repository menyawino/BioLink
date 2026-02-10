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


def drop_name_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Drop columns that likely contain personal names (PII).

    Returns (df, dropped_columns)
    """
    cols_to_drop = []
    for col in list(df.columns):
        c = str(col)
        # match standalone 'name', columns starting with name, or typical name fields
        if re.search(r"\bname\b", c, flags=re.IGNORECASE) or re.search(r"first\s*name|last\s*name|full\s*name", c, flags=re.IGNORECASE):
            cols_to_drop.append(col)

    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)
    return df, cols_to_drop


def standardize_dates(df: pd.DataFrame, dayfirst: bool = True) -> tuple[pd.DataFrame, list[str]]:
    """Convert date-like columns to pandas datetime dtype.

    Heuristics: column name contains 'date', 'dob', 'birth', 'enrol', 'exam', 'echo', 'mri'
    Returns (df, converted_columns)
    """
    date_keywords = [r"date", r"dob", r"birth", r"enrol", r"enroll", r"exam", r"examination", r"echo", r"mri"]
    pattern = re.compile("|".join(date_keywords), flags=re.IGNORECASE)
    converted = []
    for col in list(df.columns):
        if pattern.search(col):
            try:
                parsed = pd.to_datetime(df[col], dayfirst=dayfirst, errors='coerce')
            except Exception:
                parsed = pd.to_datetime(df[col].astype(str), dayfirst=dayfirst, errors='coerce')
            # Only keep conversion if a reasonable fraction parsed
            non_null = parsed.notna().sum()
            if non_null > 0:
                df[col] = parsed
                converted.append(col)

    return df, converted


def _find_city_column(df: pd.DataFrame) -> str | None:
    # Heuristic: find a column mentioning current + city + resid
    for col in df.columns:
        c = str(col).lower()
        if 'current' in c and 'city' in c:
            return col
    # fallback: any column with 'city' in name
    for col in df.columns:
        if 'city' in str(col).lower():
            return col
    return None


def _load_local_city_map(root: Path) -> dict[str, tuple[float, float]]:
    path = root / 'db' / 'city_coords.csv'
    mapping: dict[str, tuple[float, float]] = {}
    if path.exists():
        try:
            dfm = pd.read_csv(path)
            for _, r in dfm.iterrows():
                name = str(r.get('city') or r.get('name') or r.get('city_name')).strip().lower()
                lat = float(r.get('lat'))
                lon = float(r.get('lon') or r.get('lng') or r.get('lon'))
                mapping[name] = (lat, lon)
        except Exception:
            pass
    return mapping


def _save_local_city_map(root: Path, mapping: dict[str, tuple[float, float]]):
    path = root / 'db' / 'city_coords.csv'
    try:
        rows = [{'city': k, 'lat': v[0], 'lon': v[1]} for k, v in mapping.items()]
        pd.DataFrame(rows).to_csv(path, index=False)
    except Exception:
        pass


def _geocode_city_nominatim(city: str) -> tuple[float, float] | None:
    # Simple Nominatim request (OpenStreetMap). Keep it polite and minimal.
    try:
        import requests
        url = 'https://nominatim.openstreetmap.org/search'
        params = {'q': city, 'format': 'json', 'limit': 1}
        headers = {'User-Agent': 'BioLink-ETL/1.0 (+https://example.com)'}
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data:
            lat = float(data[0]['lat'])
            lon = float(data[0]['lon'])
            return (lat, lon)
    except Exception:
        return None
    return None


def geocode_cities(df: pd.DataFrame, root: Path | None = None, city_col: str | None = None, lat_col: str = 'current_city_lat', lon_col: str = 'current_city_lon', max_lookup: int = 50) -> tuple[pd.DataFrame, dict[str, tuple[float, float]]]:
    """Add latitude/longitude columns based on a city column.

    Uses local mapping `db/city_coords.csv` if present; otherwise queries Nominatim
    for up to `max_lookup` unique city names and stores results back to the local map.
    Returns (df, mapping_added)
    """
    if root is None:
        root = Path(__file__).resolve().parent.parent

    if city_col is None:
        city_col = _find_city_column(df)
    if city_col is None:
        return df, {}

    local_map = _load_local_city_map(root)
    mapping_added: dict[str, tuple[float, float]] = {}

    unique_cities = pd.Series(df[city_col].dropna().unique()).astype(str)
    # normalize
    unique_norm = unique_cities.str.strip().str.lower()
    lookup_needed = []
    for orig, norm in zip(unique_cities, unique_norm):
        if norm in local_map:
            continue
        lookup_needed.append((orig, norm))

    # limit lookups to avoid heavy external calls
    lookup_needed = lookup_needed[:max_lookup]

    for orig, norm in lookup_needed:
        res = _geocode_city_nominatim(orig)
        if res:
            local_map[norm] = res
            mapping_added[norm] = res
        else:
            # try using just city name without extra parts
            short = orig.split(',')[0]
            res2 = _geocode_city_nominatim(short)
            if res2:
                local_map[norm] = res2
                mapping_added[norm] = res2
        import time
        time.sleep(1)

    # apply mapping
    lats = []
    lons = []
    for v in df[city_col].astype(str):
        key = v.strip().lower()
        coords = local_map.get(key)
        if coords:
            lats.append(coords[0])
            lons.append(coords[1])
        else:
            lats.append(None)
            lons.append(None)

    df[lat_col] = lats
    df[lon_col] = lons

    # persist mapping for future runs
    if mapping_added:
        _save_local_city_map(root, local_map)

    return df, mapping_added


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


def run_etl(csv_path: str, table: str, schema: str, db_uri: str, replace: bool = False, nrows: int | None = None):
    csv = Path(csv_path)
    if not csv.exists():
        raise FileNotFoundError(f"CSV not found: {csv}")

    # Allow loading a subset of rows for faster tests
    if nrows is not None:
        df_raw = pd.read_csv(csv, nrows=nrows)
    else:
        df_raw = pd.read_csv(csv)
    cleaning = load_cleaning_module()
    df_clean = cleaning.apply_all_cleaning(df_raw.copy())
    # Drop PII name columns
    df_clean, dropped_names = drop_name_columns(df_clean)
    if dropped_names:
        print(f"Dropped name columns: {dropped_names}")

    # Standardize date columns into datetime dtype
    df_clean, converted_dates = standardize_dates(df_clean)
    if converted_dates:
        print(f"Converted date columns: {converted_dates}")

    # Geocode current city to lat/lon (adds `current_city_lat`, `current_city_lon`)
    try:
        df_clean, mapping_added = geocode_cities(df_clean, root=ROOT)
        if mapping_added:
            print(f"Geocoded {len(mapping_added)} new cities and saved mapping.")
    except Exception as e:
        print(f"Warning: geocoding failed: {e}")

    df_clean = sanitize_column_names(df_clean)
    write_dataframe_to_db(df_clean, table, schema, db_uri, replace=replace)
    return len(df_clean)
