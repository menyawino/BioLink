from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

from src.pipeline.step_0_column_mapping import normalize
from src.config import DATASETS, INTERIM_DIR as ROOT, REFERENCE_DIR


STEP_1_SUFFIX = "_step_1_deidentified.csv"
STEP_1_AUDIT_SUFFIX = "_step_1_retention_audit.csv"
STEP_2_SUFFIX = "_step_2_reduced.csv"
STEP_2_AUDIT_SUFFIX = "_step_2_reduction_audit.csv"
STEP_2_VALIDATION_SUFFIX = "_step_2_validation_audit.csv"

POSITIVE_CHECKBOX_VALUES = {"checked", "yes", "true", "1", "present", "positive"}
NEGATIVE_CHECKBOX_VALUES = {"unchecked", "no", "false", "0", "none", "nan", "na", "n a"}
MEANINGLESS_HEADER_NORMALIZATIONS = {"complete"}

CATEGORY_SUFFIXES = {
    "Family History & Lineage": "selected_family_history_findings",
    "Diagnoses & Medical History": "selected_diagnosis_findings",
    "Questionnaires & Reported Symptoms": "selected_reported_findings",
    "ECG & Rhythm": "selected_ecg_findings",
    "Echocardiography & Vascular Imaging": "selected_echo_findings",
    "MRI / CT & Advanced Imaging": "selected_imaging_findings",
    "Laboratory Tests & Biomarkers": "selected_lab_findings",
    "Procedures & Interventions": "selected_procedure_findings",
}

# ---------------------------------------------------------------------------
# Intra-database validation rule definitions
# ---------------------------------------------------------------------------

# Date columns that should not be in the future (relative to data collection)
DATE_COLUMNS_NO_FUTURE = {
    "enrollment date", "date of enrolment", "date of birth",
    "date (family history)", "date (risk factors)", "date (clinical exam)",
    "date (echocardiography)", "date (medications)", "date (labs)",
    "examination date", "echo date", "ecg date", "mri date",
    "date of cardiac ct", "date of cardiac mri", "date of cardotid duplex",
}

# Date columns that should also fall within the study enrollment range
# (excludes birth dates which naturally predate the study)
DATE_COLUMNS_STUDY_RANGE = {
    "enrollment date", "date of enrolment",
    "date (family history)", "date (risk factors)", "date (clinical exam)",
    "date (echocardiography)", "date (medications)", "date (labs)",
    "examination date", "echo date", "ecg date", "mri date",
    "date of cardiac ct", "date of cardiac mri", "date of cardotid duplex",
}

# Enrollment should not be before birth
ENROLLMENT_DATE_HEADERS = {"enrollment date", "date of enrolment"}
BIRTH_DATE_HEADERS = {"date of birth"}

# Conditional field rules: (parent_header_norm, parent_expected_value, child_header_norm_pattern)
# parent_expected_value: "any" means parent must be non-empty and not a negative value
CONDITIONAL_RULES = [
    # BHS: If mother is non-Egyptian -> specify should only be filled if Mother origins = Non-Egyptian
    ("mother origins", "non-egyptian", "if mother is non-egyptian"),
    # BHS: If mother is Egyptian -> city should only be filled if Mother origins = Egyptian
    ("mother origins", "egyptian", "if mother is egyptian"),
    # BHS: If father is non-Egyptian -> specify should only be filled if Father origins = Non-Egyptian
    ("father origins", "non-egyptian", "if father is non-egyptian"),
    # BHS: If father is Egyptian -> city should only be filled if Father origins = Egyptian
    ("father origins", "egyptian", "if father is egyptian"),
    # BHS: More than 1 wife -> how many should only be filled if marital status suggests multiple wives
    ("what is your marital status", "married", "if more than 1 wife"),
    # EHVol: Non-Egyptian Parents -> From where should be filled
    ("non-egyptian parents", "yes", "from where"),
    # EHVol: Current/Recent Smoker -> smoking details should be filled
    ("current/recent smoker", "yes", "how long have you been smoking"),
    ("current/recent smoker", "yes", "how many cigarettes have you been smoking"),
    # EHVol: Do you drink alcohol -> Amount should be filled
    ("do you drink alcohol", "yes", "amount of alcohol"),
    # EHVol: Do you take any medication -> List should be filled
    ("do you take any medication currently", "yes", "list these medications"),
    # EHVol: Consanguinous Marriage -> Number of children context (weaker rule, just check)
    ("consanguinous marriage", "yes", "who and what disease"),
    # BHS: Hypertension -> age of onset
    ("do you have hypertension", "yes", "if yes, please specify age of onset"),
    # BHS: Diabetes -> type and age
    ("do you have diabetes", "yes", "if yes, please specify type"),
    ("do you have diabetes", "yes", "and specify age of onset"),
    # BHS: Renal disease -> details
    ("have you been diagnosed with renal disease", "yes", "if yes, please specify age of onset"),
    # BHS: Respiratory -> details
    ("have you been diagnosed with respiratory illnesses", "yes", "if yes, please specify type and age of onset"),
]

