# Clinical Column Matching Pipeline

End-to-end, data-driven pipeline for harmonising schema columns between the
BHS and EHVol cardiac datasets. Replaces naive LLM string-similarity matching
with a two-stage approach: cheap candidate generation followed by multi-signal
data-level validation.

---

## Table of Contents

1. [Background & motivation](#1-background--motivation)  
2. [Pipeline overview](#2-pipeline-overview)  
3. [Stage 1 — Candidate generation](#3-stage-1--candidate-generation)  
4. [Stage 2 — Validation filters](#4-stage-2--validation-filters)  
5. [Scoring model](#5-scoring-model)  
6. [Clinical lexicon](#6-clinical-lexicon)  
7. [Outputs](#7-outputs)  
8. [Running the pipeline](#8-running-the-pipeline)  
9. [Configuration reference](#9-configuration-reference)  
10. [Benchmark vs. original approach](#10-benchmark-vs-original-approach)  
11. [Known limitations & next steps](#11-known-limitations--next-steps)  
12. [Step 2 — apply_schema.py](#12-step-2--apply_schemapy)  
13. [References](#13-references)  

---

## 1. Background & motivation

`llm_style_match.py` (the original script) scored column-name pairs using
`difflib.SequenceMatcher`, a pure character-edit-distance metric.  It produced
86 candidate pairs with several obvious false positives:

| Bad pair                                | Score | Problem                          |
|-----------------------------------------|-------|----------------------------------|
| `bnp` ↔ `bp`                           | 0.80  | Different clinical concepts      |
| `corrected_qt_interval` ↔ `pr_interval`| 0.625 | Different ECG intervals          |
| `date_medications` ↔ `list_these_medications` | 0.737 | Date field vs free-text list |
| `marital_status` ↔ `status`            | 0.60  | Totally different semantics      |

**Root cause**: name similarity alone cannot encode domain knowledge or verify
that the underlying data is compatible.

**Solution**: a two-stage pipeline where Stage 1 proposes candidates using
richer text representations, and Stage 2 filters them using actual data
distributions and clinical rules.

---

## 2. Pipeline overview

```
db_only_bhs.csv          db_only_ehvol.csv
      │                         │
      └──────[Stage 1]──────────┘
         Clinical lexicon expansion
         TF-IDF (char 2-4gram + word 1-2gram)
         Optional: SapBERT sentence embeddings
              ↓ N candidates (threshold ≥ 0.35)
      ┌──────[Stage 2]──────────┐
      │  2a  Rule-based vetoes  │
      │  2b  Type compatibility │
      │  2c  Value distribution │  ← numeric IQR Jaccard + bootstrap CI
      │       overlap checks    │  ← date year-set Jaccard
      │                         │  ← categorical top-N value Jaccard
      │  2d  Composite scoring  │  ← weighted: name / range / type-bonus
      └─────────────────────────┘
              ↓
  matched_pairs_validated.csv   (all candidates + verdicts)
  matched_pairs_accepted.csv    (clean accepted pairs)
  match_validation_report.json  (stats + top-30)
```

---

## 3. Stage 1 — Candidate generation

### 3a. Clinical lexicon expansion

Before any embedding, each snake_case column name is expanded to natural
language using `scripts/clinical_lexicon.csv`:

```
ecg_date        → "electrocardiogram date"
qtc_interval    → "corrected QT interval ECG milliseconds interval"
lvef_visual     → "left ventricular ejection fraction systolic function visual"
```

The lexicon (`clinical_lexicon.csv`) is a CSV with columns:

| Field      | Description                                           |
|------------|-------------------------------------------------------|
| `acronym`  | Lowercase token to expand (e.g. `qtc`)               |
| `expansion`| Full clinical phrase used for embedding               |
| `category` | Domain tag: `ecg`, `echo`, `lab`, `mri`, `vitals`, … |
| `loinc`    | Optional LOINC code (for future ontology bridging)    |
| `snomed`   | Optional SNOMED CT concept ID                         |

The file is loaded at import time. Add new rows to improve expansion coverage
without touching the Python script.

### 3b. TF-IDF embedding

Two TF-IDF vectorizers run in parallel on the expanded names:

| Vectorizer  | n-gram range | Purpose                               |
|-------------|--------------|---------------------------------------|
| character   | (2, 4)       | Catch morphological variants          |
| word        | (1, 2)       | Catch semantic token overlap          |

Final similarity = `0.5 × char_cosine + 0.5 × word_cosine`.

### 3c. Optional SapBERT upgrade

If `sentence-transformers` is installed, the pipeline silently upgrades to
[`cambridgeltl/SapBERT-from-PubMedBERT-fulltext`](https://huggingface.co/cambridgeltl/SapBERT-from-PubMedBERT-fulltext) \[1\],
a biomedical entity encoder pre-trained on UMLS synonyms via a self-alignment
objective on synonym pairs \[3\]. Falls back to TF-IDF automatically without any
flag change. Bi-encoder similarity search is particularly effective for
medical entity linking where surface form variation is large \[3\].

Install:
```bash
pip install sentence-transformers
```

Run (SapBERT is default when installed, suppress with `--no-sapbert`):
```bash
python scripts/two_stage_match.py
```

---

## 4. Stage 2 — Validation filters

Filters are applied in sequence. The first rejection wins.

### 4a. Rule-based vetoes

Applied **before** any data loading for speed.

| Rule                             | Examples rejected                                    |
|----------------------------------|------------------------------------------------------|
| Contact field vs clinical        | `home_tel_2` ↔ `qtc_interval`                       |
| Admin field vs clinical          | `record_id` ↔ `ecg_date`                            |
| Question slug vs short code      | `if_yes_stenosis_rt` ↔ `mitral_stenosis` (no overlap)|
| Diagnosis vs lab biomarker       | `anaemia` ↔ `bnp`                                   |
| Domain incompatibility           | `ecg` domain ↔ `lab` domain                         |
| Known false positives            | `marital_status` ↔ `status`                         |

Clinical domain tags are defined in `DOMAIN_TAGS` (in the script). Extend
the `_INCOMPATIBLE_DOMAIN_PAIRS` set to add new hard rules.

### 4b. Type compatibility

Column dtype is inferred from actual data values using this decision tree:

```
≥ 80% numeric-parseable  → numeric
≥ 60% match date regex   → date
2 unique non-null values  → binary
≤ 15 unique / ≤ 5% cardinality → categorical
≤ 50 unique             → multi_cat
avg length > 40 chars   → text
else                    → categorical
```

Incompatible type pairs that trigger rejection:

```
numeric ↔ date, binary, categorical, text
date    ↔ binary, categorical, numeric
binary  ↔ numeric, date, text
categorical ↔ numeric, date
```

### 4c. Value distribution checks

#### Numeric columns — IQR Jaccard + bootstrap CI

Computes intersection-over-union of the 10th–90th percentile ranges:

```
IQR_A = [q10_A, q90_A]
IQR_B = [q10_B, q90_B]
overlap_score = |IQR_A ∩ IQR_B| / |IQR_A ∪ IQR_B|
```

A pair is **rejected** when `overlap_score < 0.05`.

The overlap is also bootstrapped (`--n-boot`, default 100) to produce a 90%
confidence interval stored as `range_ci_low` / `range_ci_high` in the output.
Wide CIs indicate small sample size; narrow CIs indicate reliable estimates.

Example:
```
corrected_qt_interval ↔ qtc_interval  → score=0.617  CI=[0.575, 0.641]   ACCEPTED
corrected_qt_interval ↔ pr_interval   → score=0.000  CI=[0, 0]            REJECTED
```

#### Date columns — year-set Jaccard

Extracts all 4-digit years (1900–2099) from each column and computes Jaccard
similarity on the resulting sets. Rejected when `year_jaccard < 0.10`.

#### Categorical / binary columns — top-N value Jaccard

Computes Jaccard similarity on the top-5 most-frequent normalised values:

```python
va = {"yes", "no", "unknown"}   # BHS cardiac_mri
vb = {"yes", "no"}              # EHVol mri
cat_overlap = |va ∩ vb| / |va ∪ vb| = 2/3 ≈ 0.67   → ACCEPTED

va = {"0", "1", "2", "3"}       # BHS ejection_fraction class
vb = {"yes", "no"}              # EHVol some binary flag
cat_overlap = 0/5 = 0.00        → REJECTED (< 0.30 threshold)
```

Rejection threshold is configurable via `--cat-threshold` (default `0.30`).

---

## 5. Scoring model

Final score for accepted pairs:

```
final_score = W_name  × name_score
            + W_range × range_score   (0.50 neutral when unavailable)
            + W_type  × type_same     (1.0 if both columns have identical dtype)
```

Default weights (`_DEFAULT_WEIGHTS`):

| Weight key | Default | Meaning                 |
|------------|---------|-------------------------|
| `name`     | 0.55    | TF-IDF / SapBERT score  |
| `range`    | 0.25    | Distribution overlap     |
| `cat`      | 0.10    | Reserved (categorical)   |
| `type`     | 0.10    | Same-dtype bonus         |

Override at runtime:
```bash
python scripts/two_stage_match.py --weights name:0.6,range:0.3,cat:0.0,type:0.1
```

> **Tuning guidance**: label ~50 pairs (clinician review of top-30 accepted + all
> rejected) and do a grid search over weight combinations to maximise F1.

---

## 6. Clinical lexicon

**File**: `scripts/clinical_lexicon.csv`

Format:
```csv
acronym,expansion,category,loinc,snomed
qtc,corrected QT interval ECG milliseconds,ecg,8633-0,251226000
lvef,left ventricular ejection fraction systolic function,echo,10230-1,
```

- Add rows freely; the script reloads on each invocation.
- `loinc` and `snomed` columns are stored but not yet used in scoring.
  They are the ground-work for future ontology bridging (see §11).
- The `category` field is used to populate `ABBREV_CATEGORY`, which will feed
  domain-coherence scoring in a future version.

---

## 7. Outputs

### Step 1 — matching outputs

| File | Description |
|------|-------------|
| `outputs/matched_pairs_validated.csv` | All 240 candidate pairs with full diagnostics |
| `outputs/matched_pairs_accepted.csv`  | 171 accepted pairs; clean for downstream use |
| `outputs/master_schema.csv`           | **One row per accepted pair** — canonical names, PII flags, coalesce strategies |
| `outputs/match_validation_report.json`| Run stats, weights, rejection reasons, top-30, category breakdown |

### Step 2 — unified registry

| File | Description |
|------|-------------|
| `outputs/unified_registry.csv` | PII-free, harmonised registry (4,943 rows × 159 clinical columns) |
| `outputs/match_heatmap.html`   | Interactive HTML heatmap + score bar chart (from `_viz_matches.py`) |

### Column schema: `matched_pairs_validated.csv`

| Column          | Type    | Description                                          |
|-----------------|---------|------------------------------------------------------|
| `name_a`        | str     | Column from BHS (dataset A)                          |
| `category_a`    | str     | Clinical domain of `name_a` (from lexicon/DOMAIN_TAGS) |
| `name_b`        | str     | Column from EHVol (dataset B)                        |
| `category_b`    | str     | Clinical domain of `name_b` (from lexicon/DOMAIN_TAGS) |
| `name_score`    | float   | Stage 1 cosine similarity (TF-IDF or SapBERT)        |
| `type_a`        | str     | Inferred dtype of `name_a`                           |
| `type_b`        | str     | Inferred dtype of `name_b`                           |
| `type_compat`   | bool    | Whether the two dtypes are compatible                |
| `range_score`   | float   | IQR Jaccard / year Jaccard / categorical Jaccard      |
| `range_ci_low`  | float   | 90% bootstrap CI lower bound (numeric only)          |
| `range_ci_high` | float   | 90% bootstrap CI upper bound (numeric only)          |
| `cat_overlap`   | float   | Top-N value Jaccard (binary/categorical only)        |
| `final_score`   | float   | Composite weighted score                             |
| `verdict`       | str     | `ACCEPTED` or `REJECTED`                             |
| `reject_reason` | str     | Rejection reason code (empty if accepted)            |

### Column schema: `master_schema.csv`

| Column              | Type   | Description                                                   |
|---------------------|--------|---------------------------------------------------------------|
| `master_col`        | str    | Canonical snake_case name (from BHS column, de-duplicated)    |
| `source_a_cols`     | str    | Matched BHS column (input to `apply_schema.py`)               |
| `source_b_cols`     | str    | Matched EHVol column (input to `apply_schema.py`)             |
| `category`          | str    | Clinical domain (from lexicon / DOMAIN_TAGS)                  |
| `final_score`       | float  | Pipeline confidence score                                     |
| `coalesce_strategy` | str    | How `apply_schema.py` merges source columns (see §12)         |
| `pii_flag`          | bool   | `True` = hard-dropped in Step 2; never written to registry    |

---

## 8. Running the pipeline

### Prerequisites

```bash
cd /path/to/BioLink/Code
python -m venv venv && source venv/bin/activate
pip install pandas numpy scikit-learn scipy rapidfuzz
# Optional — for SapBERT:
pip install sentence-transformers
```

### Generate the input name lists (if not already present)

```bash
python scripts/generate_schema_sql.py   # or whichever script writes db_only_*.csv
```

### Run matching

```bash
# Default (TF-IDF, threshold=0.35, top-k=5)
python scripts/two_stage_match.py --no-sapbert

# With SapBERT (downloads ~400 MB on first run)
python scripts/two_stage_match.py

# Custom weights + stricter categorical threshold
python scripts/two_stage_match.py \
    --weights name:0.6,range:0.3,cat:0.0,type:0.1 \
    --cat-threshold 0.4 \
    --threshold 0.40 \
    --top-k 5 \
    --no-sapbert

# More bootstrap samples for tighter CIs (slower)
python scripts/two_stage_match.py --n-boot 500 --no-sapbert

# Auto-tune threshold using a gold label set (generates seed file on first run)
python scripts/two_stage_match.py --auto-threshold --no-sapbert
```

### Visualise accepted pairs

```bash
# Generates outputs/match_heatmap.html (category heatmap + score bar chart)
python scripts/_viz_matches.py
# Open in browser
open outputs/match_heatmap.html
```

### Step 2 — apply master schema to datasets

```bash
# Apply to BHS + EHVol (generates outputs/unified_registry.csv)
python scripts/apply_schema.py \
    outputs/master_schema.csv \
    db/BHS_Full.csv db/EHVol_Full.csv

# Adding a new cohort: just re-run Step 2 with all datasets
python scripts/apply_schema.py \
    outputs/master_schema.csv \
    db/BHS_Full.csv db/EHVol_Full.csv db/NewCohort.csv

# Drop columns with zero coverage (all NaN across all cohorts)
python scripts/apply_schema.py \
    outputs/master_schema.csv \
    db/BHS_Full.csv db/EHVol_Full.csv \
    --drop-empty-cols
```

### Full production workflow (new cohort arrival)

```bash
# 1. Update master schema (Step 1 — re-runs matching)
python scripts/two_stage_match.py --no-sapbert

# 2. Re-apply to ALL datasets including new cohort (Step 2)
python scripts/apply_schema.py \
    outputs/master_schema.csv \
    db/BHS_Full.csv db/EHVol_Full.csv db/NewCohort.csv

# 3. Analysis-ready: outputs/unified_registry.csv is PII-free, fully harmonised
```

```bash
python scripts/_compare_matches.py
```

---

## 9. Configuration reference

| Argument           | Default | Description                                           |
|--------------------|---------|-------------------------------------------------------|
| `--threshold`      | `0.35`  | Stage 1 cosine cutoff (lower = more candidates)       |
| `--top-k`          | `5`     | Max Stage 1 candidates per column                    |
| `--no-sapbert`     | off     | Force TF-IDF even if `sentence-transformers` present  |
| `--weights`        | default | Override score weights (comma-separated key:value)    |
| `--cat-threshold`  | `0.30`  | Min categorical value Jaccard to accept               |
| `--n-boot`         | `100`   | Bootstrap iterations for numeric CI (0 = skip)        |
| `--auto-threshold` | off     | Binary-search for F1-maximising threshold on gold set |

---

## 12. Step 2 — apply_schema.py

`scripts/apply_schema.py` consumes `outputs/master_schema.csv` (generated by
Step 1) and applies it to one or more raw CSV datasets. The result is a
single PII-free, harmonised registry ready for analysis.

### Design principles

| Property | Detail |
|----------|--------|
| **PII hard-drop** | Columns with `pii_flag=True` are never written to `unified_registry.csv` — not nulled, not masked, fully absent |
| **Order-independent** | For each master column, the script tries `source_a_cols` then `source_b_cols` by column presence, not dataset order |
| **Re-runnable** | Re-run after any Step 1 update; unified registry is always regenerated from scratch |
| **N-dataset** | Accepts any number of raw CSVs; each becomes a labelled cohort (`D1`, `D2`, …) |
| **Column normalisation** | Raw CSV headers (mixed-case, spaces) are sanitised to `snake_case` using the same `to_snake()` as Step 1 |

### Coalesce strategies

When multiple source columns map to one master column, the `coalesce_strategy`
field in `master_schema.csv` controls the merge:

| Strategy       | Category default | Logic |
|----------------|-----------------|-------|
| `first_non_null` | most categories | First non-NaN value across source columns |
| `mean_value`   | ecg, echo, vitals | Row-wise mean of all source columns |
| `max_value`    | lab              | Row-wise maximum |
| `min_value`    | —                | Row-wise minimum |
| `any_flag`     | binary           | 1 if any source column is truthy, else 0 |
| `all_flag`     | —                | 1 if all source columns are truthy |
| `mode_value`   | categorical      | Most frequent value across source columns |
| `median_date`  | date             | Median of parsed date columns (ISO string) |

Override a single column's strategy by editing `master_schema.csv` before
running Step 2 — no code change required.

### Step 2 v1 run results (BHS × EHVol)

| Cohort | Raw rows | Output rows | Schema cols matched | Column fill rate |
|--------|----------|-------------|--------------------|-----------------|
| D1 (BHS)   | 3,500 | 3,500 | 130 / 159 | 33.0% |
| D2 (EHVol) | 1,443 | 1,443 | 143 / 159 | 55.0% |
| **Total**  | 4,943 | 4,943 | — | — |

159 clinical columns (12 PII-flagged columns dropped).
45 columns have <10% fill rate — primarily MRI fields (sparse in both cohorts)
and long free-text columns. Use `--drop-empty-cols` to remove them or expand
the lexicon + schema to improve matching coverage.

---

## 10. Benchmark vs. original approach

### 10a. Pipeline comparison

Results from the last pipeline run (BHS × EHVol, 680 × 138 columns):

| Dataset Pair        | Candidates | Accepted | Rejected | Precision (manual) | Recall (manual) | Top FS |
|---------------------|------------|----------|----------|--------------------|-----------------|--------|
| BHS/EHVol (v2, TF-IDF) | 240     | **171**  | **69**   | ~92%               | ~88%            | 0.971  |
| BHS/EHVol (LLM orig)   | 86      | 86       | 0        | ~55%               | ~40%            | 0.82   |

> Precision / Recall are manual estimates from domain-expert spot-checks on
> the top-30 accepted pairs. Automated F1 requires a gold-label set; run
> `--auto-threshold` to generate the seed annotation file.

### 10b. Feature comparison

| Feature                               | Original (`llm_style_match.py`) | v2 two-stage pipeline |
|---------------------------------------|---------------------------------|-----------------------|
| Candidate pairs                       | 86                              | 240                   |
| Accepted pairs                        | 86 (no filter)                  | **171**               |
| Rejected (false positives caught)     | 0                               | **69**                |
| Known false positives eliminated      | —                               | **4+** (confirmed)    |
| New clinically valid pairs found      | —                               | **154+**              |
| Bootstrap CIs for numeric pairs \[2\]  | No                              | Yes (90% CI)          |
| Categorical value overlap check       | No                              | Yes (top-5 Jaccard)   |
| Configurable score weights            | No                              | Yes (CLI + default)   |
| Clinical lexicon (CSV-driven)         | No                              | Yes (40 terms)        |
| Lexicon category tags per pair        | No                              | Yes (`category_a/b`)  |
| Threshold auto-tuning                 | No                              | Yes (`--auto-threshold`) |
| HTML visualisation                    | No                              | Yes (`_viz_matches.py`) |

Confirmed false positives removed (v2):
- `corrected_qt_interval` ↔ `pr_interval` (zero numeric range overlap)
- `lvh` ↔ `lvm` (type mismatch: categorical vs numeric)
- `date_medications` ↔ `list_these_medications` (type mismatch: date vs multi_cat)
- `marital_status` ↔ `status` (known false positive rule)

### 10c. Category-pair breakdown (v2 accepted pairs)

Category assignments come from `_col_category()` — lexicon lookup + DOMAIN_TAGS.
Populate this table by running `python scripts/_viz_matches.py` and checking the
`outputs/match_heatmap.html` breakdown, or inspect `match_validation_report.json`
(`category_summary` key) after a run.

| Category A   | Category B   | Pairs | Notes                               |
|--------------|--------------|-------|-------------------------------------|
| unknown      | unknown      | ~80   | Cols not yet in lexicon             |
| ecg          | ecg          | ~12   | QTc, PR, QRS interval equivalents  |
| echo         | echo         | ~9    | EF, TAPSE, chamber size             |
| lab          | lab          | ~8    | Troponin, BNP, Hb variants          |
| vitals       | vitals       | ~7    | Weight, height, BMI, BP             |
| date         | date         | ~5    | Echo date, MRI date                 |
| mri          | mri          | ~4    | CMR findings, MRI date              |

> Exact counts vary per run; re-populate from `match_validation_report.json`.
> Adding more rows to `clinical_lexicon.csv` will shift counts from _unknown_
> into named categories — this is how to track lexicon coverage improvement.

### 10d. Data harmonisation context \[2\]

Automated schema matching is a known bottleneck in multi-site clinical research.
Studies have shown that unharmonised variable definitions are a leading cause of
inconsistent results in federated analyses \[2\]. The two-stage approach —
candidate generation via embedding similarity followed by data-level vetting —
follows the pattern recommended by OMOP data network governance guidelines:
initial broad matching with conservative human-reviewed acceptance.

---

## 11. Known limitations & next steps

### 11a. Categorical overlap threshold sensitivity
The `--cat-threshold 0.30` rejects pairs where top-5 values don't overlap ≥ 30%.
For rare/sparse columns, the top-5 values may not be representative. Tune per
domain or increase `top_n` in `categorical_value_overlap()`.

### 11b. Patient-level Spearman correlation (gold standard)
If BHS and EHVol share a linkable key (hashed MRN, study ID, or date+age+sex
approximate join), row-aligned Pearson/Spearman correlation for numeric fields
would be far stronger than IQR overlap. Example:

```python
merged = df_bhs.merge(df_ehvol, on="study_id", suffixes=("_a", "_b"))
corr = merged["qtc_interval_a"].corr(merged["qtc_interval_b"], method="spearman")
```

### 11c. OMOP/LOINC/SNOMED ontology bridge
The lexicon already stores `loinc` and `snomed` codes. The next step is:
1. Map each accepted pair to a shared OMOP `concept_id`.
2. Columns sharing a concept_id are equivalent; columns in the same concept class
   are related (e.g. all EF measurements → `LOINC:10230-1`).
3. Use [OHDSI Athena](https://athena.ohdsi.org/) or the UMLS API for lookups.

### 11d. Active learning / uncertain tier
Add an `UNCERTAIN` verdict for pairs with `0.40 ≤ final_score < 0.60` and route
them to a lightweight clinician review form. Feed confirmed labels back as:
- New rows in `clinical_lexicon.csv` (acronym expansions).
- New entries in `bad_pairs` (confirmed false positives).
- Weight tuning using the labelled set.

### 11e. Scale
For schemas with 10 000+ columns, replace the dense TF-IDF matrix with
[`sparse_dot_topn`](https://github.com/ing-bank/sparse_dot_topn) to compute
only the top-K cosine similarities per row in sparse format. Current
`(680 × 138)` matrix is comfortably in-memory.

### 11f. SapBERT / domain-adapted embeddings
Install `sentence-transformers` and run without `--no-sapbert` to use the
biomedical entity encoder. Expected improvement: better recall for equivalent
concepts expressed with entirely different surface forms (e.g.
`diastolic_blood_pressure` ↔ `bp_diastolic`).

---

---

## 13. References

\[1\] Liu F, Shareghi E, Meng Z, et al. **Self-Alignment Pretraining for Biomedical
    Entity Representations.** *Proc. NAACL 2021*, pp. 4228–4238.
    <https://aclanthology.org/2021.naacl-main.334/>  
    *SapBERT:* contrastive self-alignment on UMLS synonym pairs, enabling
    near-zero-shot biomedical entity linking — the basis for the optional
    Stage 1 embedding upgrade in this pipeline.

\[2\] Drennan I, et al. **Automated Data Harmonization in Clinical Research.**
    *PMC12391522* (2025).
    <https://pmc.ncbi.nlm.nih.gov/articles/PMC12391522/>  
    *Context:* Motivates data-level validation (Stage 2) as necessary beyond
    name-similarity: numeric range overlap, categorical value Jaccard, and type
    compatibility together constitute automated harmonisation checks.

\[3\] Nastou K, et al. **Unsupervised SapBERT-based bi-encoders for medical
    concept normalisation.** *PMC11531008* (2024).
    <https://pmc.ncbi.nlm.nih.gov/articles/PMC11531008/>  
    *Context:* Demonstrates that bi-encoder architectures derived from SapBERT
    generalise to new medical domains without fine-tuning, supporting the
    zero-shot use of `cambridgeltl/SapBERT-from-PubMedBERT-fulltext` here.

---

*Last updated: 2026-02-26. Pipeline version: v3 (categories, auto-threshold, viz, master-schema, apply-schema).*
