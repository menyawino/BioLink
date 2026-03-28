# Registry Pipeline (Fresh Baseline)

This pipeline aligns with your 4-step flow:

1. **Data profiling + schema matching**
   - Script: `nifi/pipeline/two_stage_match.py`
   - Output: `outputs/master_schema.csv`
   - Includes `omop_domain` + `standard_vocab` hints for OMOP readiness.

2. **PII scrubbing + schema application**
   - Script: `nifi/pipeline/apply_schema.py`
   - Output: `outputs/unified_registry.csv`

3. **OMOP CDM bootstrap mapping**
   - Script: `nifi/pipeline/omop_etl.py`
   - Output dir: `outputs/omop_cdm/`
   - Tables: `person`, `measurement`, `condition_occurrence`, `observation`

4. **Data quality + characterization**
   - Script: `nifi/pipeline/omop_quality.py`
   - Outputs:
     - `outputs/data_quality_report.html`
     - `outputs/cohort_characterization.csv`

---

## Quick Start

```bash
python3 nifi/pipeline/two_stage_match.py
python3 nifi/pipeline/apply_schema.py outputs/master_schema.csv db/BHS_Full.csv db/EHVol_Full.csv --output outputs/unified_registry.csv
python3 nifi/pipeline/omop_etl.py --unified outputs/unified_registry.csv --schema outputs/master_schema.csv --output-dir outputs/omop_cdm
python3 nifi/pipeline/omop_quality.py --input-dir outputs/omop_cdm
```

## Optional: External OHDSI tools

If available in your environment, you can add:

- WhiteRabbit / Usagi for richer source-to-standard concept mapping
- OHDSI Data Quality Dashboard (DQD)
- Achilles for characterization on a full OMOP instance

These are environment-specific and can be layered on top of this baseline.
