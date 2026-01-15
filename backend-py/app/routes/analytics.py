from fastapi import APIRouter, Depends
from sqlalchemy import text
from app.database import get_db
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/overview")
async def registry_overview(db=Depends(get_db)):
    """Basic registry overview counts; falls back to zeros when data is missing."""
    try:
        # Get total patients
        total = db.execute(text("SELECT COUNT(*) FROM patients")).scalar() or 0

        # Get gender counts
        male = db.execute(text("SELECT COUNT(*) FROM patients WHERE LOWER(gender) = 'male' OR LOWER(gender) = 'm'")).scalar() or 0
        female = db.execute(text("SELECT COUNT(*) FROM patients WHERE LOWER(gender) = 'female' OR LOWER(gender) = 'f'")).scalar() or 0

        # Get average age
        avg_age = db.execute(text("SELECT AVG(age) FROM patients WHERE age IS NOT NULL")).scalar()
        avg_age_val = float(avg_age) if avg_age is not None else 0.0

        # Get patients with imaging data
        with_echo = db.execute(text("SELECT COUNT(*) FROM patients WHERE dna_id IN (SELECT dna_id FROM echo WHERE ef IS NOT NULL)")).scalar() or 0
        with_mri = db.execute(text("SELECT COUNT(*) FROM patients WHERE dna_id IN (SELECT dna_id FROM mri WHERE lv_ejection_fraction IS NOT NULL)")).scalar() or 0
        with_ecg = db.execute(text("SELECT COUNT(*) FROM patients WHERE dna_id IN (SELECT dna_id FROM ecg WHERE conclusion IS NOT NULL)")).scalar() or 0

        # Calculate average data completeness
        completeness_result = db.execute(text("""
            SELECT AVG(data_completeness) as avg_completeness
            FROM (
                SELECT
                    COALESCE((
                        (CASE WHEN heart_rate IS NOT NULL THEN 20 ELSE 0 END) +
                        (CASE WHEN systolic_bp IS NOT NULL THEN 20 ELSE 0 END) +
                        (CASE WHEN bmi IS NOT NULL THEN 20 ELSE 0 END) +
                        (CASE WHEN echo_ef IS NOT NULL THEN 20 ELSE 0 END) +
                        (CASE WHEN mri_ef IS NOT NULL THEN 20 ELSE 0 END)
                    ), 0) as data_completeness
                FROM patient_summary
            ) as completeness_scores
        """)).scalar()
        avg_completeness = float(completeness_result) if completeness_result is not None else 0.0

        data = {
            "totalPatients": total,
            "maleCount": male,
            "femaleCount": female,
            "averageAge": f"{avg_age_val:.1f}",
            "dataCompleteness": f"{avg_completeness:.1f}",
            "withMri": with_mri,
            "withEcho": with_echo,
            "withEcg": with_ecg,
        }
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"Overview analytics failed: {e}")
        return {"success": False, "error": str(e)}


@router.get("/demographics")
async def demographics(db=Depends(get_db)):
    """Return demographic breakdown with real data from database."""
    try:
        # Age-gender distribution
        age_gender_query = text("""
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
            FROM patients
            WHERE age IS NOT NULL
            GROUP BY age_group
            ORDER BY age_group
        """)
        age_gender_results = db.execute(age_gender_query).fetchall()
        age_gender_data = [
            {"age_group": row[0], "male": row[1], "female": row[2]}
            for row in age_gender_results
        ]

        # Nationality distribution
        nationality_query = text("""
            SELECT nationality, COUNT(*) as count
            FROM patients
            WHERE nationality IS NOT NULL AND nationality != ''
            GROUP BY nationality
            ORDER BY count DESC
            LIMIT 10
        """)
        nationality_results = db.execute(nationality_query).fetchall()
        nationality_data = [
            {"nationality": row[0], "count": row[1]}
            for row in nationality_results
        ]

        return {
            "success": True,
            "data": {
                "ageGender": age_gender_data,
                "nationality": nationality_data,
                "maritalStatus": [],  # Not implemented yet
            },
        }
    except Exception as e:
        logger.error(f"Demographics analytics failed: {e}")
        return {"success": False, "error": str(e)}


