# BioLink NiFi 2.8.0 ETL Pipeline

Apache NiFi 2.8.0 pipeline with automated REST bootstrap for the documented
script ETL plan:
- **Step 1**: schema matching via `pipeline/two_stage_match.py`
- **Step 2**: harmonisation and de-identification via `pipeline/apply_schema.py`
- **Step 3**: OMOP-aligned exports via `pipeline/omop_etl.py`
- **Step 4**: quality and characterization via `pipeline/omop_quality.py`

NiFi remains the execution engine, but the ETL method now follows the scripts
pipeline rather than the older in-processor transformation logic.

---

## Architecture (auto-bootstrapped)

```
Step 1 (runs on schedule or RUN_ONCE):
GenerateFlowFile
  -> BiolinkMasterSchemaProcessor
  -> outputs/master_schema.csv

Steps 2-4 (runs on schedule or RUN_ONCE):
GenerateFlowFile
  -> BiolinkRegistryPipelineProcessor
     -> outputs/unified_registry.csv
     -> outputs/omop_cdm/*.csv
     -> outputs/data_quality_report.html
     -> outputs/cohort_characterization.csv
     -> PostgreSQL: unified_registry + omop_* tables
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
  ├── init_postgres_schema.sh      # Creates participant + harmonised tables/indexes
  ├── setup_nifi_flow.sh           # Legacy setup wrapper
  └── bootstrap_nifi_graph.py      # Idempotent REST bootstrap for Step1+Step2 graph
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

Runs the downstream script pipeline in one NiFi processor:

- Calls `pipeline/apply_schema.py` to build `outputs/unified_registry.csv`
- Calls `pipeline/omop_etl.py` to build OMOP CSV tables under `outputs/omop_cdm/`
- Calls `pipeline/omop_quality.py` to generate the HTML report and cohort characterization
- Loads the unified registry snapshot and OMOP outputs into PostgreSQL
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

This populates the root flow with Step 1 + Step 2 process groups on every stack startup.

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

## Cleaning Logic Reference

The transform processor ports the following Python ETL logic:

| Function | Source | Description |
|----------|--------|-------------|
| `parse_date` | `schema_mappings.py` | 7 date formats → ISO 8601 |
| `parse_numeric` | `schema_mappings.py` | Comma/space removal, range averaging |
| `normalize_gender` | `schema_mappings.py` | male/m/1 → "Male" |
| `normalize_boolean` | `schema_mappings.py` | yes/y/true/1/checked → True |
| `normalize_city` | `schema_mappings.py` | 70+ Egyptian city/governorate variants |
| `normalize_ethnicity` | `schema_mappings.py` | Nubian sub-groups, Egyptian |
| `normalize_bp` | `schema_mappings.py` | Strip mmHg suffix |
| `extract_systolic_bp` | `schema_mappings.py` | Split "120/80" → 120 |
| `extract_diastolic_bp` | `schema_mappings.py` | Split "120/80" → 80 |
| BP averaging | `transformer.py` | BHS: average of 3 brachial readings |
| Quality scoring | `transformer.py` | Weighted severity scoring (0–1) |
| City homogenization | `transformer.py` | CityHomogenizer with cache |
| Collision-safe IDs | `transformer.py` | `{dataset}_{id}` with fallbacks |

## Target Schema

Each dataset is loaded into its own table (`bhs_participants`, `ehvol_participants`) with the same 33-column schema:
- Identifiers (participant_id, source_dataset, source_record_id)
- Demographics (DOB, age, gender, nationality, enrollment_date)
- Location (current_city, childhood_city, father/mother origin)
- Clinical (height, weight, BMI, heart_rate, systolic/diastolic BP)
- Laboratory (HbA1c, troponin_i)
- Imaging (echo_ef, echo_date)
- Medical history (diabetes, hypertension, dyslipidemia, heart_failure)
- Lifestyle (smoker, pack_years)
- Family history (CAD, diabetes, consanguinity)
- Metadata (ingested_at, data_quality_score)
