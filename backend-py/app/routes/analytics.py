from fastapi import APIRouter, Depends
from sqlalchemy import text
from app.database import get_db
from app.diagnoses import (
    DIAGNOSIS_DEFINITIONS,
    build_comorbidity_counts_sql,
    build_comorbidity_distribution_sql,
)
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

        # Imaging availability (denormalized columns)
        with_echo = db.execute(text("SELECT COUNT(*) FROM patients WHERE echo_ef IS NOT NULL")).scalar() or 0
        with_mri = db.execute(text("SELECT COUNT(*) FROM patients WHERE mri_ef IS NOT NULL")).scalar() or 0
        with_both_echo_mri = db.execute(text("SELECT COUNT(*) FROM patients WHERE echo_ef IS NOT NULL AND mri_ef IS NOT NULL")).scalar() or 0
        # ECG isn't modeled in the denormalized schema yet
        with_ecg = 0

        # Calculate average data completeness
        completeness_result = db.execute(
            text("SELECT AVG(data_completeness) as avg_completeness FROM EHVOL")
        ).scalar()
        avg_completeness = float(completeness_result) if completeness_result is not None else 0.0

        data = {
            "totalPatients": total,
            "maleCount": male,
            "femaleCount": female,
            "averageAge": f"{avg_age_val:.1f}",
            "dataCompleteness": f"{avg_completeness:.1f}",
            "withMri": with_mri,
            "withEcho": with_echo,
            "withBothEchoMri": with_both_echo_mri,
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
        counts_sql = build_comorbidity_counts_sql("patients")
        count_row = db.execute(text(counts_sql)).fetchone()

        condition_counts = {
            definition["key"]: (count_row[idx] or 0) if count_row else 0
            for idx, definition in enumerate(DIAGNOSIS_DEFINITIONS)
        }
        condition_counts.update({
            "kidney_disease": 0,
            "liver_disease": 0,
            "anaemia": 0,
        })

        distribution_sql = build_comorbidity_distribution_sql("patients")
        distribution_results = db.execute(text(distribution_sql)).fetchall()
        distribution_data = [
            {"comorbidities": row[0], "patients": row[1]}
            for row in distribution_results
        ]

        return {
            "success": True,
            "data": {
                "conditions": condition_counts,
                "comorbidityDistribution": distribution_data,
            },
        }
    except Exception as e:
        logger.error(f"Comorbidity analytics failed: {e}")
        return {"success": False, "error": str(e)}


@router.get("/lifestyle")
async def lifestyle(db=Depends(get_db)):
    try:
        smoking_query = text("""
            SELECT
                COUNT(*) FILTER (WHERE COALESCE(current_smoker, false)) AS current_smokers,
                COUNT(*) FILTER (WHERE COALESCE(former_smoker, false)) AS former_smokers,
                COUNT(*) FILTER (WHERE NOT COALESCE(current_smoker, false) AND NOT COALESCE(former_smoker, false)) AS never_smoked
            FROM patients
        """)
        smoking_result = db.execute(smoking_query).fetchone()

        duration_query = text("""
            SELECT
                smoking_years,
                COUNT(*) AS count
            FROM patients
            WHERE COALESCE(current_smoker, false) AND smoking_years IS NOT NULL
            GROUP BY smoking_years
            ORDER BY smoking_years
        """)
        duration_results = db.execute(duration_query).fetchall()
        duration_data = [{"years": row[0], "count": row[1]} for row in duration_results]

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
            FROM EHVOL
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


@router.get("/geographic-governorates")
async def geographic_governorates(db=Depends(get_db)):
    """Get geographic statistics aggregated by Egyptian governorates."""
    try:
        # City to governorate mapping
        city_to_governorate = {
            'Cairo': 'Cairo',
            'Alexandria': 'Alexandria',
            'Giza': 'Giza',
            'Qalyubia': 'Qalyubia',
            'Sharqia': 'Sharqia',
            'Gharbya': 'Gharbia',
            'Menoufya': 'Monufia',
            'Behaira': 'Beheira',
            'Kafr El Sheikh': 'Kafr El-Sheikh',
            'Damietta': 'Damietta',
            'Port Said': 'Port Said',
            'Ismailia': 'Ismailia',
            'Suez': 'Suez',
            'Faiyum': 'Faiyum',
            'Beni Suef': 'Beni Suef',
            'Minya': 'Minya',
            'Asyut': 'Asyut',
            'Sohag': 'Sohag',
            'Qena': 'Qena',
            'Luxor': 'Luxor',
            'Aswan': 'Aswan',
            'Red Sea': 'Red Sea',
            'New Valley': 'New Valley',
            'Matruh': 'Matruh',
            'North Sinai': 'North Sinai',
            'South Sinai': 'South Sinai'
        }

        # Governorate coordinates (approximate centers)
        governorate_coords = {
            'Cairo': [31.2357, 30.0444],
            'Alexandria': [29.9187, 31.2001],
            'Giza': [31.2089, 30.0131],
            'Qalyubia': [31.2057, 30.4286],
            'Sharqia': [31.5994, 30.5877],
            'Gharbia': [30.9876, 30.8753],
            'Monufia': [30.9704, 30.5972],
            'Beheira': [30.3667, 30.5833],
            'Kafr El-Sheikh': [30.9876, 31.1111],
            'Damietta': [31.8133, 31.4167],
            'Port Said': [32.3019, 31.2653],
            'Ismailia': [32.2744, 30.6043],
            'Suez': [32.5263, 29.9737],
            'Faiyum': [30.8418, 29.3084],
            'Beni Suef': [31.0979, 29.0661],
            'Minya': [30.7503, 28.1099],
            'Asyut': [31.1656, 27.1801],
            'Sohag': [31.6948, 26.5591],
            'Qena': [32.7267, 26.1642],
            'Luxor': [32.6396, 25.6872],
            'Aswan': [32.8994, 24.0889],
            'Red Sea': [33.8387, 27.1783],
            'New Valley': [28.9167, 27.0667],
            'Matruh': [27.2373, 31.3525],
            'North Sinai': [33.6176, 30.8503],
            'South Sinai': [33.6176, 28.9667]
        }

        # Aggregate data by governorate
        governorate_query = text("""
            SELECT
                CASE
                    WHEN LOWER(current_city) LIKE '%cairo%' THEN 'Cairo'
                    WHEN LOWER(current_city) LIKE '%alexandria%' THEN 'Alexandria'
                    WHEN LOWER(current_city) LIKE '%giza%' THEN 'Giza'
                    WHEN LOWER(current_city) LIKE '%sohag%' THEN 'Sohag'
                    WHEN LOWER(current_city) LIKE '%aswan%' THEN 'Aswan'
                    WHEN LOWER(current_city) LIKE '%gharbya%' OR LOWER(current_city) LIKE '%tanta%' THEN 'Gharbia'
                    WHEN LOWER(current_city) LIKE '%behaira%' OR LOWER(current_city) LIKE '%damanhur%' THEN 'Beheira'
                    WHEN LOWER(current_city) LIKE '%menoufya%' OR LOWER(current_city) LIKE '%shibin el kom%' THEN 'Monufia'
                    WHEN LOWER(current_city) LIKE '%sharkia%' OR LOWER(current_city) LIKE '%zagazig%' THEN 'Sharqia'
                    ELSE current_city
                END as governorate,
                COUNT(*) as patient_count,
                AVG(age) as avg_age,
                COUNT(CASE WHEN gender = 'Male' OR gender = 'M' THEN 1 END) as male_count,
                COUNT(CASE WHEN gender = 'Female' OR gender = 'F' THEN 1 END) as female_count,
                COUNT(CASE WHEN high_blood_pressure = true THEN 1 END) as hypertension_count,
                COUNT(CASE WHEN diabetes_mellitus = true THEN 1 END) as diabetes_count,
                COUNT(CASE WHEN ever_smoked = true THEN 1 END) as smoking_count,
                AVG(bmi) as avg_bmi,
                AVG(systolic_bp) as avg_systolic_bp,
                AVG(hba1c) as avg_hba1c
            FROM patients
            WHERE current_city IS NOT NULL AND current_city != ''
            GROUP BY
                CASE
                    WHEN LOWER(current_city) LIKE '%cairo%' THEN 'Cairo'
                    WHEN LOWER(current_city) LIKE '%alexandria%' THEN 'Alexandria'
                    WHEN LOWER(current_city) LIKE '%giza%' THEN 'Giza'
                    WHEN LOWER(current_city) LIKE '%sohag%' THEN 'Sohag'
                    WHEN LOWER(current_city) LIKE '%aswan%' THEN 'Aswan'
                    WHEN LOWER(current_city) LIKE '%gharbya%' OR LOWER(current_city) LIKE '%tanta%' THEN 'Gharbia'
                    WHEN LOWER(current_city) LIKE '%behaira%' OR LOWER(current_city) LIKE '%damanhur%' THEN 'Beheira'
                    WHEN LOWER(current_city) LIKE '%menoufya%' OR LOWER(current_city) LIKE '%shibin el kom%' THEN 'Monufia'
                    WHEN LOWER(current_city) LIKE '%sharkia%' OR LOWER(current_city) LIKE '%zagazig%' THEN 'Sharqia'
                    ELSE current_city
                END
            ORDER BY patient_count DESC
        """)

        results = db.execute(governorate_query).fetchall()

        governorate_data = []
        for row in results:
            governorate = row[0]
            if governorate in governorate_coords:
                coords = governorate_coords[governorate]
                patient_count = row[1] or 0
                avg_age = float(row[2]) if row[2] else 0
                male_count = row[3] or 0
                female_count = row[4] or 0
                total_gender = male_count + female_count
                gender_ratio = male_count / total_gender if total_gender > 0 else 0

                # Calculate prevalence estimates (simplified)
                hypertension_rate = (row[5] or 0) / patient_count * 100 if patient_count > 0 else 0
                diabetes_rate = (row[6] or 0) / patient_count * 100 if patient_count > 0 else 0
                smoking_rate = (row[7] or 0) / patient_count * 100 if patient_count > 0 else 0

                # Estimate CVD prevalence based on risk factors
                prevalence = min(25, hypertension_rate * 0.3 + diabetes_rate * 0.4 + smoking_rate * 0.2 + (avg_age - 40) * 0.1)

                governorate_data.append({
                    "region": governorate,
                    "coordinates": coords,
                    "patientCount": patient_count,
                    "prevalence": round(prevalence, 1),
                    "demographics": {
                        "averageAge": round(avg_age, 1),
                        "genderRatio": round(gender_ratio, 2),
                        "ethnicityMix": {"arab": 95, "other": 5}  # Default assumption
                    },
                    "riskFactors": {
                        "hypertension": round(hypertension_rate, 1),
                        "diabetes": round(diabetes_rate, 1),
                        "smoking": round(smoking_rate, 1),
                        "obesity": round((row[8] or 25) - 20, 1) if row[8] else 25  # Rough estimate
                    },
                    "outcomes": {
                        "mortality": round(prevalence * 0.05, 1),  # Estimated
                        "readmission": round(prevalence * 1.2, 1),  # Estimated
                        "complications": round(prevalence * 2.0, 1)  # Estimated
                    }
                })

        return {
            "success": True,
            "data": governorate_data
        }

    except Exception as e:
        logger.error(f"Governorate geographic analytics failed: {e}")
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
            FROM EHVOL
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
            FROM EHVOL
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
