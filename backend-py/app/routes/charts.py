from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import text
from app.database import get_db
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

ALLOWED_FIELDS = {
    # Demographics
    "age",
    "gender",
    "nationality",
    # Vitals / physical
    "bmi",
    "systolic_bp",
    "diastolic_bp",
    "heart_rate",
    # Labs
    "hba1c",
    "troponin_i",
    # Imaging
    "echo_ef",
    "mri_ef",
    "ef",
    "lv_ejection_fraction",
    "lv_mass",
    "lv_edv",
    "lv_esv",
    "rv_ef",
    "smoking_years",
    # Geographic
    "current_city_category",
    "childhood_city_category",
    "migration_pattern",
    # Flags
    "has_echo",
    "has_mri",
    "data_completeness",
}

NUMERIC_FIELDS = {
    "age",
    "bmi",
    "systolic_bp",
    "diastolic_bp",
    "heart_rate",
    "hba1c",
    "troponin_i",
    "echo_ef",
    "mri_ef",
    "ef",
    "lv_ejection_fraction",
    "lv_mass",
    "lv_edv",
    "lv_esv",
    "rv_ef",
    "smoking_years",
    "data_completeness",
}


def _validate_field(field: str) -> str:
    if field not in ALLOWED_FIELDS:
        raise HTTPException(status_code=400, detail=f"Unsupported field: {field}")
    return field

def _validate_aggregation(aggregation: str) -> str:
    allowed = {"count", "avg", "sum", "min", "max"}
    if aggregation not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported aggregation: {aggregation}")
    return aggregation

def _build_base_where(x_axis: str, y_axis: str | None, group_by: str | None, aggregation: str) -> str:
    clauses = [f"{x_axis} IS NOT NULL"]
    if group_by:
        clauses.append(f"{group_by} IS NOT NULL")
    if aggregation != "count" and y_axis:
        clauses.append(f"{y_axis} IS NOT NULL")
    return " AND ".join(clauses)

@router.get("/correlation")
async def get_correlation(
    field1: str = Query(..., description="First field for correlation"),
    field2: str = Query(..., description="Second field for correlation"),
    db = Depends(get_db)
):
    """Get correlation data between two numeric fields"""
    try:
        f1 = _validate_field(field1)
        f2 = _validate_field(field2)

        stmt = text(f"""
            SELECT
                dna_id,
                {f1} AS {f1},
                {f2} AS {f2}
            FROM patient_summary
            WHERE {f1} IS NOT NULL AND {f2} IS NOT NULL
            LIMIT 500
        """)

        result = db.execute(stmt).mappings().fetchall()
        
        return {
            "success": True,
            "data": [dict(row) for row in result]
        }
    except Exception as e:
        logger.error(f"Error fetching correlation data: {e}")
        return {"success": False, "error": str(e)}


@router.get("/data")
async def get_chart_data(
    xAxis: str = Query(..., alias="xAxis"),
    yAxis: str = Query(None, alias="yAxis"),
    groupBy: str = Query(None, alias="groupBy"),
    aggregation: str = Query("count"),
    db = Depends(get_db)
):
    """Get chart data with flexible parameters"""
    try:
        xAxis = _validate_field(xAxis)
        if yAxis:
            yAxis = _validate_field(yAxis)
        if groupBy:
            groupBy = _validate_field(groupBy)

        # For simple aggregations, use patient_summary view
        if aggregation == "count" and groupBy:
            stmt = text(f"""
                SELECT {groupBy} as label, COUNT(*) as value
                FROM patient_summary
                WHERE {groupBy} IS NOT NULL
                GROUP BY {groupBy}
                ORDER BY value DESC
                LIMIT 20
            """)
        elif yAxis and aggregation in ["avg", "sum", "min", "max"]:
            agg_func = aggregation.upper()
            stmt = text(f"""
                SELECT {xAxis} as x, {agg_func}({yAxis}) as y
                FROM patient_summary
                WHERE {xAxis} IS NOT NULL AND {yAxis} IS NOT NULL
                GROUP BY {xAxis}
                ORDER BY {xAxis}
            """)
        else:
            stmt = text(f"""
                SELECT {xAxis} as label, COUNT(*) as value
                FROM patient_summary
                WHERE {xAxis} IS NOT NULL
                GROUP BY {xAxis}
                ORDER BY value DESC
                LIMIT 20
            """)
        
        result = db.execute(stmt).mappings().fetchall()
        
        return {
            "success": True,
            "data": [dict(row) for row in result]
        }
    except Exception as e:
        logger.error(f"Error fetching chart data: {e}")
        return {"success": False, "error": str(e)}


