#!/usr/bin/env python3
"""Unified ETL pipeline + governed protocol handler.

Single entry point for cleaning, DB write, Superset registration, ISO mapping, and refresh.
"""
from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import create_engine, text


THIS_DIR = Path(__file__).resolve().parent
ROOT = THIS_DIR.parent
BACKEND = ROOT / "backend-py"

PROTOCOL_VERSION = "1.0"

ISO_MAPPING = {
    "EG-MATRUH": "EG-MT",
    "EG-ISMAILIA": "EG-IS",
    "EG-ALEXANDRIA": "EG-ALX",
    "EG-OTHER": "EG-OTHER",
    "EG-SUEZ": "EG-SUZ",
    "EG-RED-SEA": "EG-BA",
    "EG-QALOUBYA": "EG-KB",
    "EG-BEHAIRA": "EG-BH",
    "EG-MENOUFYA": "EG-MNF",
    "EG-PORT-SAID": "EG-PTS",
    "EG-CAIRO": "EG-C",
    "EG-KAFR-EL-SHEIKH": "EG-KFS",
    "EG-BENI-SEWEIF": "EG-BNS",
    "EG-DAKHALIA": "EG-DK",
    "EG-SOUTH-SINAI": "EG-JS",
    "EG-ASSUIT": "EG-AST",
    "EG-GIZA": "EG-GZ",
    "EG-DAMIETTA": "EG-DT",
    "EG-QENA": "EG-KN",
    "EG-SHARKIA": "EG-SHR",
    "EG-GHARBYA": "EG-GH",
    "EG-SOHAG": "EG-SHG",
    "EG-ASWAN": "EG-ASN",
}


@dataclass
class PipelineOptions:
    csv_path: str
    table: str
    schema: str
    replace: bool = False
    nrows: int | None = None
    skip_superset: bool = False
    skip_iso_mapping: bool = False
    skip_refresh: bool = False


def _add_backend_to_path():
    if str(BACKEND) not in sys.path:
        sys.path.insert(0, str(BACKEND))