@router.get("/clinical")
async def clinical_metrics(db=Depends(get_db)):
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
async def comorbidities(db=Depends(get_db)):
    try:
        # Count comorbidities from medical data
        comorbidity_query = text("""
            SELECT
                COUNT(CASE WHEN high_blood_pressure THEN 1 END) as hypertension,
                COUNT(CASE WHEN diabetes_mellitus THEN 1 END) as diabetes,
                COUNT(CASE WHEN dyslipidemia THEN 1 END) as dyslipidemia,
                COUNT(CASE WHEN heart_attack_or_angina THEN 1 END) as cad,
                COUNT(CASE WHEN prior_heart_failure THEN 1 END) as heart_failure,
                COUNT(CASE WHEN kidney_problems THEN 1 END) as kidney_disease,
                COUNT(CASE WHEN liver_problems THEN 1 END) as liver_disease,
                COUNT(CASE WHEN anaemia THEN 1 END) as anaemia
            FROM medical
        """)
        comorbidity_result = db.execute(comorbidity_query).fetchone()

        # Comorbidity distribution (patients with 0, 1, 2, 3+ conditions)
        distribution_query = text("""
            SELECT
                comorbidity_count,
                COUNT(*) as patient_count
            FROM (
                SELECT
                    (CASE WHEN high_blood_pressure THEN 1 ELSE 0 END +
                     CASE WHEN diabetes_mellitus THEN 1 ELSE 0 END +
                     CASE WHEN dyslipidemia THEN 1 ELSE 0 END +
                     CASE WHEN heart_attack_or_angina THEN 1 ELSE 0 END +
                     CASE WHEN prior_heart_failure THEN 1 ELSE 0 END +
                     CASE WHEN kidney_problems THEN 1 ELSE 0 END +
                     CASE WHEN liver_problems THEN 1 ELSE 0 END +
                     CASE WHEN anaemia THEN 1 ELSE 0 END) as comorbidity_count
                FROM medical
            ) as comorbidity_counts
            GROUP BY comorbidity_count
            ORDER BY comorbidity_count
        """)
        distribution_results = db.execute(distribution_query).fetchall()
        distribution_data = [
            {"comorbidities": row[0], "patients": row[1]}
            for row in distribution_results
        ]

        return {
            "success": True,
            "data": {
                "conditions": {
                    "hypertension": comorbidity_result[0] or 0,
                    "diabetes": comorbidity_result[1] or 0,
                    "dyslipidemia": comorbidity_result[2] or 0,
                    "cad": comorbidity_result[3] or 0,
                    "heart_failure": comorbidity_result[4] or 0,
                    "kidney_disease": comorbidity_result[5] or 0,
                    "liver_disease": comorbidity_result[6] or 0,
                    "anaemia": comorbidity_result[7] or 0,
                },
                "comorbidityDistribution": distribution_data,
            },
        }
    except Exception as e:
        logger.error(f"Comorbidity analytics failed: {e}")
        return {"success": False, "error": str(e)}


@router.get("/lifestyle")
async def lifestyle(db=Depends(get_db)):
    try:
        # Smoking statistics
        smoking_query = text("""
            SELECT
                COUNT(CASE WHEN current_smoker THEN 1 END) as current_smokers,
                COUNT(CASE WHEN former_smoker THEN 1 END) as former_smokers,
                COUNT(CASE WHEN NOT current_smoker AND NOT former_smoker THEN 1 END) as never_smoked
            FROM lifestyle
        """)
        smoking_result = db.execute(smoking_query).fetchone()

        # Smoking duration distribution for current smokers
        duration_query = text("""
            SELECT smoking_duration_years, COUNT(*) as count
            FROM lifestyle
            WHERE current_smoker AND smoking_duration_years IS NOT NULL
            GROUP BY smoking_duration_years
            ORDER BY smoking_duration_years
        """)
        duration_results = db.execute(duration_query).fetchall()
        duration_data = [
            {"years": row[0], "count": row[1]}
            for row in duration_results
        ]

        return {
            "success": True,
            "data": {
                "smoking": {
                    "current_smokers": smoking_result[0] or 0,
                    "former_smokers": smoking_result[1] or 0,
                    "never_smoked": smoking_result[2] or 0,
                },
                "smokingDuration": duration_data,
            },
        }
    except Exception as e:
        logger.error(f"Lifestyle analytics failed: {e}")
        return {"success": False, "error": str(e)}