# Biological contradiction rules
# (field_a_header_norm, field_a_value, field_b_header_norm_pattern, field_b_value, description)
BIOLOGICAL_CONTRADICTIONS = [
    # Male cannot be pregnant
    ("gender", "male", "is there any chance you might be pregnant", "yes", "male participant marked as possibly pregnant"),
    # Non-smoker should not have smoking details
    ("what is your current smoking status", "non-smoker", "shisha: how many sessions", "any", "non-smoker has shisha session details"),
    ("what is your current smoking status", "non-smoker", "average no. of cigarettes", "any", "non-smoker has cigarette count"),
    ("what is your current smoking status", "non-smoker", "smoking years", "any", "non-smoker has smoking years"),
    # Non-drinker should not have alcohol amount
    ("do you consume alcohol", "no", "amount of alcohol", "any", "non-drinker has alcohol amount"),
    # No medication should not have medication list
    ("do you take any medication currently", "no", "list these medications", "any", "no medication but list is filled"),
    # No family history condition should not have details
    ("does any other non-cardiac condition run in your family", "no", "what is this(these) condition(s)", "any", "no family condition but details provided"),
]

# Age bounds for plausibility
MIN_PLAUSIBLE_AGE = 0
MAX_PLAUSIBLE_AGE = 120

# Study context: BHS enrollment ~2018-2020, EHVol ~2015-2016
# For EHVol, we know 2025 dates exist and are likely typos for 2015
STUDY_DATE_RANGES = {
    "BHS": (datetime(2017, 1, 1), datetime(2024, 12, 31)),
    "EHVol": (datetime(2014, 1, 1), datetime(2018, 12, 31)),
}


def step_1_input_path(dataset: str) -> Path:
    return ROOT / f"{dataset}{STEP_1_SUFFIX}"


def step_1_audit_path(dataset: str) -> Path:
    return ROOT / f"{dataset}{STEP_1_AUDIT_SUFFIX}"


def step_2_output_path(dataset: str) -> Path:
    return ROOT / f"{dataset}{STEP_2_SUFFIX}"


def step_2_audit_path(dataset: str) -> Path:
    return ROOT / f"{dataset}{STEP_2_AUDIT_SUFFIX}"


def step_2_validation_path(dataset: str) -> Path:
    return ROOT / f"{dataset}{STEP_2_VALIDATION_SUFFIX}"


def ensure_step_1_artifacts() -> None:
    missing = []
    for dataset in DATASETS:
        if not step_1_input_path(dataset).exists() or not step_1_audit_path(dataset).exists():
            missing.append(dataset)

    if not missing:
        return

    from src.pipeline.step_1_remove_pii import main as step_1_main

    print("Missing step-1 artifacts detected; running step_1_remove_pii.py first")
    step_1_main()


def read_step_1_dataset(dataset: str) -> tuple[list[str], list[list[str]], list[dict[str, str]]]:
    with step_1_input_path(dataset).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        rows = list(reader)

    if not rows:
        raise ValueError(f"{step_1_input_path(dataset).name} is empty")

    headers = rows[0]
    data_rows = rows[1:]

    with step_1_audit_path(dataset).open("r", encoding="utf-8", newline="") as handle:
        audit_rows = [row for row in csv.DictReader(handle) if row["retention_action"] == "keep"]

    if len(headers) != len(audit_rows):
        raise ValueError(
            f"Header count {len(headers)} does not match kept audit rows {len(audit_rows)} for {dataset}"
        )

    for header, audit_row in zip(headers, audit_rows):
        if header != audit_row["column_name"]:
            raise ValueError(
                f"Header mismatch for {dataset}: expected {audit_row['column_name']!r}, found {header!r}"
            )

    return headers, data_rows, audit_rows


def parse_choice_header(header: str) -> tuple[str, str] | None:
    if "(choice=" not in header:
        return None

    stem, choice_fragment = header.split("(choice=", 1)
    choice = choice_fragment.rsplit(")", 1)[0]
    return stem.strip(), choice.strip()


