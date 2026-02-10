#!/usr/bin/env python3
"""Refresh Superset dataset columns for a dataset found by table+schema or alias name.

Tries POST /api/v1/dataset/{id}/refresh, then falls back to a PUT update with the same SQL
to trigger Superset to re-introspect columns.
"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import asyncio
import aiohttp
from app.services.superset_client import SupersetClient
from app.config import settings


async def refresh_dataset(table: str, schema: str, alias: str | None = None):
    client = SupersetClient.from_settings()
    async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar(unsafe=True)) as session:
        tokens = await client.bootstrap()
        access_token = tokens['access_token']
        csrf_token = tokens.get('csrf_token')

        # find dataset by table/schema or alias name
        datasets = await client._list_resource(session, access_token, "dataset")
        matches = []
        for d in datasets:
            if alias and d.get('table_name') == alias:
                matches.append(d)
            elif d.get('table_name') == table and d.get('schema') == schema:
                matches.append(d)

        if not matches:
            print(f"No Superset dataset found for {schema}.{table} or alias {alias}")
            return 2

        for d in matches:
            dataset_id = int(d['id'])
            print(f"Refreshing dataset id={dataset_id} name={d.get('table_name')} sql={d.get('sql')}")

            # 1) Try POST /api/v1/dataset/{id}/refresh
            try:
                path = f"/api/v1/dataset/{dataset_id}/refresh"
                print("Trying POST", path)
                res = await client._request(session, "POST", path, access_token, csrf_token, json_body={})
                print("Refresh response:", res)
                continue
            except Exception as e:
                print("POST refresh failed:", e)

            # 2) Fallback: try to PUT update the dataset SQL (if available) to force re-introspection
            try:
                put_path = f"/api/v1/dataset/{dataset_id}"
                payload = {}
                # prefer existing sql if present, else construct one
                existing_sql = d.get('sql')
                if existing_sql:
                    payload['sql'] = existing_sql
                else:
                    payload['sql'] = f"SELECT * FROM {schema}.{table}"
                print("Trying PUT", put_path, "payload:", payload)
                res = await client._request(session, "PUT", put_path, access_token, csrf_token, json_body=payload)
                print("PUT update response:", res)
                continue
            except Exception as e:
                print("PUT update failed:", e)

            print(f"Failed to refresh dataset id={dataset_id}")

    return 0


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--table', required=True)
    p.add_argument('--schema', default='public')
    p.add_argument('--alias', default=None)
    args = p.parse_args()
    raise SystemExit(asyncio.run(refresh_dataset(args.table, args.schema, args.alias)))