def load_settings():
    _add_backend_to_path()
    try:
        from app.config import settings  # type: ignore
        return settings
    except Exception:
        # fallback: direct module load
        cfg_path = BACKEND / "app" / "config.py"
        spec = importlib.util.spec_from_file_location("app_config", cfg_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore
        return getattr(module, "settings")


def load_cleaning_module():
    cleaning_path = ROOT / "db" / "clean_clinical_data.py"
    spec = importlib.util.spec_from_file_location("clean_clinical_data", cleaning_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore
    return module


def sanitize_column_names(df: pd.DataFrame, mapping_name: str = "column_map_etl.csv") -> pd.DataFrame:
    max_ident = 63
    originals = list(df.columns)
    new_cols = []
    seen: dict[str, int] = {}
    for i, col in enumerate(originals):
        c = str(col).strip()
        c = c.replace("\n", " ").replace("\r", " ")
        c = re.sub(r"\s+", " ", c)
        token = re.sub(r"[^0-9A-Za-z_]", "_", c).strip("_").lower()
        if token == "":
            token = f"col_{i+1}"
        base_max = max_ident - 5
        if len(token) > base_max:
            token = token[:base_max]
        base = token
        if base in seen:
            seen[base] += 1
            suffix = f"_{seen[base]}"
            token = (base[: max_ident - len(suffix)]) + suffix
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
    cols_to_drop = []
    for col in list(df.columns):
        c = str(col)
        if re.search(r"\bname\b", c, flags=re.IGNORECASE) or re.search(r"first\s*name|last\s*name|full\s*name", c, flags=re.IGNORECASE):
            cols_to_drop.append(col)

    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)
    return df, cols_to_drop


def standardize_dates(df: pd.DataFrame, dayfirst: bool = True) -> tuple[pd.DataFrame, list[str]]:
    date_keywords = [r"date", r"dob", r"birth", r"enrol", r"enroll", r"exam", r"examination", r"echo", r"mri"]
    pattern = re.compile("|".join(date_keywords), flags=re.IGNORECASE)
    converted = []
    for col in list(df.columns):
        if pattern.search(col):
            try:
                parsed = pd.to_datetime(df[col], dayfirst=dayfirst, errors="coerce")
            except Exception:
                parsed = pd.to_datetime(df[col].astype(str), dayfirst=dayfirst, errors="coerce")
            non_null = parsed.notna().sum()
            if non_null > 0:
                df[col] = parsed
                converted.append(col)

    return df, converted


def _find_city_column(df: pd.DataFrame) -> str | None:
    for col in df.columns:
        c = str(col).lower()
        if "current" in c and "city" in c:
            return col
    for col in df.columns:
        if "city" in str(col).lower():
            return col
    return None


def _load_local_city_map(root: Path) -> dict[str, tuple[float, float]]:
    path = root / "db" / "city_coords.csv"
    mapping: dict[str, tuple[float, float]] = {}
    if path.exists():
        try:
            dfm = pd.read_csv(path)
            for _, r in dfm.iterrows():
                name = str(r.get("city") or r.get("name") or r.get("city_name")).strip().lower()
                lat = float(r.get("lat"))
                lon = float(r.get("lon") or r.get("lng") or r.get("lon"))
                mapping[name] = (lat, lon)
        except Exception:
            pass
    return mapping


def _save_local_city_map(root: Path, mapping: dict[str, tuple[float, float]]):
    path = root / "db" / "city_coords.csv"
    try:
        rows = [{"city": k, "lat": v[0], "lon": v[1]} for k, v in mapping.items()]
        pd.DataFrame(rows).to_csv(path, index=False)
    except Exception:
        pass


def _geocode_city_nominatim(city: str) -> tuple[float, float] | None:
    try:
        import requests
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": city, "format": "json", "limit": 1}
        headers = {"User-Agent": "BioLink-ETL/1.0 (+https://example.com)"}
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            return (lat, lon)
    except Exception:
        return None
    return None


def geocode_cities(
    df: pd.DataFrame,
    root: Path | None = None,
    city_col: str | None = None,
    lat_col: str = "current_city_lat",
    lon_col: str = "current_city_lon",
    max_lookup: int = 50,
) -> tuple[pd.DataFrame, dict[str, tuple[float, float]]]:
    if root is None:
        root = ROOT

    if city_col is None:
        city_col = _find_city_column(df)
    if city_col is None:
        return df, {}

    local_map = _load_local_city_map(root)
    mapping_added: dict[str, tuple[float, float]] = {}

    unique_cities = pd.Series(df[city_col].dropna().unique()).astype(str)
    unique_norm = unique_cities.str.strip().str.lower()
    lookup_needed = []
    for orig, norm in zip(unique_cities, unique_norm):
        if norm in local_map:
            continue
        lookup_needed.append((orig, norm))

    lookup_needed = lookup_needed[:max_lookup]

    for orig, norm in lookup_needed:
        res = _geocode_city_nominatim(orig)
        if res:
            local_map[norm] = res
            mapping_added[norm] = res
        else:
            short = orig.split(",")[0]
            res2 = _geocode_city_nominatim(short)
            if res2:
                local_map[norm] = res2
                mapping_added[norm] = res2
        import time
        time.sleep(1)

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

    if mapping_added:
        _save_local_city_map(root, local_map)

    return df, mapping_added


def write_dataframe_to_db(df: pd.DataFrame, table: str, schema: str, uri: str, replace: bool = False):
    engine = create_engine(uri)
    if_exists = "replace" if replace else "append"
    df.to_sql(table, engine, schema=schema, if_exists=if_exists, index=False, method="multi", chunksize=1000)


def _get_superset_client():
    _add_backend_to_path()
    from app.services.superset_client import SupersetClient  # type: ignore
    return SupersetClient.from_settings()


def _get_database_uri() -> str:
    settings = load_settings()
    return settings.database_url


def _get_superset_db_settings() -> tuple[str, str]:
    settings = load_settings()
    return settings.superset_database_name, settings.superset_database_uri


def apply_iso_mapping(engine, schema: str, table: str) -> int:
    cases = []
    for src, dst in ISO_MAPPING.items():
        cases.append(f"WHEN governorate_iso = '{src}' THEN '{dst}'")

    case_sql = "\n        ".join(cases)
    sql = f"UPDATE \"{schema}\".\"{table}\"\nSET governorate_iso = CASE\n        {case_sql}\n        ELSE governorate_iso END"
    with engine.begin() as conn:
        res = conn.execute(text(sql))
        return res.rowcount or 0


def run_etl(csv_path: str, table: str, schema: str, db_uri: str, replace: bool = False, nrows: int | None = None) -> dict[str, Any]:
    csv = Path(csv_path)
    if not csv.exists():
        raise FileNotFoundError(f"CSV not found: {csv}")

    if nrows is not None:
        df_raw = pd.read_csv(csv, nrows=nrows)
    else:
        df_raw = pd.read_csv(csv)
    cleaning = load_cleaning_module()
    df_clean = cleaning.apply_all_cleaning(df_raw.copy())

    df_clean, dropped_names = drop_name_columns(df_clean)
    df_clean, converted_dates = standardize_dates(df_clean)

    mapping_added = {}
    try:
        df_clean, mapping_added = geocode_cities(df_clean, root=ROOT)
    except Exception as e:
        print(f"Warning: geocoding failed: {e}")

    df_clean = sanitize_column_names(df_clean)
    write_dataframe_to_db(df_clean, table, schema, db_uri, replace=replace)

    return {
        "rows_written": len(df_clean),
        "dropped_name_columns": dropped_names,
        "converted_date_columns": converted_dates,
        "geocoded_new_cities": len(mapping_added),
    }


async def register_superset_alias(table: str, schema: str, alias: str) -> int | None:
    client = _get_superset_client()
    import aiohttp

    async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar(unsafe=True)) as session:
        tokens = await client.bootstrap()
        access_token = tokens["access_token"]
        csrf_token = tokens["csrf_token"]

        db_name, db_uri = _get_superset_db_settings()
        db_id = await client.get_or_create_database(session, access_token, csrf_token, db_name, db_uri)

        variants = [
            {"database": db_id, "schema": schema, "table_name": table, "dataset_name": alias},
            {"database": db_id, "schema": schema, "table_name": table, "name": alias},
            {"database": db_id, "schema": schema, "table_name": alias},
            {"database": db_id, "schema": None, "table_name": alias, "sql": f"SELECT * FROM {schema}.{table}"},
        ]

        for payload in variants:
            try:
                created = await client._request(session, "POST", "/api/v1/dataset/", access_token, csrf_token, json_body=payload)
                dataset_id = client._extract_id(created)
                if dataset_id is not None:
                    return dataset_id
            except Exception:
                continue

    return None