def column_values(data_rows: list[list[str]], column_index: int) -> list[str]:
    return [row[column_index] if column_index < len(row) else "" for row in data_rows]


def is_fully_empty(values: list[str]) -> bool:
    return all(not value.strip() for value in values)


def group_summary_type(group_audit_rows: list[dict[str, str]]) -> tuple[str, str]:
    broad_categories = [row["broad_category"] for row in group_audit_rows]
    broad_category_counts = Counter(broad_categories)
    dominant_broad_category, _ = broad_category_counts.most_common(1)[0]

    if len(broad_category_counts) == 1:
        return dominant_broad_category, CATEGORY_SUFFIXES.get(
            dominant_broad_category, "selected_findings"
        )

    return "Mixed Clinical Profiles", "selected_mixed_clinical_findings"


def collapse_checkbox_group(
    group_items: list[dict[str, str | int]],
    data_rows: list[list[str]],
) -> list[str]:
    collapsed_values: list[str] = []

    for row in data_rows:
        selected_choices: list[str] = []
        seen_choices: set[str] = set()

        for item in group_items:
            column_index = int(item["column_index"])
            choice = str(item["choice"])
            raw_value = row[column_index].strip() if column_index < len(row) else ""
            if not raw_value:
                continue

            normalized_value = normalize(raw_value)
            if normalized_value in NEGATIVE_CHECKBOX_VALUES:
                continue

            if normalized_value in POSITIVE_CHECKBOX_VALUES:
                rendered_choice = choice
            else:
                rendered_choice = f"{choice}={raw_value}"

            if rendered_choice not in seen_choices:
                selected_choices.append(rendered_choice)
                seen_choices.add(rendered_choice)

        collapsed_values.append(" | ".join(selected_choices))

    return collapsed_values


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

DATE_FORMATS = (
    "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d", "%d-%m-%Y", "%m-%d-%Y",
    "%d/%m/%y", "%m/%d/%y",
)


def try_parse_date(value: str) -> datetime | None:
    stripped = value.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(stripped, fmt)
        except ValueError:
            continue
    return None


def find_header_index(headers: list[str], pattern: str) -> int | None:
    """Find first header whose normalized form contains the pattern."""
    norm_pattern = normalize(pattern)
    for i, h in enumerate(headers):
        if norm_pattern in normalize(h):
            return i
    return None


def find_header_index_exact(headers: list[str], pattern: str) -> int | None:
    """Find first header whose normalized form exactly matches or starts with the pattern."""
    norm_pattern = normalize(pattern)
    for i, h in enumerate(headers):
        nh = normalize(h)
        if nh == norm_pattern or nh.startswith(norm_pattern + " "):
            return i
    return None


def get_value(row: list[str], idx: int | None) -> str:
    if idx is None:
        return ""
    return row[idx] if idx < len(row) else ""


def is_negative_value(value: str) -> bool:
    return normalize(value) in NEGATIVE_CHECKBOX_VALUES or not value.strip()


def is_positive_value(value: str) -> bool:
    return normalize(value) in POSITIVE_CHECKBOX_VALUES


# ---------------------------------------------------------------------------
# Validation checks
# ---------------------------------------------------------------------------

def check_unrealistic_dates(
    dataset: str,
    headers: list[str],
    data_rows: list[list[str]],
) -> list[dict[str, str]]:
    """Flag dates that are outside plausible study ranges or in the future."""
    findings: list[dict[str, str]] = []
    study_min, study_max = STUDY_DATE_RANGES.get(dataset, (datetime(2000, 1, 1), datetime(2030, 12, 31)))

    for col_idx, header in enumerate(headers):
        hnorm = normalize(header)
        check_future = any(d in hnorm for d in DATE_COLUMNS_NO_FUTURE)
        check_study_range = any(d in hnorm for d in DATE_COLUMNS_STUDY_RANGE)

        if not check_future and not check_study_range:
            continue

        for row_idx, row in enumerate(data_rows, start=2):
            raw = get_value(row, col_idx)
            if not raw.strip():
                continue

            parsed = try_parse_date(raw)
            if parsed is None:
                findings.append({
                    "dataset": dataset,
                    "row_number": str(row_idx),
                    "check_type": "unparseable_date",
                    "column_name": header,
                    "value": raw,
                    "details": f"Could not parse date using known formats",
                })
                continue

            # Check future dates
            if check_future and parsed > datetime.now() + timedelta(days=365):
                findings.append({
                    "dataset": dataset,
                    "row_number": str(row_idx),
                    "check_type": "future_date",
                    "column_name": header,
                    "value": raw,
                    "details": f"Date {parsed.date()} is more than 1 year in the future",
                })

            # Check study range (only for non-birth-date columns)
            if check_study_range and (parsed < study_min or parsed > study_max):
                findings.append({
                    "dataset": dataset,
                    "row_number": str(row_idx),
                    "check_type": "date_outside_study_range",
                    "column_name": header,
                    "value": raw,
                    "details": f"Date {parsed.date()} outside expected study range {study_min.date()} to {study_max.date()}",
                })

    return findings


