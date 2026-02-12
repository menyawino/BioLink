"""Client for the BioLink ETL governed protocol (HTTP first, stdio fallback)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]


def _http_request(payload: dict[str, Any]) -> dict[str, Any] | None:
    etl_url = os.getenv("ETL_SERVICE_URL")
    if not etl_url:
        return None
    url = etl_url.rstrip("/") + "/protocol"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body)
    except Exception:
        return None


def _stdio_request(payload: dict[str, Any]) -> dict[str, Any]:
    cmd = [sys.executable, "-m", "biolink_etl.pipeline", "--protocol-stdio"]
    proc = subprocess.run(
        cmd,
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        cwd=str(ROOT),
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ETL protocol failed: {proc.stderr.strip()}")
    if not proc.stdout.strip():
        raise RuntimeError("ETL protocol returned empty response")
    return json.loads(proc.stdout.strip().splitlines()[-1])


def run_pipeline_request(payload: dict[str, Any]) -> dict[str, Any]:
    response = _http_request(payload)
    if response is not None:
        return response
    return _stdio_request(payload)
