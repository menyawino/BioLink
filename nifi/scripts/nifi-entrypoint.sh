#!/bin/bash
# =============================================================================
# BioLink NiFi Entrypoint
#
# Configures NiFi for HTTP mode (no HTTPS/TLS), initializes PostgreSQL schema,
# then delegates to the standard NiFi startup.
# =============================================================================
set -e

echo "=== BioLink NiFi Entrypoint ==="
echo "  Configuring NiFi for HTTP-only mode on port ${NIFI_WEB_HTTP_PORT:-8443}"

NIFI_HOME="${NIFI_HOME:-/opt/nifi/nifi-current}"
PROPS="${NIFI_HOME}/conf/nifi.properties"

# Wait for the properties file to exist (NiFi image may generate it)
for i in $(seq 1 30); do
    [ -f "$PROPS" ] && break
    echo "  Waiting for nifi.properties... ($i/30)"
    sleep 2
done

if [ -f "$PROPS" ]; then
    echo "  Patching nifi.properties for HTTP mode..."

    # Disable HTTPS
    sed -i 's|^nifi\.web\.https\.host=.*|nifi.web.https.host=|' "$PROPS"
    sed -i 's|^nifi\.web\.https\.port=.*|nifi.web.https.port=|' "$PROPS"

    # Enable HTTP
    sed -i "s|^nifi\.web\.http\.host=.*|nifi.web.http.host=0.0.0.0|" "$PROPS"
    sed -i "s|^nifi\.web\.http\.port=.*|nifi.web.http.port=${NIFI_WEB_HTTP_PORT:-8443}|" "$PROPS"

    # Disable login identity providers (allow anonymous)
    sed -i 's|^nifi\.security\.user\.login\.identity\.provider=.*|nifi.security.user.login.identity.provider=|' "$PROPS"
    sed -i 's|^nifi\.security\.user\.authorizer=.*|nifi.security.user.authorizer=|' "$PROPS"

    # Clear keystore/truststore so NiFi doesn't try TLS
    sed -i 's|^nifi\.security\.keystore=.*|nifi.security.keystore=|' "$PROPS"
    sed -i 's|^nifi\.security\.keystoreType=.*|nifi.security.keystoreType=|' "$PROPS"
    sed -i 's|^nifi\.security\.keystorePasswd=.*|nifi.security.keystorePasswd=|' "$PROPS"
    sed -i 's|^nifi\.security\.keyPasswd=.*|nifi.security.keyPasswd=|' "$PROPS"
    sed -i 's|^nifi\.security\.truststore=.*|nifi.security.truststore=|' "$PROPS"
    sed -i 's|^nifi\.security\.truststoreType=.*|nifi.security.truststoreType=|' "$PROPS"
    sed -i 's|^nifi\.security\.truststorePasswd=.*|nifi.security.truststorePasswd=|' "$PROPS"

    echo "  NiFi properties patched successfully."
else
    echo "  WARNING: nifi.properties not found at $PROPS"
fi

# -------------------------------------------------------
# Initialize PostgreSQL Schema
# -------------------------------------------------------
echo "=== Initializing PostgreSQL schema ==="

DB_HOST="${DB_HOST:-postgres}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-biolink}"
DB_USER="${DB_USER:-biolink}"
DB_PASSWORD="${DB_PASSWORD:-biolink_secret}"

# Check if psql is available in the container; if not, skip
if command -v psql >/dev/null 2>&1; then
    export PGPASSWORD="$DB_PASSWORD"
    MAX_RETRIES=30
    RETRY=0
    until psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1" > /dev/null 2>&1; do
        RETRY=$((RETRY + 1))
        if [ "$RETRY" -ge "$MAX_RETRIES" ]; then
            echo "  WARNING: PostgreSQL not reachable after $MAX_RETRIES attempts (will try via NiFi later)"
            break
        fi
        echo "  Waiting for PostgreSQL... ($RETRY/$MAX_RETRIES)"
        sleep 2
    done

    if [ "$RETRY" -lt "$MAX_RETRIES" ]; then
        echo "  PostgreSQL is ready. Creating schema..."
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 <<'SQL'
-- =====================================================
-- DATASET PARTICIPANT TABLES
-- =====================================================
CREATE TABLE IF NOT EXISTS bhs_participants (
    participant_id      VARCHAR(50) PRIMARY KEY,
    source_dataset      VARCHAR(20) NOT NULL,
    source_record_id    VARCHAR(50),
    date_of_birth       DATE,
    age                 INTEGER,
    gender              VARCHAR(10),
    nationality         VARCHAR(50),
    enrollment_date     DATE,
    current_city        VARCHAR(100),
    childhood_city      VARCHAR(100),
    father_origin_city  VARCHAR(100),
    mother_origin_city  VARCHAR(100),
    height_cm           DECIMAL(5,2),
    weight_kg           DECIMAL(5,2),
    bmi                 DECIMAL(5,2),
    heart_rate          DECIMAL(5,2),
    systolic_bp         DECIMAL(5,2),
    diastolic_bp        DECIMAL(5,2),
    hba1c               DECIMAL(4,2),
    troponin_i          DECIMAL(8,4),
    echo_ef             DECIMAL(5,2),
    echo_date           DATE,
    has_diabetes        BOOLEAN,
    has_hypertension    BOOLEAN,
    has_dyslipidemia    BOOLEAN,
    has_heart_failure   BOOLEAN,
    is_smoker           BOOLEAN,
    smoking_pack_years  DECIMAL(5,2),
    family_history_cad  BOOLEAN,
    family_history_diabetes BOOLEAN,
    consanguineous_parents  BOOLEAN,
    source_raw_json        JSONB,
    ingested_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_quality_score  DECIMAL(3,2)
);