def check_temporal_consistency(
    dataset: str,
    headers: list[str],
    data_rows: list[list[str]],
) -> list[dict[str, str]]:
    """Flag rows where enrollment date is before birth date."""
    findings: list[dict[str, str]] = []

    birth_idx = None
    enroll_idx = None
    for i, h in enumerate(headers):
        nh = normalize(h)
        if nh in BIRTH_DATE_HEADERS:
            birth_idx = i
        if nh in ENROLLMENT_DATE_HEADERS:
            enroll_idx = i

    if birth_idx is None or enroll_idx is None:
        return findings

    for row_idx, row in enumerate(data_rows, start=2):
        birth_raw = get_value(row, birth_idx)
        enroll_raw = get_value(row, enroll_idx)
        if not birth_raw.strip() or not enroll_raw.strip():
            continue

        birth_dt = try_parse_date(birth_raw)
        enroll_dt = try_parse_date(enroll_raw)
        if birth_dt is None or enroll_dt is None:
            continue

        if enroll_dt < birth_dt:
            findings.append({
                "dataset": dataset,
                "row_number": str(row_idx),
                "check_type": "enrollment_before_birth",
                "column_name": f"{headers[enroll_idx]} vs {headers[birth_idx]}",
                "value": f"enroll={enroll_raw}, birth={birth_raw}",
                "details": f"Enrollment date {enroll_dt.date()} is before birth date {birth_dt.date()}",
            })
            continue

        age_at_enrollment = (enroll_dt - birth_dt).days / 365.25
        if age_at_enrollment > MAX_PLAUSIBLE_AGE:
            findings.append({
                "dataset": dataset,
                "row_number": str(row_idx),
                "check_type": "impossible_age_at_enrollment",
                "column_name": f"{headers[enroll_idx]} vs {headers[birth_idx]}",
                "value": f"enroll={enroll_raw}, birth={birth_raw}",
                "details": f"Age at enrollment would be {age_at_enrollment:.1f} years (max {MAX_PLAUSIBLE_AGE})",
            })
        elif age_at_enrollment < MIN_PLAUSIBLE_AGE:
            findings.append({
                "dataset": dataset,
                "row_number": str(row_idx),
                "check_type": "negative_age_at_enrollment",
                "column_name": f"{headers[enroll_idx]} vs {headers[birth_idx]}",
                "value": f"enroll={enroll_raw}, birth={birth_raw}",
                "details": f"Age at enrollment would be {age_at_enrollment:.1f} years",
            })

    return findings


def check_conditional_orphans(
    dataset: str,
    headers: list[str],
    data_rows: list[list[str]],
) -> list[dict[str, str]]:
    """Flag rows where conditional fields are filled but their parent condition is not met."""
    findings: list[dict[str, str]] = []

    # Build index of applicable rules for this dataset
    applicable_rules = []
    for parent_norm, parent_expected, child_pattern in CONDITIONAL_RULES:
        parent_idx = find_header_index_exact(headers, parent_norm)
        if parent_idx is None:
            parent_idx = find_header_index(headers, parent_norm)
        child_idx = find_header_index(headers, child_pattern)
        if parent_idx is not None and child_idx is not None:
            applicable_rules.append((parent_idx, parent_expected, child_idx, child_pattern))

    for row_idx, row in enumerate(data_rows, start=2):
        for parent_idx, parent_expected, child_idx, child_pattern in applicable_rules:
            parent_val = get_value(row, parent_idx)
            child_val = get_value(row, child_idx)

            if not child_val.strip():
                continue  # Child is empty, no orphan

            parent_norm = normalize(parent_val)
            child_norm = normalize(child_val)

            # Check if parent condition is met
            condition_met = False
            if parent_expected == "any":
                condition_met = parent_val.strip() and not is_negative_value(parent_val)
            elif parent_expected == "yes":
                condition_met = is_positive_value(parent_val)
            elif parent_expected == "no":
                condition_met = is_negative_value(parent_val)
            else:
                condition_met = parent_expected in parent_norm

            if not condition_met:
                findings.append({
                    "dataset": dataset,
                    "row_number": str(row_idx),
                    "check_type": "conditional_orphan",
                    "column_name": headers[child_idx],
                    "value": child_val,
                    "details": f"Parent '{headers[parent_idx]}' = '{parent_val}' (expected '{parent_expected}') but child is filled",
                })

    return findings


