from __future__ import annotations

"""
Step 4: Apply per-column range rules with outlier quarantine.

Reads step-2 reduced datasets, evaluates numeric and date columns against
plausible clinical/study ranges, quarantines out-of-range values to an audit
file, and writes a cleaned dataset with outliers blanked.
"""

import csv
import re
from datetime import datetime
from pathlib import Path

from src.pipeline.step_0_column_mapping import normalize
from src.config import DATASETS, INTERIM_DIR as ROOT, REFERENCE_DIR


STEP_2_SUFFIX = "_step_2_reduced.csv"
STEP_4_SUFFIX = "_step_4_range_cleaned.csv"
STEP_4_QUARANTINE_SUFFIX = "_step_4_quarantine_audit.csv"
STEP_4_RULES_SUFFIX = "_step_4_range_rules.csv"

DATE_FORMATS = (
    "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d", "%d-%m-%Y", "%m-%d-%Y",
    "%d/%m/%y", "%m/%d/%y",
)

INTEGER_PATTERN = re.compile(r"^[+-]?\d+$")
DECIMAL_PATTERN = re.compile(r"^[+-]?\d+(?:\.\d+)?$")


# ---------------------------------------------------------------------------
# Range rule definitions
# Each rule: (header_norm_pattern, rule_type, min, max, description)
# header_norm_pattern is matched with 'in' against normalized header
# rule_type: "numeric", "date", "integer"
# ---------------------------------------------------------------------------

