import os
import pytest
from app.services.etl_protocol_client import run_pipeline_request


@pytest.mark.integration
def test_run_etl_protocol_small_sample():
    """Run a short ETL via governed protocol (nrows=5).

    This test requires the project's DB to be available.
    """
    csv = os.path.join(os.getcwd(), "db", "EHVOL_50.csv")
    payload = {
        "version": "1.0",
        "action": "run_pipeline",
        "request_id": "test-1",
        "payload": {
            "csv": csv,
            "table": "ehvol_50_protocol_test",
            "schema": "public",
            "nrows": 5,
            "replace": True,
            "skip_superset": True,
            "skip_iso_mapping": True,
            "skip_refresh": True,
        },
    }
    response = run_pipeline_request(payload)
    assert response.get("ok") is True
    result = response.get("result") or {}
    assert result.get("etl", {}).get("rows_written") in (0, 5)
