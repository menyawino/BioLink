from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from app.database import get_db
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Field mapping for database columns
FIELD_MAP = {
    "age": ("patients", "age"),
    "bmi": ("physical_examinations", "bmi"),
    "systolic_bp": ("physical_examinations", "systolic_bp"),
    "diastolic_bp": ("physical_examinations", "diastolic_bp"),
    "heart_rate": ("physical_examinations", "heart_rate"),
    "hba1c": ("lab_results", "hba1c"),
    "ef": ("echo_data", "ef"),
    "echo_ef": ("echo_data", "ef"),
    "troponin_i": ("lab_results", "troponin_i"),
    "lv_ejection_fraction": ("mri_data", "lv_ejection_fraction"),
    "lv_mass": ("mri_data", "lv_mass"),
    "lv_edv": ("mri_data", "lv_end_diastolic_volume"),
    "lv_esv": ("mri_data", "lv_end_systolic_volume"),
    "rv_ef": ("mri_data", "rv_ejection_fraction"),
    "weight": ("physical_examinations", "weight_kg"),
    "height": ("physical_examinations", "height_cm"),
}

@router.get("/correlation")
async def get_correlation(
    field1: str = Query(..., description="First field for correlation"),
    field2: str = Query(..., description="Second field for correlation"),
    db = Depends(get_db)
):
    """Get correlation data between two numeric fields"""
    try:
        # Get table and column info for each field
        f1_info = FIELD_MAP.get(field1, ("patient_summary", field1))
        f2_info = FIELD_MAP.get(field2, ("patient_summary", field2))
        
        # Build a query using patient_summary view which has all joined data
        stmt = text(f"""
            SELECT 
                ps.dna_id,
                ps.age,
                ps.gender,
                pe.bmi,
                pe.systolic_bp,
                pe.diastolic_bp,
                pe.heart_rate,
                pe.weight_kg as weight,
                pe.height_cm as height,
                lr.hba1c,
                lr.troponin_i,
                ed.ef,
                md.lv_ejection_fraction,
                md.lv_mass,
                md.lv_end_diastolic_volume as lv_edv,
                md.lv_end_systolic_volume as lv_esv,
                md.rv_ejection_fraction as rv_ef
            FROM patients ps
            LEFT JOIN physical_examinations pe ON ps.id = pe.patient_id
            LEFT JOIN lab_results lr ON ps.id = lr.patient_id
            LEFT JOIN echo_data ed ON ps.id = ed.patient_id
            LEFT JOIN mri_data md ON ps.id = md.patient_id
            WHERE ps.age IS NOT NULL
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
