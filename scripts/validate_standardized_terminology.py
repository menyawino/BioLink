#!/usr/bin/env python3
"""
Validate terminology fields in standardized mapping artifacts.

Supported input:
- outputs/compare_columns/standardized_columns.csv
- db/schema_standardized.sql (parses _schema_registry INSERT rows)

Checks (strict):
- SDTM domain in known SDTM domain set
- SDTM variable format: uppercase alnum, <= 8 chars
- LOINC format: ddddd-d
- SNOMED CT format: digits only (6-18)
- ICD-10 WHO format (conservative)
- UCUM character set
- RxNorm concept id digits only (if present)

Exits non-zero on any validation error.
"""

from __future__ import annotations

import argparse
import csv
import io
import pathlib
import re
import sys
from typing import Iterable

import pandas as pd

SDTM_DOMAINS = {
    "AE", "CM", "CO", "DM", "DS", "DV", "EG", "EX", "FA", "HO",
    "IE", "LB", "MH", "MI", "PC", "PE", "PP", "PR", "QS", "RELREC",
    "RP", "RS", "SC", "SE", "SG", "SU", "SV", "TA", "TE", "TI",
    "TS", "TV", "VS",
}

SDTM_VAR_RE = re.compile(r"^[A-Z0-9]{1,8}$")
LOINC_RE = re.compile(r"^\d{1,5}-\d$")
SNOMED_RE = re.compile(r"^\d{6,18}$")
ICD10_RE = re.compile(r"^[A-TV-Z][0-9][0-9AB](\.[0-9A-TV-Z]{1,4})?$")
UCUM_RE = re.compile(r"^[A-Za-z0-9\[\]\(\)\./_%\*\-]+$")
RXNORM_RE = re.compile(r"^\d+$")


def clean(value):
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    text = str(value).strip()
    if not text or text.lower() == "nan" or text.upper() == "NULL":
        return None
    if re.fullmatch(r"\d+\.0+", text):
        return text.split(".")[0]
    return text


def validate_row(row: dict, row_label: str) -> list[str]:
    dataset = clean(row.get("dataset"))
    original_name = clean(row.get("original_name"))
    sdtm_domain = clean(row.get("sdtm_domain"))
    sdtm_variable = clean(row.get("sdtm_variable"))
    loinc_code = clean(row.get("loinc_code"))
    snomed_code = clean(row.get("snomed_code"))
    icd10_code = clean(row.get("icd10_code"))
    ucum_unit = clean(row.get("ucum_unit"))
    rxnorm_concept = clean(row.get("rxnorm_concept"))

    prefix = f"{row_label} [{dataset or '<dataset?>'} / {original_name or '<name?>'}]"
    errors: list[str] = []

    if sdtm_domain and sdtm_domain not in SDTM_DOMAINS:
        errors.append(f"{prefix} invalid SDTM domain: {sdtm_domain}")
    if sdtm_variable and not SDTM_VAR_RE.fullmatch(sdtm_variable):
        errors.append(f"{prefix} invalid SDTM variable: {sdtm_variable}")

    if loinc_code and not LOINC_RE.fullmatch(loinc_code):
        if SNOMED_RE.fullmatch(loinc_code):
            errors.append(f"{prefix} invalid LOINC (looks like SNOMED): {loinc_code}")
        else:
            errors.append(f"{prefix} invalid LOINC: {loinc_code}")

    if snomed_code and not SNOMED_RE.fullmatch(snomed_code):
        errors.append(f"{prefix} invalid SNOMED CT: {snomed_code}")

    if icd10_code and not ICD10_RE.fullmatch(icd10_code):
        errors.append(f"{prefix} invalid ICD-10: {icd10_code}")

    if ucum_unit and not UCUM_RE.fullmatch(ucum_unit):
        errors.append(f"{prefix} invalid UCUM: {ucum_unit}")

    if rxnorm_concept and not RXNORM_RE.fullmatch(rxnorm_concept):
        errors.append(f"{prefix} invalid RxNorm concept: {rxnorm_concept}")

    return errors


def iter_rows_from_csv(path: pathlib.Path) -> Iterable[dict]:
    df = pd.read_csv(path)
    for _, row in df.iterrows():
        yield row.to_dict()


def iter_rows_from_sql(path: pathlib.Path) -> Iterable[dict]:
    text = path.read_text(encoding="utf-8")
    matches = re.findall(r"INSERT INTO _schema_registry .*? VALUES \((.*?)\) ON CONFLICT", text)

    for raw_values in matches:
        cols = next(csv.reader(io.StringIO(raw_values), quotechar="'", delimiter=",", escapechar="\\"))
        if len(cols) < 12:
            continue
        # INSERT order in generate_schema_sql.py
        yield {
            "dataset": cols[0].strip(),
            "original_name": cols[1].strip(),
            "sdtm_domain": cols[4].strip(),
            "sdtm_variable": cols[5].strip(),
            "loinc_code": cols[6].strip(),
            "snomed_code": cols[7].strip(),
            "icd10_code": cols[8].strip(),
            "ucum_unit": cols[9].strip(),
            "rxnorm_concept": None,
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default="db/schema_standardized.sql",
        help="Path to standardized_columns.csv or schema_standardized.sql",
    )
    parser.add_argument("--max-errors", type=int, default=100)
    args = parser.parse_args()

    path = pathlib.Path(args.input)
    if not path.exists():
        print(f"ERROR: input does not exist: {path}")
        return 2

    suffix = path.suffix.lower()
    if suffix == ".csv":
        rows = iter_rows_from_csv(path)
    elif suffix == ".sql":
        rows = iter_rows_from_sql(path)
    else:
        print(f"ERROR: unsupported input type: {path}")
        return 2

    errors: list[str] = []
    total = 0
    for total, row in enumerate(rows, start=1):
        row_errors = validate_row(row, f"row {total}")
        errors.extend(row_errors)
        if len(errors) >= args.max_errors:
            break

    print(f"Validated rows: {total}")
    if errors:
        print(f"Validation errors: {len(errors)} (showing up to {args.max_errors})")
        for line in errors[: args.max_errors]:
            print(f"- {line}")
        return 1

    print("OK: terminology fields pass strict validation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
