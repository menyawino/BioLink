# Cross-Dataset Unification Strategy: BHS + EHVol

## Executive Summary

This document describes a **research-driven, zero-data-loss unification strategy** for merging the BHS (3,500 rows, 417 columns) and EHVol (1,443 rows, 132 columns) cardiovascular research datasets. The approach is grounded in modern data harmonization research: FAIR principles, OMOP CDM-inspired concept mapping, multi-modal clinical data fusion, and schema-on-read architectures.

---

## 1. Dataset Characteristics

| Feature | BHS | EHVol |
|---------|-----|-------|
| Rows | 3,500 | 1,443 |
| Columns (post-cleaning) | 417 | 132 |
| Study Period | ~2017–2024 | ~2014–2018 |
| Echo Units | mm | cm |
| MRI Data | ❌ No | ✅ Yes |
| ECG Exact Matches | ❌ No | ✅ Yes |
| Medication Slots | 10 repeating sets | 1 slot |
| Family History | 10 relatives (wide) | Checkboxes (compact) |
| Echo Wall Segments | 16 segments | None |
| Carotid Duplex | ✅ Yes | ❌ No |
| Labs | Comprehensive (25+) | Limited (HbA1c, Troponin I) |
| Primary ID | MRN (BU) | DNA ID |
| Shared ID Space | ❌ None | ❌ None |

**Critical Insight**: The datasets are **analytically independent at the participant level** (no shared IDs), but **semantically overlapping at the schema level**. This means unification must happen at the *concept* level, not the *participant* level.

---

## 2. Core Design Principles

### 2.1 Zero Data Loss
No column, value, or modality is dropped. Every original field is preserved either in the unified schema or in a companion audit table.

### 2.2 Modality-Awareness
Same clinical concept measured by different modalities (e.g., LVEF from echo vs MRI vs ECG) is **not collapsed**. Instead, modality is explicitly encoded.

### 2.3 Semantic Layering
We use a three-layer architecture:
1. **Raw Layer**: Original columns with dataset-of-origin tags
2. **Semantic Layer**: Columns mapped to canonical concepts using the classification taxonomy
3. **Harmonized Layer**: Values standardized (units, categories, formats)

### 2.4 Schema-on-Read with Materialized Views
Rather than forcing one rigid schema, we produce:
- A **unified wide table** for simple pooled analysis
- A **unified long table** for complex multi-modal analysis
- **Companion mapping tables** for transparency

---

## 3. Research Foundations

### 3.1 FAIR Principles (Wilkinson et al., 2016)
- **Findable**: Every concept has a persistent canonical name
- **Accessible**: Raw data preserved; harmonized data documented
- **Interoperable**: Shared vocabulary across datasets
- **Reusable**: Provenance tracking for every transformation

### 3.2 OMOP Common Data Model (OHDSI)
Inspired by OMOP's concept-based approach:
- Each column maps to a **canonical concept** (e.g., `lvedd`)
- Concepts have **attributes**: modality, unit, data type, value set
- Same concept + different modality = different columns

### 3.3 Multi-Modal Data Fusion (Clinical Imaging Research)
In cardiovascular research, the same biomarker can be measured by echo, MRI, CT, or invasive catheterization. Research best practice (e.g., SCMR, ASE guidelines) treats these as **complementary, not interchangeable**.

### 3.4 Tidy Data (Wickham, 2014)
- Each variable forms a column
- Each observation forms a row
- Each value is a cell
- Applied with flexibility for repeating groups (medications, relatives)

### 3.5 Schema Evolution & Data Lakes (Inmon, 2016; Stein & Morrison, 2014)
Rather than ETL (extract-transform-load), we use **ELT** (extract-load-transform):
1. Load raw data as-is
2. Apply transformations via mapping tables
3. Materialize views on demand

---

## 4. Unification Architecture

### 4.1 Column Mapping Strategy

Each column is mapped using a **4-tuple key**:
```
(broad_family, broad_category, normalized_name, modality)
```

**Example mappings:**

| BHS Column | EHVol Column | Canonical Concept | Modality | Unit |
|------------|--------------|-------------------|----------|------|
| `LVEDD` | `LVEDD` | `lvedd` | `echo` | `mm` (BHS), `cm` (EHVol) |
| `LVEF - M mode` | `EF` | `lvef` | `echo` | `%` |
| — | `Left ventricular ejection fraction` | `lvef` | `mri` | `%` |
| `Ventricular Rate` | `Rate` | `heart_rate` | `ecg` | `bpm` |
| `Heart rate` (clinical exam) | `Heart Rate` | `heart_rate` | `vitals` | `bpm` |
| `Weight in kg` | `Weight (kg)` | `weight` | `vitals` | `kg` |

### 4.2 Modality Disambiguation Rules

When the same concept appears in both datasets:
1. **If same modality**: Merge to single column, tag unit if different
2. **If different modalities**: Create separate columns with modality suffix
3. **If modality unclear**: Default to dataset-specific modality + flag for review

### 4.3 Repeating Group Handling

**BHS Medications** (10 slots × 6 fields = 60 columns):
- Transform to long format: `(participant_id, medication_index, name, category, status, route, dose, frequency)`
- This reduces 60 sparse columns to 8 dense columns

**BHS Family History** (10 relatives × 4 fields = 40 columns):
- Transform to long format: `(participant_id, relative_index, relation, event, gender, age_at_event)`

**EHVol Family History** (checkboxes + free text):
- Keep as wide format (already compact) OR pivot to long format for consistency

### 4.4 Value Set Harmonization