def check_biological_contradictions(
    dataset: str,
    headers: list[str],
    data_rows: list[list[str]],
) -> list[dict[str, str]]:
    """Flag biologically impossible combinations."""
    findings: list[dict[str, str]] = []

    # Build index of applicable rules
    applicable_rules = []
    for field_a_norm, field_a_val, field_b_pattern, field_b_val, description in BIOLOGICAL_CONTRADICTIONS:
        a_idx = find_header_index_exact(headers, field_a_norm)
        if a_idx is None:
            a_idx = find_header_index(headers, field_a_norm)
        b_idx = find_header_index(headers, field_b_pattern)
        if a_idx is not None and b_idx is not None:
            applicable_rules.append((a_idx, field_a_val, b_idx, field_b_val, description))

    for row_idx, row in enumerate(data_rows, start=2):
        for a_idx, a_expected, b_idx, b_expected, description in applicable_rules:
            a_val = get_value(row, a_idx)
            b_val = get_value(row, b_idx)

            if not b_val.strip():
                continue

            a_norm = normalize(a_val)
            b_norm = normalize(b_val)

            # Check if field A matches the triggering condition
            a_matches = False
            if a_expected == "any":
                a_matches = a_val.strip() and not is_negative_value(a_val)
            else:
                a_matches = a_expected in a_norm

            if not a_matches:
                continue

            # Check if field B contradicts
            b_contradicts = False
            if b_expected == "any":
                b_contradicts = b_val.strip() and not is_negative_value(b_val)
            elif b_expected == "yes":
                b_contradicts = is_positive_value(b_val)
            elif b_expected == "no":
                b_contradicts = is_negative_value(b_val)

            if b_contradicts:
                findings.append({
                    "dataset": dataset,
                    "row_number": str(row_idx),
                    "check_type": "biological_contradiction",
                    "column_name": f"{headers[a_idx]} vs {headers[b_idx]}",
                    "value": f"{headers[a_idx]}='{a_val}', {headers[b_idx]}='{b_val}'",
                    "details": description,
                })

    return findings


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def write_validation_audit(dataset: str, findings: list[dict[str, str]]) -> None:
    with step_2_validation_path(dataset).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "dataset",
                "row_number",
                "check_type",
                "column_name",
                "value",
                "details",
            ],
        )
        writer.writeheader()
        writer.writerows(findings)


# ---------------------------------------------------------------------------
# Main reduction logic (enhanced)
# ---------------------------------------------------------------------------

def write_reduced_dataset(dataset: str, headers: list[str], output_columns: list[list[str]]) -> None:
    with step_2_output_path(dataset).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        row_count = len(output_columns[0]) if output_columns else 0
        for row_index in range(row_count):
            writer.writerow([column[row_index] for column in output_columns])


def write_reduction_audit(dataset: str, audit_rows: list[dict[str, str]]) -> None:
    with step_2_audit_path(dataset).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "dataset",
                "action",
                "source_column_count",
                "source_columns",
                "output_column",
                "summary_type",
                "details",
            ],
        )
        writer.writeheader()
        writer.writerows(audit_rows)


