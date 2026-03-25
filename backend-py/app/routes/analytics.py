from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from app.database import get_db
from app.routes._dataset_union import aligned_union_sql
from app.routes.patients import (
    _dataset_field_exprs,
    _mri_sql_expr,
    _registry_source_table,
    _source_columns,
)
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

ALLOWED_DATASETS = {"all", "ehvol", "bhs"}
DATASET_TABLES = {"ehvol": "ehvol_participants", "bhs": "bhs_participants"}


def _validate_dataset(dataset: str) -> str:
    """Validate and normalize the dataset query parameter."""
    normalized = (dataset or "all").lower()
    if normalized not in ALLOWED_DATASETS:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid dataset '{dataset}'. Must be one of: {', '.join(sorted(ALLOWED_DATASETS))}",
        )
    return normalized


def _dataset_source(db, dataset: str | None) -> str:
    """Return the SQL source expression for the given dataset.

    Always queries the canonical participant tables (created by db_bootstrap).
    No fallback logic — if the tables are empty, endpoints return empty results.
    """
    key = _validate_dataset(dataset)
    if key == "all":
        return aligned_union_sql(db, [DATASET_TABLES["ehvol"], DATASET_TABLES["bhs"]])
    return f"{DATASET_TABLES[key]} AS registry"


def _normalized_dataset_source(db, dataset: str | None) -> str:
    source_table = _registry_source_table(db, dataset)
    columns = _source_columns(db, dataset, source_table)
    expr = _dataset_field_exprs(columns, dataset or "all")
    mri_value_expr, _ = _mri_sql_expr(columns)

    return (
        "(SELECT "
        f"CAST({expr['id_col']} AS TEXT) AS dna_id, "
        f"{expr['dataset_expr']} AS source_dataset, "
        f"{expr['age_expr']} AS age, "
        f"{expr['gender_expr']} AS gender, "
        f"{expr['nationality_expr']} AS nationality, "
        f"{expr['enrollment_expr']} AS enrollment_date, "
        f"{expr['city_expr']} AS current_city, "
        f"{expr['heart_rate_expr']} AS heart_rate, "
        f"{expr['systolic_expr']} AS systolic_bp, "
        f"{expr['diastolic_expr']} AS diastolic_bp, "
        f"{expr['bmi_expr']} AS bmi, "
        f"{expr['hba1c_expr']} AS hba1c, "
        f"{expr['echo_expr']} AS echo_ef, "
        f"{mri_value_expr} AS mri_ef, "
        f"{expr['troponin_expr']} AS troponin_i, "
        f"{expr['current_city_category_expr']} AS current_city_category "
        f"FROM {source_table}) AS registry"
    )


def _safe_column(db, table_names: list[str], column: str) -> bool:
    """Check whether *column* exists in at least one of the given tables."""
    rows = db.execute(
        text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_schema = 'public' "
            "  AND column_name = :col "
            "  AND table_name = ANY(:tables) "
            "LIMIT 1"
        ),
        {"col": column, "tables": table_names},
    ).fetchone()
    return rows is not None


