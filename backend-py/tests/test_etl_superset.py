import os
import pytest
from app.services.etl_protocol_client import run_pipeline_request


@pytest.mark.integration
def test_etl_protocol_health():
    """Ensure the ETL protocol responds to health checks.

    This test does not require NiFi/dbt to be configured.
    """
    payload = {
        "version": "1.0",
        "action": "health",
        "request_id": "test-health",
    }
    response = run_pipeline_request(payload)
    assert response.get("ok") is True
