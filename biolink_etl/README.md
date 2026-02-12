# BioLink ETL

Orchestrator for dbt + Superset refresh + optional lineage emission.

## Dataset naming convention

When you run the orchestrator with `--csv path/to/MyFile.csv`, the Superset dataset that gets published will be named after the CSV filename stem (lowercased and sanitized):

- `MyFile.csv` -> `myfile`

Technically, the orchestrator registers a Superset *virtual dataset* named `<csv_stem>` with SQL `SELECT * FROM <schema>.<table>`.

Usage (from repo root):

```bash
python3 -m biolink_etl.pipeline \
	--table ehvol_full \
	--schema public \
	--csv db/EHVol_Full.csv \
	--dbt-select ehvol_full
```

This will:
- Run dbt standardization models
- Register a Superset dataset named after the CSV stem (unless `--skip-superset`)
- Refresh Superset metadata (unless skipped)
- Emit lineage to OpenMetadata (if configured)

## Lineage visualization (lightweight)

dbt includes an open-source lineage/DAG UI:

```bash
DB_HOST=localhost DB_PORT=5432 DB_USER=biolink DB_PASSWORD=biolink_secret DB_NAME=biolink \
	dbt docs generate --project-dir biolink_etl/dbt --profiles-dir biolink_etl/dbt

DB_HOST=localhost DB_PORT=5432 DB_USER=biolink DB_PASSWORD=biolink_secret DB_NAME=biolink \
	dbt docs serve --project-dir biolink_etl/dbt --profiles-dir biolink_etl/dbt --port 8089
```

Open http://localhost:8089 and use the DAG/Lineage views.

Governed protocol (stdio):

```bash
echo '{"version":"1.0","action":"run_pipeline","request_id":"1","payload":{"table":"ehvol_cleaned","schema":"public","dbt_select":"staging.ehvol_cleaned"}}' | \
	python3 -m biolink_etl.pipeline --protocol-stdio
```

Governed protocol (HTTP):

```bash
python3 -m biolink_etl.pipeline --protocol-http --host 0.0.0.0 --port 8090
```

Legacy CSV ETL (deprecated):

- See [legacy/biolink_etl_legacy/pipeline_legacy.py](legacy/biolink_etl_legacy/pipeline_legacy.py)

Environment variables for integrations:

- `OPENMETADATA_URL` and optional `OPENMETADATA_JWT`
- `OPENMETADATA_LINEAGE_ENDPOINT` (override lineage endpoint)
- `DBT_PROJECT_DIR`, `DBT_PROFILES_DIR` (override dbt paths)