| BHS Value | EHVol Value | Unified Value |
|-----------|-------------|---------------|
| `Yes` / `No` | `Yes` / `No` | `yes` / `no` |
| `Checked` | `Checked` | `true` |
| `Unchecked` | `Unchecked` | `false` |
| `Male` / `Female` | `Male` / `Female` | `male` / `female` |
| `Smoker` / `non-smoker` / `Ex-smoker` | `Yes` / `No` | `current` / `never` / `former` |

### 4.5 Unit Standardization

For concepts with different units across datasets:
- **Option A**: Keep original values, add `_unit` column
- **Option B**: Standardize to common unit (e.g., convert EHVol cm → mm for echo)
- **Decision**: Use Option A (preserve raw) + provide Option B as derived column

---

## 5. Output Schema

### 5.1 Unified Wide Table

```
# Identity & Metadata
dataset_source          # "BHS" or "EHVol"
participant_id          # synthetic: BHS_{mrn_bu} or EHVol_{dna_id}
record_id               # original record ID

# Demographics (shared)
age, age_unit, gender, nationality, ethnicity,
marital_status, consanguinity_status, number_of_children,

# Vitals (shared)
heart_rate_vitals, heart_rate_vitals_unit,
weight, weight_unit, height, height_unit, bmi,
systolic_bp, diastolic_bp, bp_unit,

# Echo (modality-specific)
lvedd_echo, lvedd_echo_unit,
lvesd_echo, lvesd_echo_unit,
lvef_echo, lvef_echo_unit,
lvef_mri, lvef_mri_unit,        # EHVol only
lvm_echo, lvm_echo_unit,
lvm_mri, lvm_mri_unit,          # EHVol only

# ECG (modality-specific)
heart_rate_ecg, heart_rate_ecg_unit,
qrs_duration_ecg, qrs_duration_ecg_unit,
pr_interval_ecg, pr_interval_ecg_unit,
qt_interval_ecg, qt_interval_ecg_unit,

# Labs (sparse — many NULLs for EHVol)
hba1c, hba1c_unit,
troponin, troponin_unit,
creatinine, creatinine_unit,
...

# Diagnoses (shared)
hypertension, diabetes, dyslipidemia, ...

# Lifestyle (shared)
smoking_status, alcohol_status, ...

# Family History (long-format companion table)
# Medications (long-format companion table)

# BHS-Specific (preserved as-is)
carotid_imt_right, carotid_imt_left,
ascvd_risk_10yr, ...

# EHVol-Specific (preserved as-is)
mri_performed, mri_date, ...
```

### 5.2 Unified Long Table (for multi-modal analysis)

```
participant_id, concept, modality, value, unit, dataset_source, original_column
```

### 5.3 Companion Tables

1. **column_mapping.csv**: Every original column → canonical concept + modality + transformation
2. **value_set_mapping.csv**: Original values → unified values per concept
3. **unit_mapping.csv**: Concept + dataset → unit + conversion factor
4. **modality_manifest.csv**: All modalities available per concept per dataset

---

## 6. Implementation: `step_7_unify_datasets.py`

The implementation follows this pipeline:

```
Load cleaned datasets (step_4 outputs)
    ↓
Load column classifications (step_0 outputs)
    ↓
Build concept registry from all columns
    ↓
Apply semantic mapping rules
    ↓
Handle repeating groups (medications, relatives) → long format
    ↓
Apply value set harmonization
    ↓
Apply unit tagging
    ↓
Generate unified wide table
    ↓
Generate unified long table
    ↓
Generate companion mapping tables
    ↓
Write audit report
```

---

## 7. Quality Assurance

### 7.1 Coverage Metrics
- % of BHS columns mapped to canonical concepts
- % of EHVol columns mapped to canonical concepts
- % of overlapping concepts (present in both datasets)
- % of dataset-unique concepts

### 7.2 Conflict Detection
- Same concept, same modality, different units → flag
- Same concept, different value sets → flag
- Columns that cannot be mapped → preserve as-is with `unmapped_` prefix

### 7.3 Sparsity Analysis
- For each unified column: % non-null per dataset
- Identify columns that are too sparse for analysis

---

## 8. Future Extensions

### 8.1 Cross-Dataset Linkage (if IDs become available)
If a shared identifier is discovered later (e.g., national ID, biobank sample ID), the `participant_id` can be updated without reprocessing.

### 8.2 Ontology Enrichment
Map canonical concepts to standard ontologies:
- LOINC for labs
- SNOMED CT for diagnoses
- RadLex for imaging

### 8.3 Automated Concept Discovery
Use NLP/embedding models to suggest mappings for unmapped columns based on column names and value distributions.

---

## References

1. Wilkinson, M. D. et al. (2016). The FAIR Guiding Principles for scientific data management and stewardship. *Scientific Data*, 3, 160018.
2. Hripcsak, G. et al. (2015). Observational Health Data Sciences and Informatics (OHDSI): Opportunities for Observational Researchers. *Studies in Health Technology and Informatics*, 216, 574–578.
3. Wickham, H. (2014). Tidy Data. *Journal of Statistical Software*, 59(10), 1–23.
4. Inmon, B. (2016). *Data Lake Architecture: Designing the Data Lake and Avoiding the Garbage Dump*. Technics Publications.
5. Stein, B. A., & Morrison, A. (2014). The enterprise data lake: Better integration and less upkeep. *TDWI Research*.
6. Lang, R. M. et al. (2015). Recommendations for cardiac chamber quantification by echocardiography in adults. *Journal of the American Society of Echocardiography*, 28(1), 1–39.
7. Schulz-Menger, J. et al. (2013). Standardized image interpretation and post-processing in cardiovascular magnetic resonance. *Journal of Cardiovascular Magnetic Resonance*, 15, 35.
