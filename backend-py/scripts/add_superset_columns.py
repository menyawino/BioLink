#!/usr/bin/env python3
"""Add columns to a Superset dataset via API.

Usage: python3 add_superset_columns.py --dataset-id 4 --columns current_city_lat:FLOAT current_city_lon:FLOAT
"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import argparse
import asyncio
import aiohttp
from app.services.superset_client import SupersetClient


async def add_columns(dataset_id: int, columns: list[tuple[str, str]]):
    client = SupersetClient.from_settings()
    async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar(unsafe=True)) as session:
        tokens = await client.bootstrap()
        at = tokens['access_token']
        csrf = tokens.get('csrf_token')

        for name, typ in columns:
            payload = {'column_name': name, 'type': typ, 'table_id': dataset_id}
            try:
                res = await client._request(session, 'POST', '/api/v1/column/', at, csrf, json_body=payload)
                print('Created column:', name, res.get('id') if isinstance(res, dict) else res)
            except Exception as e:
                print('Create failed for', name, e)


def parse_columns(cols: list[str]) -> list[tuple[str, str]]:
    out = []
    for c in cols:
        if ':' in c:
            name, typ = c.split(':', 1)
        else:
            name, typ = c, 'FLOAT'
        out.append((name, typ))
    return out


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset-id', type=int, required=True)
    parser.add_argument('--columns', nargs='+', required=True)
    args = parser.parse_args()
    cols = parse_columns(args.columns)
    raise SystemExit(asyncio.run(add_columns(args.dataset_id, cols)))
