from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from app.database import get_db
import csv
import io
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


def _table_exists(db, table_name: str) -> bool:
    row = db.execute(
        text(
            "SELECT EXISTS ("
            "  SELECT 1 FROM information_schema.tables"
            "  WHERE table_schema = 'public' AND table_name = :t"
            ")"
        ),
        {"t": table_name},
    ).scalar()
    return bool(row)


@router.get("/tiers")
async def harmonization_tiers(db=Depends(get_db)):
    """Return harmonization tier classification for all master columns."""
    try:
        if not _table_exists(db, "harmonization_tiers"):
            return {"success": True, "data": []}

        rows = db.execute(text(
            "SELECT master_col, tier, data_type, unit, transform, "
            "       loinc, snomed, phenotype_definition, timing_window, "
            "       allowable_range, fill_rate "
            "FROM harmonization_tiers ORDER BY tier, master_col"
        )).fetchall()

        data = [
            {
                "master_col": r[0],
                "tier": r[1],
                "data_type": r[2],
                "unit": r[3] or "",
                "transform": r[4] or "",
                "loinc": r[5] or "",
                "snomed": r[6] or "",
                "phenotype_definition": r[7] or "",
                "timing_window": r[8] or "",
                "allowable_range": r[9] or "",
                "fill_rate": float(r[10]) if r[10] else 0.0,
            }
            for r in rows
        ]

        tier_summary = {}
        for item in data:
            t = item["tier"]
            tier_summary[t] = tier_summary.get(t, 0) + 1

        return {"success": True, "data": data, "summary": tier_summary}
    except Exception as e:
        logger.error(f"Harmonization tiers query failed: {e}")
        return {"success": False, "error": str(e)}


