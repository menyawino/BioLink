from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from app.database import get_db
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

ALLOWED_DATASETS = {"all", "ehvol", "bhs"}
DATASET_TABLES = {"ehvol": "ehvol_participants", "bhs": "bhs_participants"}
COMPLETENESS_EXPR = "((CASE WHEN heart_rate IS NOT NULL THEN 20 ELSE 0 END) + (CASE WHEN systolic_bp IS NOT NULL THEN 20 ELSE 0 END) + (CASE WHEN bmi IS NOT NULL THEN 20 ELSE 0 END) + (CASE WHEN echo_ef IS NOT NULL THEN 20 ELSE 0 END) + (CASE WHEN hba1c IS NOT NULL THEN 20 ELSE 0 END))"


def _dataset_key(dataset: str | None) -> str:
    normalized = (dataset or "all").lower()
    if normalized not in ALLOWED_DATASETS:
        normalized = "all"
    return normalized


def _dataset_source(dataset: str | None) -> str:
    key = _dataset_key(dataset)
    if key == "all":
        return "(SELECT * FROM ehvol_participants UNION ALL SELECT * FROM bhs_participants) registry"
    return f"{DATASET_TABLES[key]} registry"


def _mri_column_exists(db, dataset: str | None) -> bool:
    key = _dataset_key(dataset)
    table_names = [DATASET_TABLES[key]] if key in DATASET_TABLES else list(DATASET_TABLES.values())
    rows = db.execute(
        text(
            """
            SELECT table_name
            FROM information_schema.columns
            WHERE table_schema='public'
              AND column_name='mri_ef'
              AND table_name = ANY(:table_names)
            """
        ),
        {"table_names": table_names},
    ).fetchall()
    return len(rows) > 0


@router.get("/overview")
async def registry_overview(dataset: str = Query("all"), db=Depends(get_db)):
    try:
        source = _dataset_source(dataset)

        total = db.execute(text(f"SELECT COUNT(*) FROM {source}")).scalar() or 0
        male = (
            db.execute(
                text(
                    f"SELECT COUNT(*) FROM {source} WHERE LOWER(gender) IN ('male','m')"
                )
            ).scalar()
            or 0
        )
        female = (
            db.execute(
                text(
                    f"SELECT COUNT(*) FROM {source} WHERE LOWER(gender) IN ('female','f')"
                )
            ).scalar()
            or 0
        )
        avg_age = db.execute(
            text(f"SELECT AVG(age) FROM {source} WHERE age IS NOT NULL")
        ).scalar()
        with_echo = (
            db.execute(
                text(f"SELECT COUNT(*) FROM {source} WHERE echo_ef IS NOT NULL")
            ).scalar()
            or 0
        )
        mri_col_exists = _mri_column_exists(db, dataset)
        if mri_col_exists:
            with_mri = (
                db.execute(
                    text(f"SELECT COUNT(*) FROM {source} WHERE mri_ef IS NOT NULL")
                ).scalar()
                or 0
            )
            with_both_echo_mri = (
                db.execute(
                    text(
                        f"SELECT COUNT(*) FROM {source} WHERE echo_ef IS NOT NULL AND mri_ef IS NOT NULL"
                    )
                ).scalar()
                or 0
            )
        else:
            with_mri = 0
            with_both_echo_mri = 0
        avg_completeness = (
            db.execute(text(f"SELECT AVG({COMPLETENESS_EXPR}) FROM {source}")).scalar()
            or 0
        )

        return {
            "success": True,
            "data": {
                "totalPatients": total,
                "maleCount": male,
                "femaleCount": female,
                "averageAge": f"{float(avg_age or 0):.1f}",
                "dataCompleteness": f"{float(avg_completeness or 0):.1f}",
                "withMri": with_mri,
                "withEcho": with_echo,
                "withBothEchoMri": with_both_echo_mri,
                "withEcg": 0,
            },
        }
    except Exception as e:
        logger.error(f"Overview analytics failed: {e}")
        return {"success": False, "error": str(e)}


