# Pipeline Steps and Their Significance

This workspace currently implements steps 0 through 6 for two datasets:

- BHS: 3,500 rows
- EHVol: 1,443 rows

The current pipeline is designed to do seven things in order:

1. Understand what each column means.
2. Remove or retain fields based on privacy and research value.
3. Reduce empty or structurally redundant columns, plus intra-database validation.
4. Propose safe normalization strategies without overwriting the raw data.
5. Apply per-column min/max/expected-range rules with outlier quarantine.
6. Extract numeric + unit tokens and suggest canonical forms.
7. Fuzzy-match geographic and nationality values against canonical dictionaries.

## At a glance

| Dataset | Raw columns | After step 1 | After step 2 | After step 4 (range-cleaned) |
| --- | ---: | ---: | ---: | ---: |
| BHS | 703 | 669 | 417 | 417 |
| EHVol | 161 | 149 | 132 | 132 |

This shows the overall pattern clearly:

- Step 1 is mainly about privacy control.
- Step 2 is mainly about making the table analytically usable, plus catching data-quality issues.
- Step 3 does not rewrite the data; it profiles columns and suggests the safest next normalization action.
- Step 4 quarantines numeric and date outliers that fall outside plausible clinical ranges.
- Step 5 scans for embedded unit tokens (e.g., `10y`, `5 kg`) and suggests canonical forms.
- Step 6 maps free-text city and country names to canonical dictionaries via fuzzy matching.

## Step 0: Column mapping and semantic classification

Artifacts:

- `step_0_column_mapping.py`
- `BHS_column_classification.csv`
- `EHVol_column_classification.csv`

### What this step does

Step 0 reads each source column and assigns:

- a broad family, such as `Participant Context` or `Clinical Profiles`
- a broad category, such as `Demographics & Social Context` or `Laboratory Tests & Biomarkers`
- a privacy label, such as `direct_identifier`, `quasi_identifier`, `sensitive_health`, or `non_pii`

This classification is the control layer for the rest of the pipeline. Later steps do not guess what a column means; they follow this mapping.

### Real examples from the data

| Dataset | Column | Example raw values | Classification | Why it matters |
| --- | --- | --- | --- | --- |
| EHVol | `Name` | `Yassmine Essam eldin Soliman Aguib`, `alaa eldin regab ahmed` | `direct_identifier` | This is personally identifying information and should not remain in a research-ready extract. |
| EHVol | `Date of Birth` | `1/13/1983`, `2/27/1979` | `quasi_identifier` | Not a direct name or ID, but still identifying enough to need a retention decision. |
| EHVol | `Current/Recent Smoker (< 1 year)` | `No`, `Yes` | `sensitive_health` | This is clinically meaningful and belongs in the analytic dataset. |
| BHS | `Participant's Name` | `Naser Ali Mohamed Rashwan`, `Aida abdelfatah mohamed` | `direct_identifier` | Clear PII. |
| BHS | `Address` | `No.57 St Ballana awl, Nasr Elnouba, Aswan` | `direct_identifier` | Direct location detail is high-risk identifying information. |
| BHS | `Mother origins` | `Egyptian`, `Egyptian` | `sensitive_health` in `Family History & Lineage` | Family-lineage context is analytically valuable but still sensitive. |

### Why this step is significant

Without this step, the rest of the workflow would be inconsistent. The same type of field could be kept in one form and dropped in another. Step 0 creates a repeatable policy surface so privacy handling and later reduction rules are traceable and auditable.

## Step 1: Remove PII while preserving analytical value

Artifacts:

- `step_1_remove_pii.py`
- `BHS_step_1_deidentified.csv`
- `EHVol_step_1_deidentified.csv`
- `BHS_step_1_retention_audit.csv`
- `EHVol_step_1_retention_audit.csv`

### What this step does

Step 1 applies a retention rule to every column:

- `direct_identifier` columns are usually dropped.
- `sensitive_health` and `non_pii` columns are kept.
- `quasi_identifier` columns are selectively kept only when there is a clear study reason.
- columns that can be derived from retained fields are dropped to avoid redundant or conflicting values.

### Results