RANGE_RULES: list[tuple[str, str, float | None, float | None, str]] = [
    # --- Demographics / Social ---
    ("number of children", "integer", 0, 20, "plausible number of children"),
    ("how many siblings", "integer", 0, 30, "plausible number of siblings"),
    ("if more than 1 wife", "integer", 1, 10, "plausible number of wives"),

    # --- Vital signs ---
    ("heart rate", "numeric", 30, 220, "resting heart rate (bpm)"),
    ("heart rate during mri", "numeric", 30, 220, "heart rate during MRI (bpm)"),
    ("ventricular rate", "numeric", 30, 220, "ventricular rate (bpm)"),
    ("systolic blood pressure", "numeric", 50, 280, "systolic BP (mmHg)"),
    ("diastolic blood pressure", "numeric", 30, 160, "diastolic BP (mmHg)"),
    ("brachial pressure", "numeric", 50, 280, "brachial pressure (mmHg)"),
    ("bp", "numeric", 50, 280, "blood pressure (mmHg)"),

    # --- Anthropometry ---
    ("weight in kg", "numeric", 20, 300, "weight (kg)"),
    ("weight (kg)", "numeric", 20, 300, "weight (kg)"),
    ("height in cm", "numeric", 100, 250, "height (cm)"),
    ("height (cm)", "numeric", 100, 250, "height (cm)"),
    ("bmi", "numeric", 10, 80, "body mass index"),
    ("bsa", "numeric", 0.5, 3.5, "body surface area (m2)"),
    ("waist circumference", "numeric", 30, 200, "waist circumference (cm)"),
    ("hip circumference", "numeric", 30, 200, "hip circumference (cm)"),
    ("waist : hip ratio", "numeric", 0.3, 2.0, "waist-to-hip ratio"),
    ("span (cm)", "numeric", 100, 250, "arm span (cm)"),
    ("jvp", "numeric", 0, 20, "jugular venous pressure (cmH2O)"),

    # --- Echocardiography ---
    # Note: BHS echo measurements are in mm; EHVol echo measurements are in cm.
    # Ranges are widened to cover both units.
    ("lvedd", "numeric", 2, 90, "LV end-diastolic dimension (mm or cm)"),
    ("lvesd", "numeric", 2, 70, "LV end-systolic dimension (mm or cm)"),
    ("swt", "numeric", 0.3, 25, "septal wall thickness (mm or cm)"),
    ("pwt", "numeric", 0.3, 25, "posterior wall thickness (mm or cm)"),
    ("ivsd", "numeric", 0.3, 3.0, "interventricular septum diastole (cm)"),
    ("ivss", "numeric", 0.5, 4.0, "interventricular septum systole (cm)"),
    ("lvpwd", "numeric", 0.3, 3.0, "LV posterior wall diastole (cm)"),
    ("lvpws", "numeric", 0.5, 4.0, "LV posterior wall systole (cm)"),
    ("lvm", "numeric", 30, 600, "left ventricular mass (g)"),
    ("left ventricular mass", "numeric", 30, 600, "left ventricular mass (g)"),
    ("ef", "numeric", 10, 90, "ejection fraction (%)"),
    ("fs", "numeric", 5, 60, "fractional shortening (%)"),
    ("lvef", "numeric", 10, 90, "LV ejection fraction (%)"),
    ("left ventricular ejection fraction", "numeric", 10, 90, "LV ejection fraction (%)"),
    ("rwma score", "numeric", 0, 20, "regional wall motion abnormality score"),
    ("rwma index", "numeric", 0, 3, "regional wall motion abnormality index"),
    ("la diameter", "numeric", 1, 70, "left atrial diameter (mm or cm)"),
    ("la volume", "numeric", 5, 150, "left atrial volume (mL)"),
    ("rv diameters", "numeric", 1, 70, "right ventricular diameter (mm or cm)"),
    ("tapse", "numeric", 5, 40, "tricuspid annular plane systolic excursion (mm)"),
    ("pasp", "numeric", 5, 120, "pulmonary artery systolic pressure (mmHg)"),
    ("aortic root", "numeric", 1.0, 5.5, "aortic root diameter (cm)"),
    ("aortic annulus", "numeric", 1, 40, "aortic annulus diameter (mm or cm)"),
    ("sinus of valsalva", "numeric", 1, 55, "sinus of Valsalva diameter (mm or cm)"),
    ("sino-tubular junction", "numeric", 1, 50, "sino-tubular junction diameter (mm or cm)"),
    ("tubular ascending aorta", "numeric", 1, 60, "ascending aorta diameter (mm or cm)"),
    ("left atrium", "numeric", 1.0, 7.0, "left atrium diameter (cm)"),
    ("right ventricle", "numeric", 1.0, 6.0, "right ventricle diameter (cm)"),

    # --- ECG intervals ---
    ("pr interval", "numeric", 80, 350, "PR interval (ms)"),
    ("qrs duration", "numeric", 50, 200, "QRS duration (ms)"),
    ("qt interval", "numeric", 200, 600, "QT interval (ms)"),
    ("qtc interval", "numeric", 300, 600, "corrected QT interval (ms)"),
    ("corrected qt interval", "numeric", 300, 600, "corrected QT interval (ms)"),
    ("rate", "numeric", 30, 220, "heart rate (bpm)"),

    # --- ABI / vascular ---
    ("abi", "numeric", 0.3, 2.5, "ankle-brachial index"),
    ("anterior tibial pressure", "numeric", 30, 250, "ankle pressure (mmHg)"),
    ("posterior tibial pressure", "numeric", 30, 250, "ankle pressure (mmHg)"),
    ("imt", "numeric", 0.2, 3.0, "intima-media thickness (mm)"),

    # --- Risk scores ---
    ("ascvd risk", "numeric", 0, 100, "ASCVD risk (%)"),
    ("lifetime ascvd risk", "numeric", 0, 100, "lifetime ASCVD risk (%)"),
    ("current 10-year ascvd risk", "numeric", 0, 100, "10-year ASCVD risk (%)"),
    ("optimal ascvd risk", "numeric", 0, 100, "optimal ASCVD risk (%)"),

    # --- Labs ---
    ("urea", "numeric", 5, 100, "urea (mg/dL)"),
    ("creatinine", "numeric", 0.2, 15, "creatinine (mg/dL)"),
    ("egfr", "numeric", 5, 300, "eGFR (mL/min/1.73m2)"),
    ("na", "numeric", 120, 160, "sodium (mEq/L)"),
    ("k", "numeric", 2.0, 8.0, "potassium (mEq/L)"),
    ("ca", "numeric", 6.0, 14.0, "calcium (mg/dL)"),
    ("mg", "numeric", 0.5, 5.0, "magnesium (mg/dL)"),
    ("alt", "numeric", 5, 500, "alanine aminotransferase (U/L)"),
    ("ast", "numeric", 5, 500, "aspartate aminotransferase (U/L)"),
    ("total bilirubin", "numeric", 0.1, 20, "total bilirubin (mg/dL)"),
    ("direct bilirubin", "numeric", 0.0, 10, "direct bilirubin (mg/dL)"),
    ("albumin", "numeric", 1.0, 6.0, "albumin (g/dL)"),
    ("crp", "numeric", 0.01, 500, "C-reactive protein (mg/L)"),
    ("total cholesterol", "numeric", 50, 600, "total cholesterol (mg/dL)"),
    ("serum triglycerides", "numeric", 20, 2000, "triglycerides (mg/dL)"),
    ("hdl", "numeric", 5, 150, "HDL cholesterol (mg/dL)"),
    ("ldl", "numeric", 5, 400, "LDL cholesterol (mg/dL)"),
    ("vldl", "numeric", 2, 100, "VLDL cholesterol (mg/dL)"),
    ("troponin", "numeric", 0, 50, "troponin (ng/mL)"),
    ("bnp", "numeric", 1, 5000, "BNP (pg/mL)"),
    ("hemoglobin", "numeric", 4, 22, "hemoglobin (g/dL)"),
    ("hematocrit", "numeric", 15, 70, "hematocrit (%)"),
    ("rbcs", "numeric", 2.0, 8.0, "red blood cell count (M/uL)"),
    ("mcv", "numeric", 50, 130, "mean corpuscular volume (fL)"),
    ("mch", "numeric", 15, 45, "mean corpuscular hemoglobin (pg)"),
    ("mchc", "numeric", 25, 45, "mean corpuscular hemoglobin concentration (g/dL)"),
    ("rdw", "numeric", 8, 25, "red cell distribution width (%)"),
    ("platelet count", "numeric", 20, 800, "platelet count (K/uL)"),
    ("tlc", "numeric", 1, 50, "total leukocyte count (K/uL)"),
    ("t3", "numeric", 0.5, 8.0, "triiodothyronine (ng/mL)"),
    ("t4", "numeric", 0.1, 5.0, "thyroxine (ug/dL)"),
    ("tsh", "numeric", 0.01, 100, "thyroid stimulating hormone (uIU/mL)"),
    ("random blood glucose", "numeric", 30, 1200, "random blood glucose (mg/dL)"),
    ("fasting blood glucose", "numeric", 30, 600, "fasting blood glucose (mg/dL)"),
    ("hba1c", "numeric", 3.0, 20.0, "HbA1c (%)"),

    # --- Smoking / Age ---
    ("age at start of smoking", "numeric", 5, 100, "age at smoking initiation (years)"),
    ("age at smoking cessation", "numeric", 5, 100, "age at smoking cessation (years)"),
    ("smoking years", "numeric", 0, 80, "duration of smoking (years)"),
    ("shisha: how many sessions", "numeric", 0, 50, "shisha sessions per day"),
    ("shisha: how many minutes", "numeric", 1, 300, "shisha minutes per session"),
    ("average no. of cigarettes", "numeric", 0, 200, "cigarettes per day"),
    ("how many cigarettes", "numeric", 0, 200, "cigarettes per day"),
    ("how long have you been smoking", "numeric", 0, 80, "smoking duration (years)"),
    ("how many years have you been smoking", "numeric", 0, 80, "smoking duration (years)"),

    # --- Relative ages ---
    ("relative 1 age at event", "numeric", 0, 120, "relative age at event (years)"),
    ("relative 2 age at event", "numeric", 0, 120, "relative age at event (years)"),
    ("relative 3 age at event", "numeric", 0, 120, "relative age at event (years)"),
    ("relative 4 age at event", "numeric", 0, 120, "relative age at event (years)"),
    ("relative 5 age at event", "numeric", 0, 120, "relative age at event (years)"),
    ("relative 6 age at event", "numeric", 0, 120, "relative age at event (years)"),

    # --- Medication dosing ---
    ("total daily dose", "numeric", 0.01, 5000, "total daily medication dose"),
    ("frequency", "numeric", 0.01, 24, "dosing frequency (times per day)"),
]