@router.get("/demographics")
async def demographics(dataset: str = Query("all"), db=Depends(get_db)):
    try:
        source = _dataset_source(dataset)

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
async def clinical_metrics(dataset: str = Query("ehvol"), db=Depends(get_db)):
    try:
        return {
            "success": True,
            "data": {
                "bmiDistribution": [],
                "bpDistribution": [],
                "efDistribution": [],
                "hba1cDistribution": [],
            },
        }
    except Exception as e:
        logger.error(f"Clinical analytics failed: {e}")
        return {"success": False, "error": str(e)}


@router.get("/comorbidities")
async def comorbidities(dataset: str = Query("all"), db=Depends(get_db)):
    try:
        source = _dataset_source(dataset)

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
        source = _dataset_source(dataset)
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
        source = _dataset_source(dataset)

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
        source = _dataset_source(dataset)

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
            prevalence = min(
                25,
                hypertension_rate * 0.3
                + diabetes_rate * 0.4
                + smoking_rate * 0.2
                + (avg_age - 40) * 0.1,
            )

            governorate_data.append(
                {
                    "region": row[0],
                    "coordinates": [31.2357, 30.0444],
                    "patientCount": patient_count,
                    "prevalence": round(prevalence, 1),
                    "demographics": {
                        "averageAge": round(avg_age, 1),
                        "genderRatio": round(gender_ratio, 2),
                        "ethnicityMix": {"arab": 95, "other": 5},
                    },
                    "riskFactors": {
                        "hypertension": round(hypertension_rate, 1),
                        "diabetes": round(diabetes_rate, 1),
                        "smoking": round(smoking_rate, 1),
                        "obesity": round((row[8] or 25) - 20, 1) if row[8] else 25,
                    },
                    "outcomes": {
                        "mortality": round(prevalence * 0.05, 1),
                        "readmission": round(prevalence * 1.2, 1),
                        "complications": round(prevalence * 2.0, 1),
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
        source = _dataset_source(dataset)
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
        source = _dataset_source(dataset)

        completeness_result = db.execute(text(f"""
            SELECT
                ROUND(AVG(CASE WHEN heart_rate IS NOT NULL OR systolic_bp IS NOT NULL OR diastolic_bp IS NOT NULL THEN 100 ELSE 0 END)) as physical_exam,
                ROUND(AVG(CASE WHEN hba1c IS NOT NULL THEN 100 ELSE 0 END)) as lab_results,
                ROUND(AVG(CASE WHEN echo_ef IS NOT NULL THEN 100 ELSE 0 END)) as echo,
                0 as mri,
                0 as ecg,
                ROUND(AVG({COMPLETENESS_EXPR})) as overall
            FROM {source}
        """)).fetchone()

        distribution_results = db.execute(text(f"""
            SELECT
                CASE
                    WHEN {COMPLETENESS_EXPR} >= 80 THEN '80-100%'
                    WHEN {COMPLETENESS_EXPR} >= 60 THEN '60-79%'
                    WHEN {COMPLETENESS_EXPR} >= 40 THEN '40-59%'
                    WHEN {COMPLETENESS_EXPR} >= 20 THEN '20-39%'
                    ELSE '0-19%'
                END as completeness_range,
                COUNT(*) as count
            FROM {source}
            GROUP BY completeness_range
            ORDER BY completeness_range
        """)).fetchall()

        return {
            "success": True,
            "data": {
                "byCategory": {
                    "physical_exam": float(completeness_result[0] or 0),
                    "lab_results": float(completeness_result[1] or 0),
                    "echo": float(completeness_result[2] or 0),
                    "mri": float(completeness_result[3] or 0),
                    "ecg": float(completeness_result[4] or 0),
                    "overall": float(completeness_result[5] or 0),
                },
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
        return {
            "success": True,
            "data": {
                "echo": {
                    "avg_ef": 0,
                    "min_ef": 0,
                    "max_ef": 0,
                    "std_ef": 0,
                    "total": 0,
                },
                "mri": {"avg_lv_ef": 0, "avg_lv_mass": 0, "avg_lv_edv": 0, "total": 0},
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
