"""Client for the BioLink ETL governed protocol over stdio."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]


def run_pipeline_request(payload: dict[str, Any]) -> dict[str, Any]:
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