@router.get("/series")
async def get_chart_series(
    xAxis: str = Query(..., alias="xAxis"),
    yAxis: str = Query(None, alias="yAxis"),
    groupBy: str = Query(None, alias="groupBy"),
    aggregation: str = Query("count"),
    bins: int = Query(8, ge=2, le=50),
    limit: int = Query(60, ge=5, le=200),
    db = Depends(get_db)
):
    """Get chart series data for rich visualizations"""
    try:
        x_axis = _validate_field(xAxis)
        y_axis = _validate_field(yAxis) if yAxis else None
        group_by = _validate_field(groupBy) if groupBy else None
        aggregation = _validate_aggregation(aggregation)

        if aggregation != "count" and not y_axis:
            raise HTTPException(status_code=400, detail="yAxis is required for aggregation")

        base_where = _build_base_where(x_axis, y_axis, group_by, aggregation)
        group_select = f", {group_by} as series" if group_by else ""
        group_group = f", {group_by}" if group_by else ""

        if x_axis in NUMERIC_FIELDS:
            y_value_select = f", {y_axis} as y_value" if aggregation != "count" and y_axis else ""
            if aggregation == "count":
                agg_select = "COUNT(*)"
            else:
                agg_func = aggregation.upper()
                agg_select = f"{agg_func}(y_value)"

            stmt = text(f"""
                WITH stats AS (
                    SELECT MIN({x_axis}) AS min_x, MAX({x_axis}) AS max_x
                    FROM patient_summary
                    WHERE {base_where}
                ),
                binned AS (
                    SELECT
                        CASE
                            WHEN stats.min_x = stats.max_x THEN 1
                            ELSE width_bucket({x_axis}, stats.min_x, stats.max_x, :bins)
                        END AS bin,
                        stats.min_x AS min_x,
                        stats.max_x AS max_x
                        {group_select}
                        {y_value_select}
                    FROM patient_summary, stats
                    WHERE {base_where}
                )
                SELECT
                    bin,
                    min_x,
                    max_x
                    {group_select},
                    {agg_select} AS value
                FROM binned
                GROUP BY bin, min_x, max_x{group_group}
                ORDER BY bin
            """)

            result = db.execute(stmt, {"bins": bins}).mappings().fetchall()
            rows = []
            for row in result:
                min_x = row.get("min_x")
                max_x = row.get("max_x")
                bin_index = row.get("bin") or 1
                if min_x is None or max_x is None:
                    continue
                if min_x == max_x:
                    label = f"{round(min_x, 2)}"
                else:
                    bin_size = (max_x - min_x) / bins
                    start = min_x + (bin_index - 1) * bin_size
                    end = min_x + bin_index * bin_size
                    label = f"{round(start, 2)}–{round(end, 2)}"

                rows.append({
                    "label": label,
                    "value": float(row.get("value") or 0),
                    "series": row.get("series") if group_by else None,
                })

            return {"success": True, "data": rows}

        if aggregation == "count":
            agg_select = "COUNT(*)"
        else:
            agg_func = aggregation.upper()
            agg_select = f"{agg_func}({y_axis})"

        stmt = text(f"""
            SELECT {x_axis} as label{group_select}, {agg_select} as value
            FROM patient_summary
            WHERE {base_where}
            GROUP BY {x_axis}{group_group}
            ORDER BY value DESC
            LIMIT :limit
        """)

        result = db.execute(stmt, {"limit": limit}).mappings().fetchall()
        return {
            "success": True,
            "data": [
                {
                    "label": row.get("label"),
                    "value": float(row.get("value") or 0),
                    "series": row.get("series") if group_by else None,
                }
                for row in result
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching chart series: {e}")
        return {"success": False, "error": str(e)}


@router.get("/fields")
async def get_chart_fields():
    """Get available fields for charts"""
    return {
        "success": True,
        "data": {
            "numeric": [
                {"name": "age", "label": "Age", "category": "Demographics"},
                {"name": "bmi", "label": "BMI", "category": "Physical"},
                {"name": "systolic_bp", "label": "Systolic BP", "category": "Physical"},
                {"name": "diastolic_bp", "label": "Diastolic BP", "category": "Physical"},
                {"name": "heart_rate", "label": "Heart Rate", "category": "Physical"},
                {"name": "hba1c", "label": "HbA1c", "category": "Labs"},
                {"name": "troponin_i", "label": "Troponin I", "category": "Labs"},
                {"name": "ef", "label": "Echo EF", "category": "Imaging"},
                {"name": "lv_ejection_fraction", "label": "LV EF (MRI)", "category": "Imaging"},
                {"name": "lv_mass", "label": "LV Mass", "category": "Imaging"},
            ],
            "categorical": [
                {"name": "gender", "label": "Gender", "category": "Demographics"},
                {"name": "nationality", "label": "Nationality", "category": "Demographics"},
                {"name": "current_city_category", "label": "City Category", "category": "Geographic"},
                {"name": "migration_pattern", "label": "Migration Pattern", "category": "Geographic"},
            ]
        }
    }


@router.post("/generate")
async def generate_chart(config: dict, db = Depends(get_db)):
    """Generate chart data based on configuration"""
    try:
        chart_type = config.get("type", "bar")
        x_field = config.get("xField", "age")
        y_field = config.get("yField")
        group_by = config.get("groupBy")
        
        if chart_type == "scatter" and y_field:
            stmt = text(f"""
                SELECT {x_field} as x, {y_field} as y
                FROM patient_summary
                WHERE {x_field} IS NOT NULL AND {y_field} IS NOT NULL
                LIMIT 500
            """)
        elif chart_type == "bar":
            stmt = text(f"""
                SELECT {x_field} as label, COUNT(*) as value
                FROM patient_summary
                WHERE {x_field} IS NOT NULL
                GROUP BY {x_field}
                ORDER BY value DESC
                LIMIT 20
            """)
        else:
            stmt = text(f"""
                SELECT {x_field} as x, COUNT(*) as y
                FROM patient_summary
                WHERE {x_field} IS NOT NULL
                GROUP BY {x_field}
                ORDER BY {x_field}
            """)
        
        result = db.execute(stmt).mappings().fetchall()
        
        return {
            "success": True,
            "data": [dict(row) for row in result]
        }
    except Exception as e:
        logger.error(f"Error generating chart: {e}")
        return {"success": False, "error": str(e)}
