# Registry Pipeline

The legacy generated-schema workflow has been removed.

The active pipeline lives under `db/test/` and is executed through:

```bash
python3 db/test/run_pipeline.py
```

Primary outputs:

- `outputs/unified_registry.csv`
- `outputs/comparability_report.json`
- `outputs/data_quality_report.html`
- `outputs/cohort_characterization.csv`
- `db/test/step_7/unified_wide_table.csv`
- `db/test/step_7/column_mapping.csv`
- `db/test/step_7/value_set_mapping.csv`
- `db/test/step_7/unit_mapping.csv`
- `db/test/step_7/modality_manifest.csv`

Detailed step documentation:

- `db/test/PIPELINE_STEPS_AND_SIGNIFICANCE.md`
- `db/test/UNIFICATION_STRATEGY.md`