@router.get("/overview")
async def registry_overview(dataset: str = Query("all"), db=Depends(get_db)):
    try:
        source = _normalized_dataset_source(db, dataset)

        result = db.execute(text(f"""
            SELECT
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE LOWER(gender) IN ('male', 'm')) AS male,
                COUNT(*) FILTER (WHERE LOWER(gender) IN ('female', 'f')) AS female,
                AVG(age) FILTER (WHERE age IS NOT NULL) AS avg_age,
                COUNT(*) FILTER (WHERE echo_ef IS NOT NULL) AS with_echo
            FROM {source}
        """)).fetchone()

        total = result[0] or 0
        mri_row = db.execute(text(f"""
            SELECT
                COUNT(*) FILTER (WHERE mri_ef IS NOT NULL),
                COUNT(*) FILTER (WHERE echo_ef IS NOT NULL AND mri_ef IS NOT NULL)
            FROM {source}
        """)).fetchone()
        with_mri = mri_row[0] or 0
        with_both = mri_row[1] or 0

        # Per-column completeness: count non-null columns per row, average across rows
        completeness_cols = [
            "heart_rate", "systolic_bp", "diastolic_bp", "bmi", "hba1c",
            "echo_ef", "age", "gender", "enrollment_date", "current_city",
        ]
        if completeness_cols:
            parts = " + ".join(
                f"CASE WHEN {c} IS NOT NULL THEN 1 ELSE 0 END" for c in completeness_cols
            )
            avg_comp = db.execute(text(
                f"SELECT AVG(({parts}) * 100.0 / {len(completeness_cols)}) FROM {source}"
            )).scalar() or 0
        else:
            avg_comp = 0

        return {
            "success": True,
            "data": {
                "totalPatients": total,
                "maleCount": result[1] or 0,
                "femaleCount": result[2] or 0,
                "averageAge": f"{float(result[3] or 0):.1f}",
                "dataCompleteness": f"{float(avg_comp):.1f}",
                "withMri": with_mri,
                "withEcho": result[4] or 0,
                "withBothEchoMri": with_both,
                "withEcg": 0,
            },
        }
    except Exception as e:
        logger.error(f"Overview analytics failed: {e}")
        return {"success": False, "error": str(e)}


@router.get("/demographics")
async def demographics(dataset: str = Query("all"), db=Depends(get_db)):
    try:
        source = _normalized_dataset_source(db, dataset)

        age_gender_results = db.execute(text(f"""
            SELECT
                CASE
                    WHEN age < 30 THEN '18-29'
                    WHEN age < 40 THEN '30-39'
                    WHEN age < 50 THEN '40-49'
                    WHEN age < 60 THEN '50-59'
                    WHEN age < 70 THEN '60-69'
                    ELSE '70+'
                END as age_group,
                COUNT(CASE WHEN LOWER(gender) IN ('male', 'm') THEN 1 END) as male,
                COUNT(CASE WHEN LOWER(gender) IN ('female', 'f') THEN 1 END) as female
            FROM {source}
            WHERE age IS NOT NULL
            GROUP BY age_group
            ORDER BY age_group
        """)).fetchall()

        nationality_results = db.execute(text(f"""
            SELECT
                CASE
                    WHEN nationality IS NULL OR BTRIM(nationality) = '' THEN 'Unknown'
                    WHEN LOWER(nationality) LIKE '%egypt%'
                      OR LOWER(nationality) LIKE '%egyption%'
                      OR LOWER(nationality) LIKE '%egyptain%'
                      OR LOWER(nationality) LIKE '%egyptien%'
                                            OR REGEXP_REPLACE(LOWER(nationality), '[^a-z]', '', 'g') IN (
                                                    'egy', 'egyp', 'egp', 'eg', 'eyp',
                                                    'egypt', 'egyptian', 'egyption', 'egyptain', 'egyptien', 'egyptient',
                                                    'egiptian', 'egeptian', 'egyept', 'egytptian', 'egytptan',
                                                    'egyptioan', 'egyptions', 'egyptianj', 'egyptians', 'egptient'
                                            )
                      OR nationality ~ 'مصر|مصري|مصرية|مصريه'
                    THEN 'Egyptian'
                    ELSE INITCAP(BTRIM(nationality))
                END AS nationality,
                COUNT(*) AS count
            FROM {source}
            GROUP BY 1
            ORDER BY count DESC
            LIMIT 12
        """)).fetchall()

        return {
            "success": True,
            "data": {
                "ageGender": [
                    {"age_group": row[0], "male": row[1], "female": row[2]}
                    for row in age_gender_results
                ],
                "nationality": [
                    {"nationality": row[0], "count": row[1]}
                    for row in nationality_results
                ],
                "maritalStatus": [],
            },
        }
    except Exception as e:
        logger.error(f"Demographics analytics failed: {e}")
        return {"success": False, "error": str(e)}