async def refresh_superset_dataset(table: str, schema: str, alias: str | None = None) -> list[int]:
    client = _get_superset_client()
    import aiohttp

    refreshed = []
    async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar(unsafe=True)) as session:
        tokens = await client.bootstrap()
        access_token = tokens["access_token"]
        csrf_token = tokens.get("csrf_token")

        datasets = await client._list_resource(session, access_token, "dataset")
        matches = []
        for d in datasets:
            if alias and d.get("table_name") == alias:
                matches.append(d)
            elif d.get("table_name") == table and d.get("schema") == schema:
                matches.append(d)

        for d in matches:
            dataset_id = int(d["id"])
            try:
                path = f"/api/v1/dataset/{dataset_id}/refresh"
                await client._request(session, "POST", path, access_token, csrf_token, json_body={})
                refreshed.append(dataset_id)
                continue
            except Exception:
                pass

            try:
                put_path = f"/api/v1/dataset/{dataset_id}"
                existing_sql = d.get("sql")
                payload = {"sql": existing_sql or f"SELECT * FROM {schema}.{table}"}
                await client._request(session, "PUT", put_path, access_token, csrf_token, json_body=payload)
                refreshed.append(dataset_id)
            except Exception:
                continue

    return refreshed


def run_pipeline(opts: PipelineOptions) -> dict[str, Any]:
    db_uri = _get_database_uri()

    result = run_etl(
        csv_path=opts.csv_path,
        table=opts.table,
        schema=opts.schema,
        db_uri=db_uri,
        replace=opts.replace,
        nrows=opts.nrows,
    )

    out: dict[str, Any] = {"etl": result}

    if not opts.skip_superset:
        dataset_id = asyncio.run(register_superset_alias(opts.table, opts.schema, opts.table))
        out["superset_dataset_id"] = dataset_id

    if not opts.skip_iso_mapping:
        engine = create_engine(db_uri)
        updated = apply_iso_mapping(engine, opts.schema, opts.table)
        out["iso_mapping_updated"] = updated

    if not opts.skip_refresh and not opts.skip_superset:
        refreshed = asyncio.run(refresh_superset_dataset(opts.table, opts.schema, opts.table))
        out["superset_refreshed_ids"] = refreshed

    return out


