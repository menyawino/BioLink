# BioLink ETL

Small package to homogenize (clean) clinical CSVs and integrate them into the project database and Superset.

Usage (from repo root):

```bash
python3 -m biolink_etl.cli --csv db/090925_EHVol_Data.csv --table EHVOL --schema public --replace
```

This will:
- Load and run `db/clean_clinical_data.apply_all_cleaning` on the CSV
- Sanitize column names and write to the database specified by `app.config.settings.superset_database_uri`
- Save a `column_map_etl.csv` mapping file in the `biolink_etl` folder for traceability