@router.get("/clinical")
async def clinical_metrics(dataset: str = Query("all"), db=Depends(get_db)):
    try:
        source = _dataset_source(db, dataset)

        bmi_rows = db.execute(text(f"""
            SELECT
                CASE
                    WHEN bmi < 18.5 THEN 'Underweight'
                    WHEN bmi < 25 THEN 'Normal'
                    WHEN bmi < 30 THEN 'Overweight'
                    ELSE 'Obese'
                END AS category,
                COUNT(*) AS count
            FROM {source}
            WHERE bmi IS NOT NULL
            GROUP BY 1
            ORDER BY 1
        """)).fetchall()

        bp_rows = db.execute(text(f"""
            SELECT
                CASE
                    WHEN systolic_bp < 120 AND diastolic_bp < 80 THEN 'Normal'
                    WHEN systolic_bp < 130 AND diastolic_bp < 80 THEN 'Elevated'
                    WHEN systolic_bp < 140 OR diastolic_bp < 90 THEN 'Stage 1 HTN'
                    ELSE 'Stage 2 HTN'
                END AS status,
                COUNT(*) AS count
            FROM {source}
            WHERE systolic_bp IS NOT NULL AND diastolic_bp IS NOT NULL
            GROUP BY 1
            ORDER BY 1
        """)).fetchall()

        ef_rows = db.execute(text(f"""
            SELECT
                CASE
                    WHEN echo_ef >= 55 THEN 'Normal (>=55%)'
                    WHEN echo_ef >= 40 THEN 'Mildly reduced (40-54%)'
                    WHEN echo_ef >= 30 THEN 'Moderately reduced (30-39%)'
                    ELSE 'Severely reduced (<30%)'
                END AS category,
                COUNT(*) AS count
            FROM {source}
            WHERE echo_ef IS NOT NULL
            GROUP BY 1
            ORDER BY 1
        """)).fetchall()

        hba1c_rows = db.execute(text(f"""
            SELECT
                CASE
                    WHEN hba1c < 5.7 THEN 'Normal (<5.7%)'
                    WHEN hba1c < 6.5 THEN 'Pre-diabetes (5.7-6.4%)'
                    ELSE 'Diabetes (>=6.5%)'
                END AS category,
                COUNT(*) AS count
            FROM {source}
            WHERE hba1c IS NOT NULL
            GROUP BY 1
            ORDER BY 1
        """)).fetchall()

        return {
            "success": True,
            "data": {
                "bmiDistribution": [{"category": r[0], "count": r[1]} for r in bmi_rows],
                "bpDistribution": [{"status": r[0], "count": r[1]} for r in bp_rows],
                "efDistribution": [{"category": r[0], "count": r[1]} for r in ef_rows],
                "hba1cDistribution": [{"category": r[0], "count": r[1]} for r in hba1c_rows],
            },
        }
    except Exception as e:
        logger.error(f"Clinical analytics failed: {e}")
        return {"success": False, "error": str(e)}


@router.get("/comorbidities")
async def comorbidities(dataset: str = Query("all"), db=Depends(get_db)):
    try:
        source = _dataset_source(db, dataset)

        row = db.execute(text(f"""
            SELECT
                COUNT(*) FILTER (WHERE COALESCE(has_hypertension, false)) AS hypertension,
                COUNT(*) FILTER (WHERE COALESCE(has_diabetes, false)) AS diabetes,
                COUNT(*) FILTER (WHERE COALESCE(has_dyslipidemia, false)) AS dyslipidemia,
                COUNT(*) FILTER (WHERE COALESCE(family_history_cad, false)) AS cad,
                COUNT(*) FILTER (WHERE COALESCE(has_heart_failure, false)) AS heart_failure
            FROM {source}
        """)).fetchone()

        distribution_results = db.execute(text(f"""
            SELECT comorbidity_count, COUNT(*) AS patient_count
            FROM (
                SELECT (
                    CASE WHEN COALESCE(has_hypertension, false) THEN 1 ELSE 0 END +
                    CASE WHEN COALESCE(has_diabetes, false) THEN 1 ELSE 0 END +
                    CASE WHEN COALESCE(has_dyslipidemia, false) THEN 1 ELSE 0 END +
                    CASE WHEN COALESCE(family_history_cad, false) THEN 1 ELSE 0 END +
                    CASE WHEN COALESCE(has_heart_failure, false) THEN 1 ELSE 0 END
                ) AS comorbidity_count
                FROM {source}
            ) c
            GROUP BY comorbidity_count
            ORDER BY comorbidity_count
        """)).fetchall()

        return {
            "success": True,
            "data": {
                "conditions": {
                    "hypertension": row[0] if row else 0,
                    "diabetes": row[1] if row else 0,
                    "dyslipidemia": row[2] if row else 0,
                    "cad": row[3] if row else 0,
                    "heart_failure": row[4] if row else 0,
                    "kidney_disease": 0,
                    "liver_disease": 0,
                    "anaemia": 0,
                },
                "comorbidityDistribution": [
                    {"comorbidities": r[0], "patients": r[1]}
                    for r in distribution_results
                ],
            },
        }
    except Exception as e:
        logger.error(f"Comorbidity analytics failed: {e}")
        return {"success": False, "error": str(e)}


