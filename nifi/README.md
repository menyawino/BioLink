# BioLink NiFi 2.8.0 ETL Pipeline

Apache NiFi 2.8.0 pipeline with automated REST bootstrap for the documented
replacement ETL plan:
- **db/test Step 3**: normalization profiling via `db/test/step_3_profile_normalization.py`
- **db/test Step 4**: range cleaning via `db/test/step_4_apply_range_rules.py`
- **db/test Step 5**: unit extraction via `db/test/step_5_extract_units.py`
- **db/test Step 6**: fuzzy standardization via `db/test/step_6_fuzzy_match_v2.py`
- **db/test Step 7**: unified snapshot generation via `db/test/step_7_unify_datasets.py`

NiFi remains the execution engine, but the active registry pipeline now runs the
replacement scripts under `db/test/` and publishes compatibility outputs under
`outputs/` for the rest of the application.

---

## Architecture (auto-bootstrapped)

```
Registry pipeline (runs on schedule or RUN_ONCE):
GenerateFlowFile
  -> BiolinkRegistryPipelineProcessor
     -> db/test/step_7/unified_wide_table.csv
     -> outputs/unified_registry.csv
     -> outputs/comparability_report.json
     -> outputs/data_quality_report.html
     -> outputs/cohort_characterization.csv
     -> PostgreSQL: unified_registry + participant tables + comparability_report
```

## Directory Structure

```
nifi/
├── conf/                       # NiFi configuration overrides
├── extensions/                 # Java NAR extensions
├── flow/
│   └── flow.json              # NiFi 2.x flow definition (auto-loaded)
├── jdbc/
│   └── postgresql-42.7.3.jar  # PostgreSQL JDBC driver
├── processors/                 # Python processors (NiFi 2.x native)
│   ├── BiolinkCsvToJsonProcessor.py    # CSV → JSON with header sanitization
│   ├── BiolinkTransformProcessor.py    # Field mapping, type normalization, BP averaging
│   ├── BiolinkDataQualityProcessor.py  # Validation and quality scoring
│   └── BiolinkJsonToSqlProcessor.py    # JSON → PostgreSQL INSERT/UPSERT SQL
└── scripts/
  ├── init_postgres_schema.sh      # Creates participant tables/indexes
  ├── setup_nifi_flow.sh           # Legacy setup wrapper
  └── bootstrap_nifi_graph.py      # Idempotent REST bootstrap for the active registry graph
```

## Python Processors

The NiFi processors are **NiFi 2.x native Python processors** and now orchestrate
the same scripts described in `docs/README_registry_pipeline.md`.

### 1. BiolinkCsvToJsonProcessor

| Property | Default | Description |
|----------|---------|-------------|
| Dataset Type | `bhs` | `bhs` or `ehvol` |
| Batch Size | `0` | Rows per output (0 = all) |

- Reads CSV FlowFile, outputs JSON array of row objects
- Handles BOM, encoding, header sanitization
- Remaps EHVol column names to canonical form

### 2. BiolinkRegistryPipelineProcessor

Runs the replacement `db/test` pipeline in one NiFi processor:

- Calls `db/test/run_pipeline.py` to execute steps 3-7 and publish compatibility outputs
- Builds `outputs/unified_registry.csv` from `db/test/step_7/unified_wide_table.csv`
- Writes `outputs/comparability_report.json`, `outputs/data_quality_report.html`, and `outputs/cohort_characterization.csv`
- Clears stale legacy OMOP and harmonization tables before loading the current unified snapshot into PostgreSQL
- Persists a JSON manifest in `registry_etl_runs`

## Quick Start

### 1. Initialize the database schema

```bash
# From the project root
docker compose exec postgres bash -c \
  "PGPASSWORD=biolink_secret psql -U biolink -d biolink" < nifi/scripts/init_postgres_schema.sh
```

Or run the schema script from within the NiFi container:

```bash
docker compose exec nifi /opt/nifi/scripts/init_postgres_schema.sh
```

### 2. Start NiFi

```bash
docker compose up -d nifi
```

NiFi 2.8.0 UI will be available at **https://localhost:8443/nifi/**

NiFi uses HTTPS with a self-signed certificate in this setup, so the browser may
show a certificate warning on first load. Continue past the warning to reach the
login screen.

Login: `admin` / `biolink_nifi_secret_123`

### 3. Flow bootstrap runs automatically

`docker-compose.yml` includes a one-shot `nifi-bootstrap` service that waits for
NiFi health and runs:

```bash
python3 /app/nifi/scripts/bootstrap_nifi_graph.py \
  --nifi-url https://nifi:8443 \
  --username admin \
  --password biolink_nifi_secret_123
```

This populates the root flow with the active db/test registry pipeline on every stack startup.

Manual re-run:

```bash
docker compose run --rm nifi-bootstrap
```

### 4. Controller service

The bootstrap script creates/enables **BioLink PostgreSQL DBCP** at root.
No manual controller-service setup is required during normal startup.

The connection pool uses parameter context `BioLink Parameters` with:
- URL: `jdbc:postgresql://postgres:5432/biolink`
- Driver: `org.postgresql.Driver`
- Driver path: `/opt/nifi/jdbc/postgresql-42.7.3.jar`
- User: `biolink`

### 5. Frontend wiring

Frontend ETL Designer reads `VITE_NIFI_URL` (wired in compose build args),
defaulting to `/nifi/` for same-origin proxy embedding.

## Docker Compose Changes

Key changes from NiFi 1.26.0 → 2.8.0:

| Setting | Old (1.26.0) | New (2.8.0) |
|---------|-------------|-------------|
| Image | `apache/nifi:1.26.0` | `apache/nifi:2.8.0` |
| HTTPS port | 8444 (separate) | Removed (HTTP-only for dev) |
| Python extensions | Not supported | `NIFI_PYTHON_EXTENSIONS_SOURCE_DIRECTORY_DEFAULT` |
| Processor mount | N/A | `./nifi/processors:/opt/nifi/nifi-current/python_extensions` |
| Health check retries | 5 | 10 (NiFi 2.x slower startup) |
| Start period | 60s | 90s |

## Current Outputs

The active pipeline publishes:

- `outputs/unified_registry.csv`
- `outputs/comparability_report.json`
- `outputs/data_quality_report.html`
- `outputs/cohort_characterization.csv`
- `db/test/step_7/unified_wide_table.csv`
- `db/test/step_7/column_mapping.csv`
- `db/test/step_7/value_set_mapping.csv`
- `db/test/step_7/unit_mapping.csv`
- `db/test/step_7/modality_manifest.csv`
- Demographics (DOB, age, gender, nationality, enrollment_date)
- Location (current_city, childhood_city, father/mother origin)
- Clinical (height, weight, BMI, heart_rate, systolic/diastolic BP)
- Laboratory (HbA1c, troponin_i)
- Imaging (echo_ef, echo_date)
- Medical history (diabetes, hypertension, dyslipidemia, heart_failure)
- Lifestyle (smoker, pack_years)
- Family history (CAD, diabetes, consanguinity)
- Metadata (ingested_at, data_quality_score)