def step_2_input_path(dataset: str) -> Path:
    return ROOT / f"{dataset}{STEP_2_SUFFIX}"


def step_4_output_path(dataset: str) -> Path:
    return ROOT / f"{dataset}{STEP_4_SUFFIX}"


def step_4_quarantine_path(dataset: str) -> Path:
    return ROOT / f"{dataset}{STEP_4_QUARANTINE_SUFFIX}"


def step_4_rules_path(dataset: str) -> Path:
    return ROOT / f"{dataset}{STEP_4_RULES_SUFFIX}"


def ensure_step_2_artifacts() -> None:
    missing = [dataset for dataset in DATASETS if not step_2_input_path(dataset).exists()]
    if not missing:
        return
    from src.pipeline.step_2_reduce_sparse_columns import main as step_2_main
    print("Missing step-2 artifacts detected; running step_2_reduce_sparse_columns.py first")
    step_2_main()


def read_step_2_dataset(dataset: str) -> tuple[list[str], list[list[str]]]:
    with step_2_input_path(dataset).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        rows = list(reader)
    if not rows:
        raise ValueError(f"{step_2_input_path(dataset).name} is empty")
    return rows[0], rows[1:]


def try_parse_number(value: str) -> float | None:
    """Try to parse a strict numeric value."""
    stripped = value.strip()
    if not stripped:
        return None
    # Reject things like "01-Feb" or "60/50" that are not simple numbers
    if not DECIMAL_PATTERN.match(stripped):
        return None
    try:
        return float(stripped)
    except ValueError:
        return None