@router.get("/geographic")
async def geographic(db=Depends(get_db)):
    try:
        # City category distribution
        city_category_query = text("""
            SELECT current_city_category, COUNT(*) as count
            FROM patient_summary
            WHERE current_city_category IS NOT NULL
            GROUP BY current_city_category
            ORDER BY count DESC
        """)
        city_category_results = db.execute(city_category_query).fetchall()
        city_category_data = [
            {"category": row[0], "count": row[1]}
            for row in city_category_results
        ]

        # City distribution (top cities)
        city_query = text("""
            SELECT current_city, COUNT(*) as count
            FROM patients
            WHERE current_city IS NOT NULL AND current_city != ''
            GROUP BY current_city
            ORDER BY count DESC
            LIMIT 10
        """)
        city_results = db.execute(city_query).fetchall()
        city_distribution_data = [
            {"city": row[0], "count": row[1]}
            for row in city_results
        ]

        return {
            "success": True,
            "data": {
                "cityCategory": city_category_data,
                "migration": [],  # Not implemented yet
                "cityDistribution": city_distribution_data,
            },
        }
    except Exception as e:
        logger.error(f"Geographic analytics failed: {e}")
        return {"success": False, "error": str(e)}


@router.get("/enrollment-trends")
async def enrollment_trends(db=Depends(get_db)):
    try:
        # Monthly enrollment trends
        trends_query = text("""
            SELECT
                DATE_TRUNC('month', enrollment_date) as month,
                COUNT(*) as enrolled
            FROM patients
            WHERE enrollment_date IS NOT NULL
            GROUP BY DATE_TRUNC('month', enrollment_date)
            ORDER BY month
        """)
        trends_results = db.execute(trends_query).fetchall()

        # Calculate cumulative enrollment
        cumulative = 0
        trends_data = []
        for row in trends_results:
            cumulative += row[1]
            trends_data.append({
                "month": row[0].strftime("%Y-%m") if row[0] else "Unknown",
                "enrolled": row[1],
                "cumulative": cumulative
            })

        return {"success": True, "data": trends_data}
    except Exception as e:
        logger.error(f"Enrollment trends analytics failed: {e}")
        return {"success": False, "error": str(e)}


@router.get("/data-quality")
async def data_quality(db=Depends(get_db)):
    try:
        # Calculate completeness by category
        completeness_query = text("""
            SELECT
                ROUND(AVG(CASE WHEN heart_rate IS NOT NULL OR systolic_bp IS NOT NULL OR diastolic_bp IS NOT NULL THEN 100 ELSE 0 END)) as physical_exam,
                ROUND(AVG(CASE WHEN hba1c IS NOT NULL THEN 100 ELSE 0 END)) as lab_results,
                ROUND(AVG(CASE WHEN echo_ef IS NOT NULL THEN 100 ELSE 0 END)) as echo,
                ROUND(AVG(CASE WHEN mri_ef IS NOT NULL THEN 100 ELSE 0 END)) as mri,
                ROUND(AVG(CASE WHEN dna_id IN (SELECT dna_id FROM ecg) THEN 100 ELSE 0 END)) as ecg,
                ROUND(AVG(data_completeness)) as overall
            FROM patient_summary
        """)
        completeness_result = db.execute(completeness_query).fetchone()

        # Data completeness distribution
        distribution_query = text("""
            SELECT
                CASE
                    WHEN data_completeness >= 80 THEN '80-100%'
                    WHEN data_completeness >= 60 THEN '60-79%'
                    WHEN data_completeness >= 40 THEN '40-59%'
                    WHEN data_completeness >= 20 THEN '20-39%'
                    ELSE '0-19%'
                END as completeness_range,
                COUNT(*) as count
            FROM patient_summary
            GROUP BY completeness_range
            ORDER BY completeness_range
        """)
        distribution_results = db.execute(distribution_query).fetchall()
        distribution_data = [
            {"range": row[0], "count": row[1]}
            for row in distribution_results
        ]

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
                "distribution": distribution_data,
            },
        }
    except Exception as e:
        logger.error(f"Data quality analytics failed: {e}")
        return {"success": False, "error": str(e)}


@router.get("/imaging")
async def imaging(db=Depends(get_db)):
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
                "mri": {
                    "avg_lv_ef": 0,
                    "avg_lv_mass": 0,
                    "avg_lv_edv": 0,
                    "total": 0,
                },
            },
        }
    except Exception as e:
        logger.error(f"Imaging analytics failed: {e}")
        return {"success": False, "error": str(e)}


@router.get("/ecg")
async def ecg(db=Depends(get_db)):
    try:
        return {
            "success": True,
            "data": {
                "conclusions": [],
                "abnormalities": {
                    "p_wave": 0,
                    "qrs": 0,
                    "st_segment": 0,
                    "t_wave": 0,
                },
                "rhythmDistribution": [],
            },
        }
    except Exception as e:
        logger.error(f"ECG analytics failed: {e}")
        return {"success": False, "error": str(e)}
