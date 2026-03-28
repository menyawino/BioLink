from __future__ import annotations

import pathlib

from sqlalchemy import text
from sqlalchemy.engine import Engine
import logging

# Path to the NiFi-generated wide-table schema (mounted at /app/db in the container)
_STANDARDIZED_SCHEMA_PATH = pathlib.Path("/app/db/schema_standardized.sql")

logger = logging.getLogger(__name__)


def _standardized_table_state(conn) -> tuple[bool, bool]:
    rows = conn.execute(
        text(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name IN ('bhs_participants', 'ehvol_participants')
            """
        )
    ).fetchall()
    present = {row[0] for row in rows}
    both_present = {"bhs_participants", "ehvol_participants"}.issubset(present)
    any_present = bool(present)
    return both_present, any_present


MIGRATION_SQL = """
-- Denormalized patients table (single source of truth for the demo app)
-- We keep this as a single wide table for dev/demo stability.
CREATE TABLE IF NOT EXISTS patients (
    dna_id TEXT PRIMARY KEY
);

-- Migrate/upgrade: add any missing columns used by the API.
ALTER TABLE patients ADD COLUMN IF NOT EXISTS date_of_birth DATE;
ALTER TABLE patients ADD COLUMN IF NOT EXISTS age INTEGER;
ALTER TABLE patients ADD COLUMN IF NOT EXISTS gender TEXT;
ALTER TABLE patients ADD COLUMN IF NOT EXISTS nationality TEXT;
ALTER TABLE patients ADD COLUMN IF NOT EXISTS enrollment_date DATE;
ALTER TABLE patients ADD COLUMN IF NOT EXISTS current_city TEXT;

ALTER TABLE patients ADD COLUMN IF NOT EXISTS current_city_category TEXT;
ALTER TABLE patients ADD COLUMN IF NOT EXISTS childhood_city_category TEXT;
ALTER TABLE patients ADD COLUMN IF NOT EXISTS migration_pattern TEXT;

ALTER TABLE patients ADD COLUMN IF NOT EXISTS heart_rate DOUBLE PRECISION;
ALTER TABLE patients ADD COLUMN IF NOT EXISTS systolic_bp DOUBLE PRECISION;
ALTER TABLE patients ADD COLUMN IF NOT EXISTS diastolic_bp DOUBLE PRECISION;
ALTER TABLE patients ADD COLUMN IF NOT EXISTS height_cm DOUBLE PRECISION;
ALTER TABLE patients ADD COLUMN IF NOT EXISTS weight_kg DOUBLE PRECISION;
ALTER TABLE patients ADD COLUMN IF NOT EXISTS bmi DOUBLE PRECISION;
ALTER TABLE patients ADD COLUMN IF NOT EXISTS bsa DOUBLE PRECISION;

ALTER TABLE patients ADD COLUMN IF NOT EXISTS hba1c DOUBLE PRECISION;
ALTER TABLE patients ADD COLUMN IF NOT EXISTS troponin_i DOUBLE PRECISION;

ALTER TABLE patients ADD COLUMN IF NOT EXISTS echo_date DATE;
ALTER TABLE patients ADD COLUMN IF NOT EXISTS echo_ef DOUBLE PRECISION;
ALTER TABLE patients ADD COLUMN IF NOT EXISTS mri_date DATE;
ALTER TABLE patients ADD COLUMN IF NOT EXISTS mri_ef DOUBLE PRECISION;
ALTER TABLE patients ADD COLUMN IF NOT EXISTS rv_ef DOUBLE PRECISION;

ALTER TABLE patients ADD COLUMN IF NOT EXISTS current_smoker BOOLEAN;
ALTER TABLE patients ADD COLUMN IF NOT EXISTS former_smoker BOOLEAN;
ALTER TABLE patients ADD COLUMN IF NOT EXISTS ever_smoked BOOLEAN;
ALTER TABLE patients ADD COLUMN IF NOT EXISTS smoking_years DOUBLE PRECISION;
ALTER TABLE patients ADD COLUMN IF NOT EXISTS cigarettes_per_day INTEGER;
ALTER TABLE patients ADD COLUMN IF NOT EXISTS drinks_alcohol BOOLEAN;
ALTER TABLE patients ADD COLUMN IF NOT EXISTS takes_medication BOOLEAN;

ALTER TABLE patients ADD COLUMN IF NOT EXISTS diabetes_mellitus BOOLEAN;
ALTER TABLE patients ADD COLUMN IF NOT EXISTS high_blood_pressure BOOLEAN;
ALTER TABLE patients ADD COLUMN IF NOT EXISTS dyslipidemia BOOLEAN;
ALTER TABLE patients ADD COLUMN IF NOT EXISTS heart_attack_or_angina BOOLEAN;
ALTER TABLE patients ADD COLUMN IF NOT EXISTS prior_heart_failure BOOLEAN;

ALTER TABLE patients ADD COLUMN IF NOT EXISTS history_sudden_death BOOLEAN;
ALTER TABLE patients ADD COLUMN IF NOT EXISTS history_premature_cad BOOLEAN;

-- Patient genomic variants (ingested from VCFs)
CREATE TABLE IF NOT EXISTS patient_genomic_variants (
    id BIGSERIAL PRIMARY KEY,
    dna_id TEXT NOT NULL,
    chrom TEXT NOT NULL,
    pos INTEGER NOT NULL,
    ref TEXT NOT NULL,
    alt TEXT NOT NULL,
    variant_id TEXT,
    gene TEXT,
    genotype TEXT,
    clinical_significance TEXT,
    condition TEXT,
    frequency DOUBLE PRECISION,
    source_vcf TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS patient_genomic_variants_dna_id_idx ON patient_genomic_variants(dna_id);
CREATE INDEX IF NOT EXISTS patient_genomic_variants_gene_idx ON patient_genomic_variants(gene);
CREATE UNIQUE INDEX IF NOT EXISTS patient_genomic_variants_uidx ON patient_genomic_variants(dna_id, chrom, pos, ref, alt, genotype);

ALTER TABLE patients ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE patients ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

-- Add a stable numeric id for frontend (non-breaking on existing DBs)
ALTER TABLE patients ADD COLUMN IF NOT EXISTS id BIGSERIAL;
UPDATE patients
SET id = nextval(pg_get_serial_sequence('patients', 'id'))
WHERE id IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS patients_id_uidx ON patients(id);

-- Patient note extractions: structured extraction outputs from LLM-based
-- processors (e.g., langextract). Store JSONB so the frontend or analytics
-- can query or rehydrate extraction results later.
CREATE TABLE IF NOT EXISTS patient_note_extractions (
    id BIGSERIAL PRIMARY KEY,
    patient_id BIGINT,
    chunk_id INTEGER,
    extraction JSONB,
    source TEXT,
    stage INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS patient_note_extractions_patient_id_idx ON patient_note_extractions(patient_id);

-- Audit log: persistent record of security and data-access events
CREATE TABLE IF NOT EXISTS audit_log (
    id BIGSERIAL PRIMARY KEY,
    event_type TEXT NOT NULL,
    username TEXT,
    request_id TEXT,
    payload JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS audit_log_event_type_idx ON audit_log(event_type);
CREATE INDEX IF NOT EXISTS audit_log_username_idx ON audit_log(username);
CREATE INDEX IF NOT EXISTS audit_log_created_at_idx ON audit_log(created_at DESC);
"""


VIEW_SQL = """
-- EHVOL view: legacy compatibility layer over the patients table.
-- Analytics now queries participant tables directly; this view is kept
-- only for backward compatibility with Superset dashboards / ad‑hoc SQL.
DROP VIEW IF EXISTS EHVOL;
CREATE VIEW EHVOL AS
SELECT
    id,
    dna_id,
    age,
    gender,
    nationality,
    enrollment_date,
    current_city,
    heart_rate,
    systolic_bp,
    diastolic_bp,
    height_cm,
    weight_kg,
    bsa,
    bmi,
    hba1c,
    troponin_i,
    echo_ef,
    mri_ef,
    echo_ef AS ef,
    mri_ef AS lv_ejection_fraction,
    rv_ef,
    current_city_category,
    childhood_city_category,
    migration_pattern,
    (mri_ef IS NOT NULL) AS has_mri,
    (echo_ef IS NOT NULL) AS has_echo,
    EXISTS (
        SELECT 1 FROM patient_genomic_variants v
        WHERE v.dna_id = patients.dna_id
    ) AS has_genomics
FROM patients;

"""


def ensure_schema(engine: Engine) -> None:
    """Create/upgrade the minimal DB objects required by the API.

    The repo contains code that *used* to assume many normalized tables.
    For a stable demo/dev experience, we keep a single denormalized table
    + a view that all read endpoints use.

    In addition we bootstrap the two wide NiFi-ingested tables:
      * bhs_participants  — all BHS columns mapped to SDTM / CDISC
      * ehvol_participants — all EHVol columns mapped to SDTM / CDISC
    These are generated by nifi/pipeline/generate_schema_sql.py and written to
    db/schema_standardized.sql; NiFi will INSERT rows as it processes CSV files.
    """
    # (1) Legacy patients table + column migrations
    with engine.begin() as conn:
        conn.execute(text(MIGRATION_SQL))
    # (2) Legacy EHVOL view
    with engine.begin() as conn:
        conn.execute(text(VIEW_SQL))
    # (3) Standardised wide tables (_schema_registry, bhs_participants, ehvol_participants, core VIEW)
    #     schema_standardized.sql contains many statements (DDL + 844 INSERT/UPSERT rows);
    #     we use the raw psycopg2 connection which supports multi-statement execution.
    with engine.connect() as conn:
        both_present, any_present = _standardized_table_state(conn)

    if _STANDARDIZED_SCHEMA_PATH.exists():
        if both_present:
            logger.info(
                "Database schema bootstrap: standardized participant tables already exist; skipping destructive schema replay"
            )
        elif any_present:
            logger.warning(
                "Database schema bootstrap: partial participant-table state detected; skipping destructive schema replay to preserve existing data"
            )
        else:
            standardized_sql = _STANDARDIZED_SCHEMA_PATH.read_text()
            raw = engine.raw_connection()
            try:
                cur = raw.cursor()
                cur.execute(standardized_sql)
                raw.commit()
                cur.close()
            finally:
                raw.close()
            logger.info("Database schema bootstrap: ✓ _schema_registry + bhs_participants + ehvol_participants")
    else:
        logger.warning(
            "Database schema bootstrap: schema_standardized.sql not found at %s — "
            "NiFi wide tables will NOT be created. "
            "Run nifi/pipeline/generate_schema_sql.py and ensure db/ is mounted.",
            _STANDARDIZED_SCHEMA_PATH,
        )
    logger.info("Database schema bootstrap: ✓ ensured")
