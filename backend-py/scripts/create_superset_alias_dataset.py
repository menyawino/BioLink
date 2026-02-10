#!/usr/bin/env python3
"""Create an alias Superset dataset pointing to the same physical table.

Tries several payload shapes (including a SQL-based virtual dataset) until one succeeds.
"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import asyncio
from app.services.superset_client import SupersetClient


async def create_alias(table: str, schema: str, alias: str):
    client = SupersetClient.from_settings()
    import aiohttp
    from app.config import settings

    async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar(unsafe=True)) as session:
        tokens = await client.bootstrap()
        access_token = tokens['access_token']
        csrf_token = tokens['csrf_token']

        db_id = await client.get_or_create_database(
            session, access_token, csrf_token, settings.superset_database_name, settings.superset_database_uri
        )

        # Try payload variants
        variants = [
            {"database": db_id, "schema": schema, "table_name": table, "dataset_name": alias},
            {"database": db_id, "schema": schema, "table_name": table, "name": alias},
            {"database": db_id, "schema": schema, "table_name": alias},
            {"database": db_id, "schema": None, "table_name": alias, "sql": f"SELECT * FROM {schema}.{table}"},
        ]

        for payload in variants:
            try:
                print("Trying payload:", payload)
                created = await client._request(session, "POST", "/api/v1/dataset/", access_token, csrf_token, json_body=payload)
                print("Created dataset:", created)
                return 0
            except Exception as e:
                print("Payload failed:", e)

        print("All creation attempts failed")
        return 2


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--table', required=True)
    p.add_argument('--schema', default='public')
    p.add_argument('--alias', required=True)
    args = p.parse_args()
    raise SystemExit(asyncio.run(create_alias(args.table, args.schema, args.alias)))
