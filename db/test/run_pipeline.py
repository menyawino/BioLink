from __future__ import annotations

import argparse
import csv
import json
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from src.pipeline.step_3_profile_normalization import main as step_3_main
from src.pipeline.step_4_apply_range_rules import main as step_4_main
from src.pipeline.step_5_extract_units import main as step_5_main
from src.pipeline.step_6_fuzzy_match_v2 import main as step_6_main
from src.pipeline.step_7_unify_datasets import unify_datasets as step_7_main

from src.config import PROCESSED_DIR, INTERIM_DIR

STEP7_DIR = PROCESSED_DIR / "step_7"

EXACT_SENSITIVE_EXPORT_FIELDS = {
    "birth_demographics",
    "mrn_ahc_admin",
    "mrn_bu_admin",
    "name",
}

SENSITIVE_EXPORT_TOKENS = {
    "address", "birth", "contact", "date", "dob", "email", "mobile",
    "mrn", "passport", "phone", "postal", "street", "tel", "telephone", "zip",
}

DATASET_TO_COHORT = {
    "bhs": "D1",
    "ehvol": "D2",
}


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _remove_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def _dataset_identity(raw_value: str | None) -> tuple[str, str]:
    normalized = str(raw_value or "").strip().lower()
    if normalized == "bhs":
        return "BHS", "bhs"
    if normalized == "ehvol":
        return "EHVol", "ehvol"
    title = str(raw_value or "unknown").strip() or "unknown"
    return title, normalized or "unknown"


def _should_publish_field(field_name: str) -> bool:
    normalized = field_name.strip().lower()
    if not normalized:
        return False
    if normalized in EXACT_SENSITIVE_EXPORT_FIELDS:
        return False
    tokens = {token for token in normalized.split("_") if token}
    if tokens & SENSITIVE_EXPORT_TOKENS:
        return False
    return True


def _build_compatibility_snapshot(step7_dir: Path, output_path: Path) -> tuple[list[dict[str, str]], list[str]]:
    source_path = step7_dir / "unified_wide_table.csv"
    with source_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        source_rows = list(reader)
        source_fields = list(reader.fieldnames or [])

    if not source_fields:
        raise ValueError(f"{source_path} is missing a header row")

    compat_fields = [field for field in source_fields if _should_publish_field(field)]
    insert_at = compat_fields.index("participant_id") + 1 if "participant_id" in compat_fields else len(compat_fields)
    if "cohort" not in compat_fields:
        compat_fields.insert(insert_at, "cohort")
        insert_at += 1
    if "source_dataset" not in compat_fields:
        compat_fields.insert(insert_at, "source_dataset")

    compatibility_rows: list[dict[str, str]] = []
    for row in source_rows:
        dataset_display, dataset_normalized = _dataset_identity(row.get("dataset_source"))
        compat_row = dict(row)
        compat_row["dataset_source"] = dataset_display
        compat_row["source_dataset"] = dataset_normalized
        compat_row["cohort"] = DATASET_TO_COHORT.get(dataset_normalized, "")
        compatibility_rows.append({field: compat_row.get(field, "") for field in compat_fields})

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=compat_fields)
        writer.writeheader()
        writer.writerows(compatibility_rows)

    return compatibility_rows, compat_fields


def _write_characterization(rows: list[dict[str, str]], fields: list[str], output_path: Path) -> None:
    dataset_counts = Counter()
    for row in rows:
        dataset_display, _ = _dataset_identity(row.get("dataset_source"))
        dataset_counts[dataset_display] += 1

    analytic_columns = [
        field
        for field in fields
        if field not in {"dataset_source", "participant_id", "source_dataset", "cohort"}
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["dataset_source", "participant_count", "analytic_column_count"],
        )
        writer.writeheader()
        for dataset_name in sorted(dataset_counts):
            writer.writerow(
                {
                    "dataset_source": dataset_name,
                    "participant_count": dataset_counts[dataset_name],
                    "analytic_column_count": len(analytic_columns),
                }
            )


def _write_json_copy(source_path: Path, output_path: Path) -> dict:
    audit = json.loads(source_path.read_text(encoding="utf-8"))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    return audit


