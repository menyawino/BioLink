# BioLink ETL

Small package to homogenize (clean) clinical CSVs and integrate them into the project database and Superset.

Usage (from repo root):

```bash
python3 -m biolink_etl.pipeline --csv db/090925_EHVol_Data.csv --table EHVOL --schema public --replace
```

This will:
- Load and run `db/clean_clinical_data.apply_all_cleaning` on the CSV
- Sanitize column names and write to the database specified by `app.config.settings.database_url`
- Register the dataset in Superset (unless `--skip-superset`)
- Apply governorate ISO mapping and refresh Superset metadata (unless skipped)
- Save a `column_map_etl.csv` mapping file in the `biolink_etl` folder for traceability

Governed protocol (stdio):

```bash
echo '{"version":"1.0","action":"run_pipeline","request_id":"1","payload":{"csv":"db/EHVOL_50.csv","table":"ehvol_50_test","schema":"public","nrows":50,"skip_superset":true}}' | \
	python3 -m biolink_etl.pipeline --protocol-stdio
```
