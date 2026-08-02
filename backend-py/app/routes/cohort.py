"""
Cohort query and export endpoints for BioLink API.

Provides structured cohort selection, summary statistics, and CSV export
based on the patient registry tables.
"""

import csv
import io
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import text

from app.database import get_db
from app.routes.auth import get_current_active_user
from app.routes.patients import _registry_source_table

router = APIRouter()
logger = logging.getLogger(__name__)


class CohortCriteria(BaseModel):
    dataset: str = "all"
    gender: Optional[str] = None
    ageMin: Optional[int] = None
    ageMax: Optional[int] = None
    hasDiabetes: Optional[bool] = None
    hasHypertension: Optional[bool] = None
    hasSmoking: Optional[bool] = None
    hasEcho: Optional[bool] = None
    hasMri: Optional[bool] = None
    hasGenomics: Optional[bool] = None
    nationality: Optional[str] = None


class CohortSummaryRequest(BaseModel):
    patientIds: List[int]


class CohortExportRequest(BaseModel):
    patientIds: List[int]
    fields: Optional[List[str]] = None


def _source_expr(db, dataset: str) -> str:
    return _registry_source_table(db, dataset)


@router.post("/query")
async def query_cohort(
    criteria: CohortCriteria,
    _user=Depends(get_current_active_user),
    db=Depends(get_db),
):
    """Execute a cohort query and return matching patients."""
    try:
        source = _source_expr(db, criteria.dataset)
        conditions = ["1=1"]
        params: dict = {}

        if criteria.gender:
            conditions.append("LOWER(gender) = :gender")
            params["gender"] = criteria.gender.lower()
        if criteria.ageMin is not None:
            conditions.append("age >= :age_min")
            params["age_min"] = criteria.ageMin
        if criteria.ageMax is not None:
            conditions.append("age <= :age_max")
            params["age_max"] = criteria.ageMax
        if criteria.nationality:
            conditions.append("LOWER(nationality) = :nationality")
            params["nationality"] = criteria.nationality.lower()
        if criteria.hasEcho is not None:
            conditions.append("(echo_ef IS NOT NULL) = :has_echo")
            params["has_echo"] = criteria.hasEcho
        if criteria.hasDiabetes is not None:
            conditions.append("COALESCE(has_diabetes, false) = :has_diabetes")
            params["has_diabetes"] = criteria.hasDiabetes
        if criteria.hasHypertension is not None:
            conditions.append("COALESCE(has_hypertension, false) = :has_htn")
            params["has_htn"] = criteria.hasHypertension

        where = " AND ".join(conditions)
        rows = db.execute(
            text(f"SELECT COALESCE(CAST(dna_id AS TEXT), CAST(id AS TEXT)) AS dna_id, COALESCE(CAST(dna_id AS TEXT), CAST(id AS TEXT)) AS participant_id, age, gender, nationality FROM {source} WHERE {where} LIMIT 5000"),
            params,
        ).mappings().fetchall()

        return {
            "success": True,
            "data": {
                "patients": [dict(r) for r in rows],
                "count": len(rows),
                "criteria": criteria.model_dump(exclude_none=True),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cohort query failed: {e}")
        return {"success": False, "error": str(e)}


@router.post("/summary")
async def cohort_summary(
    body: CohortSummaryRequest,
    _user=Depends(get_current_active_user),
    db=Depends(get_db),
):
    """Return summary statistics for a set of patient IDs."""
    try:
        if not body.patientIds:
            return {"success": True, "data": {}}

        ids = [str(i) for i in body.patientIds[:5000]]  # cap

        source = _source_expr(db, "all")
        row = db.execute(
            text(
                f"SELECT COUNT(*), AVG(age), "
                f"COUNT(*) FILTER (WHERE LOWER(gender) IN ('male','m')), "
                f"COUNT(*) FILTER (WHERE LOWER(gender) IN ('female','f')), "
                f"AVG(bmi), AVG(systolic_bp), AVG(hba1c) "
                f"FROM {source} WHERE (CAST(dna_id AS TEXT) = ANY(:ids) OR CAST(id AS TEXT) = ANY(:ids))"
            ),
            {"ids": ids},
        ).fetchone()

        return {
            "success": True,
            "data": {
                "totalPatients": row[0] or 0,
                "averageAge": round(float(row[1] or 0), 1),
                "maleCount": row[2] or 0,
                "femaleCount": row[3] or 0,
                "avgBmi": round(float(row[4] or 0), 1),
                "avgSystolicBp": round(float(row[5] or 0), 1),
                "avgHba1c": round(float(row[6] or 0), 1),
            },
        }
    except Exception as e:
        logger.error(f"Cohort summary failed: {e}")
        return {"success": False, "error": str(e)}


@router.post("/export")
async def export_cohort(
    body: CohortExportRequest,
    _user=Depends(get_current_active_user),
    db=Depends(get_db),
):
    """Export cohort patient data as CSV."""
    try:
        if not body.patientIds:
            raise HTTPException(status_code=400, detail="No patient IDs provided")

        ids = [str(i) for i in body.patientIds[:5000]]
        fields = [f for f in (body.fields or list(ALLOWED_EXPORT_FIELDS)) if f in ALLOWED_EXPORT_FIELDS]
        if not fields:
            fields = list(ALLOWED_EXPORT_FIELDS)

        select_cols = ", ".join([f if f != "participant_id" else "COALESCE(CAST(dna_id AS TEXT), CAST(id AS TEXT)) AS participant_id" for f in fields])
        source = _source_expr(db, "all")

        rows = db.execute(
            text(f"SELECT {select_cols} FROM {source} WHERE (CAST(dna_id AS TEXT) = ANY(:ids) OR CAST(id AS TEXT) = ANY(:ids))"),
            {"ids": ids},
        ).mappings().fetchall()

        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(fields)
        for r in rows:
            writer.writerow([r.get(f) for f in fields])

        buf.seek(0)
        return StreamingResponse(
            iter([buf.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=cohort_export.csv"},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cohort export failed: {e}")
        return {"success": False, "error": str(e)}
