#!/usr/bin/env python3
"""Check Superset for dataset existence by table and schema."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import asyncio
import aiohttp
from app.services.superset_client import SupersetClient
from app.config import settings


async def main(table_name: str, schema: str):
    client = SupersetClient.from_settings()
    async with aiohttp.ClientSession() as session:
        access_token = await client._login(session)
        # csrf optional
        datasets = await client._list_resource(session, access_token, "dataset")
        matches = [d for d in datasets if d.get("table_name") == table_name and d.get("schema") == schema]
        if not matches:
            print(f"No Superset dataset found for {schema}.{table_name}")
            return 1
        for d in matches:
            print("Found dataset:")
            print(f"  id: {d.get('id')}")
            print(f"  table_name: {d.get('table_name')}")
            print(f"  schema: {d.get('schema')}")
            print(f"  database: {d.get('database')}")
            print(f"  extra: {d}")
    return 0


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--table', default='EHVOL')
    p.add_argument('--schema', default='public')
    args = p.parse_args()
    raise SystemExit(asyncio.run(main(args.table, args.schema)))