def _write_report_html(audit: dict, rows: list[dict[str, str]], fields: list[str], output_path: Path) -> None:
    dataset_rows = audit.get("datasets", {})
    concept_summary = audit.get("concepts", {})
    output_summary = audit.get("outputs", {})
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>BioLink Registry Pipeline Report</title>
  <style>
    body {{ font-family: Helvetica, Arial, sans-serif; margin: 32px; color: #10233c; }}
    h1, h2 {{ margin-bottom: 0.4rem; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1rem 0 2rem; }}
    th, td {{ border: 1px solid #c8d4e3; padding: 0.65rem; text-align: left; }}
    th {{ background: #eef4fb; }}
    .meta {{ color: #4a5d75; margin-bottom: 1.5rem; }}
  </style>
</head>
<body>
  <h1>BioLink Replacement Pipeline Report</h1>
  <p class="meta">Generated at {_timestamp()} using the db/test step pipeline.</p>

  <h2>Datasets</h2>
  <table>
    <thead>
      <tr><th>Dataset</th><th>Rows</th><th>Columns</th></tr>
    </thead>
    <tbody>
      <tr><td>BHS</td><td>{dataset_rows.get('BHS', {}).get('rows', 0)}</td><td>{dataset_rows.get('BHS', {}).get('columns', 0)}</td></tr>
      <tr><td>EHVol</td><td>{dataset_rows.get('EHVol', {}).get('rows', 0)}</td><td>{dataset_rows.get('EHVol', {}).get('columns', 0)}</td></tr>
    </tbody>
  </table>

  <h2>Unified Snapshot</h2>
  <table>
    <thead>
      <tr><th>Metric</th><th>Value</th></tr>
    </thead>
    <tbody>
      <tr><td>Unified rows</td><td>{len(rows)}</td></tr>
      <tr><td>Unified columns</td><td>{len(fields)}</td></tr>
      <tr><td>Total canonical concepts</td><td>{concept_summary.get('total', 0)}</td></tr>
      <tr><td>Shared concepts</td><td>{concept_summary.get('shared', 0)}</td></tr>
      <tr><td>Column mapping entries</td><td>{output_summary.get('column_mapping_entries', 0)}</td></tr>
    </tbody>
  </table>
</body>
</html>
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the replacement db/test BioLink pipeline.")
    parser.add_argument("--unified-output", default="unified_registry.csv")
    parser.add_argument("--comparability-output", default="comparability_report.json")
    parser.add_argument("--report-html", default="data_quality_report.html")
    parser.add_argument("--characterization-output", default="cohort_characterization.csv")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    unified_output = (PROCESSED_DIR / args.unified_output).resolve()
    comparability_output = (PROCESSED_DIR / args.comparability_output).resolve()
    report_html = (PROCESSED_DIR / args.report_html).resolve()
    characterization_output = (PROCESSED_DIR / args.characterization_output).resolve()

    for path in [
        STEP7_DIR,
        unified_output,
        comparability_output,
        report_html,
        characterization_output,
    ]:
        _remove_path(path)

    print("Running Step 3...")
    step_3_main()
    print("Running Step 4...")
    step_4_main()
    print("Running Step 5...")
    step_5_main()
    print("Running Step 6...")
    step_6_main()
    print("Running Step 7...")
    step_7_main()

    rows, fields = _build_compatibility_snapshot(STEP7_DIR, unified_output)
    audit = _write_json_copy(STEP7_DIR / "unification_audit.json", comparability_output)
    _write_report_html(audit, rows, fields, report_html)
    _write_characterization(rows, fields, characterization_output)

    print(json.dumps(
        {
            "pipeline": "db/test",
            "generated_at": _timestamp(),
            "unified_output": str(unified_output),
            "comparability_output": str(comparability_output),
            "report_html": str(report_html),
            "characterization_output": str(characterization_output),
        },
        indent=2,
    ))

    print("Cleaning up intermediate files...")
    if INTERIM_DIR.exists():
        shutil.rmtree(INTERIM_DIR)
        INTERIM_DIR.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()