@router.get("/lifestyle")
async def lifestyle(dataset: str = Query("all"), db=Depends(get_db)):
    try:
        source = _dataset_source(db, dataset)
        smoking_result = db.execute(text(f"""
            SELECT
                COUNT(*) FILTER (WHERE COALESCE(is_smoker, false)) AS current_smokers,
                0 AS former_smokers,
                COUNT(*) FILTER (WHERE NOT COALESCE(is_smoker, false)) AS never_smoked
            FROM {source}
        """)).fetchone()

        return {
            "success": True,
            "data": {
                "smoking": {
                    "current_smokers": smoking_result[0] or 0,
                    "former_smokers": smoking_result[1] or 0,
                    "never_smoked": smoking_result[2] or 0,
                },
                "smokingDuration": [],
            },
        }
    except Exception as e:
        logger.error(f"Lifestyle analytics failed: {e}")
        return {"success": False, "error": str(e)}


@router.get("/geographic")
async def geographic(dataset: str = Query("all"), db=Depends(get_db)):
    try:
        source = _dataset_source(db, dataset)

        city_results = db.execute(text(f"""
            SELECT current_city, COUNT(*) as count
            FROM {source}
            WHERE current_city IS NOT NULL AND current_city != ''
            GROUP BY current_city
            ORDER BY count DESC
            LIMIT 10
        """)).fetchall()

        return {
            "success": True,
            "data": {
                "cityCategory": [],
                "migration": [],
                "cityDistribution": [
                    {"city": row[0], "count": row[1]} for row in city_results
                ],
            },
        }
    except Exception as e:
        logger.error(f"Geographic analytics failed: {e}")
        return {"success": False, "error": str(e)}


