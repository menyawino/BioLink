from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import text
from app.database import get_db
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Allowed columns for sorting to prevent SQL injection
ALLOWED_SORT_COLUMNS = {"dna_id", "age", "gender", "nationality"}

@router.get("")
async def get_patients(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=1000),
    search: str = None,
    gender: str = None,
    ageMin: int = Query(None, alias="ageMin"),
    ageMax: int = Query(None, alias="ageMax"),
    sortBy: str = Query("dna_id", alias="sortBy"),
    sortOrder: str = Query("asc", alias="sortOrder"),
    # Data availability filters
    hasEcho: bool = Query(None, alias="hasEcho"),
    hasMri: bool = Query(None, alias="hasMri"),
    hasGenomics: bool = Query(None, alias="hasGenomics"),
    hasLabs: bool = Query(None, alias="hasLabs"),
    hasImaging: bool = Query(None, alias="hasImaging"),
    minDataCompleteness: int = Query(None, alias="minDataCompleteness"),
    # Geographic filters
    nationality: str = None,
    region: str = None,
    # Temporal filters
    enrollmentDateFrom: str = Query(None, alias="enrollmentDateFrom"),
    enrollmentDateTo: str = Query(None, alias="enrollmentDateTo"),
    # Clinical/risk factor filters
    hasDiabetes: bool = Query(None, alias="hasDiabetes"),
    hasHypertension: bool = Query(None, alias="hasHypertension"),
    hasSmoking: bool = Query(None, alias="hasSmoking"),
    hasObesity: bool = Query(None, alias="hasObesity"),
    hasFamilyHistory: bool = Query(None, alias="hasFamilyHistory"),
    db = Depends(get_db)
):
    """Search and filter patients in the registry"""
    try:
        # Build a safe, parameterized filter query
        conditions = ["1=1"]
        params = {}

        if search:
            conditions.append("(dna_id ILIKE :search OR nationality ILIKE :search)")
            params["search"] = f"%{search}%"

        if gender:
            conditions.append("gender = :gender")
            params["gender"] = gender

        if ageMin is not None:
            conditions.append("age >= :age_min")
            params["age_min"] = ageMin

        if ageMax is not None:
            conditions.append("age <= :age_max")
            params["age_max"] = ageMax

        # Data availability filters (backed by patient_summary flags)
        if hasEcho is not None:
            conditions.append("has_echo = :has_echo")
            params["has_echo"] = hasEcho

        if hasMri is not None:
            conditions.append("has_mri = :has_mri")
            params["has_mri"] = hasMri

        if minDataCompleteness is not None:
            conditions.append("data_completeness >= :min_data_completeness")
            params["min_data_completeness"] = minDataCompleteness

        # Geographic filters
        if nationality:
            conditions.append("nationality = :nationality")
            params["nationality"] = nationality

        # Temporal filters
        if enrollmentDateFrom:
            conditions.append("enrollment_date >= :enrollment_date_from")
            params["enrollment_date_from"] = enrollmentDateFrom

        if enrollmentDateTo:
            conditions.append("enrollment_date <= :enrollment_date_to")
            params["enrollment_date_to"] = enrollmentDateTo

        # Clinical / risk factor filters (best-effort; nullable columns)
        if hasDiabetes is not None:
            conditions.append("COALESCE(diabetes_mellitus, false) = :has_diabetes")
            params["has_diabetes"] = hasDiabetes

        if hasHypertension is not None:
            conditions.append("COALESCE(high_blood_pressure, false) = :has_hypertension")
            params["has_hypertension"] = hasHypertension

        if hasSmoking is not None:
            conditions.append("COALESCE(current_smoker, false) = :has_smoking")
            params["has_smoking"] = hasSmoking

        if hasObesity is not None:
            conditions.append("COALESCE(bmi, 0) >= 30") if hasObesity else conditions.append("(bmi IS NULL OR bmi < 30)")

        # Validate and sanitize sort parameters
        sort_column = sortBy if sortBy in ALLOWED_SORT_COLUMNS else "dna_id"
        sort_direction = "DESC" if sortOrder.lower() == "desc" else "ASC"

        # Calculate offset for pagination
        offset = (page - 1) * limit
        params["limit"] = limit
        params["offset"] = offset

        # Get total count for pagination
        count_stmt = text(
            f"SELECT COUNT(*) as total FROM patient_summary WHERE {' AND '.join(conditions)}"
        )
        total_result = db.execute(count_stmt, params).fetchone()
        total = total_result[0] if total_result else 0

        # Get paginated results using patient_summary view for complete data
        stmt = text(
            "SELECT id, dna_id, age, gender, nationality, enrollment_date, current_city, "
            "heart_rate, systolic_bp, diastolic_bp, bmi, hba1c, echo_ef, mri_ef, "
            "current_city_category, has_mri, has_echo, data_completeness "
            "FROM patient_summary "
            f"WHERE {' AND '.join(conditions)} "
            f"ORDER BY {sort_column} {sort_direction} "
            "LIMIT :limit OFFSET :offset"
        )

        patients = db.execute(stmt, params).mappings().fetchall()
        
        total_pages = (total + limit - 1) // limit if limit > 0 else 1
        
        return {
            "success": True,
            "data": [dict(row) for row in patients],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "totalPages": total_pages
            }
        }
    except Exception as e:
        logger.error(f"Error fetching patients: {e}")
        return {"success": False, "error": str(e)}


