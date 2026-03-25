#!/usr/bin/env python3
"""
STEP 4: Data quality + characterization for OMOP-style outputs.

Input directory (default: outputs/omop_cdm) should contain one of each:
  - person.parquet or person.csv
  - measurement.parquet or measurement.csv
  - condition_occurrence.parquet or condition_occurrence.csv
  - observation.parquet or observation.csv

Outputs:
  - outputs/data_quality_report.html
  - outputs/cohort_characterization.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run quality + characterization on OMOP extracts")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("outputs/omop_cdm"),
        help="Directory containing OMOP extract tables",
    )
    parser.add_argument(
        "--report-html",
        type=Path,
        default=Path("outputs/data_quality_report.html"),
        help="Output HTML quality report",
    )
    parser.add_argument(
        "--characterization-csv",
        type=Path,
        default=Path("outputs/cohort_characterization.csv"),
        help="Output characterization CSV",
    )
    return parser.parse_args()


def _load_table(input_dir: Path, name: str) -> pd.DataFrame:
    pq = input_dir / f"{name}.parquet"
    csv = input_dir / f"{name}.csv"
    if pq.exists():
        return pd.read_parquet(pq)
    if csv.exists():
        return pd.read_csv(csv)
    return pd.DataFrame()


def _safe_rate(numer: int, denom: int) -> float:
    if denom <= 0:
        return 0.0
    return float(numer) / float(denom)


def _check_person(person: pd.DataFrame) -> List[Dict]:
    checks: List[Dict] = []
    total = int(len(person))

    if total == 0:
        checks.append({"check": "person_non_empty", "status": "FAIL", "details": "person table is empty"})
        return checks

    dup = int(person["person_id"].duplicated().sum()) if "person_id" in person.columns else total
    null_id = int(person["person_id"].isna().sum()) if "person_id" in person.columns else total

    checks.extend(
        [
            {
                "check": "person_non_empty",
                "status": "PASS" if total > 0 else "FAIL",
                "details": f"rows={total}",
            },
            {
                "check": "person_id_not_null",
                "status": "PASS" if null_id == 0 else "FAIL",
                "details": f"null_person_id={null_id}",
            },
            {
                "check": "person_id_unique",
                "status": "PASS" if dup == 0 else "FAIL",
                "details": f"duplicate_person_id={dup}",
            },
        ]
    )
    return checks


def _check_fk(table: pd.DataFrame, table_name: str, person_ids: set) -> Dict:
    if table.empty:
        return {
            "check": f"{table_name}_person_fk",
            "status": "WARN",
            "details": "table empty",
        }

    if "person_id" not in table.columns:
        return {
            "check": f"{table_name}_person_fk",
            "status": "FAIL",
            "details": "person_id column missing",
        }

    missing = int((~table["person_id"].isin(person_ids)).sum())
    return {
        "check": f"{table_name}_person_fk",
        "status": "PASS" if missing == 0 else "FAIL",
        "details": f"orphan_rows={missing}",
    }


def _characterize(
    person: pd.DataFrame,
    measurement: pd.DataFrame,
    condition: pd.DataFrame,
    observation: pd.DataFrame,
) -> pd.DataFrame:
    rows: List[Dict] = []

    rows.append({"section": "cohort", "metric": "n_person", "value": int(len(person))})
    rows.append({"section": "cohort", "metric": "n_measurement", "value": int(len(measurement))})
    rows.append({"section": "cohort", "metric": "n_condition_occurrence", "value": int(len(condition))})
    rows.append({"section": "cohort", "metric": "n_observation", "value": int(len(observation))})

    if not person.empty and "gender_source_value" in person.columns:
        g = (
            person["gender_source_value"]
            .fillna("unknown")
            .astype(str)
            .str.strip()
            .str.lower()
            .value_counts(dropna=False)
        )
        for k, v in g.items():
            rows.append({"section": "person", "metric": f"gender:{k}", "value": int(v)})

    if not condition.empty and "source_field" in condition.columns:
        c = condition["source_field"].value_counts().head(30)
        for k, v in c.items():
            rows.append({"section": "condition", "metric": f"source_field:{k}", "value": int(v)})

    if not measurement.empty:
        if "source_field" in measurement.columns:
            m = measurement["source_field"].value_counts().head(30)
            for k, v in m.items():
                rows.append({"section": "measurement", "metric": f"source_field:{k}", "value": int(v)})

        if "value_as_number" in measurement.columns:
            num = pd.to_numeric(measurement["value_as_number"], errors="coerce")
            rows.append({"section": "measurement", "metric": "numeric_non_null", "value": int(num.notna().sum())})
            if num.notna().any():
                rows.append({"section": "measurement", "metric": "numeric_mean", "value": float(num.mean())})
                rows.append({"section": "measurement", "metric": "numeric_p50", "value": float(num.median())})

    return pd.DataFrame(rows)


def _to_html(checks: pd.DataFrame, char_df: pd.DataFrame) -> str:
    style = """
    <style>
      body { font-family: Arial, sans-serif; margin: 24px; }
      table { border-collapse: collapse; width: 100%; margin-bottom: 24px; }
      th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
      th { background: #f4f4f4; }
      .PASS { color: #117733; font-weight: bold; }
      .WARN { color: #aa7700; font-weight: bold; }
      .FAIL { color: #bb2222; font-weight: bold; }
    </style>
    """

    checks_html = checks.copy()
    checks_html["status"] = checks_html["status"].apply(lambda s: f'<span class="{s}">{s}</span>')

    return f"""
    <html>
      <head><meta charset=\"utf-8\"><title>OMOP Data Quality Report</title>{style}</head>
      <body>
        <h1>OMOP Data Quality Report</h1>
        <h2>Checks</h2>
        {checks_html.to_html(index=False, escape=False)}
        <h2>Cohort Characterization (summary)</h2>
        {char_df.to_html(index=False)}
      </body>
    </html>
    """


def main() -> None:
    args = _parse_args()

    person = _load_table(args.input_dir, "person")
    measurement = _load_table(args.input_dir, "measurement")
    condition = _load_table(args.input_dir, "condition_occurrence")
    observation = _load_table(args.input_dir, "observation")

    checks: List[Dict] = []
    checks.extend(_check_person(person))

    person_ids = set(person["person_id"].tolist()) if not person.empty and "person_id" in person.columns else set()
    checks.append(_check_fk(measurement, "measurement", person_ids))
    checks.append(_check_fk(condition, "condition_occurrence", person_ids))
    checks.append(_check_fk(observation, "observation", person_ids))

    if not measurement.empty and "value_as_number" in measurement.columns:
        num = pd.to_numeric(measurement["value_as_number"], errors="coerce")
        null_num = int(num.isna().sum())
        checks.append(
            {
                "check": "measurement_numeric_completeness",
                "status": "PASS" if _safe_rate(null_num, len(measurement)) < 0.8 else "WARN",
                "details": f"null_numeric={null_num}/{len(measurement)}",
            }
        )

    checks_df = pd.DataFrame(checks)
    char_df = _characterize(person, measurement, condition, observation)

    args.characterization_csv.parent.mkdir(parents=True, exist_ok=True)
    char_df.to_csv(args.characterization_csv, index=False)

    html = _to_html(checks_df, char_df)
    args.report_html.parent.mkdir(parents=True, exist_ok=True)
    args.report_html.write_text(html)

    print(f"[omop_quality] Wrote report: {args.report_html}")
    print(f"[omop_quality] Wrote characterization: {args.characterization_csv}")


if __name__ == "__main__":
    main()