def reduce_dataset(dataset: str) -> None:
    headers, data_rows, audit_rows = read_step_1_dataset(dataset)

    meaningless_indices = {
        column_index
        for column_index, header in enumerate(headers)
        if normalize(header) in MEANINGLESS_HEADER_NORMALIZATIONS
    }

    fully_empty_indices = {
        column_index
        for column_index in range(len(headers))
        if column_index not in meaningless_indices and is_fully_empty(column_values(data_rows, column_index))
    }

    choice_groups: dict[str, list[dict[str, str | int]]] = defaultdict(list)
    group_first_indices: dict[str, int] = {}
    for column_index, (header, audit_row) in enumerate(zip(headers, audit_rows)):
        if column_index in fully_empty_indices:
            continue

        parsed_choice = parse_choice_header(header)
        if not parsed_choice:
            continue

        stem, choice = parsed_choice
        group_first_indices.setdefault(stem, column_index)
        choice_groups[stem].append(
            {
                "column_index": column_index,
                "header": header,
                "choice": choice,
                "broad_category": audit_row["broad_category"],
            }
        )

    collapsible_groups = {
        stem: items
        for stem, items in choice_groups.items()
        if len(items) >= 2
    }

    reduced_headers: list[str] = []
    reduced_columns: list[list[str]] = []
    reduction_audit_rows: list[dict[str, str]] = []
    processed_group_stems: set[str] = set()
    collapsed_group_count = 0
    collapsed_source_columns = 0

    for column_index, (header, audit_row) in enumerate(zip(headers, audit_rows)):
        if column_index in meaningless_indices:
            reduction_audit_rows.append(
                {
                    "dataset": dataset,
                    "action": "drop_meaningless_column",
                    "source_column_count": "1",
                    "source_columns": header,
                    "output_column": "",
                    "summary_type": audit_row["broad_category"],
                    "details": "removed structural completion column with no analytical meaning",
                }
            )
            continue

        if column_index in fully_empty_indices:
            reduction_audit_rows.append(
                {
                    "dataset": dataset,
                    "action": "drop_fully_empty_column",
                    "source_column_count": "1",
                    "source_columns": header,
                    "output_column": "",
                    "summary_type": audit_row["broad_category"],
                    "details": "column was 100% empty after step 1",
                }
            )
            continue

        parsed_choice = parse_choice_header(header)
        if parsed_choice:
            stem, _ = parsed_choice
            if stem in collapsible_groups:
                if stem in processed_group_stems:
                    continue

                group_items = collapsible_groups[stem]
                group_audit_rows = [audit_rows[int(item["column_index"])] for item in group_items]
                dominant_type, suffix = group_summary_type(group_audit_rows)
                output_header = f"{stem} - {suffix}"
                collapsed_values = collapse_checkbox_group(group_items, data_rows)

                if not is_fully_empty(collapsed_values):
                    reduced_headers.append(output_header)
                    reduced_columns.append(collapsed_values)
                    reduction_audit_rows.append(
                        {
                            "dataset": dataset,
                            "action": "collapse_checkbox_group",
                            "source_column_count": str(len(group_items)),
                            "source_columns": " | ".join(str(item["header"]) for item in group_items),
                            "output_column": output_header,
                            "summary_type": dominant_type,
                            "details": "concatenated checked or populated checkbox choices into one typed summary column",
                        }
                    )
                    collapsed_group_count += 1
                    collapsed_source_columns += len(group_items)
                else:
                    reduction_audit_rows.append(
                        {
                            "dataset": dataset,
                            "action": "drop_empty_checkbox_group",
                            "source_column_count": str(len(group_items)),
                            "source_columns": " | ".join(str(item["header"]) for item in group_items),
                            "output_column": "",
                            "summary_type": dominant_type,
                            "details": "all checkbox values resolved to blank after removing unchecked defaults",
                        }
                    )

                processed_group_stems.add(stem)
                continue

        reduced_headers.append(header)
        reduced_columns.append(column_values(data_rows, column_index))

    write_reduced_dataset(dataset, reduced_headers, reduced_columns)
    write_reduction_audit(dataset, reduction_audit_rows)

    # Run intra-database validation checks
    validation_findings: list[dict[str, str]] = []
    validation_findings.extend(check_unrealistic_dates(dataset, headers, data_rows))
    validation_findings.extend(check_temporal_consistency(dataset, headers, data_rows))
    validation_findings.extend(check_conditional_orphans(dataset, headers, data_rows))
    validation_findings.extend(check_biological_contradictions(dataset, headers, data_rows))
    write_validation_audit(dataset, validation_findings)

    print(
        f"{dataset}: started with {len(headers)} columns, removed {len(meaningless_indices)} meaningless columns, removed {len(fully_empty_indices)} fully empty columns, "
        f"collapsed {collapsed_group_count} checkbox groups ({collapsed_source_columns} source columns), "
        f"finished with {len(reduced_headers)} columns"
    )
    print(f"  reduced output: {step_2_output_path(dataset).name}")
    print(f"  reduction audit: {step_2_audit_path(dataset).name}")
    print(f"  validation audit: {step_2_validation_path(dataset).name} ({len(validation_findings)} findings)")


def main() -> None:
    ensure_step_1_artifacts()
    for dataset in DATASETS:
        reduce_dataset(dataset)


if __name__ == "__main__":
    main()