| Dataset | Kept | Dropped | Main drop pattern |
| --- | ---: | ---: | --- |
| BHS | 669 | 34 | 26 direct identifiers, 4 nonessential quasi-identifiers, 2 calculatable ages, 2 derived smoking metrics |
| EHVol | 149 | 12 | 10 direct identifiers, 1 calculatable age, 1 high-risk quasi-identifier |

### Real examples from the data

#### Examples of fields dropped

| Dataset | Column dropped | Reason |
| --- | --- | --- |
| BHS | `Participant's Name` | direct identifier |
| BHS | `Address` | direct identifier |
| BHS | `Contact number 1` | direct identifier |
| BHS | `Upload consent scan 1` | direct identifier |
| EHVol | `Record ID` | direct identifier |
| EHVol | `Name` | direct identifier |
| EHVol | `Home Tel.` | direct identifier |
| EHVol | `Email` | direct identifier |
| EHVol | `Address` | direct identifier |

#### Examples of fields kept

| Dataset | Column kept | Retention reason | Why the keep is important |
| --- | --- | --- | --- |
| BHS | `Enrollment date` | retain enrollment date as requested | Preserves study timing. |
| BHS | `Date of birth` | retain birth date as requested | Keeps age-related analysis possible. |
| BHS | `Gender` | retain sex/gender for study analysis | Important demographic stratifier. |
| BHS | `What ethnicity do you consider yourself?` | retain ethnicity for study analysis | Important for subgroup analysis. |
| BHS | `Can you speak Nubian?` | retain language background for study analysis | Preserves social and cultural context. |
| EHVol | `DNA ID` | retain identifier by request | Keeps the study linkage requested by the workflow. |
| EHVol | `Date of Birth` | retain birth date as requested | Preserves time and age analysis. |
| EHVol | `Gender` | retain sex/gender for study analysis | Important demographic feature. |
| EHVol | `Nationality` | retain coarse nationality for study analysis | Useful, but still needs later normalization. |
| EHVol | `Current City of Residence` | retain city-level residence data for study analysis | Keeps geographic context at the requested level. |

#### Example of dropping derived redundancy

- BHS drops `Current age` and `Age at enrollment` because they can be calculated from retained date fields.
- EHVol drops `Age` for the same reason after keeping `Date of Birth`.

### Why this step is significant

This is the privacy-value balance of the pipeline. It removes obvious re-identifiers such as names, phone numbers, and addresses, but it does not strip the dataset so aggressively that the study becomes unusable. The retention audit makes every keep and drop explicit, which is critical for compliance review and later scientific interpretation.

## Step 2: Reduce sparse, empty, and structural columns

Artifacts:

- `step_2_reduce_sparse_columns.py`
- `BHS_step_2_reduced.csv`
- `EHVol_step_2_reduced.csv`
- `BHS_step_2_reduction_audit.csv`
- `EHVol_step_2_reduction_audit.csv`

### What this step does

Step 2 improves table shape in three ways:

1. Drops structural columns such as `Complete?` that describe form workflow rather than biology or clinical status.
2. Drops columns that are completely empty after step 1.
3. Collapses repeated checkbox groups into a single summary column.

### Results

| Dataset | Meaningless columns dropped | Fully empty columns dropped | Checkbox groups collapsed | Source checkbox columns condensed | Final columns |
| --- | ---: | ---: | ---: | ---: | ---: |
| BHS | 14 | 35 | 18 | 212 | 417 |
| EHVol | 10 | 3 | 1 | 5 | 132 |

### Real examples from the data

#### Structural or empty columns removed

| Dataset | Column | Action | Significance |
| --- | --- | --- | --- |
| EHVol | `Complete?` | dropped as meaningless | A form-completion marker is not an analytical variable. |
| EHVol | `Fat Mass` | dropped as fully empty | A column with no values adds width but no signal. |
| EHVol | `Fat-Free Mass` | dropped as fully empty | Same reason. |
| EHVol | `Number of wives` | dropped as fully empty | No usable data survived into the deidentified output. |
| BHS | `Relative 7 relation` | dropped as fully empty | Prevents sparse tail columns from cluttering the table. |
| BHS | `Relative 7 event` | dropped as fully empty | Same reason. |