@router.get("/provenance")
async def provenance(
    master_col: str = Query(None, description="Filter by master column name"),
    validation_status: str = Query(None, description="Filter by PASS or FAIL"),
    cohort: str = Query(None, description="Filter by cohort label"),
    limit: int = Query(1000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    db=Depends(get_db),
):
    """Return per-field provenance records with optional filters."""
    try:
        if not _table_exists(db, "harmonization_provenance"):
            return {"success": True, "data": [], "total": 0}

        conditions = []
        params: dict = {"lim": limit, "off": offset}

        if master_col:
            conditions.append("master_col = :mc")
            params["mc"] = master_col
        if validation_status:
            conditions.append("validation_status = :vs")
            params["vs"] = validation_status.upper()
        if cohort:
            conditions.append("cohort = :co")
            params["co"] = cohort

        where = (" WHERE " + " AND ".join(conditions)) if conditions else ""

        total = db.execute(
            text(f"SELECT COUNT(*) FROM harmonization_provenance{where}"),
            params,
        ).scalar()

        rows = db.execute(
            text(
                f"SELECT row_index, cohort, master_col, source_cols, source_value, "
                f"       transform, harmonized_value, validation_status, "
                f"       validation_reason, tier, unit, confidence, reviewer_approved "
                f"FROM harmonization_provenance{where} "
                f"ORDER BY row_index, master_col LIMIT :lim OFFSET :off"
            ),
            params,
        ).fetchall()

        data = [
            {
                "row_index": r[0],
                "cohort": r[1],
                "master_col": r[2],
                "source_cols": r[3],
                "source_value": r[4],
                "transform": r[5],
                "harmonized_value": r[6],
                "validation_status": r[7],
                "validation_reason": r[8],
                "tier": r[9],
                "unit": r[10] or "",
                "confidence": r[11] or "",
                "reviewer_approved": r[12],
            }
            for r in rows
        ]

        return {"success": True, "data": data, "total": total}
    except Exception as e:
        logger.error(f"Provenance query failed: {e}")
        return {"success": False, "error": str(e)}


@router.get("/provenance/summary")
async def provenance_summary(db=Depends(get_db)):
    """Return aggregated provenance statistics."""
    try:
        if not _table_exists(db, "harmonization_provenance"):
            return {"success": True, "data": {}}

        result = db.execute(text("""
            SELECT
                COUNT(*) AS total_records,
                COUNT(*) FILTER (WHERE validation_status = 'PASS') AS pass_count,
                COUNT(*) FILTER (WHERE validation_status = 'FAIL') AS fail_count,
                COUNT(DISTINCT master_col) AS columns_tracked,
                COUNT(DISTINCT cohort) AS cohorts
            FROM harmonization_provenance
        """)).fetchone()

        by_tier = db.execute(text("""
            SELECT tier, validation_status, COUNT(*) AS cnt
            FROM harmonization_provenance
            GROUP BY tier, validation_status
            ORDER BY tier, validation_status
        """)).fetchall()

        top_failures = db.execute(text("""
            SELECT master_col, validation_reason, COUNT(*) AS cnt
            FROM harmonization_provenance
            WHERE validation_status = 'FAIL'
            GROUP BY master_col, validation_reason
            ORDER BY cnt DESC
            LIMIT 20
        """)).fetchall()

        return {
            "success": True,
            "data": {
                "total_records": result[0] or 0,
                "pass_count": result[1] or 0,
                "fail_count": result[2] or 0,
                "columns_tracked": result[3] or 0,
                "cohorts": result[4] or 0,
                "by_tier": [
                    {"tier": r[0], "status": r[1], "count": r[2]}
                    for r in by_tier
                ],
                "top_failures": [
                    {"master_col": r[0], "reason": r[1], "count": r[2]}
                    for r in top_failures
                ],
            },
        }
    except Exception as e:
        logger.error(f"Provenance summary failed: {e}")
        return {"success": False, "error": str(e)}


@router.get("/comparability")
async def comparability_report(db=Depends(get_db)):
    """Return the cohort comparability analysis report."""
    try:
        if not _table_exists(db, "comparability_report"):
            return {"success": True, "data": {}}

        row = db.execute(text(
            "SELECT report FROM comparability_report ORDER BY created_at DESC LIMIT 1"
        )).fetchone()

        if not row:
            return {"success": True, "data": {}}

        return {"success": True, "data": row[0]}
    except Exception as e:
        logger.error(f"Comparability report query failed: {e}")
        return {"success": False, "error": str(e)}


@router.get("/dictionary")
async def data_dictionary(db=Depends(get_db)):
    """Return a data dictionary built from the _schema_registry and harmonization_tiers tables."""
    try:
        if not _table_exists(db, "_schema_registry"):
            return {"success": True, "data": []}

        rows = db.execute(text(
            "SELECT sr.master_col, sr.data_type, sr.bhs_col, sr.ehvol_col, "
            "       ht.tier, ht.unit, ht.loinc, ht.snomed, ht.phenotype_definition, "
            "       ht.allowable_range "
            "FROM _schema_registry sr "
            "LEFT JOIN harmonization_tiers ht ON ht.master_col = sr.master_col "
            "ORDER BY COALESCE(ht.tier, 99), sr.master_col"
        )).fetchall()

        data = [
            {
                "master_col": r[0],
                "data_type": r[1],
                "bhs_source": r[2] or "",
                "ehvol_source": r[3] or "",
                "tier": r[4] or "",
                "unit": r[5] or "",
                "loinc": r[6] or "",
                "snomed": r[7] or "",
                "phenotype_definition": r[8] or "",
                "allowable_range": r[9] or "",
            }
            for r in rows
        ]

        return {"success": True, "data": data, "total": len(data)}
    except Exception as e:
        logger.error(f"Data dictionary query failed: {e}")
        return {"success": False, "error": str(e)}


@router.get("/export")
async def export_harmonization(
    format: str = Query("csv", description="Export format: csv"),
    db=Depends(get_db),
):
    """Export harmonization tiers as a downloadable CSV."""
    try:
        if not _table_exists(db, "harmonization_tiers"):
            return {"success": False, "error": "harmonization_tiers table not found"}

        rows = db.execute(text(
            "SELECT master_col, tier, data_type, unit, transform, "
            "       loinc, snomed, phenotype_definition, timing_window, "
            "       allowable_range, fill_rate "
            "FROM harmonization_tiers ORDER BY tier, master_col"
        )).fetchall()

        columns = [
            "master_col", "tier", "data_type", "unit", "transform",
            "loinc", "snomed", "phenotype_definition", "timing_window",
            "allowable_range", "fill_rate",
        ]

        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(columns)
        for r in rows:
            writer.writerow(list(r))

        buf.seek(0)
        return StreamingResponse(
            iter([buf.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=harmonization_tiers.csv"},
        )
    except Exception as e:
        logger.error(f"Harmonization export failed: {e}")
        return {"success": False, "error": str(e)}
