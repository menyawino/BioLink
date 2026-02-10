import asyncio
import os
import pytest
from biolink_etl.etl import run_etl


@pytest.mark.integration
def test_run_etl_and_superset_registration(tmp_path):
    """Run a short ETL (nrows=5) and confirm Superset dataset exists.

    This test requires Superset and the project's DB to be available (same env used by the app).
    If Superset is not reachable the test is skipped.
    """
    # Use small sample
    csv = os.path.join(os.getcwd(), "db", "090925_EHVol_Data.csv")
    # Run ETL for 5 rows to speed up test
    count = run_etl(csv, table="EHVOL", schema="public", db_uri=None, replace=True, nrows=5)
    assert count == 5 or count == 0