#### Checkbox groups collapsed into one field

EHVol family-history example:

- Five source columns describing family conditions were collapsed into one output column:
  `Do any of your own children, parents or siblings have any of the following health conditions - selected_family_history_findings`
- Real values in the collapsed column include:
  - `Diabetes | High Blood Pressure` (204 rows)
  - `High Blood Pressure` (180 rows)
  - `Diabetes` (177 rows)
  - `Heart Disease | Diabetes | High Blood Pressure` (63 rows)

Why this matters:

- Before collapse, the information was spread across multiple sparse yes/no columns.
- After collapse, the same clinical meaning is preserved in one interpretable summary field.

BHS examples:

- `Pericardium - selected_mixed_clinical_findings`
  - `Normal` (3427 rows)
  - `effusion` (6 rows)
  - `Normal | (28) Other diseases of pericardium | (28.1) Pericardial effusion (noninflammatory)` (1 row)
- `Abnormality - selected_ecg_findings`
  - `None` (3053 rows)
  - `T-wave inversion` (260 rows)
  - `T-wave inversion | ST-seg depression` (39 rows)

Why this matters:

- These are clinically rich patterns, but they were originally fragmented across many checkbox columns.
- Collapsing them keeps the content while cutting dimensionality sharply.

### Why this step is significant

This is the step that makes the dataset easier to review, query, and model. It is especially important for BHS, where the table shrinks from 669 columns after deidentification to 417 columns after reduction. That is a large improvement in usability without throwing away clinically meaningful combinations.

## Step 3: Profile normalization strategies safely

Artifacts:

- `step_3_profile_normalization.py`
- `BHS_step_3_normalization_profile.csv`
- `EHVol_step_3_normalization_profile.csv`
- `BHS_step_3_value_examples.csv`
- `EHVol_step_3_value_examples.csv`

### What this step does

Step 3 does not directly normalize the dataset. Instead, it profiles each surviving column and recommends the safest normalization strategy based on observed values.

Examples of proposed strategies include:

- `parse_date_preserve_raw_backup`
- `parse_integer_preserve_raw_backup`
- `parse_decimal_preserve_raw_backup`
- `normalize_boolean_tokens_preserve_raw_backup`
- `review_for_controlled_vocabulary_mapping`
- `preserve_verbatim_pending_manual_review`
- `split_pipe_delimited_multiselect_preserve_raw`

Every profile row is marked `requires_manual_review = yes`, which is important: this step is advisory, not destructive.

### Main strategy patterns observed

| Dataset | Most common proposed strategies |
| --- | --- |
| BHS | controlled vocabulary review (161 columns), decimal parsing (72), boolean normalization (55), integer parsing (49) |
| EHVol | boolean normalization (50 columns), decimal parsing (21), controlled vocabulary review (20), integer parsing (14) |

### Real examples from the data

#### High-confidence numeric or date normalization

| Dataset | Column | Proposed strategy | Evidence from real values | Why this is significant |
| --- | --- | --- | --- | --- |
| EHVol | `Date of Birth` | `parse_date_preserve_raw_backup` | `01/01/1992`, `3/20/2000`, `6/26/1997` | Safe date parsing can standardize format while preserving the original source string. |
| BHS | `Weight in kg` | `parse_decimal_preserve_raw_backup` | `75`, `65`, `80`, `85` | Numeric fields become analysis-ready with low ambiguity. |
| BHS | `Heart rate` | `parse_integer_preserve_raw_backup` | `68`, `70`, `74`, `73` | Good candidate for typed numeric storage. |
| BHS | `Enrollment date` | `parse_date_preserve_raw_backup` | `25/08/2019`, `24/02/2019`, `22/12/2019` | Preserves study chronology in a machine-usable form. |

#### Controlled vocabulary review is needed

| Dataset | Column | Proposed strategy | Evidence from real values | Why this is significant |
| --- | --- | --- | --- | --- |
| BHS | `Gender` | `review_for_controlled_vocabulary_mapping` | `Female` (2183), `Male` (1317) | Small category set, but should still be mapped explicitly, not by assumption. |
| BHS | `What ethnicity do you consider yourself?` | `review_for_controlled_vocabulary_mapping` | `Fedutchi` (2319), `Arab` (1119), `Kenuzi` (60), `other` (2) | The values are compact and analyzable, but need a formal vocabulary table. |