def find_applicable_rules(header: str) -> list[tuple[str, str, float | None, float | None, str]]:
    """Return all range rules whose pattern matches a whole word in the normalized header.

    Tokenizes the header by spaces, hyphens, and parentheses to avoid
    false positives (e.g. 'abi' matching 'date (abi)' or 'k' matching 'smoking').
    Also skips columns that contain obvious non-numeric context words.
    """
    hnorm = normalize(header)
    # Skip columns that are clearly non-numeric
    skip_context = {"date", "name", "category", "class", "chart", "status", "health today",
                    "consent", "accept", "inform", "operation", "surgical", "malignancy",
                    "kidney problems", "muscloskeletal", "heart attack", "angina"}
    if any(ctx in hnorm for ctx in skip_context):
        return []

    # Extract alphanumeric tokens (also split on hyphens and parentheses)
    tokens = set(re.findall(r"[a-z0-9]+", hnorm))
    matches = []
    for pattern, rule_type, min_val, max_val, description in RANGE_RULES:
        if pattern in tokens:
            matches.append((pattern, rule_type, min_val, max_val, description))
    return matches


def apply_range_rules(
    dataset: str,
    headers: list[str],
    data_rows: list[list[str]],
) -> tuple[list[list[str]], list[dict[str, str]], list[dict[str, str]]]:
    """
    Returns (cleaned_rows, quarantine_records, active_rules).
    cleaned_rows has outliers blanked.
    """
    cleaned_rows: list[list[str]] = []
    quarantine: list[dict[str, str]] = []
    active_rules: list[dict[str, str]] = []

    # Determine which columns have rules
    column_rules: list[list[tuple[str, str, float | None, float | None, str]]] = []
    for header in headers:
        rules = find_applicable_rules(header)
        column_rules.append(rules)
        for pattern, rule_type, min_val, max_val, description in rules:
            active_rules.append({
                "dataset": dataset,
                "column_name": header,
                "matched_pattern": pattern,
                "rule_type": rule_type,
                "min_value": str(min_val) if min_val is not None else "",
                "max_value": str(max_val) if max_val is not None else "",
                "description": description,
            })

    for row_idx, row in enumerate(data_rows, start=2):
        cleaned_row = list(row)
        for col_idx, header in enumerate(headers):
            rules = column_rules[col_idx]
            if not rules:
                continue

            raw_value = row[col_idx] if col_idx < len(row) else ""
            if not raw_value.strip():
                continue

            # Use the first matching rule (most specific patterns are listed first)
            _, rule_type, min_val, max_val, description = rules[0]

            if rule_type in ("numeric", "integer"):
                parsed = try_parse_number(raw_value)
                if parsed is None:
                    # Non-numeric in a numeric column -> quarantine as unparseable
                    quarantine.append({
                        "dataset": dataset,
                        "row_number": str(row_idx),
                        "column_name": header,
                        "raw_value": raw_value,
                        "parsed_value": "",
                        "rule_type": rule_type,
                        "min_value": str(min_val) if min_val is not None else "",
                        "max_value": str(max_val) if max_val is not None else "",
                        "quarantine_reason": "unparseable_numeric",
                        "details": f"Expected numeric for '{description}' but got non-numeric value",
                    })
                    cleaned_row[col_idx] = ""
                    continue

                out_of_range = False
                if min_val is not None and parsed < min_val:
                    out_of_range = True
                if max_val is not None and parsed > max_val:
                    out_of_range = True

                if out_of_range:
                    quarantine.append({
                        "dataset": dataset,
                        "row_number": str(row_idx),
                        "column_name": header,
                        "raw_value": raw_value,
                        "parsed_value": str(parsed),
                        "rule_type": rule_type,
                        "min_value": str(min_val) if min_val is not None else "",
                        "max_value": str(max_val) if max_val is not None else "",
                        "quarantine_reason": "out_of_range",
                        "details": f"Value {parsed} outside range [{min_val}, {max_val}] for '{description}'",
                    })
                    cleaned_row[col_idx] = ""

        cleaned_rows.append(cleaned_row)

    return cleaned_rows, quarantine, active_rules


