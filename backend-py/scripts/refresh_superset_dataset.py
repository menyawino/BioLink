#!/usr/bin/env python3
"""Refresh Superset dataset metadata for a given table and schema.

Tries common Superset API endpoints for refreshing dataset metadata.
"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import asyncio
import aiohttp
from app.services.superset_client import SupersetClient


async def refresh_dataset(table: str, schema: str) -> int:
    client = SupersetClient.from_settings()
    async with aiohttp.ClientSession() as session:
        access_token = await client._login(session)
        csrf_token = await client._csrf(session, access_token)

        datasets = await client._list_resource(session, access_token, "dataset")
        matches = [d for d in datasets if d.get("table_name") == table and d.get("schema") == schema]
        if not matches:
            print(f"No dataset found for {schema}.{table}")
            return 1
        ds = matches[0]
        ds_id = ds.get("id")
        print(f"Found dataset id={ds_id}, attempting refresh...")

        endpoints = [
            f"/api/v1/dataset/{ds_id}/refresh",
            f"/api/v1/dataset/{ds_id}/refresh_metadata",
            f"/api/v1/dataset/{ds_id}/refresh_values",
        ]

        last_err = None
        for ep in endpoints:
            try:
                print(f"Calling {ep} ...")
                res = await client._request(session, "POST", ep, access_token, csrf_token)
                print("Refresh response:", res)
                return 0
            except Exception as e:
                print(f"Endpoint {ep} failed: {e}")
                last_err = e

        # Fallback: try updating the dataset via PUT which may trigger metadata sync
        try:
            payload = {
                "database": ds.get("database", {}).get("id"),
                "schema": ds.get("schema"),
                "table_name": ds.get("table_name"),
            }
            print(f"Attempting PUT /api/v1/dataset/{ds_id} with payload {payload}")
            updated = await client._request(session, "PUT", f"/api/v1/dataset/{ds_id}", access_token, csrf_token, json_body=payload)
            print("PUT update response:", updated)
            return 0
        except Exception as e:
            print(f"PUT update failed: {e}")
            last_err = e

        # As another fallback, try refreshing the parent database metadata
        try:
            db_id = ds.get('database', {}).get('id')
            if db_id:
                print(f"Attempting POST /api/v1/database/{db_id}/refresh")
                db_res = await client._request(session, 'POST', f"/api/v1/database/{db_id}/refresh", access_token, csrf_token)
                print('Database refresh response:', db_res)
                return 0
        except Exception as e:
            print(f"Database refresh failed: {e}")

        print(f"All refresh attempts failed. Last error: {last_err}")
        return 2


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--table', required=True)
    p.add_argument('--schema', default='public')
    args = p.parse_args()
    raise SystemExit(asyncio.run(refresh_dataset(args.table, args.schema)))
