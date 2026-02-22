#!/usr/bin/env python3
"""Initialize PostgreSQL schema for NiFi ETL pipeline."""
import subprocess, sys

SQL = """
-- BHS indexes
CREATE INDEX IF NOT EXISTS idx_bhs_source_dataset ON bhs_participants(source_dataset);
CREATE INDEX IF NOT EXISTS idx_bhs_age ON bhs_participants(age);
CREATE INDEX IF NOT EXISTS idx_bhs_gender ON bhs_participants(gender);
CREATE INDEX IF NOT EXISTS idx_bhs_current_city ON bhs_participants(current_city);
CREATE INDEX IF NOT EXISTS idx_bhs_quality_score ON bhs_participants(data_quality_score);
CREATE INDEX IF NOT EXISTS idx_bhs_ingested_at ON bhs_participants(ingested_at);

-- EHVol indexes
CREATE INDEX IF NOT EXISTS idx_ehvol_source_dataset ON ehvol_participants(source_dataset);
CREATE INDEX IF NOT EXISTS idx_ehvol_age ON ehvol_participants(age);
CREATE INDEX IF NOT EXISTS idx_ehvol_gender ON ehvol_participants(gender);
CREATE INDEX IF NOT EXISTS idx_ehvol_current_city ON ehvol_participants(current_city);
CREATE INDEX IF NOT EXISTS idx_ehvol_quality_score ON ehvol_participants(data_quality_score);
CREATE INDEX IF NOT EXISTS idx_ehvol_ingested_at ON ehvol_participants(ingested_at);

-- ETL run history
CREATE TABLE IF NOT EXISTS etl_run_history (
    run_id VARCHAR(100) PRIMARY KEY,
    dataset_type VARCHAR(20),
    source_file VARCHAR(500),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    rows_processed INTEGER,
    rows_loaded INTEGER,
    quality_score DECIMAL(3,2),
    status VARCHAR(20),
    error_message TEXT
);

-- City homogenization audit
CREATE TABLE IF NOT EXISTS city_homogenization_audit (
    id SERIAL PRIMARY KEY,
    original_value VARCHAR(200),
    normalized_value VARCHAR(100),
    dataset_source VARCHAR(20),
    occurrence_count INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(original_value, dataset_source)
);
"""

result = subprocess.run(
    ["docker", "exec", "-i", "biolink-postgres", "psql", "-U", "biolink", "-d", "biolink"],
    input=SQL, capture_output=True, text=True
)
print(result.stdout)
if result.stderr:
    print(result.stderr)
sys.exit(result.returncode)