def write_cleaned_dataset(dataset: str, headers: list[str], rows: list[list[str]]) -> None:
    with step_4_output_path(dataset).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerows(rows)


def write_quarantine_audit(dataset: str, records: list[dict[str, str]]) -> None:
    with step_4_quarantine_path(dataset).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "dataset",
                "row_number",
                "column_name",
                "raw_value",
                "parsed_value",
                "rule_type",
                "min_value",
                "max_value",
                "quarantine_reason",
                "details",
            ],
        )
        writer.writeheader()
        writer.writerows(records)


def write_rules_manifest(dataset: str, rules: list[dict[str, str]]) -> None:
    with step_4_rules_path(dataset).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "dataset",
                "column_name",
                "matched_pattern",
                "rule_type",
                "min_value",
                "max_value",
                "description",
            ],
        )
        writer.writeheader()
        writer.writerows(rules)


def process_dataset(dataset: str) -> None:
    headers, data_rows = read_step_2_dataset(dataset)
    cleaned_rows, quarantine, active_rules = apply_range_rules(dataset, headers, data_rows)

    write_cleaned_dataset(dataset, headers, cleaned_rows)
    write_quarantine_audit(dataset, quarantine)
    write_rules_manifest(dataset, active_rules)

    print(
        f"{dataset}: checked {len(data_rows)} rows against {len(active_rules)} range rules, "
        f"quarantined {len(quarantine)} values"
    )
    print(f"  cleaned output: {step_4_output_path(dataset).name}")
    print(f"  quarantine audit: {step_4_quarantine_path(dataset).name}")
    print(f"  rules manifest: {step_4_rules_path(dataset).name}")


def main() -> None:
    ensure_step_2_artifacts()
    for dataset in DATASETS:
        process_dataset(dataset)


if __name__ == "__main__":
    main()