CREATE TABLE IF NOT EXISTS ehvol_participants (
    participant_id      VARCHAR(50) PRIMARY KEY,
    source_dataset      VARCHAR(20) NOT NULL,
    source_record_id    VARCHAR(50),
    date_of_birth       DATE,
    age                 INTEGER,
    gender              VARCHAR(10),
    nationality         VARCHAR(50),
    enrollment_date     DATE,
    current_city        VARCHAR(100),
    childhood_city      VARCHAR(100),
    father_origin_city  VARCHAR(100),
    mother_origin_city  VARCHAR(100),
    height_cm           DECIMAL(5,2),
    weight_kg           DECIMAL(5,2),
    bmi                 DECIMAL(5,2),
    heart_rate          DECIMAL(5,2),
    systolic_bp         DECIMAL(5,2),
    diastolic_bp        DECIMAL(5,2),
    hba1c               DECIMAL(4,2),
    troponin_i          DECIMAL(8,4),
    echo_ef             DECIMAL(5,2),
    echo_date           DATE,
    has_diabetes        BOOLEAN,
    has_hypertension    BOOLEAN,
    has_dyslipidemia    BOOLEAN,
    has_heart_failure   BOOLEAN,
    is_smoker           BOOLEAN,
    smoking_pack_years  DECIMAL(5,2),
    family_history_cad  BOOLEAN,
    family_history_diabetes BOOLEAN,
    consanguineous_parents  BOOLEAN,
    source_raw_json        JSONB,
    ingested_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_quality_score  DECIMAL(3,2)
);

CREATE OR REPLACE VIEW unified_participants AS
SELECT * FROM bhs_participants
UNION ALL
SELECT * FROM ehvol_participants;

-- =====================================================
-- ETL RUN HISTORY
-- =====================================================
CREATE TABLE IF NOT EXISTS etl_run_history (
    run_id          SERIAL PRIMARY KEY,
    pipeline        VARCHAR(50) DEFAULT 'nifi',
    dataset         VARCHAR(20),
    started_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finished_at     TIMESTAMP,
    records_loaded  INTEGER DEFAULT 0,
    records_rejected INTEGER DEFAULT 0,
    status          VARCHAR(20) DEFAULT 'running',
    details         JSONB
);

-- =====================================================
-- CITY HOMOGENIZATION AUDIT
-- =====================================================
CREATE TABLE IF NOT EXISTS city_homogenization_audit (
    id              SERIAL PRIMARY KEY,
    original_value  VARCHAR(200),
    normalized_value VARCHAR(100),
    dataset         VARCHAR(20),
    field_name      VARCHAR(50),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- INDEXES
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_bhs_source_dataset ON bhs_participants(source_dataset);
CREATE INDEX IF NOT EXISTS idx_bhs_gender ON bhs_participants(gender);
CREATE INDEX IF NOT EXISTS idx_bhs_current_city ON bhs_participants(current_city);
CREATE INDEX IF NOT EXISTS idx_bhs_age ON bhs_participants(age);
CREATE INDEX IF NOT EXISTS idx_bhs_quality ON bhs_participants(data_quality_score);
CREATE INDEX IF NOT EXISTS idx_bhs_ingested ON bhs_participants(ingested_at);

CREATE INDEX IF NOT EXISTS idx_ehvol_source_dataset ON ehvol_participants(source_dataset);
CREATE INDEX IF NOT EXISTS idx_ehvol_gender ON ehvol_participants(gender);
CREATE INDEX IF NOT EXISTS idx_ehvol_current_city ON ehvol_participants(current_city);
CREATE INDEX IF NOT EXISTS idx_ehvol_age ON ehvol_participants(age);
CREATE INDEX IF NOT EXISTS idx_ehvol_quality ON ehvol_participants(data_quality_score);
CREATE INDEX IF NOT EXISTS idx_ehvol_ingested ON ehvol_participants(ingested_at);
SQL
        echo "  Schema initialization complete."
    fi
else
    echo "  psql not found in container; schema must be initialized externally."
fi

# -------------------------------------------------------
# Start NiFi
# -------------------------------------------------------
echo "=== Starting Apache NiFi ==="
exec "${NIFI_HOME}/bin/nifi.sh" run
