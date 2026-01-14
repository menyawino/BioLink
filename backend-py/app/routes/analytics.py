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
        total = db.execute(text("SELECT COUNT(*) FROM patients")).scalar() or 0
        male = db.execute(text("SELECT COUNT(*) FROM patients WHERE LOWER(gender) = 'male'"))
        male = male.scalar() if male is not None else 0
        female = db.execute(text("SELECT COUNT(*) FROM patients WHERE LOWER(gender) = 'female'"))
        female = female.scalar() if female is not None else 0
        avg_age = db.execute(text("SELECT AVG(age) FROM patients WHERE age IS NOT NULL")).scalar()
        avg_age_val = float(avg_age) if avg_age is not None else 0.0

        data = {
            "totalPatients": total,
            "maleCount": male,
            "femaleCount": female,
            "averageAge": f"{avg_age_val:.1f}",
            "dataCompleteness": "0",
            "withMri": 0,
            "withEcho": 0,
            "withEcg": 0,
        }
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"Overview analytics failed: {e}")
        return {"success": False, "error": str(e)}


@router.get("/demographics")
async def demographics(db=Depends(get_db)):
    """Return demographic breakdown; currently returns empty aggregates if not computed."""
    try:
        return {
            "success": True,
            "data": {
                "ageGender": [],
                "nationality": [],
                "maritalStatus": [],
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
        return {
            "success": True,
            "data": {
                "conditions": {
                    "hypertension": 0,
                    "diabetes": 0,
                    "dyslipidemia": 0,
                    "cad": 0,
                    "heart_failure": 0,
                    "lung_disease": 0,
                    "kidney_disease": 0,
                    "neurological": 0,
                },
                "comorbidityDistribution": [],
            },
        }
    except Exception as e:
        logger.error(f"Comorbidity analytics failed: {e}")
        return {"success": False, "error": str(e)}


@router.get("/lifestyle")
async def lifestyle(db=Depends(get_db)):
    try:
        return {
            "success": True,
            "data": {
                "smoking": {
                    "current_smokers": 0,
                    "former_smokers": 0,
                    "never_smoked": 0,
                },
                "smokingDuration": [],
            },
        }
    except Exception as e:
        logger.error(f"Lifestyle analytics failed: {e}")
        return {"success": False, "error": str(e)}


@router.get("/geographic")
async def geographic(db=Depends(get_db)):
    try:
        return {
            "success": True,
            "data": {
                "cityCategory": [],
                "migration": [],
                "cityDistribution": [],
            },
        }
    except Exception as e:
        logger.error(f"Geographic analytics failed: {e}")
        return {"success": False, "error": str(e)}


@router.get("/enrollment-trends")
async def enrollment_trends(db=Depends(get_db)):
    try:
        return {"success": True, "data": []}
    except Exception as e:
        logger.error(f"Enrollment trends analytics failed: {e}")
        return {"success": False, "error": str(e)}


@router.get("/data-quality")
async def data_quality(db=Depends(get_db)):
    try:
        return {
            "success": True,
            "data": {
                "byCategory": {
                    "physical_exam": 0,
                    "lab_results": 0,
                    "ecg": 0,
                    "echo": 0,
                    "mri": 0,
                    "overall": 0,
                },
                "distribution": [],
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
