"""
Step 5: Unit-extraction pass that parses numeric + unit tokens
and suggests canonical forms (e.g., 10y -> 10 years).

Reads step-2 reduced datasets, scans all text values for patterns that look
like "number + unit", records suggestions, and writes an audit file.
It does NOT modify the raw data.
"""

import csv
import re
from collections import Counter, defaultdict
from pathlib import Path

from src.pipeline.step_0_column_mapping import normalize
from src.config import DATASETS, INTERIM_DIR as ROOT, REFERENCE_DIR


STEP_2_SUFFIX = "_step_2_reduced.csv"
STEP_5_SUFFIX = "_step_5_unit_suggestions.csv"

# Patterns that capture numeric + unit tokens in free text
UNIT_PATTERNS = [
    # Years / Age
    (re.compile(r"(\d+(?:\.\d+)?)\s*(y|yr|yrs|year|years)\b", re.IGNORECASE), "years", "age/duration"),
    (re.compile(r"(\d+(?:\.\d+)?)\s*(mo|mos|month|months)\b", re.IGNORECASE), "months", "duration"),
    (re.compile(r"(\d+(?:\.\d+)?)\s*(wk|wks|week|weeks)\b", re.IGNORECASE), "weeks", "duration"),
    (re.compile(r"(\d+(?:\.\d+)?)\s*(d|day|days)\b", re.IGNORECASE), "days", "duration"),

    # Weight
    (re.compile(r"(\d+(?:\.\d+)?)\s*(kg|kgs|kilogram|kilograms)\b", re.IGNORECASE), "kg", "weight"),
    (re.compile(r"(\d+(?:\.\d+)?)\s*(g|gm|gms|gram|grams)\b", re.IGNORECASE), "g", "weight"),
    (re.compile(r"(\d+(?:\.\d+)?)\s*(lb|lbs|pound|pounds)\b", re.IGNORECASE), "lb", "weight"),

    # Height / Length
    (re.compile(r"(\d+(?:\.\d+)?)\s*(cm|cms|centimeter|centimeters)\b", re.IGNORECASE), "cm", "length"),
    (re.compile(r"(\d+(?:\.\d+)?)\s*(mm|mms|millimeter|millimeters)\b", re.IGNORECASE), "mm", "length"),
    (re.compile(r"(\d+(?:\.\d+)?)\s*(m|meter|meters|metre|metres)\b", re.IGNORECASE), "m", "length"),
    (re.compile(r"(\d+(?:\.\d+)?)\s*(inch|inches|in)\b", re.IGNORECASE), "in", "length"),
    (re.compile(r"(\d+(?:\.\d+)?)\s*(ft|foot|feet)\b", re.IGNORECASE), "ft", "length"),

    # Pressure
    (re.compile(r"(\d+(?:\.\d+)?)\s*(mmhg|mm hg)\b", re.IGNORECASE), "mmHg", "pressure"),

    # Volume
    (re.compile(r"(\d+(?:\.\d+)?)\s*(ml|mL|milliliter|milliliters|millilitre|millilitres)\b", re.IGNORECASE), "mL", "volume"),
    (re.compile(r"(\d+(?:\.\d+)?)\s*(l|L|liter|liters|litre|litres)\b", re.IGNORECASE), "L", "volume"),

    # Concentration / Dose
    (re.compile(r"(\d+(?:\.\d+)?)\s*(mg|milligram|milligrams)\b", re.IGNORECASE), "mg", "mass"),
    (re.compile(r"(\d+(?:\.\d+)?)\s*(mcg|ug|microgram|micrograms)\b", re.IGNORECASE), "mcg", "mass"),
    (re.compile(r"(\d+(?:\.\d+)?)\s*(ng|nanogram|nanograms)\b", re.IGNORECASE), "ng", "mass"),
    (re.compile(r"(\d+(?:\.\d+)?)\s*(pg|picogram|picograms)\b", re.IGNORECASE), "pg", "mass"),
    (re.compile(r"(\d+(?:\.\d+)?)\s*(iu|IU|unit|units)\b", re.IGNORECASE), "IU", "dose"),

    # Percentage (often written without % in text)
    (re.compile(r"(\d+(?:\.\d+)?)\s*(%|percent|pct)\b", re.IGNORECASE), "%", "proportion"),

    # Rate / Count
    (re.compile(r"(\d+(?:\.\d+)?)\s*(cpm|counts per minute|counts/min)\b", re.IGNORECASE), "cpm", "rate"),
    (re.compile(r"(\d+(?:\.\d+)?)\s*(bpm|beats per minute|beats/min)\b", re.IGNORECASE), "bpm", "rate"),
]