@router.get("/search/{query}")
async def search_patients(
    query: str,
    limit: int = Query(20, ge=1, le=100),
    db = Depends(get_db)
):
    """Search patients by DNA ID or nationality"""
    try:
        params = {"search": f"%{query}%", "limit": limit}
        stmt = text(
            "SELECT id, dna_id, age, gender, nationality, enrollment_date, current_city, "
            "heart_rate, systolic_bp, diastolic_bp, bmi, hba1c, echo_ef, mri_ef, "
            "current_city_category, has_mri, has_echo, data_completeness "
            "FROM patient_summary "
            "WHERE dna_id ILIKE :search OR nationality ILIKE :search "
            "ORDER BY dna_id ASC "
            "LIMIT :limit"
        )
        patients = db.execute(stmt, params).mappings().fetchall()
        return {
            "success": True,
            "data": [dict(row) for row in patients]
        }
    except Exception as e:
        logger.error(f"Error searching patients: {e}")
        return {"success": False, "error": str(e)}


@router.get("/{dna_id}")
async def get_patient(dna_id: str, db = Depends(get_db)):
    """Get detailed patient information by DNA ID"""
    try:
        patient_stmt = text("""
            SELECT *
            FROM patients
            WHERE dna_id = :dna_id
        """)
        patient = db.execute(patient_stmt, {"dna_id": dna_id}).mappings().fetchone()
        
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        patient_data = dict(patient)

        # Build nested objects from the denormalized row (keep the frontend contract stable)
        lifestyle = {
            "current_smoker": bool(patient_data.get("current_smoker") or False),
            "smoking_duration": None,
            "cigarettes_per_day": patient_data.get("cigarettes_per_day"),
            "drinks_alcohol": bool(patient_data.get("drinks_alcohol") or False),
            "takes_medication": bool(patient_data.get("takes_medication") or False),
            "ever_smoked": bool(patient_data.get("ever_smoked") or False),
            "smoking_years": patient_data.get("smoking_years"),
        }

        exclusion = None
        family = None

        medical = {
            "heart_attack_or_angina": bool(patient_data.get("heart_attack_or_angina") or False),
            "high_blood_pressure": bool(patient_data.get("high_blood_pressure") or False),
            "dyslipidemia": bool(patient_data.get("dyslipidemia") or False),
            "rheumatic_fever": False,
            "anaemia": False,
            "lung_problems": False,
            "kidney_problems": False,
            "liver_problems": False,
            "diabetes_mellitus": bool(patient_data.get("diabetes_mellitus") or False),
            "prior_heart_failure": bool(patient_data.get("prior_heart_failure") or False),
            "neurological_problems": False,
            "musculoskeletal_problems": False,
            "autoimmune_problems": False,
            "undergone_surgery": False,
            "procedure_details": None,
            "malignancy": False,
            "comorbidity": int(
                bool(patient_data.get("high_blood_pressure") or False)
                + bool(patient_data.get("diabetes_mellitus") or False)
                + bool(patient_data.get("dyslipidemia") or False)
                + bool(patient_data.get("heart_attack_or_angina") or False)
                + bool(patient_data.get("prior_heart_failure") or False)
            ),
        }

        physical = {
            "examination_date": patient_data.get("enrollment_date"),
            "examination_type": "Enrollment",
            "heart_rate": patient_data.get("heart_rate"),
            "regularity": None,
            "bp_reading": None,
            "systolic_bp": patient_data.get("systolic_bp"),
            "diastolic_bp": patient_data.get("diastolic_bp"),
            "height_cm": patient_data.get("height_cm"),
            "weight_kg": patient_data.get("weight_kg"),
            "bmi": patient_data.get("bmi"),
            "bsa": patient_data.get("bsa"),
            "jvp": None,
            "abnormal_physical_structure": False,
            "s1": None,
            "s2": None,
            "s3": False,
            "s4": False,
        }

        labs = {
            "hba1c": patient_data.get("hba1c"),
            "troponin_i": patient_data.get("troponin_i"),
            "hba1c_outlier": False,
            "troponin_outlier": False,
            "heart_rate_outlier": False,
        }

        ecg = {
            "rate": None,
            "rate_clean": None,
            "rhythm": None,
            "p_wave_abnormality": False,
            "pr_interval": None,
            "qrs_duration": None,
            "qrs_abnormalities": False,
            "st_segment_abnormalities": False,
            "qtc_interval": None,
            "t_wave_abnormalities": False,
            "ecg_conclusion": None,
            "missing_ecg": True,
        }

        echo = {
            "echo_date": patient_data.get("echo_date"),
            "aortic_root": None,
            "left_atrium": None,
            "right_ventricle": None,
            "lvedd": None,
            "lvesd": None,
            "ivsd": None,
            "ivss": None,
            "lvpwd": None,
            "lvpws": None,
            "ef": patient_data.get("echo_ef"),
            "fs": None,
            "subaortic_membrane": False,
            "mitral_regurge": None,
            "mitral_stenosis": False,
            "tricuspid_regurge": None,
            "tricuspid_stenosis": False,
            "aortic_regurge": None,
            "aortic_stenosis": False,
            "pulmonary_regurge": None,
            "pulmonary_stenosis": False,
            "missing_echo": patient_data.get("echo_ef") is None,
        }

        mri = {
            "mri_performed": patient_data.get("mri_ef") is not None,
            "heart_rate_during_mri": None,
            "mri_date": patient_data.get("mri_date"),
            "lv_ejection_fraction": patient_data.get("mri_ef"),
            "lv_end_diastolic_volume": None,
            "lv_end_systolic_volume": None,
            "lv_mass": None,
            "rv_ejection_fraction": patient_data.get("rv_ef"),
            "missing_mri": patient_data.get("mri_ef") is None,
        }
        
        # Build response
        result = {
            "id": patient_data.get("id"),
            "dna_id": patient_data.get("dna_id"),
            "age": patient_data.get("age"),
            "gender": patient_data.get("gender"),
            "nationality": patient_data.get("nationality"),
            "enrollment_date": patient_data.get("enrollment_date"),
            "current_city": patient_data.get("current_city"),
            "heart_rate": patient_data.get("heart_rate"),
            "systolic_bp": patient_data.get("systolic_bp"),
            "diastolic_bp": patient_data.get("diastolic_bp"),
            "bmi": patient_data.get("bmi"),
            "hba1c": patient_data.get("hba1c"),
            "echo_ef": patient_data.get("echo_ef"),
            "mri_ef": patient_data.get("mri_ef"),
            "current_city_category": patient_data.get("current_city_category"),
            "has_mri": patient_data.get("mri_ef") is not None,
            "has_echo": patient_data.get("echo_ef") is not None,
            "data_completeness": int(
                (20 if patient_data.get("heart_rate") is not None else 0)
                + (20 if patient_data.get("systolic_bp") is not None else 0)
                + (20 if patient_data.get("bmi") is not None else 0)
                + (20 if patient_data.get("echo_ef") is not None else 0)
                + (20 if patient_data.get("mri_ef") is not None else 0)
            ),
            "date_of_birth": patient_data.get("date_of_birth"),
            "is_pregnant": False,
            "father_city_origin": None,
            "childhood_city": None,
            "consent_obtained": True,
            "lifestyle": lifestyle,
            "exclusion": exclusion,
            "family": family,
            "medical": medical,
            "physical": physical,
            "labs": labs,
            "ecg": ecg,
            "echo": echo,
            "mri": mri,
            "geographic": {
                "current_city_category": patient_data.get("current_city_category"),
                "childhood_city_category": patient_data.get("childhood_city_category"),
                "migration_pattern": patient_data.get("migration_pattern"),
            }
        }
        
        return {"success": True, "data": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching patient {dna_id}: {e}")
        return {"success": False, "error": str(e)}


@router.get("/{dna_id}/vitals")
async def get_patient_vitals(dna_id: str, db = Depends(get_db)):
    """Get patient vital signs"""
    try:
        stmt = text("""
            SELECT
                systolic_bp,
                diastolic_bp,
                heart_rate,
                weight_kg,
                height_cm,
                bmi,
                bsa,
                hba1c,
                troponin_i
            FROM patients
            WHERE dna_id = :dna_id
        """)
        row = db.execute(stmt, {"dna_id": dna_id}).mappings().fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Patient not found")

        return {
            "success": True,
            "data": {
                "current": {
                    "systolic": row.get("systolic_bp"),
                    "diastolic": row.get("diastolic_bp"),
                    "heartRate": row.get("heart_rate"),
                    "weight": row.get("weight_kg"),
                    "height": row.get("height_cm"),
                    "bmi": row.get("bmi"),
                    "bsa": row.get("bsa"),
                    "hba1c": row.get("hba1c"),
                    "troponin": row.get("troponin_i"),
                }
            },
        }
    except Exception as e:
        logger.error(f"Error fetching vitals for {dna_id}: {e}")
        return {"success": False, "error": str(e)}


@router.get("/{dna_id}/imaging")
async def get_patient_imaging(dna_id: str, db = Depends(get_db)):
    """Get patient imaging data (Echo and MRI)"""
    try:
        stmt = text("""
            SELECT echo_date, echo_ef, mri_date, mri_ef, rv_ef
            FROM patients
            WHERE dna_id = :dna_id
        """)
        row = db.execute(stmt, {"dna_id": dna_id}).mappings().fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Patient not found")

        echo = None
        if row.get("echo_ef") is not None or row.get("echo_date") is not None:
            echo = {
                "echo_date": row.get("echo_date"),
                "aortic_root": None,
                "left_atrium": None,
                "right_ventricle": None,
                "lvedd": None,
                "lvesd": None,
                "ivsd": None,
                "ivss": None,
                "lvpwd": None,
                "lvpws": None,
                "ef": row.get("echo_ef"),
                "fs": None,
                "subaortic_membrane": False,
                "mitral_regurge": None,
                "mitral_stenosis": False,
                "tricuspid_regurge": None,
                "tricuspid_stenosis": False,
                "aortic_regurge": None,
                "aortic_stenosis": False,
                "pulmonary_regurge": None,
                "pulmonary_stenosis": False,
                "missing_echo": row.get("echo_ef") is None,
            }

        mri = None
        if row.get("mri_ef") is not None or row.get("mri_date") is not None:
            mri = {
                "mri_performed": row.get("mri_ef") is not None,
                "heart_rate_during_mri": None,
                "mri_date": row.get("mri_date"),
                "lv_ejection_fraction": row.get("mri_ef"),
                "lv_end_diastolic_volume": None,
                "lv_end_systolic_volume": None,
                "lv_mass": None,
                "rv_ejection_fraction": row.get("rv_ef"),
                "missing_mri": row.get("mri_ef") is None,
            }

        return {"success": True, "data": {"echo": echo, "mri": mri}}
    except Exception as e:
        logger.error(f"Error fetching imaging for {dna_id}: {e}")
        return {"success": False, "error": str(e)}


@router.get("/{dna_id}/risk-factors")
async def get_patient_risk_factors(dna_id: str, db = Depends(get_db)):
    """Get patient risk factors"""
    try:
        stmt = text("""
            SELECT
                dna_id,
                age,
                bmi,
                COALESCE(diabetes_mellitus, false) AS diabetes_mellitus,
                COALESCE(high_blood_pressure, false) AS high_blood_pressure,
                COALESCE(dyslipidemia, false) AS dyslipidemia,
                COALESCE(current_smoker, false) AS current_smoker,
                COALESCE(ever_smoked, false) AS ever_smoked,
                COALESCE(heart_attack_or_angina, false) AS heart_attack_or_angina,
                COALESCE(history_sudden_death, false) AS history_sudden_death,
                COALESCE(history_premature_cad, false) AS history_premature_cad
            FROM patients
            WHERE dna_id = :dna_id
        """)
        row = db.execute(stmt, {"dna_id": dna_id}).mappings().fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Patient not found")

        obese = (row.get("bmi") or 0) >= 30

        risk_score = 0
        risk_score += 2 if row.get("diabetes_mellitus") else 0
        risk_score += 2 if row.get("high_blood_pressure") else 0
        risk_score += 2 if row.get("dyslipidemia") else 0
        risk_score += 2 if row.get("current_smoker") else 0
        risk_score += 1 if obese else 0
        risk_score += 2 if row.get("heart_attack_or_angina") else 0
        risk_score += 1 if (row.get("age") or 0) >= 55 else 0

        return {
            "success": True,
            "data": {
                "dna_id": row.get("dna_id"),
                "diabetes_mellitus": bool(row.get("diabetes_mellitus")),
                "high_blood_pressure": bool(row.get("high_blood_pressure")),
                "dyslipidemia": bool(row.get("dyslipidemia")),
                "current_smoker": bool(row.get("current_smoker")),
                "ever_smoked": bool(row.get("ever_smoked")),
                "obese": bool(obese),
                "heart_attack_or_angina": bool(row.get("heart_attack_or_angina")),
                "history_sudden_death": bool(row.get("history_sudden_death")),
                "history_premature_cad": bool(row.get("history_premature_cad")),
                "risk_score": int(risk_score),
            },
        }
    except Exception as e:
        logger.error(f"Error fetching risk factors for {dna_id}: {e}")
        return {"success": False, "error": str(e)}