@router.get("/geographic-governorates")
async def geographic_governorates(dataset: str = Query("all"), db=Depends(get_db)):
    try:
        source = _dataset_source(db, dataset)

        results = db.execute(text(f"""
            SELECT current_city as governorate,
                   COUNT(*) as patient_count,
                   AVG(age) as avg_age,
                   COUNT(CASE WHEN LOWER(gender) IN ('male','m') THEN 1 END) as male_count,
                   COUNT(CASE WHEN LOWER(gender) IN ('female','f') THEN 1 END) as female_count,
                   COUNT(CASE WHEN COALESCE(has_hypertension, false) THEN 1 END) as hypertension_count,
                   COUNT(CASE WHEN COALESCE(has_diabetes, false) THEN 1 END) as diabetes_count,
                   COUNT(CASE WHEN COALESCE(is_smoker, false) THEN 1 END) as smoking_count,
                   AVG(bmi) as avg_bmi,
                   AVG(systolic_bp) as avg_systolic_bp,
                   AVG(hba1c) as avg_hba1c
            FROM {source}
            WHERE current_city IS NOT NULL AND current_city != ''
            GROUP BY current_city
            ORDER BY patient_count DESC
            LIMIT 50
        """)).fetchall()

        governorate_data = []
        for row in results:
            patient_count = row[1] or 0
            avg_age = float(row[2]) if row[2] else 0
            male_count = row[3] or 0
            female_count = row[4] or 0
            total_gender = male_count + female_count
            gender_ratio = male_count / total_gender if total_gender > 0 else 0
            hypertension_rate = (
                (row[5] or 0) / patient_count * 100 if patient_count > 0 else 0
            )
            diabetes_rate = (
                (row[6] or 0) / patient_count * 100 if patient_count > 0 else 0
            )
            smoking_rate = (
                (row[7] or 0) / patient_count * 100 if patient_count > 0 else 0
            )
            avg_bmi = float(row[8]) if row[8] else None
            obesity_rate = (
                round(avg_bmi - 25, 1) if avg_bmi and avg_bmi > 25 else 0
            )

            governorate_data.append(
                {
                    "region": row[0],
                    "patientCount": patient_count,
                    "demographics": {
                        "averageAge": round(avg_age, 1),
                        "genderRatio": round(gender_ratio, 2),
                    },
                    "riskFactors": {
                        "hypertension": round(hypertension_rate, 1),
                        "diabetes": round(diabetes_rate, 1),
                        "smoking": round(smoking_rate, 1),
                        "obesity": obesity_rate,
                    },
                    "vitals": {
                        "avgBmi": round(avg_bmi, 1) if avg_bmi else None,
                        "avgSystolicBp": round(float(row[9]), 1) if row[9] else None,
                        "avgHba1c": round(float(row[10]), 1) if row[10] else None,
                    },
                }
            )

        return {"success": True, "data": governorate_data}
    except Exception as e:
        logger.error(f"Governorate geographic analytics failed: {e}")
        return {"success": False, "error": str(e)}


@router.get("/enrollment-trends")
async def enrollment_trends(dataset: str = Query("all"), db=Depends(get_db)):
    try:
        source = _dataset_source(db, dataset)
        rows = db.execute(text(f"""
            SELECT DATE_TRUNC('month', enrollment_date) as month, COUNT(*) as enrolled
            FROM {source}
            WHERE enrollment_date IS NOT NULL
              AND enrollment_date >= DATE '1900-01-01'
              AND enrollment_date < (CURRENT_DATE + INTERVAL '1 year')
            GROUP BY DATE_TRUNC('month', enrollment_date)
            ORDER BY month
        """)).fetchall()

        cumulative = 0
        data = []
        for row in rows:
            cumulative += row[1]
            data.append(
                {
                    "month": row[0].strftime("%Y-%m") if row[0] else "Unknown",
                    "enrolled": row[1],
                    "cumulative": cumulative,
                }
            )

        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"Enrollment trends analytics failed: {e}")
        return {"success": False, "error": str(e)}


