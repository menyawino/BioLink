from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Engine
import logging

logger = logging.getLogger(__name__)


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
"""


VIEW_SQL = """

 -- EHVOL view: what list/search/analytics/charts should use
-- EHVOL view: what list/search/analytics/charts should use
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
    NULL::DOUBLE PRECISION AS lv_mass,
    NULL::DOUBLE PRECISION AS lv_edv,
    NULL::DOUBLE PRECISION AS lv_esv,
    rv_ef AS rv_ef,
    current_city_category,
    childhood_city_category,
    migration_pattern,
    (mri_ef IS NOT NULL) AS has_mri,
    (echo_ef IS NOT NULL) AS has_echo,
    EXISTS (
        SELECT 1 FROM patient_genomic_variants v
        WHERE v.dna_id = patients.dna_id
    ) AS has_genomics,
    COALESCE((
        (CASE WHEN heart_rate IS NOT NULL THEN 20 ELSE 0 END) +
        (CASE WHEN systolic_bp IS NOT NULL THEN 20 ELSE 0 END) +
        (CASE WHEN bmi IS NOT NULL THEN 20 ELSE 0 END) +
        (CASE WHEN echo_ef IS NOT NULL THEN 20 ELSE 0 END) +
        (CASE WHEN mri_ef IS NOT NULL THEN 20 ELSE 0 END)
    ), 0) AS data_completeness
FROM patients;

"""


def ensure_schema(engine: Engine) -> None:
    """Create/upgrade the minimal DB objects required by the API.

    The repo contains code that *used* to assume many normalized tables.
    For a stable demo/dev experience, we keep a single denormalized table
    + a view that all read endpoints use.
    """
    # Run migrations first (commit), then create/update the view.
    # This avoids rolling back column additions if view creation fails.
    with engine.begin() as conn:
        conn.execute(text(MIGRATION_SQL))
    with engine.begin() as conn:
        conn.execute(text(VIEW_SQL))
    logger.info("Database schema bootstrap: ✓ ensured")