def _protocol_error(request_id: str | None, message: str) -> dict[str, Any]:
    return {
        "version": PROTOCOL_VERSION,
        "request_id": request_id,
        "ok": False,
        "error": {"message": message},
    }


def handle_protocol_request(payload: dict[str, Any]) -> dict[str, Any]:
    version = payload.get("version")
    action = payload.get("action")
    request_id = payload.get("request_id")

    if version != PROTOCOL_VERSION:
        return _protocol_error(request_id, f"Unsupported protocol version: {version}")

    if action == "health":
        return {"version": PROTOCOL_VERSION, "request_id": request_id, "ok": True, "result": {"status": "ok"}}

    if action != "run_pipeline":
        return _protocol_error(request_id, f"Unsupported action: {action}")

    params = payload.get("payload") or {}
    try:
        opts = PipelineOptions(
            csv_path=params["csv"],
            table=params["table"],
            schema=params.get("schema", "public"),
            replace=bool(params.get("replace", False)),
            nrows=params.get("nrows"),
            skip_superset=bool(params.get("skip_superset", False)),
            skip_iso_mapping=bool(params.get("skip_iso_mapping", False)),
            skip_refresh=bool(params.get("skip_refresh", False)),
        )
    except KeyError as e:
        return _protocol_error(request_id, f"Missing required field: {e}")

    try:
        result = run_pipeline(opts)
        return {"version": PROTOCOL_VERSION, "request_id": request_id, "ok": True, "result": result}
    except Exception as e:
        return _protocol_error(request_id, str(e))


def run_protocol_stdio(loop: bool = False):
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        line = line.strip()
        if not line:
            if loop:
                continue
            break
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as e:
            response = _protocol_error(None, f"Invalid JSON: {e}")
            print(json.dumps(response))
            if not loop:
                break
            continue

        response = handle_protocol_request(payload)
        print(json.dumps(response))
        if not loop:
            break


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="BioLink unified ETL pipeline")
    parser.add_argument("--csv", help="CSV to load")
    parser.add_argument("--table", help="Destination table name")
    parser.add_argument("--schema", default="public", help="Destination schema")
    parser.add_argument("--replace", action="store_true", help="Replace table instead of append")
    parser.add_argument("--nrows", type=int, default=None, help="Limit rows for quick runs")
    parser.add_argument("--skip-superset", action="store_true", help="Skip Superset registration/refresh")
    parser.add_argument("--skip-iso-mapping", action="store_true", help="Skip governorate ISO mapping")
    parser.add_argument("--skip-refresh", action="store_true", help="Skip Superset metadata refresh")
    parser.add_argument("--protocol-stdio", action="store_true", help="Read one request from stdin and respond on stdout")
    parser.add_argument("--protocol-loop", action="store_true", help="Read requests in a loop from stdin")
    return parser.parse_args()


def main():
    args = parse_args()

    if args.protocol_stdio or args.protocol_loop:
        run_protocol_stdio(loop=args.protocol_loop)
        return

    if not args.csv or not args.table:
        print("Error: --csv and --table are required unless using --protocol-stdio")
        sys.exit(2)

    opts = PipelineOptions(
        csv_path=args.csv,
        table=args.table,
        schema=args.schema,
        replace=args.replace,
        nrows=args.nrows,
        skip_superset=args.skip_superset,
        skip_iso_mapping=args.skip_iso_mapping,
        skip_refresh=args.skip_refresh,
    )

    result = run_pipeline(opts)
    print(json.dumps({"ok": True, "result": result}, indent=2))


if __name__ == "__main__":
    main()