@router.get("/data-quality")
async def data_quality(dataset: str = Query("all"), db=Depends(get_db)):
    try:
        source = _dataset_source(db, dataset)
        tables = list(DATASET_TABLES.values())

        # Per-category completeness using actual column availability
        physical_cols = [c for c in ["heart_rate", "systolic_bp", "diastolic_bp", "height_cm", "weight_kg", "bmi"] if _safe_column(db, tables, c)]
        lab_cols = [c for c in ["hba1c", "troponin_i"] if _safe_column(db, tables, c)]
        echo_cols = [c for c in ["echo_ef"] if _safe_column(db, tables, c)]
        mri_cols = [c for c in ["mri_ef"] if _safe_column(db, tables, c)]

        def _avg_completeness(cols: list[str]) -> float:
            if not cols:
                return 0.0
            parts = " + ".join(f"CASE WHEN {c} IS NOT NULL THEN 1 ELSE 0 END" for c in cols)
            val = db.execute(text(f"SELECT AVG(({parts}) * 100.0 / {len(cols)}) FROM {source}")).scalar()
            return float(val or 0)

        cat = {
            "physical_exam": round(_avg_completeness(physical_cols), 1),
            "lab_results": round(_avg_completeness(lab_cols), 1),
            "echo": round(_avg_completeness(echo_cols), 1),
            "mri": round(_avg_completeness(mri_cols), 1),
            "ecg": 0.0,
        }
        all_cols = physical_cols + lab_cols + echo_cols + mri_cols
        cat["overall"] = round(_avg_completeness(all_cols), 1) if all_cols else 0.0

        # Completeness distribution
        if all_cols:
            parts = " + ".join(f"CASE WHEN {c} IS NOT NULL THEN 1 ELSE 0 END" for c in all_cols)
            expr = f"({parts}) * 100.0 / {len(all_cols)}"
            distribution_results = db.execute(text(f"""
                SELECT
                    CASE
                        WHEN {expr} >= 80 THEN '80-100%'
                        WHEN {expr} >= 60 THEN '60-79%'
                        WHEN {expr} >= 40 THEN '40-59%'
                        WHEN {expr} >= 20 THEN '20-39%'
                        ELSE '0-19%'
                    END AS completeness_range,
                    COUNT(*) AS count
                FROM {source}
                GROUP BY 1 ORDER BY 1
            """)).fetchall()
        else:
            distribution_results = []

        # Per-variable completeness
        per_variable = []
        total_row = db.execute(text(f"SELECT COUNT(*) FROM {source}")).scalar() or 0
        for col in all_cols:
            non_null = db.execute(
                text(f"SELECT COUNT(*) FROM {source} WHERE {col} IS NOT NULL")
            ).scalar() or 0
            pct = round(non_null / total_row * 100, 1) if total_row > 0 else 0.0
            per_variable.append({"variable": col, "filled": non_null, "total": total_row, "percent": pct})

        return {
            "success": True,
            "data": {
                "byCategory": cat,
                "perVariable": per_variable,
                "distribution": [
                    {"range": r[0], "count": r[1]} for r in distribution_results
                ],
            },
        }
    except Exception as e:
        logger.error(f"Data quality analytics failed: {e}")
        return {"success": False, "error": str(e)}


@router.get("/imaging")
async def imaging(dataset: str = Query("all"), db=Depends(get_db)):
    try:
        source = _dataset_source(db, dataset)
        tables = list(DATASET_TABLES.values())

        echo_row = db.execute(text(f"""
            SELECT
                ROUND(AVG(echo_ef)::numeric, 1),
                ROUND(MIN(echo_ef)::numeric, 1),
                ROUND(MAX(echo_ef)::numeric, 1),
                ROUND(STDDEV(echo_ef)::numeric, 1),
                COUNT(*) FILTER (WHERE echo_ef IS NOT NULL)
            FROM {source}
        """)).fetchone()

        mri_data = {"avg_lv_ef": 0, "avg_lv_mass": 0, "avg_lv_edv": 0, "total": 0}
        if _safe_column(db, tables, "mri_ef"):
            mri_row = db.execute(text(f"""
                SELECT
                    ROUND(AVG(mri_ef)::numeric, 1),
                    COUNT(*) FILTER (WHERE mri_ef IS NOT NULL)
                FROM {source}
            """)).fetchone()
            mri_data["avg_lv_ef"] = float(mri_row[0] or 0)
            mri_data["total"] = mri_row[1] or 0

        return {
            "success": True,
            "data": {
                "echo": {
                    "avg_ef": float(echo_row[0] or 0),
                    "min_ef": float(echo_row[1] or 0),
                    "max_ef": float(echo_row[2] or 0),
                    "std_ef": float(echo_row[3] or 0),
                    "total": echo_row[4] or 0,
                },
                "mri": mri_data,
            },
        }
    except Exception as e:
        logger.error(f"Imaging analytics failed: {e}")
        return {"success": False, "error": str(e)}


@router.get("/ecg")
async def ecg(dataset: str = Query("all"), db=Depends(get_db)):
    try:
        return {
            "success": True,
            "data": {
                "conclusions": [],
                "abnormalities": {"p_wave": 0, "qrs": 0, "st_segment": 0, "t_wave": 0},
                "rhythmDistribution": [],
            },
        }
    except Exception as e:
        logger.error(f"ECG analytics failed: {e}")
        return {"success": False, "error": str(e)}