#### Preserve raw text until manual review

| Dataset | Column | Proposed strategy | Evidence from real values | Why this is significant |
| --- | --- | --- | --- | --- |
| EHVol | `Nationality` | `preserve_verbatim_pending_manual_review` | `Egyptian`, `EGY`, `egyptian`, `egy`, `Egyption`, `Egypt` | These all probably refer to the same concept, but automatic collapsing without a curated dictionary could introduce mistakes. |
| BHS | `If mother is Egyptian, please specify city/` | `preserve_verbatim_pending_manual_review` | `Old ballana`, `Old Ballana`, `old ballana`, `Old Qatta, elnuba`, `Esna, Luxor` | The field is important, but spelling, casing, and phrasing vary enough that only a surgical normalization rule is safe. |

#### Step-2 summary columns are recognized explicitly

Collapsed multiselect columns are detected and assigned `split_pipe_delimited_multiselect_preserve_raw`.

That matters because a value such as `Heart Disease | Diabetes | High Blood Pressure` is not a single category. It is a multi-valued list that should eventually be split into structured flags or a related table, while the original summary string is preserved.

### Why this step is significant

This step prevents premature normalization. It separates fields that are safe to type automatically from fields that need a curated dictionary or manual review. That is the right tradeoff for clinical and demographic data, where an aggressive auto-cleaning rule can silently damage meaning.

## Step 4: Apply per-column range rules with outlier quarantine

Artifacts:

- `step_4_apply_range_rules.py`
- `BHS_step_4_range_cleaned.csv`
- `EHVol_step_4_range_cleaned.csv`
- `BHS_step_4_quarantine_audit.csv`
- `EHVol_step_4_quarantine_audit.csv`
- `BHS_step_4_range_rules.csv`
- `EHVol_step_4_range_rules.csv`

### What this step does

Step 4 reads the step-2 reduced dataset and evaluates numeric and date columns against clinically plausible min/max ranges. Values that fall outside the expected range are quarantined (blanked in the cleaned output and logged) rather than silently kept.

Range rules cover:

- Vital signs: heart rate (30-220 bpm), systolic BP (50-280 mmHg), diastolic BP (30-160 mmHg)
- Anthropometry: weight (20-300 kg), height (100-250 cm), BMI (10-80)
- Echocardiography: LVEDD (20-90 mm), LVESD (10-70 mm), EF (10-90%), LVM (30-600 g)
- ECG intervals: PR (80-350 ms), QRS (50-200 ms), QTc (300-600 ms)
- Labs: creatinine (0.2-15 mg/dL), eGFR (5-300), HbA1c (3-20%), troponin (0-50 ng/mL)
- Risk scores: ASCVD risk (0-100%)
- Social/demographic: number of children (0-20), siblings (0-30)
- Smoking: age at start (5-100 years), cigarettes per day (0-200)

### How quarantine works

When a value is out of range or unparseable as numeric:

1. The raw value is preserved in the quarantine audit.
2. The cleaned dataset receives a blank in that cell.
3. The audit records: row number, column, raw value, parsed value, expected range, and reason.

This means downstream analysis can trust that every numeric value in the cleaned file has passed a plausibility gate.

### Why this step is significant

Clinical datasets often contain data-entry errors: a BP of 500, a weight of 5 kg, or a creatinine of 99. Step 4 catches these before they distort statistics or models. The quarantine audit also makes it easy to feed suspect values back to the data-collection team for correction.

## Step 5: Extract unit tokens and suggest canonical forms

Artifacts:

- `step_5_extract_units.py`
- `BHS_step_5_unit_suggestions.csv`
- `EHVol_step_5_unit_suggestions.csv`

### What this step does

Step 5 scans all text values for patterns that look like "number + unit" and suggests a canonical representation. It does NOT modify the raw data; it only produces suggestions.

Supported dimensions and canonical units:

| Dimension | Raw forms detected | Canonical form |
| --- | --- | --- |
| Duration | `10y`, `5 yr`, `3 years` | `10 years` |
| Duration | `6 mo`, `12 months` | `6 months` |
| Weight | `70kg`, `150 lbs` | `70 kg`, `150 lb` |
| Length | `165cm`, `5 ft` | `165 cm`, `5 ft` |
| Pressure | `120 mmhg` | `120 mmHg` |
| Volume | `500ml`, `2 L` | `500 mL`, `2 L` |
| Mass (dose) | `5 mg`, `100 mcg` | `5 mg`, `100 mcg` |
| Proportion | `50%`, `25 percent` | `50 %` |
| Rate | `72 bpm` | `72 bpm` |

### Example of what it catches

A free-text field containing `"Patient has been smoking for 10y and 3mo"` would yield two suggestions:

- `10y` -> `10 years`
- `3mo` -> `3 months`

### Why this step is significant

Many clinical forms allow free-text entry for duration, dose, or size. Without unit extraction, a value like `10y` and `10 years` are treated as different strings. Step 5 makes these explicit so that a later normalization step can collapse them into a single typed numeric + unit representation.

## Step 6: Fuzzy-match geographic and nationality values against canonical dictionaries

Artifacts:

- `step_6_fuzzy_match.py`
- `BHS_step_6_fuzzy_suggestions.csv`
- `EHVol_step_6_fuzzy_suggestions.csv`

### What this step does

Step 6 scans columns that are likely to contain city or country names and compares each unique value against canonical dictionaries:

- **Cities**: loaded from `city_coords.csv` (e.g., `cairo`, `alexandria`, `aswan`, `sohag`)
- **Countries**: a built-in list of ~80 common nationalities (e.g., `egyptian`, `saudi`, `sudanese`)

For each unique value, it reports one of three outcomes:

1. **exact_canonical** — the value already matches a dictionary entry exactly.
2. **fuzzy_suggestion** — the value is similar enough (>= 75% sequence similarity) to a dictionary entry and a mapping is suggested.
3. **no_match** — the value does not resemble any dictionary entry and needs manual review.

### Real examples from the data

| Dataset | Column | Raw value | Suggested canonical | Match type |
| --- | --- | --- | --- | --- |
| EHVol | `Nationality` | `Egyptian` | `egyptian` | exact_canonical |
| EHVol | `Nationality` | `EGY` | `egyptian` | fuzzy_suggestion |
| EHVol | `Nationality` | `egy` | `egyptian` | fuzzy_suggestion |
| EHVol | `Nationality` | `Egyption` | `egyptian` | fuzzy_suggestion |
| BHS | `If mother is Egyptian, please specify city/` | `Old ballana` | (no match — needs manual review) | no_match |
| BHS | `If mother is Egyptian, please specify city/` | `Esna, Luxor` | (no match — needs manual review) | no_match |

### Why this step is significant

Geographic and nationality fields are often the messiest categorical data in multi-site studies. Spelling variations, abbreviations, and typos (`egy` vs `Egyptian`) fragment what should be a single category. Step 6 provides a curated, reviewable mapping table so that normalization can be done surgically rather than by guesswork.

## Recommended next step: Step 7 — Apply approved normalization rules into parallel canonical fields

Steps 3 through 6 are all advisory or quarantine-based. They do not overwrite raw data. Step 7 should be the first step that actually writes normalized outputs.

### What Step 7 should do

Step 7 should read the Step 2 reduced dataset together with the outputs from Steps 3-6, then apply only approved normalization rules.

The key rule is this:

- never overwrite the raw source column
- write normalized values into parallel canonical columns
- log every transformation in an audit file
- quarantine unresolved values instead of forcing them into a guessed category

### What the outputs should look like

Recommended artifacts:

- `step_7_apply_normalization.py`
- `BHS_step_7_normalized.csv`
- `EHVol_step_7_normalized.csv`
- `BHS_step_7_normalization_audit.csv`
- `EHVol_step_7_normalization_audit.csv`
- optional mapping tables such as `BHS_step_7_vocabulary_map.csv` and `EHVol_step_7_vocabulary_map.csv`

The normalized dataset should keep the original columns and add derived canonical fields such as:

- `<column>__normalized`
- `<column>__parsed_date`
- `<column>__numeric`
- `<column>__boolean`
- `<column>__tokens`

### What Step 7 should normalize first

Step 7 should start with high-confidence strategies from Step 3, because those are the least risky.

#### Priority 1: dates

Examples:

- EHVol `Date of Birth`: parse values such as `01/01/1992`, `3/20/2000`, and `6/26/1997` into a canonical ISO date field while retaining the raw source string.
- BHS `Enrollment date`: convert values such as `25/08/2019`, `24/02/2019`, and `22/12/2019` into a parallel parsed date field.

Why first:

- the observed values are strongly date-like
- the step-3 guardrail is already clear
- typed dates immediately improve cohort timing and age-derived analysis

#### Priority 2: numeric fields

Examples:

- BHS `Heart rate`: create a numeric field from values such as `68`, `70`, `74`, `73`
- BHS `Weight in kg`: create a numeric field from values such as `75`, `65`, `80`, `85`
- EHVol lab and vital fields with consistent numeric patterns should follow the same rule

Why second:

- these are usually safe to type
- downstream statistics and QC depend on consistent numeric representation

#### Priority 3: booleans

Examples:

- BHS `Previous Patient at AHC`: normalize `Yes` and `No` into a canonical boolean representation
- EHVol `Is there any chance you might be pregnant?`: normalize `Yes` and `No` into a canonical boolean representation

Why third:

- boolean fields are common and easy to standardize
- explicit true/false coding reduces ambiguity in downstream modeling

#### Priority 4: collapsed multiselect fields

Examples:

- EHVol `Do any of your own children, parents or siblings have any of the following health conditions - selected_family_history_findings`
  should split values such as `Diabetes | High Blood Pressure` into a token list or separate flags while preserving the raw string
- BHS `Abnormality - selected_ecg_findings`
  should split values such as `T-wave inversion | ST-seg depression` into structured findings

Why fourth:

- these columns already contain compact summaries from Step 2
- splitting them produces far more usable analytic features than leaving them as one long string

#### Priority 5: geographic / nationality canonicalization (using Step 6 output)

Use the fuzzy-match suggestions from Step 6 to create an explicit mapping table, then apply it to produce canonical nationality and city columns.

### What Step 7 should not normalize automatically

Some fields should remain verbatim until a curated dictionary exists.

Examples:

- BHS `If mother is Egyptian, please specify city/`: `Old ballana`, `Old Ballana`, `old ballana`, `Old Qatta, elnuba`, `Esna, Luxor`

For these fields, Step 7 should do only controlled cleanup such as:

- trimming whitespace
- storing a lowercased comparison key if needed for review
- routing unmatched variants into a review table

It should not silently merge them into one value unless the mapping has been explicitly approved.

### What the Step 7 audit should record

Each normalization action should have a row in the audit output with fields like:

- dataset
- source_column
- strategy_applied
- raw_value
- normalized_value
- status such as `normalized`, `unchanged`, `unresolved`, or `rejected`
- rule_version or mapping_version

This matters because normalization changes meaning more subtly than deidentification does. The audit has to make each mapping reviewable.

### Why this should be Step 7

Steps 3-6 already answer the questions "what looks safe to normalize?", "what values are out of range?", "what units are hidden in text?", and "what geographic values can be canonicalized?". Step 7 should answer the next one: "apply the safe parts now, and isolate the risky parts for manual review."

That makes Step 7 the bridge from profiling to production-ready analytic data.

## Overall significance of the pipeline

The workflow becomes a controlled progression:

1. Step 0 defines what each field is.
2. Step 1 removes direct identifiers and documents every retention decision.
3. Step 2 removes empty structure and condenses sparse checkbox layouts.
4. Step 3 creates a safe roadmap for future normalization without altering the raw values.
5. Step 4 should apply only approved normalization rules into canonical derived fields with a full audit trail.

The most important outcome is not just cleaner data. It is cleaner data with an audit trail.

- Privacy decisions are explicit.
- Data reduction decisions are explicit.
- Normalization suggestions are explicit.
- Applied normalizations are explicit.

That makes the outputs easier to defend scientifically and easier to review from a governance perspective.