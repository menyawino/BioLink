from __future__ import annotations

import csv
import io
import json
import logging
import os
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

router = APIRouter()
logger = logging.getLogger(__name__)


def _workspace_root() -> Path:
    explicit_root = os.getenv("BIOLINK_WORKSPACE_ROOT")
    if explicit_root:
        return Path(explicit_root)

    candidates = [
        Path("/app"),
        Path(__file__).resolve().parents[3],
        Path.cwd(),
    ]
    for candidate in candidates:
        if (candidate / "db" / "test" / "step_7").exists():
            return candidate
    return candidates[0]


def _artifact_path(*parts: str) -> Path:
    return _workspace_root().joinpath(*parts)


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _is_int(value: str) -> bool:
    try:
        int(value)
        return True
    except ValueError:
        return False


def _is_float(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False


def _infer_data_type(samples: list[str]) -> str:
    values = [value.strip() for value in samples if value and value.strip()]
    if not values:
        return "text"

    lowered = {value.lower() for value in values[:50]}
    if lowered and lowered.issubset({"true", "false", "yes", "no", "0", "1"}):
        return "boolean"
    if all(_is_int(value) for value in values[:50]):
        return "integer"
    if all(_is_float(value) for value in values[:50]):
        return "number"
    if all(len(value) == 10 and value[4:5] == "-" and value[7:8] == "-" for value in values[:50]):
        return "date"
    return "text"


@lru_cache(maxsize=1)
def _artifact_snapshot() -> dict[str, Any]:
    column_mapping_rows = _read_csv_rows(_artifact_path("db", "test", "step_7", "column_mapping.csv"))
    modality_rows = _read_csv_rows(_artifact_path("db", "test", "step_7", "modality_manifest.csv"))
    unit_rows = _read_csv_rows(_artifact_path("db", "test", "step_7", "unit_mapping.csv"))
    value_set_rows = _read_csv_rows(_artifact_path("db", "test", "step_7", "value_set_mapping.csv"))
    unified_rows = _read_csv_rows(_artifact_path("db", "test", "step_7", "unified_wide_table.csv"))

    audit_path = _artifact_path("db", "test", "step_7", "unification_audit.json")
    audit = {}
    if audit_path.exists():
        with audit_path.open(encoding="utf-8") as handle:
            audit = json.load(handle)

    units_by_concept: dict[str, set[str]] = defaultdict(set)
    for row in unit_rows:
        concept = (row.get("concept") or "").strip()
        unit = (row.get("unit") or "").strip()
        if concept and unit:
            units_by_concept[concept].add(unit)

    valueset_counts: dict[str, int] = defaultdict(int)
    for row in value_set_rows:
        concept = (row.get("concept") or "").strip()
        if concept:
            valueset_counts[concept] += 1

    modality_by_concept: dict[str, str] = {}
    for row in modality_rows:
        concept = (row.get("concept") or "").strip()
        modality = (row.get("modality") or "").strip()
        if concept and modality and concept not in modality_by_concept:
            modality_by_concept[concept] = modality

    samples_by_concept: dict[str, list[str]] = defaultdict(list)
    fill_rate_by_concept: dict[str, float] = {}
    if unified_rows:
        total_rows = len(unified_rows)
        non_empty_counts: dict[str, int] = defaultdict(int)
        for row in unified_rows:
            for key, value in row.items():
                if not key or key in {"participant_id", "cohort", "source_dataset", "dataset_source"}:
                    continue
                text = (value or "").strip()
                if text:
                    non_empty_counts[key] += 1
                    if len(samples_by_concept[key]) < 50:
                        samples_by_concept[key].append(text)
        for concept, count in non_empty_counts.items():
            fill_rate_by_concept[concept] = count / total_rows if total_rows else 0.0

    concepts: dict[str, dict[str, Any]] = {}
    rows_by_concept: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in column_mapping_rows:
        concept = (row.get("canonical_concept") or "").strip()
        if concept:
            rows_by_concept[concept].append(row)

    for concept, rows in rows_by_concept.items():
        dataset_sources: dict[str, list[str]] = defaultdict(list)
        broad_category = ""
        pii_label = ""
        for row in rows:
            dataset = (row.get("dataset") or "").strip().upper()
            source = (row.get("original_column") or "").strip()
            if dataset and source and source not in dataset_sources[dataset]:
                dataset_sources[dataset].append(source)
            if not broad_category:
                broad_category = (row.get("broad_category") or "").strip()
            if not pii_label:
                pii_label = (row.get("pii_label") or "").strip()

        cohort_count = sum(1 for dataset in ("BHS", "EHVOL") if dataset_sources.get(dataset))
        tier = "1" if cohort_count == 2 else "2"
        coverage_reason = "Shared across BHS and EHVol" if cohort_count == 2 else (
            "Available only in BHS" if dataset_sources.get("BHS") else "Available only in EHVol"
        )
        unit_values = sorted(units_by_concept.get(concept, set()))
        concepts[concept] = {
            "master_col": concept,
            "data_type": _infer_data_type(samples_by_concept.get(concept, [])),
            "bhs_source": ", ".join(dataset_sources.get("BHS", [])),
            "ehvol_source": ", ".join(dataset_sources.get("EHVOL", [])),
            "tier": tier,
            "unit": ", ".join(unit_values),
            "loinc": "",
            "snomed": "",
            "phenotype_definition": modality_by_concept.get(concept, broad_category),
            "allowable_range": f"{valueset_counts[concept]} normalized values" if valueset_counts.get(concept) else "",
            "transform": "value set normalization" if valueset_counts.get(concept) else "direct mapping",
            "timing_window": "",
            "fill_rate": round(fill_rate_by_concept.get(concept, 0.0), 4),
            "coverage_reason": coverage_reason,
            "pii_label": pii_label,
        }

    dictionary = [concepts[key] for key in sorted(concepts)]
    tiers = [
        {
            "master_col": item["master_col"],
            "tier": item["tier"],
            "data_type": item["data_type"],
            "unit": item["unit"],
            "transform": item["transform"],
            "loinc": item["loinc"],
            "snomed": item["snomed"],
            "phenotype_definition": item["phenotype_definition"],
            "timing_window": item["timing_window"],
            "allowable_range": item["allowable_range"],
            "fill_rate": item["fill_rate"],
        }
        for item in dictionary
    ]

    shared_count = sum(1 for item in dictionary if item["tier"] == "1")
    single_count = len(dictionary) - shared_count
    top_gaps = [
        {
            "master_col": item["master_col"],
            "reason": item["coverage_reason"],
            "count": 1,
        }
        for item in dictionary
        if item["tier"] != "1"
    ][:20]

    provenance_records = []
    for index, row in enumerate(column_mapping_rows, start=1):
        concept = (row.get("canonical_concept") or "").strip()
        concept_row = concepts.get(concept)
        if not concept_row:
            continue
        cohort = (row.get("dataset") or "").strip().upper()
        provenance_records.append(
            {
                "row_index": index,
                "cohort": cohort,
                "master_col": concept,
                "source_cols": (row.get("original_column") or "").strip(),
                "source_value": "",
                "transform": concept_row["transform"],
                "harmonized_value": concept,
                "validation_status": "PASS" if concept_row["tier"] == "1" else "REVIEW",
                "validation_reason": concept_row["coverage_reason"],
                "tier": concept_row["tier"],
                "unit": concept_row["unit"],
                "confidence": "high" if concept_row["tier"] == "1" else "medium",
                "reviewer_approved": concept_row["tier"] == "1",
            }
        )

    summary = {
        "total_records": len(column_mapping_rows),
        "pass_count": shared_count,
        "fail_count": single_count,
        "columns_tracked": len(dictionary),
        "cohorts": len(audit.get("datasets", {}) or {"BHS": {}, "EHVol": {}}),
        "by_tier": [
            {"tier": "1", "status": "shared", "count": shared_count},
            {"tier": "2", "status": "single_cohort", "count": single_count},
        ],
        "top_failures": top_gaps,
    }

    return {
        "dictionary": dictionary,
        "tiers": tiers,
        "provenance": provenance_records,
        "summary": summary,
    }


@router.get("/tiers")
async def harmonization_tiers():
    snapshot = _artifact_snapshot()
    summary: dict[str, int] = defaultdict(int)
    for item in snapshot["tiers"]:
        summary[item["tier"]] += 1
    return {"success": True, "data": snapshot["tiers"], "summary": dict(summary)}


@router.get("/provenance")
async def provenance(
    master_col: str | None = Query(None, description="Filter by master column name"),
    validation_status: str | None = Query(None, description="Filter by PASS or REVIEW"),
    cohort: str | None = Query(None, description="Filter by cohort label"),
    limit: int = Query(1000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
):
    rows = _artifact_snapshot()["provenance"]
    filtered = rows
    if master_col:
        filtered = [row for row in filtered if row["master_col"] == master_col]
    if validation_status:
        filtered = [row for row in filtered if row["validation_status"] == validation_status.upper()]
    if cohort:
        filtered = [row for row in filtered if row["cohort"] == cohort.upper()]
    return {
        "success": True,
        "data": filtered[offset: offset + limit],
        "total": len(filtered),
    }


@router.get("/provenance/summary")
async def provenance_summary():
    return {"success": True, "data": _artifact_snapshot()["summary"]}


@router.get("/comparability")
async def comparability_report():
    report_path = _artifact_path("outputs", "comparability_report.json")
    if not report_path.exists():
        return {"success": True, "data": {}}
    with report_path.open(encoding="utf-8") as handle:
        return {"success": True, "data": json.load(handle)}


@router.get("/comparability-report")
async def comparability_report_alias():
    return await comparability_report()


@router.get("/dictionary")
async def data_dictionary():
    return {"success": True, "data": _artifact_snapshot()["dictionary"], "total": len(_artifact_snapshot()["dictionary"])}


@router.get("/export")
async def export_harmonization(
    format: str = Query("csv", description="Export format: csv"),
):
    if format.lower() != "csv":
        return {"success": False, "error": "Unsupported export format"}

    rows = _artifact_snapshot()["dictionary"]
    columns = [
        "master_col",
        "data_type",
        "tier",
        "unit",
        "bhs_source",
        "ehvol_source",
        "loinc",
        "snomed",
        "allowable_range",
        "phenotype_definition",
    ]

    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=columns)
    writer.writeheader()
    for row in rows:
        writer.writerow({column: row.get(column, "") for column in columns})

    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=registry_mapping_dictionary.csv"},
    )