# Common non-unit words that should not be flagged
SKIP_WORDS = {
    "no", "yes", "unknown", "na", "n/a", "none", "normal", "abnormal",
    "present", "absent", "positive", "negative", "checked", "unchecked",
}


def step_2_input_path(dataset: str) -> Path:
    return ROOT / f"{dataset}{STEP_2_SUFFIX}"


def step_5_output_path(dataset: str) -> Path:
    return ROOT / f"{dataset}{STEP_5_SUFFIX}"


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


def extract_unit_suggestions(value: str) -> list[dict[str, str]]:
    """Return list of suggestion dicts for a single cell value."""
    suggestions = []
    stripped = value.strip()
    if not stripped:
        return suggestions

    # Skip boolean-like and known non-unit values
    if normalize(stripped) in SKIP_WORDS:
        return suggestions

    # Skip pure numbers (already handled by step 4)
    if re.match(r"^[+-]?\d+(?:\.\d+)?$", stripped):
        return suggestions

    for pattern, canonical_unit, dimension in UNIT_PATTERNS:
        for match in pattern.finditer(stripped):
            numeric_part = match.group(1)
            raw_unit = match.group(2)
            start, end = match.span()
            suggestions.append({
                "raw_value": stripped,
                "extracted_numeric": numeric_part,
                "raw_unit": raw_unit,
                "canonical_unit": canonical_unit,
                "dimension": dimension,
                "match_span": f"{start}:{end}",
                "suggested_canonical": f"{numeric_part} {canonical_unit}",
            })

    return suggestions


def scan_dataset_for_units(dataset: str, headers: list[str], data_rows: list[list[str]]) -> list[dict[str, str]]:
    """Scan all values and collect unit-extraction suggestions."""
    records: list[dict[str, str]] = []

    # Track per-column statistics
    column_counts: dict[str, Counter[str]] = defaultdict(Counter)

    for row_idx, row in enumerate(data_rows, start=2):
        for col_idx, header in enumerate(headers):
            raw_value = row[col_idx] if col_idx < len(row) else ""
            suggestions = extract_unit_suggestions(raw_value)
            for suggestion in suggestions:
                records.append({
                    "dataset": dataset,
                    "row_number": str(row_idx),
                    "column_name": header,
                    "raw_value": suggestion["raw_value"],
                    "extracted_numeric": suggestion["extracted_numeric"],
                    "raw_unit": suggestion["raw_unit"],
                    "canonical_unit": suggestion["canonical_unit"],
                    "dimension": suggestion["dimension"],
                    "match_span": suggestion["match_span"],
                    "suggested_canonical": suggestion["suggested_canonical"],
                })
                key = f"{suggestion['canonical_unit']}:{suggestion['dimension']}"
                column_counts[header][key] += 1

    return records


def write_unit_suggestions(dataset: str, records: list[dict[str, str]]) -> None:
    with step_5_output_path(dataset).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "dataset",
                "row_number",
                "column_name",
                "raw_value",
                "extracted_numeric",
                "raw_unit",
                "canonical_unit",
                "dimension",
                "match_span",
                "suggested_canonical",
            ],
        )
        writer.writeheader()
        writer.writerows(records)


def process_dataset(dataset: str) -> None:
    headers, data_rows = read_step_2_dataset(dataset)
    records = scan_dataset_for_units(dataset, headers, data_rows)
    write_unit_suggestions(dataset, records)

    # Summarize by column
    column_summary: dict[str, Counter[str]] = defaultdict(Counter)
    for record in records:
        key = f"{record['canonical_unit']}:{record['dimension']}"
        column_summary[record["column_name"]][key] += 1

    print(f"{dataset}: scanned {len(data_rows)} rows, found {len(records)} unit-extraction suggestions")
    print(f"  suggestions output: {step_5_output_path(dataset).name}")

    # Print top columns with suggestions
    if column_summary:
        print("  top columns with unit suggestions:")
        for col, counts in sorted(column_summary.items(), key=lambda x: -sum(x[1].values()))[:10]:
            total = sum(counts.values())
            top_units = ", ".join(f"{k}({v})" for k, v in counts.most_common(3))
            print(f"    - {col}: {total} suggestions ({top_units})")


def main() -> None:
    ensure_step_2_artifacts()
    for dataset in DATASETS:
        process_dataset(dataset)


if __name__ == "__main__":
    main()
