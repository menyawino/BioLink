from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import text
from app.database import get_db
from app.config import settings
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

        # Validate and sanitize sort parameters
        sort_column = sortBy if sortBy in ALLOWED_SORT_COLUMNS else "dna_id"
        sort_direction = "DESC" if sortOrder.lower() == "desc" else "ASC"

        # Calculate offset for pagination
        offset = (page - 1) * limit
        params["limit"] = limit
        params["offset"] = offset

        # Get total count for pagination
        count_stmt = text(
            f"SELECT COUNT(*) as total FROM patients WHERE {' AND '.join(conditions)}"
        )
        total_result = db.execute(count_stmt, params).fetchone()
        total = total_result[0] if total_result else 0

        # Get paginated results using patient_summary view for complete data
        stmt = text(
            "SELECT dna_id, age, gender, nationality, enrollment_date, "
            "heart_rate, systolic_bp, diastolic_bp, bmi, hba1c, echo_ef, mri_ef, "
            "current_city_category, "
            "CASE WHEN mri_ef IS NOT NULL THEN true ELSE false END as has_mri, "
            "CASE WHEN echo_ef IS NOT NULL THEN true ELSE false END as has_echo, "
            "COALESCE(("
            "  (CASE WHEN heart_rate IS NOT NULL THEN 20 ELSE 0 END) + "
            "  (CASE WHEN systolic_bp IS NOT NULL THEN 20 ELSE 0 END) + "
            "  (CASE WHEN bmi IS NOT NULL THEN 20 ELSE 0 END) + "
            "  (CASE WHEN echo_ef IS NOT NULL THEN 20 ELSE 0 END) + "
            "  (CASE WHEN mri_ef IS NOT NULL THEN 20 ELSE 0 END)"
            "), 0) as data_completeness "
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
            "SELECT dna_id, age, gender, nationality, enrollment_date, "
            "heart_rate, systolic_bp, diastolic_bp, bmi, hba1c, echo_ef, mri_ef, "
            "current_city_category, "
            "CASE WHEN mri_ef IS NOT NULL THEN true ELSE false END as has_mri, "
            "CASE WHEN echo_ef IS NOT NULL THEN true ELSE false END as has_echo "
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
        # Get basic patient info
        patient_stmt = text("""
            SELECT p.*, 
                   gd.current_city_category, gd.childhood_city_category, gd.migration_pattern
            FROM patients p
            LEFT JOIN geographic_data gd ON p.id = gd.patient_id
            WHERE p.dna_id = :dna_id
        """)
        patient = db.execute(patient_stmt, {"dna_id": dna_id}).mappings().fetchone()
        
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        patient_data = dict(patient)
        patient_id = patient_data.get("id")
        
        # Get related data
        lifestyle = db.execute(
            text("SELECT * FROM lifestyle_data WHERE patient_id = :id"),
            {"id": patient_id}
        ).mappings().fetchone()
        
        exclusion = db.execute(
            text("SELECT * FROM exclusion_criteria WHERE patient_id = :id"),
            {"id": patient_id}
        ).mappings().fetchone()
        
        family = db.execute(
            text("SELECT * FROM family_history WHERE patient_id = :id"),
            {"id": patient_id}
        ).mappings().fetchone()
        
        medical = db.execute(
            text("SELECT * FROM medical_history WHERE patient_id = :id"),
            {"id": patient_id}
        ).mappings().fetchone()
        
        physical = db.execute(
            text("SELECT * FROM physical_examinations WHERE patient_id = :id ORDER BY examination_date DESC LIMIT 1"),
            {"id": patient_id}
        ).mappings().fetchone()
        
        labs = db.execute(
            text("SELECT * FROM lab_results WHERE patient_id = :id"),
            {"id": patient_id}
        ).mappings().fetchone()
        
        ecg = db.execute(
            text("SELECT * FROM ecg_data WHERE patient_id = :id"),
            {"id": patient_id}
        ).mappings().fetchone()
        
        echo = db.execute(
            text("SELECT * FROM echo_data WHERE patient_id = :id ORDER BY echo_date DESC LIMIT 1"),
            {"id": patient_id}
        ).mappings().fetchone()
        
        mri = db.execute(
            text("SELECT * FROM mri_data WHERE patient_id = :id ORDER BY mri_date DESC LIMIT 1"),
            {"id": patient_id}
        ).mappings().fetchone()
        
        # Build response
        result = {
            **patient_data,
            "has_mri": mri is not None and mri.get("mri_performed", False),
            "has_echo": echo is not None,
            "heart_rate": physical.get("heart_rate") if physical else None,
            "systolic_bp": physical.get("systolic_bp") if physical else None,
            "diastolic_bp": physical.get("diastolic_bp") if physical else None,
            "bmi": physical.get("bmi") if physical else None,
            "hba1c": labs.get("hba1c") if labs else None,
            "echo_ef": echo.get("ef") if echo else None,
            "mri_ef": mri.get("lv_ejection_fraction") if mri else None,
            "lifestyle": dict(lifestyle) if lifestyle else None,
            "exclusion": dict(exclusion) if exclusion else None,
            "family": dict(family) if family else None,
            "medical": dict(medical) if medical else None,
            "physical": dict(physical) if physical else None,
            "labs": dict(labs) if labs else None,
            "ecg": dict(ecg) if ecg else None,
            "echo": dict(echo) if echo else None,
            "mri": dict(mri) if mri else None,
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
            SELECT pe.heart_rate, pe.systolic_bp, pe.diastolic_bp, pe.bmi,
                   pe.height_cm, pe.weight_kg, pe.bsa, pe.regularity,
                   pe.examination_date, lr.hba1c, lr.troponin_i
            FROM patients p
            LEFT JOIN physical_examinations pe ON p.id = pe.patient_id
            LEFT JOIN lab_results lr ON p.id = lr.patient_id
            WHERE p.dna_id = :dna_id
            ORDER BY pe.examination_date DESC
            LIMIT 1
        """)
        result = db.execute(stmt, {"dna_id": dna_id}).mappings().fetchone()
        
        if not result:
            return {"success": True, "data": None}
        
        return {"success": True, "data": dict(result)}
    except Exception as e:
        logger.error(f"Error fetching vitals for {dna_id}: {e}")
        return {"success": False, "error": str(e)}


@router.get("/{dna_id}/imaging")
async def get_patient_imaging(dna_id: str, db = Depends(get_db)):
    """Get patient imaging data (Echo and MRI)"""
    try:
        # Get Echo data
        echo_stmt = text("""
            SELECT ed.* FROM echo_data ed
            JOIN patients p ON p.id = ed.patient_id
            WHERE p.dna_id = :dna_id
            ORDER BY ed.echo_date DESC
            LIMIT 1
        """)
        echo = db.execute(echo_stmt, {"dna_id": dna_id}).mappings().fetchone()
        
        # Get MRI data
        mri_stmt = text("""
            SELECT md.* FROM mri_data md
            JOIN patients p ON p.id = md.patient_id
            WHERE p.dna_id = :dna_id
            ORDER BY md.mri_date DESC
            LIMIT 1
        """)
        mri = db.execute(mri_stmt, {"dna_id": dna_id}).mappings().fetchone()
        
        # Get ECG data
        ecg_stmt = text("""
            SELECT ecg.* FROM ecg_data ecg
            JOIN patients p ON p.id = ecg.patient_id
            WHERE p.dna_id = :dna_id
        """)
        ecg = db.execute(ecg_stmt, {"dna_id": dna_id}).mappings().fetchone()
        
        return {
            "success": True,
            "data": {
                "echo": dict(echo) if echo else None,
                "mri": dict(mri) if mri else None,
                "ecg": dict(ecg) if ecg else None
            }
        }
    except Exception as e:
        logger.error(f"Error fetching imaging for {dna_id}: {e}")
        return {"success": False, "error": str(e)}


@router.get("/{dna_id}/risk-factors")
async def get_patient_risk_factors(dna_id: str, db = Depends(get_db)):
    """Get patient risk factors"""
    try:
        stmt = text("""
            SELECT 
                mh.diabetes_mellitus as diabetes,
                mh.high_blood_pressure as hypertension,
                mh.dyslipidemia,
                ls.current_smoker as smoking,
                CASE WHEN pe.bmi >= 30 THEN true ELSE false END as obesity,
                mh.prior_heart_failure as heart_failure,
                mh.heart_attack_or_angina as cad,
                mh.kidney_problems as kidney_disease,
                mh.comorbidity as comorbidity_count,
                pe.bmi,
                pe.systolic_bp,
                pe.diastolic_bp,
                lr.hba1c,
                ed.ef as echo_ef
            FROM patients p
            LEFT JOIN medical_history mh ON p.id = mh.patient_id
            LEFT JOIN lifestyle_data ls ON p.id = ls.patient_id
            LEFT JOIN physical_examinations pe ON p.id = pe.patient_id
            LEFT JOIN lab_results lr ON p.id = lr.patient_id
            LEFT JOIN echo_data ed ON p.id = ed.patient_id
            WHERE p.dna_id = :dna_id
        """)
        result = db.execute(stmt, {"dna_id": dna_id}).mappings().fetchone()
        
        if not result:
            return {"success": True, "data": None}
        
        return {"success": True, "data": dict(result)}
    except Exception as e:
        logger.error(f"Error fetching risk factors for {dna_id}: {e}")
        return {"success": False, "error": str(e)}
