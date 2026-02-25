"""
BioLink Unified Transform Processor for Apache NiFi 2.8.0

This NiFi Python processor ports the cleaning and transformation logic
from biolink_etl/schema_mappings.py and biolink_etl/transformer.py.

It reads CSV records (as JSON FlowFile content), applies field mappings,
type normalization, city homogenization, BP averaging, and quality scoring,
then outputs records conforming to the participant ingestion schema.
"""

import json
import re
from datetime import datetime
from nifiapi.flowfiletransform import FlowFileTransform, FlowFileTransformResult
from nifiapi.properties import PropertyDescriptor, ExpressionLanguageScope


# =============================================================================
# CITY / GOVERNORATE NORMALIZATION MAP
# =============================================================================

CITY_NORMALIZATION_MAP = {
    "cairo": "Cairo",
    "al qahira": "Cairo",
    "al-qahira": "Cairo",
    "alqahira": "Cairo",
    "alexandria": "Alexandria",
    "alex": "Alexandria",
    "al iskandariya": "Alexandria",
    "giza": "Giza",
    "al jizah": "Giza",
    "gizeh": "Giza",
    "aswan": "Aswan",
    "asswan": "Aswan",
    "luxor": "Luxor",
    "al uqsur": "Luxor",
    "asyut": "Asyut",
    "assiut": "Asyut",
    "beheira": "Beheira",
    "al buhayrah": "Beheira",
    "beni suef": "Beni Suef",
    "bani suwayf": "Beni Suef",
    "dakahlia": "Dakahlia",
    "dakhalia": "Dakahlia",
    "ad dakhaliyah": "Dakahlia",
    "damietta": "Damietta",
    "dimyat": "Damietta",
    "faiyum": "Faiyum",
    "al fayyum": "Faiyum",
    "gharbia": "Gharbia",
    "al gharbiyah": "Gharbia",
    "ismailia": "Ismailia",
    "al ismailiyah": "Ismailia",
    "kafr el sheikh": "Kafr El Sheikh",
    "kafr ash shaykh": "Kafr El Sheikh",
    "matrouh": "Matrouh",
    "matruh": "Matrouh",
    "minya": "Minya",
    "al minya": "Minya",
    "monufia": "Monufia",
    "al minufiyah": "Monufia",
    "menoufia": "Monufia",
    "new valley": "New Valley",
    "al wadi al jadid": "New Valley",
    "north sinai": "North Sinai",
    "shamal sina": "North Sinai",
    "port said": "Port Said",
    "bur said": "Port Said",
    "qalyubia": "Qalyubia",
    "al qalyubiyah": "Qalyubia",
    "qena": "Qena",
    "qina": "Qena",
    "red sea": "Red Sea",
    "al bahr al ahmar": "Red Sea",
    "sharqia": "Sharqia",
    "ash sharqiyah": "Sharqia",
    "sohag": "Sohag",
    "sawhaj": "Sohag",
    "south sinai": "South Sinai",
    "janub sina": "South Sinai",
    "suez": "Suez",
    "as suways": "Suez",
    "6th of october": "6th of October",
    "sheikh zayed": "Sheikh Zayed",
    "nasr city": "Cairo",
    "helwan": "Cairo",
    "maadi": "Cairo",
    "ballana": "Ballana",
    "fedutchi": "Fedutchi",
    "dahmit": "Dahmit",
}

# =============================================================================
# UNIFIED SCHEMA FIELD MAPPINGS
# =============================================================================

# Maps unified_field -> { "bhs": source_field(s), "ehvol": source_field(s) }
FIELD_MAPPINGS = {
    "participant_id": {
        "bhs": "Record ID",
        "ehvol": "DNA ID",
    },
    "source_record_id": {
        "bhs": "Record ID",
        "ehvol": "Record ID",
    },
    "date_of_birth": {
        "bhs": "Date of birth",
        "ehvol": "Date of Birth",
        "transform": "parse_date",
    },
    "age": {
        "bhs": "Age at enrollment",
        "ehvol": "Age",
        "transform": "parse_integer",
        "validation": {"type": "range", "min": 0, "max": 120},
    },
    "gender": {
        "bhs": "Gender",
        "ehvol": "Gender",
        "transform": "normalize_gender",
    },
    "nationality": {
        "bhs": "What ethnicity do you consider yourself?",
        "ehvol": "Nationality",
        "transform": "normalize_ethnicity",
    },
    "enrollment_date": {
        "bhs": "Enrollment date",
        "ehvol": "Date of Enrolment",
        "transform": "parse_date",
    },
    "current_city": {
        "bhs": "Address",
        "ehvol": "Current City of Residence",
        "transform": "normalize_city",
    },
    "childhood_city": {
        "bhs": "If mother is Egyptian, please specify city/",
        "ehvol": "City of Residence during childhood",
        "transform": "normalize_city",
    },
    "father_origin_city": {
        "bhs": "Father's gov of origin",
        "ehvol": "Father's City of Origin",
        "transform": "normalize_city",
    },
    "mother_origin_city": {
        "bhs": "Mother's gov of origin",
        "ehvol": None,
        "transform": "normalize_city",
    },
    "height_cm": {
        "bhs": "Height in cm",
        "ehvol": "Height (cm)",
        "transform": "parse_numeric",
        "validation": {"type": "range", "min": 50, "max": 250},
    },
    "weight_kg": {
        "bhs": "Weight in kg",
        "ehvol": "Weight (kg)",
        "transform": "parse_numeric",
        "validation": {"type": "range", "min": 2, "max": 300},
    },
    "bmi": {
        "bhs": "BMI",
        "ehvol": "BMI",
        "transform": "parse_numeric",
        "validation": {"type": "range", "min": 10, "max": 60},
    },
    "heart_rate": {
        "bhs": "Heart rate",
        "ehvol": "Heart Rate",
        "transform": "parse_numeric",
        "validation": {"type": "range", "min": 30, "max": 200},
    },
    "systolic_bp": {
        "bhs": [
            "Systolic Blood Pressure - Right Brachial - Measurement 1",
            "Systolic Blood Pressure - Right Brachial - Measurement 2",
            "Systolic Blood Pressure - Right Brachial - Measurement 3",
        ],
        "ehvol": "BP",
        "transform": "bp_systolic",
        "validation": {"type": "range", "min": 70, "max": 250},
    },
    "diastolic_bp": {
        "bhs": [
            "Diastolic Blood Pressure - Right Brachial - Measurement 1",
            "Diastolic Blood Pressure - Right Brachial - Measurement 2",
            "Diastolic Blood Pressure - Right Brachial - Measurement 3",
        ],
        "ehvol": "BP",
        "transform": "bp_diastolic",
        "validation": {"type": "range", "min": 40, "max": 150},
    },
    "hba1c": {
        "bhs": "HbA1c",
        "ehvol": "HbA1c",
        "transform": "parse_numeric",
        "validation": {"type": "range", "min": 3, "max": 20},
    },
    "troponin_i": {
        "bhs": "Troponin I",
        "ehvol": "Troponin I",
        "transform": "parse_numeric",
    },
    "echo_ef": {
        "bhs": "EF",
        "ehvol": "EF",
        "transform": "parse_numeric",
        "validation": {"type": "range", "min": 10, "max": 80},
    },
    "echo_date": {
        "bhs": "Date (Echocardiography)",
        "ehvol": "Echo Date",
        "transform": "parse_date",
    },
    "has_diabetes": {
        "bhs": "Do you have Diabetes?",
        "ehvol": "Diabetes Mellitus",
        "transform": "normalize_boolean",
    },
    "has_hypertension": {
        "bhs": None,
        "ehvol": "High blood pressure",
        "transform": "normalize_boolean",
    },
    "has_dyslipidemia": {
        "bhs": "Do you have Hyperlipidemia?",
        "ehvol": "Dyslipidemia",
        "transform": "normalize_boolean",
    },
    "has_heart_failure": {
        "bhs": "Have you been hospitalized due to heart failure?",
        "ehvol": "Prior Heart Failure (previous Hx)",
        "transform": "normalize_boolean",
    },
    "is_smoker": {
        "bhs": "What is your current smoking status?",
        "ehvol": "Current/Recent Smoker (< 1 year)",
        "transform": "normalize_boolean",
    },
    "smoking_pack_years": {
        "bhs": "Smoking Index (Current)",
        "ehvol": None,
        "transform": "parse_numeric",
    },
    "family_history_cad": {
        "bhs": "Has anyone in your family (parents, grandparents or siblings) experienced sudden death, MI, stroke, or hospitalization due to heart failure?",
        "ehvol": "Do any of your own children, parents or siblings have any of the following health conditions (choice=Heart Disease)",
        "transform": "normalize_boolean",
    },
    "family_history_diabetes": {
        "bhs": None,
        "ehvol": "Do any of your own children, parents or siblings have any of the following health conditions (choice=Diabetes)",
        "transform": "normalize_boolean",
    },
    "consanguineous_parents": {
        "bhs": "What is the familial relationship between your father and mother?",
        "ehvol": "Offspring of Consanguinous Marriage",
        "transform": "consanguinity",
    },
}


# =============================================================================
# TRANSFORM FUNCTIONS  (ported from biolink_etl/schema_mappings.py)
# =============================================================================

def _safe_str(value):
    """Safely convert to stripped string, return None for empty."""
    if value is None:
        return None
    s = str(value).strip()
    return s if s else None


def parse_date(value, dataset):
    if not (s := _safe_str(value)):
        return None

    # Normalize separators and trim time suffixes if present.
    s = re.split(r"[T ]", s, maxsplit=1)[0].strip()
    s = re.sub(r"[.]0+$", "", s)
    s = s.replace("\\", "/")

    # Support common date layouts seen in both registries.
    formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d.%m.%Y",
        "%m/%d/%Y",
        "%m-%d-%Y",
        "%m.%d.%Y",
        "%d/%m/%y",
        "%d-%m-%y",
        "%m/%d/%y",
        "%m-%d-%y",
    ]

    parsed = None
    for fmt in formats:
        try:
            parsed = datetime.strptime(s, fmt)
            break
        except ValueError:
            continue

    if parsed is None:
        return None

    # Reject clearly invalid years but keep older legitimate history (e.g., 2001).
    # Lower bound is intentionally broad (1900), upper bound allows slight future drift.
    min_year = 1900
    max_year = datetime.utcnow().year + 1
    if parsed.year < min_year or parsed.year > max_year:
        return None

    return parsed.strftime("%Y-%m-%d")


def parse_numeric(value, dataset):
    if not (s := _safe_str(value)):
        return None
    s = s.replace(",", "").replace(" ", "")
    # Handle ranges -> take average
    if "-" in s and s.replace("-", "").replace(".", "").isdigit():
        parts = s.split("-")
        if len(parts) == 2:
            try:
                return (float(parts[0]) + float(parts[1])) / 2
            except ValueError:
                pass
    try:
        return float(s)
    except ValueError:
        return None


def parse_integer(value, dataset):
    num = parse_numeric(value, dataset)
    return int(num) if num is not None else None


def normalize_gender(value, dataset):
    if not (s := _safe_str(value)):
        return None
    s = s.lower()
    if s in ("male", "m", "1", "boy", "man"):
        return "Male"
    if s in ("female", "f", "2", "girl", "woman"):
        return "Female"
    return None


def normalize_boolean(value, dataset):
    if not (s := _safe_str(value)):
        return None
    s = s.lower()
    if s in ("yes", "y", "true", "t", "1", "checked", "check"):
        return True
    if s in ("no", "n", "false", "f", "0", "unchecked", "uncheck"):
        return False
    return None


def normalize_city(value, dataset):
    if not (s := _safe_str(value)):
        return None
    city = s.lower()
    if city in CITY_NORMALIZATION_MAP:
        return CITY_NORMALIZATION_MAP[city]
    city_clean = re.sub(r"\s+(governorate|gov|city)$", "", city)
    city_clean = re.sub(r"^(the|el|al)\s+", "", city_clean)
    if city_clean in CITY_NORMALIZATION_MAP:
        return CITY_NORMALIZATION_MAP[city_clean]
    return s.title()


def normalize_ethnicity(value, dataset):
    if not (s := _safe_str(value)):
        return None
    eth = s.strip()
    elow = eth.lower()

    # Nubian variants (keep legacy keys)
    if elow in ("fedutchi", "fedicci", "fedici"):
        return "Nubian_Fedutchi"
    if elow in ("ballana", "ballena"):
        return "Nubian_Ballana"
    if elow in ("dahmit", "dahmeet"):
        return "Nubian_Dahmit"
    if "nubian" in elow:
        return "Nubian_Other"

    # Egyptian — catch many misspellings and Arabic/French variants
    # common latin-script misspellings
    egyptian_aliases = {
        "egyptian", "egyption", "egyptain", "egyptien", "egyptient",
        "egyptan", "egyptan", "egy", "egyp", "egiptian", "eg", "egp", "eyp"
    }
    token = re.sub(r"[^\w\u0600-\u06FF]+", "", elow)  # keep arabic letters too
    token_latin = re.sub(r"[^a-z]+", "", elow)
    if (
        any(a in token for a in ("egypt", "egyptian"))
        or token in egyptian_aliases
        or re.search(r"e[gq]y?p+t", token_latin)
    ):
        return "Egyptian"

    # Arabic script: look for root مصر / مصري / مصريه variants
    if re.search(r"مصر|مصري|مصرية|مصريه|مصريين|مصريين", eth):
        return "Egyptian"

    # Fallback: Title-case the original cleaned string
    return eth.title()


def normalize_bp(value, dataset):
    if not (s := _safe_str(value)):
        return None
    s = re.sub(r"\s*(mmhg|mm hg)$", "", s, flags=re.IGNORECASE)
    return parse_numeric(s, dataset)


def extract_systolic_bp(value, dataset):
    if not (s := _safe_str(value)):
        return None
    if "/" in s:
        return parse_numeric(s.split("/")[0], dataset)
    return normalize_bp(value, dataset)


def extract_diastolic_bp(value, dataset):
    if not (s := _safe_str(value)):
        return None
    if "/" in s:
        parts = s.split("/")
        if len(parts) > 1:
            return parse_numeric(parts[1], dataset)
    return None


def consanguinity_transform(value, dataset):
    """BHS uses free-text relationship, EHVol uses boolean."""
    if dataset == "ehvol":
        return normalize_boolean(value, dataset)
    if not (s := _safe_str(value)):
        return None
    return s.lower() not in ("none", "no", "", "not related")


# Dispatch table
TRANSFORM_FUNCTIONS = {
    "parse_date": parse_date,
    "parse_numeric": parse_numeric,
    "parse_integer": parse_integer,
    "normalize_gender": normalize_gender,
    "normalize_boolean": normalize_boolean,
    "normalize_city": normalize_city,
    "normalize_ethnicity": normalize_ethnicity,
    "bp_systolic": None,   # handled specially
    "bp_diastolic": None,  # handled specially
    "consanguinity": consanguinity_transform,
}



# =============================================================================
# FULL SCHEMA REGISTRY
# Generated from _schema_registry: 703 BHS + 161 EHVol mappings.
# Keys: original CSV column name  →  Value: standardised pg_col_name
# FIELD_MAPPINGS source keys take priority; this covers ALL remaining columns.
# =============================================================================

# BHS: original_name -> pg_col_name
BHS_REGISTRY = {
    "ALT": "alt",
    "AR": "ar",
    "AS": "as",
    "AST": "ast",
    "Abnormality (choice=None)": "abnormality_choice_none",
    "Abnormality (choice=Pathological Q waves)": "abnormality_choice_pathological_q_waves",
    "Abnormality (choice=ST-seg depression)": "abnormality_choice_st_seg_depression",
    "Abnormality (choice=ST-seg elevation)": "abnormality_choice_st_seg_elevation",
    "Abnormality (choice=T-wave inversion)": "abnormality_choice_t_wave_inversion",
    "Acute Rheumatic Fever (choice=(55) Rheumatic fever without heart involvement)": "acute_rheumatic_fever_choice_55_rheumatic_fever_without_heart_i",
    "Acute Rheumatic Fever (choice=(56) Rheumatic fever with heart involvement)": "acute_rheumatic_fever_choice_56_rheumatic_fever_with_heart_invo",
    "Acute Rheumatic Fever (choice=(57) Rheumatic chorea)": "acute_rheumatic_fever_choice_57_rheumatic_chorea",
    "Address": "address",
    "Age at enrollment": "age_at_enrollment",
    "Age at smoking cessation": "age_at_smoking_cessation",
    "Age at start of smoking": "age_at_start_of_smoking",
    "Agree to CMR": "agree_to_cmr",
    "Agree to CT": "agree_to_ct",
    "Agree to consent": "agree_to_consent",
    "Agree to have an ECG": "agree_to_have_an_ecg",
    "Agree to provide family history": "agree_to_provide_family_history",
    "Agree to undergo TTE": "agree_to_undergo_tte",
    "Agree to undergo carotid duplex": "agree_to_undergo_carotid_duplex",
    "Agree to withdraw samples for lab workup": "agree_to_withdraw_samples_for_lab_workup",
    "Albumin": "albumin",
    "Alternate contact 1 name": "alternate_contact_1_name",
    "Alternate contact 1 number -1": "alternate_contact_1_number_1",
    "Alternate contact 1 number -2": "alternate_contact_1_number_2",
    "Alternate contact 1 relation": "alternate_contact_1_relation",
    "Alternate contact 2 name": "alternate_contact_2_name",
    "Alternate contact 2 number -1": "alternate_contact_2_number_1",
    "Alternate contact 2 number -2": "alternate_contact_2_number_2",
    "Alternate contact 2 relation": "alternate_contact_2_relation",
    "Angina": "angina",
    "Any modifications to the medications that  study subject has been using before recruitment to BHS?": "any_modifications_to_the_medications_that_study_subject_has_bee",
    "Aortic annulus (mid systole)": "aortic_annulus_mid_systole",
    "Apex": "apex",
    "Apical - Anterior": "apical_anterior",
    "Apical - Inferior": "apical_inferior",
    "Apical - Lateral": "apical_lateral",
    "Apical - Septal": "apical_septal",
    "Atheromatous plaque - left": "atheromatous_plaque_left",
    "Atheromatous plaque - right": "atheromatous_plaque_right",
    "Average no. of cigarettes per day": "average_no_of_cigarettes_per_day",
    "BMI": "bmi",
    "BNP": "bnp",
    "BP Pressure chart / monitoring conclusion": "bp_pressure_chart_monitoring_conclusion",
    "Basal - Anterior": "basal_anterior",
    "Basal - Anterolateral": "basal_anterolateral",
    "Basal - Anteroseptal": "basal_anteroseptal",
    "Basal - Inferior": "basal_inferior",
    "Basal - Inferolateral": "basal_inferolateral",
    "Basal - Inferoseptal": "basal_inferoseptal",
    "Brachial pressure (highest side)": "brachial_pressure_highest_side",
    "CBC": "cbc",
    "CRP": "crp",
    "CRP.1": "crp_1",
    "CT - Specify": "ct_specify",
    "Ca": "ca",
    "Can you read and write in Arabic?": "can_you_read_and_write_in_arabic",
    "Can you speak Nubian?": "can_you_speak_nubian",
    "Cardiac Arrhythmias (choice=(58) Bradycardia/ bradyarrythmia)": "cardiac_arrhythmias_choice_58_bradycardia_bradyarrythmia",
    "Cardiac Arrhythmias (choice=(58.0) Sinus bradycardia)": "cardiac_arrhythmias_choice_58_0_sinus_bradycardia",
    "Cardiac Arrhythmias (choice=(58.1) Sick sinus syndrome)": "cardiac_arrhythmias_choice_58_1_sick_sinus_syndrome",
    "Cardiac Arrhythmias (choice=(58.2) Atrio-ventricular (AV) conduction block)": "cardiac_arrhythmias_choice_58_2_atrio_ventricular_av_conduction",
    "Cardiac Arrhythmias (choice=(58.2a)  ---- First degree AV block)": "cardiac_arrhythmias_choice_58_2a_first_degree_av_block",
    "Cardiac Arrhythmias (choice=(58.2b)  ---- Second degree AV block)": "cardiac_arrhythmias_choice_58_2b_second_degree_av_block",
    "Cardiac Arrhythmias (choice=(58.2c)  ---- Third degree AV block)": "cardiac_arrhythmias_choice_58_2c_third_degree_av_block",
    "Cardiac Arrhythmias (choice=(58.3) Intraventricular conduction abnormalities)": "cardiac_arrhythmias_choice_58_3_intraventricular_conduction_abn",
    "Cardiac Arrhythmias (choice=(59) Tachycardia/ tachyarrythmia)": "cardiac_arrhythmias_choice_59_tachycardia_tachyarrythmia",
    "Cardiac Arrhythmias (choice=(59.0) Supraventricular tachyarrythmia)": "cardiac_arrhythmias_choice_59_0_supraventricular_tachyarrythmia",
    "Cardiac Arrhythmias (choice=(59.1) Ventricular tachyarrythmia)": "cardiac_arrhythmias_choice_59_1_ventricular_tachyarrythmia",
    "Cardiac Arrhythmias (choice=---- Atrial fibrillation (AF))": "cardiac_arrhythmias_choice_atrial_fibrillation_af",
    "Cardiac Arrhythmias (choice=---- Atrial flutter)": "cardiac_arrhythmias_choice_atrial_flutter",
    "Cardiac Arrhythmias (choice=---- Atrial tachycardia)": "cardiac_arrhythmias_choice_atrial_tachycardia",
    "Cardiac Arrhythmias (choice=---- Premature supraventricular contractions)": "cardiac_arrhythmias_choice_premature_supraventricular_contracti",
    "Cardiac Arrhythmias (choice=---- Premature ventricular contractions)": "cardiac_arrhythmias_choice_premature_ventricular_contractions",
    "Cardiac Arrhythmias (choice=---- SVT/ PSVT/ AVRT/ AVNRT)": "cardiac_arrhythmias_choice_svt_psvt_avrt_avnrt",
    "Cardiac Arrhythmias (choice=---- Ventricular extrasystoles)": "cardiac_arrhythmias_choice_ventricular_extrasystoles",
    "Cardiac Arrhythmias (choice=---- Ventricular fibrillation (VF))": "cardiac_arrhythmias_choice_ventricular_fibrillation_vf",
    "Cardiac Arrhythmias (choice=---- Ventricular tachycardia (VT))": "cardiac_arrhythmias_choice_ventricular_tachycardia_vt",
    "Cardiac Arrhythmias (choice=---- bradycardia-tachycardia syndrome)": "cardiac_arrhythmias_choice_bradycardia_tachycardia_syndrome",
    "Cardiac Arrhythmias (choice=---- sinus pauses)": "cardiac_arrhythmias_choice_sinus_pauses",
    "Cardiac CT": "cardiac_ct",
    "Cardiac MRI": "cardiac_mri",
    "Carotid Duplex": "carotid_duplex",
    "Category": "category",
    "Category.1": "category_1",
    "Category.10": "category_10",
    "Category.11": "category_11",
    "Category.12": "category_12",
    "Category.13": "category_13",
    "Category.14": "category_14",
    "Category.2": "category_2",
    "Category.3": "category_3",
    "Category.4": "category_4",
    "Category.5": "category_5",
    "Category.6": "category_6",
    "Category.7": "category_7",
    "Category.8": "category_8",
    "Category.9": "category_9",
    "Cerebrovascular diseases (choice=(53) Acute disorders of cerebral circulation)": "cerebrovascular_diseases_choice_53_acute_disorders_of_cerebral_",
    "Cerebrovascular diseases (choice=(53.0) Transient ischemic attack (TIA))": "cerebrovascular_diseases_choice_53_0_transient_ischemic_attack_",
    "Cerebrovascular diseases (choice=(53.1) Stroke)": "cerebrovascular_diseases_choice_53_1_stroke",
    "Cerebrovascular diseases (choice=(54) Other cerebrovascular disease)": "cerebrovascular_diseases_choice_54_other_cerebrovascular_diseas",
    "Cerebrovascular diseases (choice=---- Haemorrhagic stroke)": "cerebrovascular_diseases_choice_haemorrhagic_stroke",
    "Cerebrovascular diseases (choice=---- Ischaemic stroke)": "cerebrovascular_diseases_choice_ischaemic_stroke",
    "Clinical - Ambulatory BP monitoring": "clinical_ambulatory_bp_monitoring",
    "Clinical - BP chart": "clinical_bp_chart",
    "Clinical - Clinical follow-up": "clinical_clinical_follow_up",
    "Complete?": "complete",
    "Complete?.1": "complete_1",
    "Complete?.10": "complete_10",
    "Complete?.11": "complete_11",
    "Complete?.12": "complete_12",
    "Complete?.13": "complete_13",
    "Complete?.2": "complete_2",
    "Complete?.3": "complete_3",
    "Complete?.4": "complete_4",
    "Complete?.5": "complete_5",
    "Complete?.6": "complete_6",
    "Complete?.7": "complete_7",
    "Complete?.8": "complete_8",
    "Complete?.9": "complete_9",
    "Complications of Heart Diseases (choice=(33) Cardiac septal defect, acquired)": "complications_of_heart_diseases_choice_33_cardiac_septal_defect",
    "Complications of Heart Diseases (choice=(34) Rupture of chordae tendineae, not elsewhere classified)": "complications_of_heart_diseases_choice_34_rupture_of_chordae_te",
    "Complications of Heart Diseases (choice=(35) Rupture of papillary muscle, not elsewhere classified)": "complications_of_heart_diseases_choice_35_rupture_of_papillary_",
    "Complications of Heart Diseases (choice=(36) Intracardiac thrombosis, not elsewhere classified)": "complications_of_heart_diseases_choice_36_intracardiac_thrombos",
    "Complications of Heart Diseases (choice=(37) Cardiomegaly)": "complications_of_heart_diseases_choice_37_cardiomegaly",
    "Complications of Heart Diseases (choice=(37.0) Right ventricular hypertrophy)": "complications_of_heart_diseases_choice_37_0_right_ventricular_h",
    "Complications of Heart Diseases (choice=(37.1) Left ventricular hypertrophy)": "complications_of_heart_diseases_choice_37_1_left_ventricular_hy",
    "Complications of Heart Diseases (choice=(38) Postcardiotomy syndrome)": "complications_of_heart_diseases_choice_38_postcardiotomy_syndro",
    "Congenital Heart Defect": "congenital_heart_defect",
    "Consent obtained": "consent_obtained",
    "Contact number 1": "contact_number_1",
    "Contact number 2": "contact_number_2",
    "Contact number 3": "contact_number_3",
    "Coronary Angiography / Angioplasty / Stenting": "coronary_angiography_angioplasty_stenting",
    "Coronary intervention decision (needs revision)": "coronary_intervention_decision_needs_revision",
    "Coronary intervention report 1": "coronary_intervention_report_1",
    "Coronary intervention report 2": "coronary_intervention_report_2",
    "Creatinine": "creatinine",
    "Current 10-Year ASCVD Risk (%)": "current_10_year_ascvd_risk",
    "Current age": "current_age",
    "Date": "date",
    "Date (ABI)": "date_abi",
    "Date (Clinical Exam)": "date_clinical_exam",
    "Date (Consent)": "date_consent",
    "Date (Demographic Data)": "date_demographic_data",
    "Date (Echocardiography)": "date_echocardiography",
    "Date (Family History)": "date_family_history",
    "Date (Medications)": "date_medications",
    "Date (Risk Factors)": "date_risk_factors",
    "Date (labs)": "date_labs",
    "Date (plan)": "date_plan",
    "Date of Cardotid Duplex": "date_of_cardotid_duplex",
    "Date of birth": "date_of_birth",
    "Date of cardiac CT": "date_of_cardiac_ct",
    "Date of cardiac MRI": "date_of_cardiac_mri",
    "Date of coronary intervention": "date_of_coronary_intervention",
    "Degenerative valve disease": "degenerative_valve_disease",
    "Diastolic Blood Pressure - Right Brachial - Measurement 1": "diastolic_blood_pressure_right_brachial_measurement_1",
    "Diastolic Blood Pressure - Right Brachial - Measurement 2": "diastolic_blood_pressure_right_brachial_measurement_2",
    "Diastolic Blood Pressure - Right Brachial - Measurement 3": "diastolic_blood_pressure_right_brachial_measurement_3",
    "Direct bilirubin": "direct_bilirubin",
    "Diseases of arteries, arterioles and capillaries (choice=(48) Atherosclerosis)": "diseases_of_arteries_arterioles_and_capillaries_choice_48_ather",
    "Diseases of arteries, arterioles and capillaries (choice=(49) Aortic aneurysm and dissection)": "diseases_of_arteries_arterioles_and_capillaries_choice_49_aorti",
    "Diseases of arteries, arterioles and capillaries (choice=(49.0) Dissection of aorta (any part))": "diseases_of_arteries_arterioles_and_capillaries_choice_49_0_dis",
    "Diseases of arteries, arterioles and capillaries (choice=(49.1) Thoracic aortic aneurysm)": "diseases_of_arteries_arterioles_and_capillaries_choice_49_1_tho",
    "Diseases of arteries, arterioles and capillaries (choice=(49.2) Abdominal aortic aneurysm)": "diseases_of_arteries_arterioles_and_capillaries_choice_49_2_abd",
    "Diseases of arteries, arterioles and capillaries (choice=(49.3) Thoracoabdominal aortic aneurysm)": "diseases_of_arteries_arterioles_and_capillaries_choice_49_3_tho",
    "Diseases of arteries, arterioles and capillaries (choice=(50) Other aneurysm)": "diseases_of_arteries_arterioles_and_capillaries_choice_50_other",
    "Diseases of arteries, arterioles and capillaries (choice=(51) Peripheral vascular disease)": "diseases_of_arteries_arterioles_and_capillaries_choice_51_perip",
    "Diseases of arteries, arterioles and capillaries (choice=(52) Arterial embolism and thrombosis)": "diseases_of_arteries_arterioles_and_capillaries_choice_52_arter",
    "Diseases of arteries, arterioles and capillaries (choice=---- Abdominal AA without rupture)": "diseases_of_arteries_arterioles_and_capillaries_choice_abdomina",
    "Diseases of arteries, arterioles and capillaries (choice=---- Intermittent claudication)": "diseases_of_arteries_arterioles_and_capillaries_choice_intermit",
    "Diseases of arteries, arterioles and capillaries (choice=---- Ruptured abdominal AA)": "diseases_of_arteries_arterioles_and_capillaries_choice_ruptured",
    "Diseases of arteries, arterioles and capillaries (choice=---- Ruptured thoracic AA)": "diseases_of_arteries_arterioles_and_capillaries_choice_ruptured",
    "Diseases of arteries, arterioles and capillaries (choice=---- Ruptured thoraco-abdominal AA)": "diseases_of_arteries_arterioles_and_capillaries_choice_ruptured",
    "Diseases of arteries, arterioles and capillaries (choice=---- Spasm of artery)": "diseases_of_arteries_arterioles_and_capillaries_choice_spasm_of",
    "Diseases of arteries, arterioles and capillaries (choice=---- Thoracic AA without rupture)": "diseases_of_arteries_arterioles_and_capillaries_choice_thoracic",
    "Diseases of arteries, arterioles and capillaries (choice=---- Thoraco-abdominal AA without rupture)": "diseases_of_arteries_arterioles_and_capillaries_choice_thoraco_",
    "Diseases of arteries, arterioles and capillaries (choice=---- arteriosclerosis)": "diseases_of_arteries_arterioles_and_capillaries_choice_arterios",
    "Diseases of arteries, arterioles and capillaries (choice=---- arteriosclerotic vascular disease)": "diseases_of_arteries_arterioles_and_capillaries_choice_arterios",
    "Diseases of arteries, arterioles and capillaries (choice=---- atheroma)": "diseases_of_arteries_arterioles_and_capillaries_choice_atheroma",
    "Diseases of arteries, arterioles and capillaries (choice=---- atherosclerosis)": "diseases_of_arteries_arterioles_and_capillaries_choice_atherosc",
    "Do any of your children have congenital malformations or diseases?": "do_any_of_your_children_have_congenital_malformations_or_diseas",
    "Do you consume alcohol?": "do_you_consume_alcohol",
    "Do you get it when you walk at an ordinary pace on the level?": "do_you_get_it_when_you_walk_at_an_ordinary_pace_on_the_level",
    "Do you get this pain or discomfort when you walk uphill or hurry?": "do_you_get_this_pain_or_discomfort_when_you_walk_uphill_or_hurr",
    "Do you have Diabetes?": "do_you_have_diabetes",
    "Do you have Erectile dysfunction?": "do_you_have_erectile_dysfunction",
    "Do you have Hyperlipidemia?": "do_you_have_hyperlipidemia",
    "Do you have Hypertension?": "do_you_have_hypertension",
    "Do you have more than one wife?": "do_you_have_more_than_one_wife",
    "Do you smoke shisha or cigarettes or both?": "do_you_smoke_shisha_or_cigarettes_or_both",
    "Does it go away when you stand still?": "does_it_go_away_when_you_stand_still",
    "ECG": "ecg",
    "ECG - PDF": "ecg_pdf",
    "ECG - XML": "ecg_xml",
    "ECG / Holter monitoring conclusion": "ecg_holter_monitoring_conclusion",
    "ECG Date": "ecg_date",
    "EF class": "ef_class",
    "Echocardiography": "echocardiography",
    "Ectopic beats": "ectopic_beats",
    "Electrolytes (Na, K, Ca, Mg ...)": "electrolytes_na_k_ca_mg",
    "Endocardium (choice=(23) Acute and subacute endocarditis)": "endocardium_choice_23_acute_and_subacute_endocarditis",
    "Endocardium (choice=(23.0) Rheumatic diseases of endocardium, valve unspecified)": "endocardium_choice_23_0_rheumatic_diseases_of_endocardium_valve",
    "Endocardium (choice=(23.1) Nonrheumatic mitral valve disorders)": "endocardium_choice_23_1_nonrheumatic_mitral_valve_disorders",
    "Endocardium (choice=(24) Endocarditis, valve unspecified)": "endocardium_choice_24_endocarditis_valve_unspecified",
    "Endocardium (choice=(24.0) Acute rheumatic endocarditis)": "endocardium_choice_24_0_acute_rheumatic_endocarditis",
    "Endocardium (choice=(25) Endocarditis and heart valve disorders in diseases classified elsewhere)": "endocardium_choice_25_endocarditis_and_heart_valve_disorders_in",
    "Enrollment date": "enrollment_date",
    "Exact duration of smoking cessation  * Please select the time unit in the next field (Years, Months, or Days)": "exact_duration_of_smoking_cessation_please_select_the_time_unit",
    "Extra notes": "extra_notes",
    "Fasting Blood Glucose": "fasting_blood_glucose",
    "Fasting blood sugar": "fasting_blood_sugar",
    "Father origins": "father_origins",
    "Father's gov of origin": "father_s_gov_of_origin",
    "Findings / Comments  (If there is any changes in parameters related to core clinical examination in recruitment sheet, please go the relevant fields and change accordingly)": "findings_comments_if_there_is_any_changes_in_parameters_related",
    "For any missing data in this sheet that CANNOT BE ACQUIRED NOW OR IN FUTURE: is it due to POOR ECHOCARDIOGRAPHY WINDOW or TECHNICAL DIFFICULTIES related to this patient? Please specify details in the next box.": "for_any_missing_data_in_this_sheet_that_cannot_be_acquired_now_",
    "Frequency": "frequency",
    "Frequency.1": "frequency_1",
    "Frequency.10": "frequency_10",
    "Frequency.11": "frequency_11",
    "Frequency.12": "frequency_12",
    "Frequency.13": "frequency_13",
    "Frequency.14": "frequency_14",
    "Frequency.2": "frequency_2",
    "Frequency.3": "frequency_3",
    "Frequency.4": "frequency_4",
    "Frequency.5": "frequency_5",
    "Frequency.6": "frequency_6",
    "Frequency.7": "frequency_7",
    "Frequency.8": "frequency_8",
    "Frequency.9": "frequency_9",
    "Further comments": "further_comments",
    "Further plan": "further_plan",
    "Further plan details": "further_plan_details",
    "Further plan document": "further_plan_document",
    "Gender": "gender",
    "HDL": "hdl",
    "Has anyone in your family (parents, grandparents or siblings) experienced sudden death, MI, stroke, or hospitalization due to heart failure?": "has_anyone_in_your_family_parents_grandparents_or_siblings_expe",
    "Have you been diagnosed with PVD?": "have_you_been_diagnosed_with_pvd",
    "Have you been diagnosed with RHD?": "have_you_been_diagnosed_with_rhd",
    "Have you been diagnosed with Renal disease?": "have_you_been_diagnosed_with_renal_disease",
    "Have you been diagnosed with Respiratory illnesses?": "have_you_been_diagnosed_with_respiratory_illnesses",
    "Have you been diagnosed with Rheumatic Fever?": "have_you_been_diagnosed_with_rheumatic_fever",
    "Have you been diagnosed with congenital heart disease?": "have_you_been_diagnosed_with_congenital_heart_disease",
    "Have you been hospitalized due to heart failure?": "have_you_been_hospitalized_due_to_heart_failure",
    "Have you ever been diagnosed with MI?": "have_you_ever_been_diagnosed_with_mi",
    "Have you ever had a severe pain across the front of your chest lasting for half an hour or more?": "have_you_ever_had_a_severe_pain_across_the_front_of_your_chest_",
    "Have you ever had any pain or discomfort in your chest?": "have_you_ever_had_any_pain_or_discomfort_in_your_chest",
    "Have you experienced shortness of breath?": "have_you_experienced_shortness_of_breath",
    "Have you had a prior Stroke or TIA?": "have_you_had_a_prior_stroke_or_tia",
    "Have you had any other cardiac procedures?": "have_you_had_any_other_cardiac_procedures",
    "Have you received Influenza Immunization within a YEAR?": "have_you_received_influenza_immunization_within_a_year",
    "Have you undergone a Coronary angioplasty/Stent?": "have_you_undergone_a_coronary_angioplasty_stent",
    "Have you undergone a prior CABG?": "have_you_undergone_a_prior_cabg",
    "HbA1C": "hba1c",
    "HbA1c": "hba1c",
    "Heart Failure (choice=(14) Acute Heart Failure)": "heart_failure_choice_14_acute_heart_failure",
    "Heart Failure (choice=(15) Left-sided heart failure)": "heart_failure_choice_15_left_sided_heart_failure",
    "Heart Failure (choice=(15.0) Heart failure with reduced ejection fraction (HFrEF) (EF?40%))": "heart_failure_choice_15_0_heart_failure_with_reduced_ejection_f",
    "Heart Failure (choice=(15.1) Heart failure with preserved ejection fraction (HFpEF) (EF?50%))": "heart_failure_choice_15_1_heart_failure_with_preserved_ejection",
    "Heart Failure (choice=(15.2) Heart failure with borderline ejection fraction (HFpEF) (EF=41-49%))": "heart_failure_choice_15_2_heart_failure_with_borderline_ejectio",
    "Heart Failure (choice=(16) Right-sided heart failure)": "heart_failure_choice_16_right_sided_heart_failure",
    "Heart rate": "heart_rate",
    "Height in cm": "height_in_cm",
    "Hematocrit": "hematocrit",
    "Hemoglobin": "hemoglobin",
    "Hip circumference in cm": "hip_circumference_in_cm",
    "Holter": "holter",
    "Household identifier": "household_identifier",
    "How soon?": "how_soon",
    "Hypertensive diseases (choice=(39) Essential (primary) hypertension)": "hypertensive_diseases_choice_39_essential_primary_hypertension",
    "Hypertensive diseases (choice=(39.0) Arterial hypertension)": "hypertensive_diseases_choice_39_0_arterial_hypertension",
    "Hypertensive diseases (choice=(40) Hypertensive heart disease)": "hypertensive_diseases_choice_40_hypertensive_heart_disease",
    "Hypertensive diseases (choice=(41) Hypertensive renal disease)": "hypertensive_diseases_choice_41_hypertensive_renal_disease",
    "Hypertensive diseases (choice=(41.0) Hypertensive nephropathy)": "hypertensive_diseases_choice_41_0_hypertensive_nephropathy",
    "Hypertensive diseases (choice=(42) Hypertensive heart disease and Hypertensive renal disease)": "hypertensive_diseases_choice_42_hypertensive_heart_disease_and_",
    "Hypertensive diseases (choice=(43) Secondary hypertension)": "hypertensive_diseases_choice_43_secondary_hypertension",
    "Hypertensive diseases (choice=(43.0) Renovascular hypertension)": "hypertensive_diseases_choice_43_0_renovascular_hypertension",
    "Hypotensive diseases (choice=(44) Idiopathic hypotension)": "hypotensive_diseases_choice_44_idiopathic_hypotension",
    "Hypotensive diseases (choice=(45) Orthostatic hypotension)": "hypotensive_diseases_choice_45_orthostatic_hypotension",
    "Hypotensive diseases (choice=(46) Hypotension due to drugs)": "hypotensive_diseases_choice_46_hypotension_due_to_drugs",
    "Hypotensive diseases (choice=(47) Hypotension, unspecified)": "hypotensive_diseases_choice_47_hypotension_unspecified",
    "IMT - left in mm": "imt_left_in_mm",
    "IMT - right in mm": "imt_right_in_mm",
    "INR": "inr",
    "If father is Egyptian, please specify city": "if_father_is_egyptian_please_specify_city",
    "If father is non-Egyptian, please specify": "if_father_is_non_egyptian_please_specify",
    "If mother is Egyptian, please specify city/": "if_mother_is_egyptian_please_specify_city",
    "If mother is non-Egyptian, please specify": "if_mother_is_non_egyptian_please_specify",
    "If other, specify": "if_other_specify",
    "If yes,  age of onset": "if_yes_age_of_onset",
    "If yes, please note MRN": "if_yes_please_note_mrn",
    "If yes, please specify": "if_yes_please_specify",
    "If yes, please specify age of onset": "if_yes_please_specify_age_of_onset",
    "If yes, please specify age of onset, and details.": "if_yes_please_specify_age_of_onset_and_details",
    "If yes, please specify age of onset.1": "if_yes_please_specify_age_of_onset_1",
    "If yes, please specify age of onset.2": "if_yes_please_specify_age_of_onset_2",
    "If yes, please specify age of onset.3": "if_yes_please_specify_age_of_onset_3",
    "If yes, please specify age of onset.4": "if_yes_please_specify_age_of_onset_4",
    "If yes, please specify date": "if_yes_please_specify_date",
    "If yes, please specify date of CABG": "if_yes_please_specify_date_of_cabg",
    "If yes, please specify details, and age of onset": "if_yes_please_specify_details_and_age_of_onset",
    "If yes, please specify disease": "if_yes_please_specify_disease",
    "If yes, please specify number and date of hospitalizations": "if_yes_please_specify_number_and_date_of_hospitalizations",
    "If yes, please specify the highest degree obtained": "if_yes_please_specify_the_highest_degree_obtained",
    "If yes, please specify type": "if_yes_please_specify_type",
    "If yes, please specify type and age of onset": "if_yes_please_specify_type_and_age_of_onset",
    "If yes, please specify type and date": "if_yes_please_specify_type_and_date",
    "If yes, stenosis % (LT)": "if_yes_stenosis_lt",
    "If yes, stenosis % (RT)": "if_yes_stenosis_rt",
    "In general, how would you rate your health today?": "in_general_how_would_you_rate_your_health_today",
    "Intervention required": "intervention_required",
    "Ischaemic heart diseases (choice=(10) Complications following acute myocardial infarction)": "ischaemic_heart_diseases_choice_10_complications_following_acut",
    "Ischaemic heart diseases (choice=(10.0) Haemopericardium)": "ischaemic_heart_diseases_choice_10_0_haemopericardium",
    "Ischaemic heart diseases (choice=(10.1) Atrial septal defect)": "ischaemic_heart_diseases_choice_10_1_atrial_septal_defect",
    "Ischaemic heart diseases (choice=(10.2) Ventricular septal defect)": "ischaemic_heart_diseases_choice_10_2_ventricular_septal_defect",
    "Ischaemic heart diseases (choice=(10.3) Rupture of cardiac wall without haemopericardium)": "ischaemic_heart_diseases_choice_10_3_rupture_of_cardiac_wall_wi",
    "Ischaemic heart diseases (choice=(10.4) Rupture of chordae tendineae)": "ischaemic_heart_diseases_choice_10_4_rupture_of_chordae_tendine",
    "Ischaemic heart diseases (choice=(10.5) Rupture of papillary muscle)": "ischaemic_heart_diseases_choice_10_5_rupture_of_papillary_muscl",
    "Ischaemic heart diseases (choice=(10.6) Thrombosis of atrium, auricular appendage, and ventricle)": "ischaemic_heart_diseases_choice_10_6_thrombosis_of_atrium_auric",
    "Ischaemic heart diseases (choice=(10.7) Other current complications following acute MI)": "ischaemic_heart_diseases_choice_10_7_other_current_complication",
    "Ischaemic heart diseases (choice=(12) Other acute ischaemic heart diseases)": "ischaemic_heart_diseases_choice_12_other_acute_ischaemic_heart_",
    "Ischaemic heart diseases (choice=(12.0) Coronary thrombosis not resulting in myocardial infarction)": "ischaemic_heart_diseases_choice_12_0_coronary_thrombosis_not_re",
    "Ischaemic heart diseases (choice=(12.1) Dresslers syndrome)": "ischaemic_heart_diseases_choice_12_1_dresslers_syndrome",
    "Ischaemic heart diseases (choice=(13) Chronic ischaemic heart disease)": "ischaemic_heart_diseases_choice_13_chronic_ischaemic_heart_dise",
    "Ischaemic heart diseases (choice=(13.0) Atherosclerotic cardiovascular disease)": "ischaemic_heart_diseases_choice_13_0_atherosclerotic_cardiovasc",
    "Ischaemic heart diseases (choice=(13.1) Atherosclerotic heart disease)": "ischaemic_heart_diseases_choice_13_1_atherosclerotic_heart_dise",
    "Ischaemic heart diseases (choice=(13.2) Old myocardial infarction)": "ischaemic_heart_diseases_choice_13_2_old_myocardial_infarction",
    "Ischaemic heart diseases (choice=(13.3) Aneurysm of heart)": "ischaemic_heart_diseases_choice_13_3_aneurysm_of_heart",
    "Ischaemic heart diseases (choice=(13.4) Coronary artery aneurysm)": "ischaemic_heart_diseases_choice_13_4_coronary_artery_aneurysm",
    "Ischaemic heart diseases (choice=(13.5) Ischaemic cardiomyopathy)": "ischaemic_heart_diseases_choice_13_5_ischaemic_cardiomyopathy",
    "Ischaemic heart diseases (choice=(13.6) Silent myocardial ischaemia)": "ischaemic_heart_diseases_choice_13_6_silent_myocardial_ischaemi",
    "Ischaemic heart diseases (choice=(13.7) Other forms of chronic ischaemic heart disease)": "ischaemic_heart_diseases_choice_13_7_other_forms_of_chronic_isc",
    "Ischaemic heart diseases (choice=(9) Acute coronary syndrome)": "ischaemic_heart_diseases_choice_9_acute_coronary_syndrome",
    "Ischaemic heart diseases (choice=(9.0) Non-ST-elevation acute coronary syndrome (NSTE-ACS))": "ischaemic_heart_diseases_choice_9_0_non_st_elevation_acute_coro",
    "Ischaemic heart diseases (choice=(9.1) ST-elevation acute coronary syndrome (STE-ACS))": "ischaemic_heart_diseases_choice_9_1_st_elevation_acute_coronary",
    "Ischaemic heart diseases (choice=----- Non-ST-Elevation myocardial infarct (NSTEMI))": "ischaemic_heart_diseases_choice_non_st_elevation_myocardial_inf",
    "Ischaemic heart diseases (choice=----- Unstable Angina)": "ischaemic_heart_diseases_choice_unstable_angina",
    "K": "k",
    "Kidney functions": "kidney_functions",
    "LA diameter - PLAX": "la_diameter_plax",
    "LA volume - Simpson's": "la_volume_simpson_s",
    "LDL": "ldl",
    "LV diastolic dysfunction": "lv_diastolic_dysfunction",
    "LV size": "lv_size",
    "LVEDD": "lvedd",
    "LVEF - M mode": "lvef_m_mode",
    "LVEF - Simpson's": "lvef_simpson_s",
    "LVEF - Visual": "lvef_visual",
    "LVESD": "lvesd",
    "LVH": "lvh",
    "LVH.1": "lvh_1",
    "Left anterior tibial ABI": "left_anterior_tibial_abi",
    "Left anterior tibial pressure": "left_anterior_tibial_pressure",
    "Left atrial size": "left_atrial_size",
    "Left posterior tibial ABI": "left_posterior_tibial_abi",
    "Left posterior tibial pressure": "left_posterior_tibial_pressure",
    "Life Sciences re-sampling": "life_sciences_re_sampling",
    "Lifetime ASCVD risk (%)": "lifetime_ascvd_risk",
    "Lipid profile": "lipid_profile",
    "Liver functions": "liver_functions",
    "Lower limb Duplex": "lower_limb_duplex",
    "MCH": "mch",
    "MCHC": "mchc",
    "MCV": "mcv",
    "MR": "mr",
    "MRI - Specify": "mri_specify",
    "MRN (AHC)": "mrn_ahc",
    "MRN (BU)": "mrn_bu",
    "MS": "ms",
    "Major category (choice=CHD)": "major_category_choice_chd",
    "Major category (choice=Cardiomyopathy)": "major_category_choice_cardiomyopathy",
    "Major category (choice=HF)": "major_category_choice_hf",
    "Major category (choice=IHD)": "major_category_choice_ihd",
    "Major category (choice=None)": "major_category_choice_none",
    "Major category (choice=Other CV disease)": "major_category_choice_other_cv_disease",
    "Major category (choice=Other co-morbdidites / risk factors)": "major_category_choice_other_co_morbdidites_risk_factors",
    "Major category (choice=PHT)": "major_category_choice_pht",
    "Major category (choice=RHD)": "major_category_choice_rhd",
    "Major category (choice=Valvular)": "major_category_choice_valvular",
    "Mg": "mg",
    "Midventricular - Anterior": "midventricular_anterior",
    "Midventricular - Anterolateral": "midventricular_anterolateral",
    "Midventricular - Anteroseptal": "midventricular_anteroseptal",
    "Midventricular - Inferior": "midventricular_inferior",
    "Midventricular - Inferolateral": "midventricular_inferolateral",
    "Midventricular - Inferoseptal": "midventricular_inferoseptal",
    "Moderate or severe valvular lesion": "moderate_or_severe_valvular_lesion",
    "Mother origins": "mother_origins",
    "Mother's gov of origin": "mother_s_gov_of_origin",
    "Myocardial perfusion imaging": "myocardial_perfusion_imaging",
    "Myocardium / Cardiomyopathy (choice=(17) Acute myocarditis)": "myocardium_cardiomyopathy_choice_17_acute_myocarditis",
    "Myocardium / Cardiomyopathy (choice=(18) Chronic myocarditis)": "myocardium_cardiomyopathy_choice_18_chronic_myocarditis",
    "Myocardium / Cardiomyopathy (choice=(19) Myocarditis in diseases classified elsewhere)": "myocardium_cardiomyopathy_choice_19_myocarditis_in_diseases_cla",
    "Myocardium / Cardiomyopathy (choice=(19.0)  Rheumatic myocarditis)": "myocardium_cardiomyopathy_choice_19_0_rheumatic_myocarditis",
    "Myocardium / Cardiomyopathy (choice=(20) Myocardial degeneration)": "myocardium_cardiomyopathy_choice_20_myocardial_degeneration",
    "Myocardium / Cardiomyopathy (choice=(21) Cardiomyopathy)": "myocardium_cardiomyopathy_choice_21_cardiomyopathy",
    "Myocardium / Cardiomyopathy (choice=(21.0) Dilated cardiomyopathy)": "myocardium_cardiomyopathy_choice_21_0_dilated_cardiomyopathy",
    "Myocardium / Cardiomyopathy (choice=(21.1) Obstructive hypertrophy cardiomyopathy)": "myocardium_cardiomyopathy_choice_21_1_obstructive_hypertrophy_c",
    "Myocardium / Cardiomyopathy (choice=(21.2) Other hypertrophic cardiomyopathy)": "myocardium_cardiomyopathy_choice_21_2_other_hypertrophic_cardio",
    "Myocardium / Cardiomyopathy (choice=(21.3) Endomyocardial (eosinophilic) disease)": "myocardium_cardiomyopathy_choice_21_3_endomyocardial_eosinophil",
    "Myocardium / Cardiomyopathy (choice=(21.4) Endocardial fibroelastosis)": "myocardium_cardiomyopathy_choice_21_4_endocardial_fibroelastosi",
    "Myocardium / Cardiomyopathy (choice=(21.5) Other restrictive cardiomyopathy)": "myocardium_cardiomyopathy_choice_21_5_other_restrictive_cardiom",
    "Myocardium / Cardiomyopathy (choice=(21.6) Alcoholic cardiomyopathy)": "myocardium_cardiomyopathy_choice_21_6_alcoholic_cardiomyopathy",
    "Myocardium / Cardiomyopathy (choice=(21.8) Other cardiomyopathies)": "myocardium_cardiomyopathy_choice_21_8_other_cardiomyopathies",
    "Myocardium / Cardiomyopathy (choice=(22) Cardiomyopathy in diseases classified elsewhere)": "myocardium_cardiomyopathy_choice_22_cardiomyopathy_in_diseases_",
    "Myocardium / Cardiomyopathy (choice=---- Arrhythmogenic right ventricular dysplasia)": "myocardium_cardiomyopathy_choice_arrhythmogenic_right_ventricul",
    "Myocardium / Cardiomyopathy (choice=---- Endomyocardial (tropical) fibrosis)": "myocardium_cardiomyopathy_choice_endomyocardial_tropical_fibros",
    "Myocardium / Cardiomyopathy (choice=---- Eosinophilic myocarditis)": "myocardium_cardiomyopathy_choice_eosinophilic_myocarditis",
    "Myocardium / Cardiomyopathy (choice=---- Loefflers endocarditis)": "myocardium_cardiomyopathy_choice_loefflers_endocarditis",
    "Myxomatous valve disease": "myxomatous_valve_disease",
    "Myxomatous valve(s) (choice=Aortic)": "myxomatous_valve_s_choice_aortic",
    "Myxomatous valve(s) (choice=Mitral)": "myxomatous_valve_s_choice_mitral",
    "Myxomatous valve(s) (choice=Pulmonary)": "myxomatous_valve_s_choice_pulmonary",
    "Myxomatous valve(s) (choice=Tricuspid)": "myxomatous_valve_s_choice_tricuspid",
    "Na": "na",
    "Name": "name",
    "Name.1": "name_1",
    "Name.10": "name_10",
    "Name.11": "name_11",
    "Name.12": "name_12",
    "Name.13": "name_13",
    "Name.14": "name_14",
    "Name.2": "name_2",
    "Name.3": "name_3",
    "Name.4": "name_4",
    "Name.5": "name_5",
    "Name.6": "name_6",
    "Name.7": "name_7",
    "Name.8": "name_8",
    "Name.9": "name_9",
    "Native AV morphology": "native_av_morphology",
    "Optimal ASCVD Risk": "optimal_ascvd_risk",
    "Other co-morbidities  / risk factors (choice=Diabetes mellitus)": "other_co_morbidities_risk_factors_choice_diabetes_mellitus",
    "Other co-morbidities  / risk factors (choice=Dyslipidemia)": "other_co_morbidities_risk_factors_choice_dyslipidemia",
    "Other co-morbidities  / risk factors (choice=Familial hypercholesterolemia)": "other_co_morbidities_risk_factors_choice_familial_hypercholeste",
    "Other co-morbidities  / risk factors (choice=Hypertension)": "other_co_morbidities_risk_factors_choice_hypertension",
    "Other co-morbidities  / risk factors (choice=None)": "other_co_morbidities_risk_factors_choice_none",
    "Other co-morbidities  / risk factors (choice=Other)": "other_co_morbidities_risk_factors_choice_other",
    "Other echocardiographic findings": "other_echocardiographic_findings",
    "Other ethnicity": "other_ethnicity",
    "Other laboratory results to report": "other_laboratory_results_to_report",
    "Others imaging modality- Specify": "others_imaging_modality_specify",
    "Others lab work - Specify": "others_lab_work_specify",
    "PASP": "pasp",
    "PR": "pr",
    "PS": "ps",
    "PWT": "pwt",
    "Participant's Name": "participant_s_name",
    "Pedigree": "pedigree",
    "Pericardium (choice=(26) Acute pericarditis)": "pericardium_choice_26_acute_pericarditis",
    "Pericardium (choice=(26.0) Acute rheumatic pericarditis)": "pericardium_choice_26_0_acute_rheumatic_pericarditis",
    "Pericardium (choice=(27) Chronic pericarditis)": "pericardium_choice_27_chronic_pericarditis",
    "Pericardium (choice=(27.0) Chronic adhesive pericarditis)": "pericardium_choice_27_0_chronic_adhesive_pericarditis",
    "Pericardium (choice=(27.1) Chronic constrictive pericarditis)": "pericardium_choice_27_1_chronic_constrictive_pericarditis",
    "Pericardium (choice=(27.2) Chronic rheumatic pericarditis)": "pericardium_choice_27_2_chronic_rheumatic_pericarditis",
    "Pericardium (choice=(28) Other diseases of pericardium)": "pericardium_choice_28_other_diseases_of_pericardium",
    "Pericardium (choice=(28.0) Haemopericardium, not elsewhere classified)": "pericardium_choice_28_0_haemopericardium_not_elsewhere_classifi",
    "Pericardium (choice=(28.1) Pericardial effusion (noninflammatory))": "pericardium_choice_28_1_pericardial_effusion_noninflammatory",
    "Pericardium (choice=(29) Other specified diseases of pericardium)": "pericardium_choice_29_other_specified_diseases_of_pericardium",
    "Pericardium (choice=(29.0) Cardiac tamponade)": "pericardium_choice_29_0_cardiac_tamponade",
    "Pericardium (choice=(30) Pericarditis in diseases classified elsewhere)": "pericardium_choice_30_pericarditis_in_diseases_classified_elsew",
    "Pericardium (choice=Normal)": "pericardium_choice_normal",
    "Pericardium (choice=calcified)": "pericardium_choice_calcified",
    "Pericardium (choice=effusion)": "pericardium_choice_effusion",
    "Platelet count": "platelet_count",
    "Prescription document by BHS clinic": "prescription_document_by_bhs_clinic",
    "Present, or most recent past, occupation": "present_or_most_recent_past_occupation",
    "Previous Patient at AHC": "previous_patient_at_ahc",
    "Pulmonary hypertension": "pulmonary_hypertension",
    "Pulmonary vascular disease  (choice=(31) Pulmonary hypertension)": "pulmonary_vascular_disease_choice_31_pulmonary_hypertension",
    "Pulmonary vascular disease  (choice=(31.0) Pulmonary arterial hypertension)": "pulmonary_vascular_disease_choice_31_0_pulmonary_arterial_hyper",
    "Pulmonary vascular disease  (choice=(31.1) Pulmonary hypertension due to left-heart disease (pulmonary venous hypertension))": "pulmonary_vascular_disease_choice_31_1_pulmonary_hypertension_d",
    "Pulmonary vascular disease  (choice=(31.2) Pulmonary hypertension associated with respiratory or chronic hypoxic lung disease)": "pulmonary_vascular_disease_choice_31_2_pulmonary_hypertension_a",
    "Pulmonary vascular disease  (choice=(32) Pulmonary embolism)": "pulmonary_vascular_disease_choice_32_pulmonary_embolism",
    "Pulmonary vascular disease  (choice=(32.3) Chronic thromboembolic/ embolic pulmonary hypertension)": "pulmonary_vascular_disease_choice_32_3_chronic_thromboembolic_e",
    "Pulmonary vascular disease  (choice=(32.4) Pulmonary hypertension from unclear mechanisms)": "pulmonary_vascular_disease_choice_32_4_pulmonary_hypertension_f",
    "Pulmonary vascular disease  (choice=---- COPD / interstitial lung disease)": "pulmonary_vascular_disease_choice_copd_interstitial_lung_diseas",
    "Pulmonary vascular disease  (choice=---- Chronic kindey failure)": "pulmonary_vascular_disease_choice_chronic_kindey_failure",
    "Pulmonary vascular disease  (choice=---- Congenital heart disease)": "pulmonary_vascular_disease_choice_congenital_heart_disease",
    "Pulmonary vascular disease  (choice=---- Idiopathic / Primary)": "pulmonary_vascular_disease_choice_idiopathic_primary",
    "Pulmonary vascular disease  (choice=---- LV Systolic dysfunction)": "pulmonary_vascular_disease_choice_lv_systolic_dysfunction",
    "Pulmonary vascular disease  (choice=---- LV diastolic dysfunction)": "pulmonary_vascular_disease_choice_lv_diastolic_dysfunction",
    "Pulmonary vascular disease  (choice=---- Metabolic disorder)": "pulmonary_vascular_disease_choice_metabolic_disorder",
    "Pulmonary vascular disease  (choice=---- Obstructive sleep apnea)": "pulmonary_vascular_disease_choice_obstructive_sleep_apnea",
    "Pulmonary vascular disease  (choice=---- Secondary to systemic disorders)": "pulmonary_vascular_disease_choice_secondary_to_systemic_disorde",
    "Pulmonary vascular disease  (choice=---- Systemic disorder)": "pulmonary_vascular_disease_choice_systemic_disorder",
    "Pulmonary vascular disease  (choice=---- Valvular heart Disease)": "pulmonary_vascular_disease_choice_valvular_heart_disease",
    "QRS duration": "qrs_duration",
    "QRS width >= 120 ms": "qrs_width_120_ms",
    "QT interval": "qt_interval",
    "RBCs": "rbcs",
    "RDW": "rdw",
    "RHD-affected valves (choice=Aortic)": "rhd_affected_valves_choice_aortic",
    "RHD-affected valves (choice=Mitral)": "rhd_affected_valves_choice_mitral",
    "RHD-affected valves (choice=Pulmonary)": "rhd_affected_valves_choice_pulmonary",
    "RHD-affected valves (choice=Tricuspid)": "rhd_affected_valves_choice_tricuspid",
    "RV diameters - basal": "rv_diameters_basal",
    "RV diameters - longitudinal": "rv_diameters_longitudinal",
    "RV diameters - mild": "rv_diameters_mild",
    "RV size": "rv_size",
    "RWMA Index": "rwma_index",
    "RWMA Score": "rwma_score",
    "Random Blood Glucose": "random_blood_glucose",
    "Record ID": "record_id",
    "Refer to AHC clinic - BMV": "refer_to_ahc_clinic_bmv",
    "Refer to AHC clinic - EP": "refer_to_ahc_clinic_ep",
    "Refer to AHC clinic - GUCH": "refer_to_ahc_clinic_guch",
    "Refer to AHC clinic - General": "refer_to_ahc_clinic_general",
    "Refer to AHC clinic - Heart failure": "refer_to_ahc_clinic_heart_failure",
    "Refer to AHC clinic - LVAD": "refer_to_ahc_clinic_lvad",
    "Refer to AHC clinic - Other - Specify": "refer_to_ahc_clinic_other_specify",
    "Refer to AHC clinic - Pulmonary": "refer_to_ahc_clinic_pulmonary",
    "Refer to AHC clinic - TAVI": "refer_to_ahc_clinic_tavi",
    "Refer to another speciality clinic - Specify": "refer_to_another_speciality_clinic_specify",
    "Regional wall motion abnormalities": "regional_wall_motion_abnormalities",
    "Relative 1 age at event": "relative_1_age_at_event",
    "Relative 1 event": "relative_1_event",
    "Relative 1 gender": "relative_1_gender",
    "Relative 1 relation": "relative_1_relation",
    "Relative 10 age at event": "relative_10_age_at_event",
    "Relative 10 event": "relative_10_event",
    "Relative 10 gender": "relative_10_gender",
    "Relative 10 relation": "relative_10_relation",
    "Relative 2 age at event": "relative_2_age_at_event",
    "Relative 2 event": "relative_2_event",
    "Relative 2 gender": "relative_2_gender",
    "Relative 2 relation": "relative_2_relation",
    "Relative 3 age at event": "relative_3_age_at_event",
    "Relative 3 event": "relative_3_event",
    "Relative 3 gender": "relative_3_gender",
    "Relative 3 relation": "relative_3_relation",
    "Relative 4 age at event": "relative_4_age_at_event",
    "Relative 4 event": "relative_4_event",
    "Relative 4 gender": "relative_4_gender",
    "Relative 4 relation": "relative_4_relation",
    "Relative 5 age at event": "relative_5_age_at_event",
    "Relative 5 event": "relative_5_event",
    "Relative 5 gender": "relative_5_gender",
    "Relative 5 relation": "relative_5_relation",
    "Relative 6 age at event": "relative_6_age_at_event",
    "Relative 6 event": "relative_6_event",
    "Relative 6 gender": "relative_6_gender",
    "Relative 6 relation": "relative_6_relation",
    "Relative 7 age at event": "relative_7_age_at_event",
    "Relative 7 event": "relative_7_event",
    "Relative 7 gender": "relative_7_gender",
    "Relative 7 relation": "relative_7_relation",
    "Relative 8 age at event": "relative_8_age_at_event",
    "Relative 8 event": "relative_8_event",
    "Relative 8 gender": "relative_8_gender",
    "Relative 8 relation": "relative_8_relation",
    "Relative 9 age at event": "relative_9_age_at_event",
    "Relative 9 event": "relative_9_event",
    "Relative 9 gender": "relative_9_gender",
    "Relative 9 relation": "relative_9_relation",
    "Renal Duplex": "renal_duplex",
    "Results": "results",
    "Rheumatic valvular heart disease": "rheumatic_valvular_heart_disease",
    "Rhythm in ECG": "rhythm_in_ecg",
    "Right anterior tibial ABI": "right_anterior_tibial_abi",
    "Right anterior tibial pressure": "right_anterior_tibial_pressure",
    "Right posterior tibial ABI": "right_posterior_tibial_abi",
    "Right posterior tibial pressure": "right_posterior_tibial_pressure",
    "Route": "route",
    "Route.1": "route_1",
    "Route.10": "route_10",
    "Route.11": "route_11",
    "Route.12": "route_12",
    "Route.13": "route_13",
    "Route.14": "route_14",
    "Route.2": "route_2",
    "Route.3": "route_3",
    "Route.4": "route_4",
    "Route.5": "route_5",
    "Route.6": "route_6",
    "Route.7": "route_7",
    "Route.8": "route_8",
    "Route.9": "route_9",
    "SWT": "swt",
    "Serum triglycerides": "serum_triglycerides",
    "Shisha: How many minutes per session?": "shisha_how_many_minutes_per_session",
    "Shisha: How many sessions per day?": "shisha_how_many_sessions_per_day",
    "Sino-tubular junction (end diastole)": "sino_tubular_junction_end_diastole",
    "Sinus of Valsalva (end diastole)": "sinus_of_valsalva_end_diastole",
    "Smoking Index (Current)": "smoking_index_current",
    "Smoking Index (Former)": "smoking_index_former",
    "Smoking years": "smoking_years",
    "Specify CT scan region(s) of interest": "specify_ct_scan_region_s_of_interest",
    "Specify MRI scan region(s) of interest": "specify_mri_scan_region_s_of_interest",
    "Specify X-Ray region(s) of interest": "specify_x_ray_region_s_of_interest",
    "Specify congenital defect": "specify_congenital_defect",
    "Specify degenerated valve(s) (choice=Aortic)": "specify_degenerated_valve_s_choice_aortic",
    "Specify degenerated valve(s) (choice=Mitral)": "specify_degenerated_valve_s_choice_mitral",
    "Specify degenerated valve(s) (choice=Pulmonary)": "specify_degenerated_valve_s_choice_pulmonary",
    "Specify degenerated valve(s) (choice=Tricuspid)": "specify_degenerated_valve_s_choice_tricuspid",
    "Specify other AHC clinic referral": "specify_other_ahc_clinic_referral",
    "Specify other lab work": "specify_other_lab_work",
    "Specify other requested imaging modality(ies)": "specify_other_requested_imaging_modality_ies",
    "Specify speciality clinic referral": "specify_speciality_clinic_referral",
    "Status": "status",
    "Status.1": "status_1",
    "Status.10": "status_10",
    "Status.11": "status_11",
    "Status.12": "status_12",
    "Status.13": "status_13",
    "Status.14": "status_14",
    "Status.2": "status_2",
    "Status.3": "status_3",
    "Status.4": "status_4",
    "Status.5": "status_5",
    "Status.6": "status_6",
    "Status.7": "status_7",
    "Status.8": "status_8",
    "Status.9": "status_9",
    "Subject is on treatment?": "subject_is_on_treatment",
    "Systolic Blood Pressure - Right Brachial - Measurement 1": "systolic_blood_pressure_right_brachial_measurement_1",
    "Systolic Blood Pressure - Right Brachial - Measurement 2": "systolic_blood_pressure_right_brachial_measurement_2",
    "Systolic Blood Pressure - Right Brachial - Measurement 3": "systolic_blood_pressure_right_brachial_measurement_3",
    "T3": "t3",
    "T4": "t4",
    "TAPSE": "tapse",
    "TLC": "tlc",
    "TR": "tr",
    "TS": "ts",
    "TSH": "tsh",
    "Thyroid functions": "thyroid_functions",
    "Time unit for smoking cessation duration": "time_unit_for_smoking_cessation_duration",
    "Total bilirubin": "total_bilirubin",
    "Total cholesterol": "total_cholesterol",
    "Total daily dose": "total_daily_dose",
    "Total daily dose.1": "total_daily_dose_1",
    "Total daily dose.10": "total_daily_dose_10",
    "Total daily dose.11": "total_daily_dose_11",
    "Total daily dose.12": "total_daily_dose_12",
    "Total daily dose.13": "total_daily_dose_13",
    "Total daily dose.14": "total_daily_dose_14",
    "Total daily dose.2": "total_daily_dose_2",
    "Total daily dose.3": "total_daily_dose_3",
    "Total daily dose.4": "total_daily_dose_4",
    "Total daily dose.5": "total_daily_dose_5",
    "Total daily dose.6": "total_daily_dose_6",
    "Total daily dose.7": "total_daily_dose_7",
    "Total daily dose.8": "total_daily_dose_8",
    "Total daily dose.9": "total_daily_dose_9",
    "Troponin": "troponin",
    "Tubular ascending aorta (end-diastole) distance from sinotubular junction": "tubular_ascending_aorta_end_diastole_distance_from_sinotubular_",
    "Tubular ascending aorta (end-diastole) max diameter": "tubular_ascending_aorta_end_diastole_max_diameter",
    "Upload consent scan 1": "upload_consent_scan_1",
    "Upload consent scan 2": "upload_consent_scan_2",
    "Upper limb Duplex": "upper_limb_duplex",
    "Urea": "urea",
    "Valvular Heart Disease (choice=(1) Congenital)": "valvular_heart_disease_choice_1_congenital",
    "Valvular Heart Disease (choice=(2) Rheumatic)": "valvular_heart_disease_choice_2_rheumatic",
    "Valvular Heart Disease (choice=(3) Degenerative)": "valvular_heart_disease_choice_3_degenerative",
    "Valvular Heart Disease (choice=(4) Mitral valve diseases)": "valvular_heart_disease_choice_4_mitral_valve_diseases",
    "Valvular Heart Disease (choice=(4.0) Mitral stenosis)": "valvular_heart_disease_choice_4_0_mitral_stenosis",
    "Valvular Heart Disease (choice=(4.1) mitral insufficiency)": "valvular_heart_disease_choice_4_1_mitral_insufficiency",
    "Valvular Heart Disease (choice=(4.2) Mitral stenosis with insufficiency)": "valvular_heart_disease_choice_4_2_mitral_stenosis_with_insuffic",
    "Valvular Heart Disease (choice=(4.3) Mitral (valve) prolapse)": "valvular_heart_disease_choice_4_3_mitral_valve_prolapse",
    "Valvular Heart Disease (choice=(5) Aortic valve diseases)": "valvular_heart_disease_choice_5_aortic_valve_diseases",
    "Valvular Heart Disease (choice=(5.0) Aortic stenosis)": "valvular_heart_disease_choice_5_0_aortic_stenosis",
    "Valvular Heart Disease (choice=(5.1) Aortic insufficiency)": "valvular_heart_disease_choice_5_1_aortic_insufficiency",
    "Valvular Heart Disease (choice=(5.2) Aortic stenosis with insufficiency)": "valvular_heart_disease_choice_5_2_aortic_stenosis_with_insuffic",
    "Valvular Heart Disease (choice=(5.3) Bicuspid aortic valve)": "valvular_heart_disease_choice_5_3_bicuspid_aortic_valve",
    "Valvular Heart Disease (choice=(6) Tricuspid valve diseases)": "valvular_heart_disease_choice_6_tricuspid_valve_diseases",
    "Valvular Heart Disease (choice=(6.0) Tricuspid stenosis)": "valvular_heart_disease_choice_6_0_tricuspid_stenosis",
    "Valvular Heart Disease (choice=(6.1) Tricuspid insufficiency)": "valvular_heart_disease_choice_6_1_tricuspid_insufficiency",
    "Valvular Heart Disease (choice=(6.2) Tricuspid stenosis with insufficiency)": "valvular_heart_disease_choice_6_2_tricuspid_stenosis_with_insuf",
    "Valvular Heart Disease (choice=(7) Pulmonary valve diseases)": "valvular_heart_disease_choice_7_pulmonary_valve_diseases",
    "Valvular Heart Disease (choice=(7.0) Pulmonary stenosis)": "valvular_heart_disease_choice_7_0_pulmonary_stenosis",
    "Valvular Heart Disease (choice=(7.1) Pulmonary insufficiency)": "valvular_heart_disease_choice_7_1_pulmonary_insufficiency",
    "Valvular Heart Disease (choice=(7.2) Pulmonary stenosis with insufficiency)": "valvular_heart_disease_choice_7_2_pulmonary_stenosis_with_insuf",
    "Valvular Heart Disease (choice=(8) Multiple valve diseases)": "valvular_heart_disease_choice_8_multiple_valve_diseases",
    "Valvular Heart Disease (choice=(8.0) Disorders of both mitral and aortic valves)": "valvular_heart_disease_choice_8_0_disorders_of_both_mitral_and_",
    "Valvular Heart Disease (choice=(8.1) Disorders of both mitral and tricuspid valves)": "valvular_heart_disease_choice_8_1_disorders_of_both_mitral_and_",
    "Valvular Heart Disease (choice=(8.2) Disorders of both aortic and tricuspid valves)": "valvular_heart_disease_choice_8_2_disorders_of_both_aortic_and_",
    "Valvular Heart Disease (choice=(8.3) Combined disorders of mitral, aortic and tricuspid valves)": "valvular_heart_disease_choice_8_3_combined_disorders_of_mitral_",
    "Ventricular Rate": "ventricular_rate",
    "Waist : Hip Ratio": "waist_hip_ratio",
    "Waist circumference in cm": "waist_circumference_in_cm",
    "Weight in kg": "weight_in_kg",
    "What ethnicity do you consider yourself?": "what_ethnicity_do_you_consider_yourself",
    "What is the familial relationship between you and your spouse?": "what_is_the_familial_relationship_between_you_and_your_spouse",
    "What is the familial relationship between your father and mother?": "what_is_the_familial_relationship_between_your_father_and_mothe",
    "What is your current smoking status?": "what_is_your_current_smoking_status",
    "What is your marital status?": "what_is_your_marital_status",
    "What is your occupational status?": "what_is_your_occupational_status",
    "When you get any pain or discomfort in your chest what do you do?": "when_you_get_any_pain_or_discomfort_in_your_chest_what_do_you_d",
    "Where": "where",
    "Why there are missing data that cannot be acquired in this sheet?": "why_there_are_missing_data_that_cannot_be_acquired_in_this_shee",
    "X-Ray - Specify": "x_ray_specify",
    "and specify age of onset": "and_specify_age_of_onset",
    "corrected QT interval": "corrected_qt_interval",
    "eGFR (Female)": "egfr_female",
    "eGFR (Male)": "egfr_male",
    "if more than 1 wife, how many?": "if_more_than_1_wife_how_many",
    "vLDL": "vldl",
}

# EHVol: original_name -> pg_col_name
EHVOL_REGISTRY = {
    "Abnormal physical structure": "abnormal_physical_structure",
    "Address": "address",
    "Age": "age",
    "Amount of Alcohol": "amount_of_alcohol",
    "Anaemia": "anaemia",
    "Aortic Regurge": "aortic_regurge",
    "Aortic Root": "aortic_root",
    "Aortic Stenosis": "aortic_stenosis",
    "Are you one of a twin or triplet ?": "are_you_one_of_a_twin_or_triplet",
    "Are your parents, grandparents or great grandparents from non-Egyptian origin?": "are_your_parents_grandparents_or_great_grandparents_from_non_eg",
    "Autoimmune problems": "autoimmune_problems",
    "BMI": "bmi",
    "BP": "bp",
    "BSA": "bsa",
    "City of Residence during childhood": "city_of_residence_during_childhood",
    "Communication difficulties": "communication_difficulties",
    "Complete?": "complete",
    "Complete?.1": "complete_1",
    "Complete?.2": "complete_2",
    "Complete?.3": "complete_3",
    "Complete?.4": "complete_4",
    "Complete?.5": "complete_5",
    "Complete?.6": "complete_6",
    "Complete?.7": "complete_7",
    "Complete?.8": "complete_8",
    "Complete?.9": "complete_9",
    "Consanguinous Marriage": "consanguinous_marriage",
    "Consent Scan": "consent_scan",
    "Consent obtained?": "consent_obtained",
    "Contraindications for MRI": "contraindications_for_mri",
    "Current City of Residence": "current_city_of_residence",
    "Current/Recent Smoker (< 1 year)": "current_recent_smoker_1_year",
    "DNA ID": "dna_id",
    "Date of Birth": "date_of_birth",
    "Date of Enrolment": "date_of_enrolment",
    "Diabetes Mellitus": "diabetes_mellitus",
    "Diabetes Therapy": "diabetes_therapy",
    "Do any of your own children, parents or siblings have any of the following health conditions (choice=Diabetes)": "do_any_of_your_own_children_parents_or_siblings_have_any_of_the",
    "Do any of your own children, parents or siblings have any of the following health conditions (choice=Heart Disease)": "do_any_of_your_own_children_parents_or_siblings_have_any_of_the",
    "Do any of your own children, parents or siblings have any of the following health conditions (choice=High Blood Pressure)": "do_any_of_your_own_children_parents_or_siblings_have_any_of_the",
    "Do any of your own children, parents or siblings have any of the following health conditions (choice=Stroke)": "do_any_of_your_own_children_parents_or_siblings_have_any_of_the",
    "Do any of your own children, parents or siblings have any of the following health conditions (choice=Sudden unexpected death)": "do_any_of_your_own_children_parents_or_siblings_have_any_of_the",
    "Do you drink alcohol?": "do_you_drink_alcohol",
    "Do you take any medication currently?": "do_you_take_any_medication_currently",
    "Do you wish to be informed if we discover any abnormality was detected during the course of this study?": "do_you_wish_to_be_informed_if_we_discover_any_abnormality_was_d",
    "Does any other non-cardiac condition run in your family?": "does_any_other_non_cardiac_condition_run_in_your_family",
    "Dyslipidemia": "dyslipidemia",
    "ECG_Conclusion": "ecg_conclusion",
    "EF": "ef",
    "Echo Date": "echo_date",
    "Email": "email",
    "Examination Date": "examination_date",
    "FS": "fs",
    "Fat Mass": "fat_mass",
    "Fat-Free Mass": "fat_free_mass",
    "Father's City of Origin": "father_s_city_of_origin",
    "Father's City of Origin.1": "father_s_city_of_origin_1",
    "From where?": "from_where",
    "Gender": "gender",
    "Have you undergone an operation or any surgical procedures?": "have_you_undergone_an_operation_or_any_surgical_procedures",
    "HbA1c": "hba1c",
    "Heart Attack or Angina": "heart_attack_or_angina",
    "Heart Rate": "heart_rate",
    "Heart Rate during MRI": "heart_rate_during_mri",
    "Height (cm)": "height_cm",
    "High blood pressure": "high_blood_pressure",
    "History of Familial Cardiomyopathies": "history_of_familial_cardiomyopathies",
    "History of Premature CAD": "history_of_premature_cad",
    "History of Sudden Death History": "history_of_sudden_death_history",
    "Home Tel.": "home_tel",
    "Home Tel. 2": "home_tel_2",
    "How long have you been smoking?": "how_long_have_you_been_smoking",
    "How many cigarettes have you been smoking a day before you quit?": "how_many_cigarettes_have_you_been_smoking_a_day_before_you_quit",
    "How many cigarettes have you been smoking a day?": "how_many_cigarettes_have_you_been_smoking_a_day",
    "How many siblings you have?": "how_many_siblings_you_have",
    "How many years have you been smoking?": "how_many_years_have_you_been_smoking",
    "IVSd": "ivsd",
    "IVSs": "ivss",
    "Is there any chance you might be pregnant?": "is_there_any_chance_you_might_be_pregnant",
    "JVP": "jvp",
    "Kidney problems": "kidney_problems",
    "Known CVS disease": "known_cvs_disease",
    "Known Collagen disease": "known_collagen_disease",
    "LVEDD": "lvedd",
    "LVESD": "lvesd",
    "LVM": "lvm",
    "LVPWd": "lvpwd",
    "LVPWs": "lvpws",
    "Left Atrium": "left_atrium",
    "Left ventricular EF": "left_ventricular_ef",
    "Left ventricular ejection fraction": "left_ventricular_ejection_fraction",
    "Left ventricular end diastolic volume": "left_ventricular_end_diastolic_volume",
    "Left ventricular end systolic volume": "left_ventricular_end_systolic_volume",
    "Left ventricular mass": "left_ventricular_mass",
    "List these medications": "list_these_medications",
    "Liver Problems": "liver_problems",
    "Lung Problems": "lung_problems",
    "MRI": "mri",
    "MRI Date": "mri_date",
    "Malignancy": "malignancy",
    "Malignancy details": "malignancy_details",
    "Marital Status": "marital_status",
    "Mitral Regurge": "mitral_regurge",
    "Mitral Stenosis": "mitral_stenosis",
    "Mobile Tel.": "mobile_tel",
    "Mobile Tel. 2": "mobile_tel_2",
    "Muscloskeletal Problems": "muscloskeletal_problems",
    "Name": "name",
    "Name.1": "name_1",
    "Nationality": "nationality",
    "Neurological problems": "neurological_problems",
    "Non-Egyptian Parents?": "non_egyptian_parents",
    "Notes": "notes",
    "Number of Children": "number_of_children",
    "Number of wives": "number_of_wives",
    "Offspring of Consanguinous Marriage": "offspring_of_consanguinous_marriage",
    "Other": "other",
    "Other Findings": "other_findings",
    "Other MRI findings": "other_mri_findings",
    "P wave abnormality": "p_wave_abnormality",
    "PR interval": "pr_interval",
    "Parents' occupation": "parents_occupation",
    "Physical abnormality details": "physical_abnormality_details",
    "Pregnant female": "pregnant_female",
    "Prior Heart Failure (previous Hx)": "prior_heart_failure_previous_hx",
    "Procedure details": "procedure_details",
    "Pulmonary Regurge": "pulmonary_regurge",
    "Pulmonary stenosis": "pulmonary_stenosis",
    "QRS abnormalities": "qrs_abnormalities",
    "QRS duration": "qrs_duration",
    "QTc interval": "qtc_interval",
    "Rate": "rate",
    "Record ID": "record_id",
    "Regularity": "regularity",
    "Rheumatic Fever": "rheumatic_fever",
    "Rhythm": "rhythm",
    "Right Ventricle": "right_ventricle",
    "Right ventricular EF": "right_ventricular_ef",
    "S1": "s1",
    "S2": "s2",
    "S3": "s3",
    "S4": "s4",
    "ST segment abnormalities": "st_segment_abnormalities",
    "Span (cm)": "span_cm",
    "Specifiy P wave abnormality": "specifiy_p_wave_abnormality",
    "Specifiy QRS abnormality": "specifiy_qrs_abnormality",
    "Specifiy ST seg. abnormality": "specifiy_st_seg_abnormality",
    "Specifiy T wave abnormality": "specifiy_t_wave_abnormality",
    "Subaortic Membrane": "subaortic_membrane",
    "T wave abnormalities": "t_wave_abnormalities",
    "Tricuspid Regurge": "tricuspid_regurge",
    "Tricuspid Stenosis": "tricuspid_stenosis",
    "Troponin I": "troponin_i",
    "Type": "type",
    "Unwilling to participate": "unwilling_to_participate",
    "Volunteer under 18 year old ?": "volunteer_under_18_year_old",
    "We may contact you yearly to follow up on your health, do you accept?": "we_may_contact_you_yearly_to_follow_up_on_your_health_do_you_ac",
    "Weight (kg)": "weight_kg",
    "What is this(these) condition(s)?": "what_is_this_these_condition_s",
    "Where did you spend your childhood?": "where_did_you_spend_your_childhood",
    "Who and what disease?": "who_and_what_disease",
}

# BHS: pg_col_name -> sql_type
BHS_SQL_TYPES = {
    "abnormality_choice_none": "BOOLEAN",
    "abnormality_choice_pathological_q_waves": "BOOLEAN",
    "abnormality_choice_st_seg_depression": "BOOLEAN",
    "abnormality_choice_st_seg_elevation": "BOOLEAN",
    "abnormality_choice_t_wave_inversion": "BOOLEAN",
    "acute_rheumatic_fever_choice_55_rheumatic_fever_without_heart_i": "BOOLEAN",
    "acute_rheumatic_fever_choice_56_rheumatic_fever_with_heart_invo": "BOOLEAN",
    "acute_rheumatic_fever_choice_57_rheumatic_chorea": "BOOLEAN",
    "address": "VARCHAR(100)",
    "age_at_enrollment": "INTEGER",
    "age_at_smoking_cessation": "INTEGER",
    "age_at_start_of_smoking": "INTEGER",
    "agree_to_cmr": "TEXT",
    "agree_to_consent": "TEXT",
    "agree_to_ct": "TEXT",
    "agree_to_have_an_ecg": "TEXT",
    "agree_to_provide_family_history": "TEXT",
    "agree_to_undergo_carotid_duplex": "TEXT",
    "agree_to_undergo_tte": "TEXT",
    "agree_to_withdraw_samples_for_lab_workup": "TEXT",
    "albumin": "FLOAT",
    "alt": "FLOAT",
    "alternate_contact_1_name": "TEXT",
    "alternate_contact_1_number_1": "TEXT",
    "alternate_contact_1_number_2": "TEXT",
    "alternate_contact_1_relation": "TEXT",
    "alternate_contact_2_name": "TEXT",
    "alternate_contact_2_number_1": "TEXT",
    "alternate_contact_2_number_2": "TEXT",
    "alternate_contact_2_relation": "TEXT",
    "and_specify_age_of_onset": "TEXT",
    "angina": "BOOLEAN",
    "any_modifications_to_the_medications_that_study_subject_has_bee": "TEXT",
    "aortic_annulus_mid_systole": "FLOAT",
    "apex": "VARCHAR(50)",
    "apical_anterior": "INTEGER",
    "apical_inferior": "INTEGER",
    "apical_lateral": "INTEGER",
    "apical_septal": "INTEGER",
    "ar": "VARCHAR(50)",
    "as": "VARCHAR(50)",
    "ast": "FLOAT",
    "atheromatous_plaque_left": "BOOLEAN",
    "atheromatous_plaque_right": "BOOLEAN",
    "average_no_of_cigarettes_per_day": "INTEGER",
    "basal_anterior": "INTEGER",
    "basal_anterolateral": "INTEGER",
    "basal_anteroseptal": "INTEGER",
    "basal_inferior": "INTEGER",
    "basal_inferolateral": "INTEGER",
    "basal_inferoseptal": "INTEGER",
    "bmi": "FLOAT",
    "bnp": "FLOAT",
    "bp_pressure_chart_monitoring_conclusion": "TEXT",
    "brachial_pressure_highest_side": "FLOAT",
    "ca": "FLOAT",
    "can_you_read_and_write_in_arabic": "BOOLEAN",
    "can_you_speak_nubian": "BOOLEAN",
    "cardiac_arrhythmias_choice_58_0_sinus_bradycardia": "BOOLEAN",
    "cardiac_arrhythmias_choice_58_1_sick_sinus_syndrome": "BOOLEAN",
    "cardiac_arrhythmias_choice_58_2_atrio_ventricular_av_conduction": "BOOLEAN",
    "cardiac_arrhythmias_choice_58_2a_first_degree_av_block": "BOOLEAN",
    "cardiac_arrhythmias_choice_58_2b_second_degree_av_block": "BOOLEAN",
    "cardiac_arrhythmias_choice_58_2c_third_degree_av_block": "BOOLEAN",
    "cardiac_arrhythmias_choice_58_3_intraventricular_conduction_abn": "BOOLEAN",
    "cardiac_arrhythmias_choice_58_bradycardia_bradyarrythmia": "BOOLEAN",
    "cardiac_arrhythmias_choice_59_0_supraventricular_tachyarrythmia": "BOOLEAN",
    "cardiac_arrhythmias_choice_59_1_ventricular_tachyarrythmia": "BOOLEAN",
    "cardiac_arrhythmias_choice_59_tachycardia_tachyarrythmia": "BOOLEAN",
    "cardiac_arrhythmias_choice_atrial_fibrillation_af": "BOOLEAN",
    "cardiac_arrhythmias_choice_atrial_flutter": "BOOLEAN",
    "cardiac_arrhythmias_choice_atrial_tachycardia": "BOOLEAN",
    "cardiac_arrhythmias_choice_bradycardia_tachycardia_syndrome": "BOOLEAN",
    "cardiac_arrhythmias_choice_premature_supraventricular_contracti": "BOOLEAN",
    "cardiac_arrhythmias_choice_premature_ventricular_contractions": "BOOLEAN",
    "cardiac_arrhythmias_choice_sinus_pauses": "BOOLEAN",
    "cardiac_arrhythmias_choice_svt_psvt_avrt_avnrt": "BOOLEAN",
    "cardiac_arrhythmias_choice_ventricular_extrasystoles": "BOOLEAN",
    "cardiac_arrhythmias_choice_ventricular_fibrillation_vf": "BOOLEAN",
    "cardiac_arrhythmias_choice_ventricular_tachycardia_vt": "BOOLEAN",
    "cardiac_ct": "BOOLEAN",
    "cardiac_mri": "BOOLEAN",
    "carotid_duplex": "BOOLEAN",
    "category": "VARCHAR(100)",
    "category_1": "VARCHAR(100)",
    "category_10": "VARCHAR(100)",
    "category_11": "VARCHAR(100)",
    "category_12": "VARCHAR(100)",
    "category_13": "VARCHAR(100)",
    "category_14": "VARCHAR(100)",
    "category_2": "VARCHAR(100)",
    "category_3": "VARCHAR(100)",
    "category_4": "VARCHAR(100)",
    "category_5": "VARCHAR(100)",
    "category_6": "VARCHAR(100)",
    "category_7": "VARCHAR(100)",
    "category_8": "VARCHAR(100)",
    "category_9": "VARCHAR(100)",
    "cbc": "BOOLEAN",
    "cerebrovascular_diseases_choice_53_0_transient_ischemic_attack_": "BOOLEAN",
    "cerebrovascular_diseases_choice_53_1_stroke": "BOOLEAN",
    "cerebrovascular_diseases_choice_53_acute_disorders_of_cerebral_": "BOOLEAN",
    "cerebrovascular_diseases_choice_54_other_cerebrovascular_diseas": "BOOLEAN",
    "cerebrovascular_diseases_choice_haemorrhagic_stroke": "BOOLEAN",
    "cerebrovascular_diseases_choice_ischaemic_stroke": "BOOLEAN",
    "clinical_ambulatory_bp_monitoring": "TEXT",
    "clinical_bp_chart": "TEXT",
    "clinical_clinical_follow_up": "TEXT",
    "complete": "BOOLEAN",
    "complete_1": "BOOLEAN",
    "complete_10": "BOOLEAN",
    "complete_11": "BOOLEAN",
    "complete_12": "BOOLEAN",
    "complete_13": "BOOLEAN",
    "complete_2": "BOOLEAN",
    "complete_3": "BOOLEAN",
    "complete_4": "BOOLEAN",
    "complete_5": "BOOLEAN",
    "complete_6": "BOOLEAN",
    "complete_7": "BOOLEAN",
    "complete_8": "BOOLEAN",
    "complete_9": "BOOLEAN",
    "complications_of_heart_diseases_choice_33_cardiac_septal_defect": "BOOLEAN",
    "complications_of_heart_diseases_choice_34_rupture_of_chordae_te": "BOOLEAN",
    "complications_of_heart_diseases_choice_35_rupture_of_papillary_": "BOOLEAN",
    "complications_of_heart_diseases_choice_36_intracardiac_thrombos": "BOOLEAN",
    "complications_of_heart_diseases_choice_37_0_right_ventricular_h": "BOOLEAN",
    "complications_of_heart_diseases_choice_37_1_left_ventricular_hy": "BOOLEAN",
    "complications_of_heart_diseases_choice_37_cardiomegaly": "BOOLEAN",
    "complications_of_heart_diseases_choice_38_postcardiotomy_syndro": "BOOLEAN",
    "congenital_heart_defect": "VARCHAR(200)",
    "consent_obtained": "TEXT",
    "contact_number_1": "VARCHAR(50)",
    "contact_number_2": "VARCHAR(50)",
    "contact_number_3": "VARCHAR(50)",
    "coronary_angiography_angioplasty_stenting": "BOOLEAN",
    "coronary_intervention_decision_needs_revision": "TEXT",
    "coronary_intervention_report_1": "TEXT",
    "coronary_intervention_report_2": "TEXT",
    "corrected_qt_interval": "FLOAT",
    "creatinine": "FLOAT",
    "crp": "FLOAT",
    "crp_1": "TEXT",
    "ct_specify": "TEXT",
    "current_10_year_ascvd_risk": "FLOAT",
    "current_age": "INTEGER",
    "date": "DATE",
    "date_abi": "DATE",
    "date_clinical_exam": "DATE",
    "date_consent": "DATE",
    "date_demographic_data": "DATE",
    "date_echocardiography": "DATE",
    "date_family_history": "DATE",
    "date_labs": "DATE",
    "date_medications": "DATE",
    "date_of_birth": "DATE",
    "date_of_cardiac_ct": "DATE",
    "date_of_cardiac_mri": "DATE",
    "date_of_cardotid_duplex": "DATE",
    "date_of_coronary_intervention": "DATE",
    "date_plan": "DATE",
    "date_risk_factors": "DATE",
    "degenerative_valve_disease": "BOOLEAN",
    "diastolic_blood_pressure_right_brachial_measurement_1": "FLOAT",
    "diastolic_blood_pressure_right_brachial_measurement_2": "FLOAT",
    "diastolic_blood_pressure_right_brachial_measurement_3": "FLOAT",
    "direct_bilirubin": "FLOAT",
    "diseases_of_arteries_arterioles_and_capillaries_choice_48_ather": "BOOLEAN",
    "diseases_of_arteries_arterioles_and_capillaries_choice_49_0_dis": "BOOLEAN",
    "diseases_of_arteries_arterioles_and_capillaries_choice_49_1_tho": "BOOLEAN",
    "diseases_of_arteries_arterioles_and_capillaries_choice_49_2_abd": "BOOLEAN",
    "diseases_of_arteries_arterioles_and_capillaries_choice_49_3_tho": "BOOLEAN",
    "diseases_of_arteries_arterioles_and_capillaries_choice_49_aorti": "BOOLEAN",
    "diseases_of_arteries_arterioles_and_capillaries_choice_50_other": "BOOLEAN",
    "diseases_of_arteries_arterioles_and_capillaries_choice_51_perip": "BOOLEAN",
    "diseases_of_arteries_arterioles_and_capillaries_choice_52_arter": "BOOLEAN",
    "diseases_of_arteries_arterioles_and_capillaries_choice_abdomina": "BOOLEAN",
    "diseases_of_arteries_arterioles_and_capillaries_choice_arterios": "BOOLEAN",
    "diseases_of_arteries_arterioles_and_capillaries_choice_atheroma": "BOOLEAN",
    "diseases_of_arteries_arterioles_and_capillaries_choice_atherosc": "BOOLEAN",
    "diseases_of_arteries_arterioles_and_capillaries_choice_intermit": "BOOLEAN",
    "diseases_of_arteries_arterioles_and_capillaries_choice_ruptured": "BOOLEAN",
    "diseases_of_arteries_arterioles_and_capillaries_choice_spasm_of": "BOOLEAN",
    "diseases_of_arteries_arterioles_and_capillaries_choice_thoracic": "BOOLEAN",
    "diseases_of_arteries_arterioles_and_capillaries_choice_thoraco_": "BOOLEAN",
    "do_any_of_your_children_have_congenital_malformations_or_diseas": "BOOLEAN",
    "do_you_consume_alcohol": "BOOLEAN",
    "do_you_get_it_when_you_walk_at_an_ordinary_pace_on_the_level": "BOOLEAN",
    "do_you_get_this_pain_or_discomfort_when_you_walk_uphill_or_hurr": "BOOLEAN",
    "do_you_have_diabetes": "TEXT",
    "do_you_have_erectile_dysfunction": "BOOLEAN",
    "do_you_have_hyperlipidemia": "TEXT",
    "do_you_have_hypertension": "BOOLEAN",
    "do_you_have_more_than_one_wife": "BOOLEAN",
    "do_you_smoke_shisha_or_cigarettes_or_both": "BOOLEAN",
    "does_it_go_away_when_you_stand_still": "BOOLEAN",
    "ecg": "BOOLEAN",
    "ecg_date": "DATE",
    "ecg_holter_monitoring_conclusion": "TEXT",
    "ecg_pdf": "TEXT",
    "ecg_xml": "TEXT",
    "echocardiography": "BOOLEAN",
    "ectopic_beats": "BOOLEAN",
    "ef_class": "VARCHAR(50)",
    "egfr_female": "FLOAT",
    "egfr_male": "FLOAT",
    "electrolytes_na_k_ca_mg": "BOOLEAN",
    "endocardium_choice_23_0_rheumatic_diseases_of_endocardium_valve": "BOOLEAN",
    "endocardium_choice_23_1_nonrheumatic_mitral_valve_disorders": "BOOLEAN",
    "endocardium_choice_23_acute_and_subacute_endocarditis": "BOOLEAN",
    "endocardium_choice_24_0_acute_rheumatic_endocarditis": "BOOLEAN",
    "endocardium_choice_24_endocarditis_valve_unspecified": "BOOLEAN",
    "endocardium_choice_25_endocarditis_and_heart_valve_disorders_in": "BOOLEAN",
    "enrollment_date": "DATE",
    "exact_duration_of_smoking_cessation_please_select_the_time_unit": "FLOAT",
    "extra_notes": "TEXT",
    "fasting_blood_glucose": "FLOAT",
    "fasting_blood_sugar": "FLOAT",
    "father_origins": "VARCHAR(100)",
    "father_s_gov_of_origin": "TEXT",
    "findings_comments_if_there_is_any_changes_in_parameters_related": "TEXT",
    "for_any_missing_data_in_this_sheet_that_cannot_be_acquired_now_": "TEXT",
    "frequency": "VARCHAR(50)",
    "frequency_1": "VARCHAR(50)",
    "frequency_10": "VARCHAR(50)",
    "frequency_11": "VARCHAR(50)",
    "frequency_12": "VARCHAR(50)",
    "frequency_13": "VARCHAR(50)",
    "frequency_14": "VARCHAR(50)",
    "frequency_2": "VARCHAR(50)",
    "frequency_3": "VARCHAR(50)",
    "frequency_4": "VARCHAR(50)",
    "frequency_5": "VARCHAR(50)",
    "frequency_6": "VARCHAR(50)",
    "frequency_7": "VARCHAR(50)",
    "frequency_8": "VARCHAR(50)",
    "frequency_9": "VARCHAR(50)",
    "further_comments": "TEXT",
    "further_plan": "TEXT",
    "further_plan_details": "TEXT",
    "further_plan_document": "TEXT",
    "gender": "VARCHAR(10)",
    "has_anyone_in_your_family_parents_grandparents_or_siblings_expe": "BOOLEAN",
    "have_you_been_diagnosed_with_congenital_heart_disease": "BOOLEAN",
    "have_you_been_diagnosed_with_pvd": "BOOLEAN",
    "have_you_been_diagnosed_with_renal_disease": "BOOLEAN",
    "have_you_been_diagnosed_with_respiratory_illnesses": "BOOLEAN",
    "have_you_been_diagnosed_with_rhd": "BOOLEAN",
    "have_you_been_diagnosed_with_rheumatic_fever": "BOOLEAN",
    "have_you_been_hospitalized_due_to_heart_failure": "TEXT",
    "have_you_ever_been_diagnosed_with_mi": "BOOLEAN",
    "have_you_ever_had_a_severe_pain_across_the_front_of_your_chest_": "BOOLEAN",
    "have_you_ever_had_any_pain_or_discomfort_in_your_chest": "BOOLEAN",
    "have_you_experienced_shortness_of_breath": "BOOLEAN",
    "have_you_had_a_prior_stroke_or_tia": "BOOLEAN",
    "have_you_had_any_other_cardiac_procedures": "BOOLEAN",
    "have_you_received_influenza_immunization_within_a_year": "BOOLEAN",
    "have_you_undergone_a_coronary_angioplasty_stent": "BOOLEAN",
    "have_you_undergone_a_prior_cabg": "BOOLEAN",
    "hba1c": "FLOAT",
    "hdl": "FLOAT",
    "heart_failure_choice_14_acute_heart_failure": "BOOLEAN",
    "heart_failure_choice_15_0_heart_failure_with_reduced_ejection_f": "BOOLEAN",
    "heart_failure_choice_15_1_heart_failure_with_preserved_ejection": "BOOLEAN",
    "heart_failure_choice_15_2_heart_failure_with_borderline_ejectio": "BOOLEAN",
    "heart_failure_choice_15_left_sided_heart_failure": "BOOLEAN",
    "heart_failure_choice_16_right_sided_heart_failure": "BOOLEAN",
    "heart_rate": "FLOAT",
    "height_in_cm": "FLOAT",
    "hematocrit": "FLOAT",
    "hemoglobin": "FLOAT",
    "hip_circumference_in_cm": "FLOAT",
    "holter": "BOOLEAN",
    "household_identifier": "VARCHAR(50)",
    "how_soon": "TEXT",
    "hypertensive_diseases_choice_39_0_arterial_hypertension": "BOOLEAN",
    "hypertensive_diseases_choice_39_essential_primary_hypertension": "BOOLEAN",
    "hypertensive_diseases_choice_40_hypertensive_heart_disease": "BOOLEAN",
    "hypertensive_diseases_choice_41_0_hypertensive_nephropathy": "BOOLEAN",
    "hypertensive_diseases_choice_41_hypertensive_renal_disease": "BOOLEAN",
    "hypertensive_diseases_choice_42_hypertensive_heart_disease_and_": "BOOLEAN",
    "hypertensive_diseases_choice_43_0_renovascular_hypertension": "BOOLEAN",
    "hypertensive_diseases_choice_43_secondary_hypertension": "BOOLEAN",
    "hypotensive_diseases_choice_44_idiopathic_hypotension": "BOOLEAN",
    "hypotensive_diseases_choice_45_orthostatic_hypotension": "BOOLEAN",
    "hypotensive_diseases_choice_46_hypotension_due_to_drugs": "BOOLEAN",
    "hypotensive_diseases_choice_47_hypotension_unspecified": "BOOLEAN",
    "if_father_is_egyptian_please_specify_city": "TEXT",
    "if_father_is_non_egyptian_please_specify": "TEXT",
    "if_more_than_1_wife_how_many": "TEXT",
    "if_mother_is_egyptian_please_specify_city": "VARCHAR(100)",
    "if_mother_is_non_egyptian_please_specify": "TEXT",
    "if_other_specify": "TEXT",
    "if_yes_age_of_onset": "TEXT",
    "if_yes_please_note_mrn": "TEXT",
    "if_yes_please_specify": "TEXT",
    "if_yes_please_specify_age_of_onset": "TEXT",
    "if_yes_please_specify_age_of_onset_1": "TEXT",
    "if_yes_please_specify_age_of_onset_2": "TEXT",
    "if_yes_please_specify_age_of_onset_3": "TEXT",
    "if_yes_please_specify_age_of_onset_4": "TEXT",
    "if_yes_please_specify_age_of_onset_and_details": "TEXT",
    "if_yes_please_specify_date": "TEXT",
    "if_yes_please_specify_date_of_cabg": "TEXT",
    "if_yes_please_specify_details_and_age_of_onset": "TEXT",
    "if_yes_please_specify_disease": "TEXT",
    "if_yes_please_specify_number_and_date_of_hospitalizations": "TEXT",
    "if_yes_please_specify_the_highest_degree_obtained": "TEXT",
    "if_yes_please_specify_type": "TEXT",
    "if_yes_please_specify_type_and_age_of_onset": "TEXT",
    "if_yes_please_specify_type_and_date": "TEXT",
    "if_yes_stenosis_lt": "TEXT",
    "if_yes_stenosis_rt": "TEXT",
    "imt_left_in_mm": "FLOAT",
    "imt_right_in_mm": "FLOAT",
    "in_general_how_would_you_rate_your_health_today": "TEXT",
    "inr": "FLOAT",
    "intervention_required": "TEXT",
    "ischaemic_heart_diseases_choice_10_0_haemopericardium": "BOOLEAN",
    "ischaemic_heart_diseases_choice_10_1_atrial_septal_defect": "BOOLEAN",
    "ischaemic_heart_diseases_choice_10_2_ventricular_septal_defect": "BOOLEAN",
    "ischaemic_heart_diseases_choice_10_3_rupture_of_cardiac_wall_wi": "BOOLEAN",
    "ischaemic_heart_diseases_choice_10_4_rupture_of_chordae_tendine": "BOOLEAN",
    "ischaemic_heart_diseases_choice_10_5_rupture_of_papillary_muscl": "BOOLEAN",
    "ischaemic_heart_diseases_choice_10_6_thrombosis_of_atrium_auric": "BOOLEAN",
    "ischaemic_heart_diseases_choice_10_7_other_current_complication": "BOOLEAN",
    "ischaemic_heart_diseases_choice_10_complications_following_acut": "BOOLEAN",
    "ischaemic_heart_diseases_choice_12_0_coronary_thrombosis_not_re": "BOOLEAN",
    "ischaemic_heart_diseases_choice_12_1_dresslers_syndrome": "BOOLEAN",
    "ischaemic_heart_diseases_choice_12_other_acute_ischaemic_heart_": "BOOLEAN",
    "ischaemic_heart_diseases_choice_13_0_atherosclerotic_cardiovasc": "BOOLEAN",
    "ischaemic_heart_diseases_choice_13_1_atherosclerotic_heart_dise": "BOOLEAN",
    "ischaemic_heart_diseases_choice_13_2_old_myocardial_infarction": "BOOLEAN",
    "ischaemic_heart_diseases_choice_13_3_aneurysm_of_heart": "BOOLEAN",
    "ischaemic_heart_diseases_choice_13_4_coronary_artery_aneurysm": "BOOLEAN",
    "ischaemic_heart_diseases_choice_13_5_ischaemic_cardiomyopathy": "BOOLEAN",
    "ischaemic_heart_diseases_choice_13_6_silent_myocardial_ischaemi": "BOOLEAN",
    "ischaemic_heart_diseases_choice_13_7_other_forms_of_chronic_isc": "BOOLEAN",
    "ischaemic_heart_diseases_choice_13_chronic_ischaemic_heart_dise": "BOOLEAN",
    "ischaemic_heart_diseases_choice_9_0_non_st_elevation_acute_coro": "BOOLEAN",
    "ischaemic_heart_diseases_choice_9_1_st_elevation_acute_coronary": "BOOLEAN",
    "ischaemic_heart_diseases_choice_9_acute_coronary_syndrome": "BOOLEAN",
    "ischaemic_heart_diseases_choice_non_st_elevation_myocardial_inf": "BOOLEAN",
    "ischaemic_heart_diseases_choice_unstable_angina": "BOOLEAN",
    "k": "FLOAT",
    "kidney_functions": "BOOLEAN",
    "la_diameter_plax": "FLOAT",
    "la_volume_simpson_s": "FLOAT",
    "ldl": "FLOAT",
    "left_anterior_tibial_abi": "FLOAT",
    "left_anterior_tibial_pressure": "FLOAT",
    "left_atrial_size": "FLOAT",
    "left_posterior_tibial_abi": "FLOAT",
    "left_posterior_tibial_pressure": "FLOAT",
    "life_sciences_re_sampling": "TEXT",
    "lifetime_ascvd_risk": "FLOAT",
    "lipid_profile": "BOOLEAN",
    "liver_functions": "BOOLEAN",
    "lower_limb_duplex": "BOOLEAN",
    "lv_diastolic_dysfunction": "VARCHAR(50)",
    "lv_size": "FLOAT",
    "lvedd": "FLOAT",
    "lvef_m_mode": "FLOAT",
    "lvef_simpson_s": "FLOAT",
    "lvef_visual": "FLOAT",
    "lvesd": "FLOAT",
    "lvh": "BOOLEAN",
    "lvh_1": "TEXT",
    "major_category_choice_cardiomyopathy": "BOOLEAN",
    "major_category_choice_chd": "BOOLEAN",
    "major_category_choice_hf": "BOOLEAN",
    "major_category_choice_ihd": "BOOLEAN",
    "major_category_choice_none": "BOOLEAN",
    "major_category_choice_other_co_morbdidites_risk_factors": "BOOLEAN",
    "major_category_choice_other_cv_disease": "BOOLEAN",
    "major_category_choice_pht": "BOOLEAN",
    "major_category_choice_rhd": "BOOLEAN",
    "major_category_choice_valvular": "BOOLEAN",
    "mch": "FLOAT",
    "mchc": "FLOAT",
    "mcv": "FLOAT",
    "mg": "FLOAT",
    "midventricular_anterior": "INTEGER",
    "midventricular_anterolateral": "INTEGER",
    "midventricular_anteroseptal": "INTEGER",
    "midventricular_inferior": "INTEGER",
    "midventricular_inferolateral": "INTEGER",
    "midventricular_inferoseptal": "INTEGER",
    "moderate_or_severe_valvular_lesion": "BOOLEAN",
    "mother_origins": "VARCHAR(100)",
    "mother_s_gov_of_origin": "TEXT",
    "mr": "VARCHAR(50)",
    "mri_specify": "TEXT",
    "mrn_ahc": "TEXT",
    "mrn_bu": "TEXT",
    "ms": "VARCHAR(50)",
    "myocardial_perfusion_imaging": "BOOLEAN",
    "myocardium_cardiomyopathy_choice_17_acute_myocarditis": "BOOLEAN",
    "myocardium_cardiomyopathy_choice_18_chronic_myocarditis": "BOOLEAN",
    "myocardium_cardiomyopathy_choice_19_0_rheumatic_myocarditis": "BOOLEAN",
    "myocardium_cardiomyopathy_choice_19_myocarditis_in_diseases_cla": "BOOLEAN",
    "myocardium_cardiomyopathy_choice_20_myocardial_degeneration": "BOOLEAN",
    "myocardium_cardiomyopathy_choice_21_0_dilated_cardiomyopathy": "BOOLEAN",
    "myocardium_cardiomyopathy_choice_21_1_obstructive_hypertrophy_c": "BOOLEAN",
    "myocardium_cardiomyopathy_choice_21_2_other_hypertrophic_cardio": "BOOLEAN",
    "myocardium_cardiomyopathy_choice_21_3_endomyocardial_eosinophil": "BOOLEAN",
    "myocardium_cardiomyopathy_choice_21_4_endocardial_fibroelastosi": "BOOLEAN",
    "myocardium_cardiomyopathy_choice_21_5_other_restrictive_cardiom": "BOOLEAN",
    "myocardium_cardiomyopathy_choice_21_6_alcoholic_cardiomyopathy": "BOOLEAN",
    "myocardium_cardiomyopathy_choice_21_8_other_cardiomyopathies": "BOOLEAN",
    "myocardium_cardiomyopathy_choice_21_cardiomyopathy": "BOOLEAN",
    "myocardium_cardiomyopathy_choice_22_cardiomyopathy_in_diseases_": "BOOLEAN",
    "myocardium_cardiomyopathy_choice_arrhythmogenic_right_ventricul": "BOOLEAN",
    "myocardium_cardiomyopathy_choice_endomyocardial_tropical_fibros": "BOOLEAN",
    "myocardium_cardiomyopathy_choice_eosinophilic_myocarditis": "BOOLEAN",
    "myocardium_cardiomyopathy_choice_loefflers_endocarditis": "BOOLEAN",
    "myxomatous_valve_disease": "VARCHAR(50)",
    "myxomatous_valve_s_choice_aortic": "BOOLEAN",
    "myxomatous_valve_s_choice_mitral": "BOOLEAN",
    "myxomatous_valve_s_choice_pulmonary": "BOOLEAN",
    "myxomatous_valve_s_choice_tricuspid": "BOOLEAN",
    "na": "FLOAT",
    "name": "VARCHAR(200)",
    "name_1": "VARCHAR(200)",
    "name_10": "VARCHAR(200)",
    "name_11": "VARCHAR(200)",
    "name_12": "VARCHAR(200)",
    "name_13": "VARCHAR(200)",
    "name_14": "VARCHAR(200)",
    "name_2": "VARCHAR(200)",
    "name_3": "VARCHAR(200)",
    "name_4": "VARCHAR(200)",
    "name_5": "VARCHAR(200)",
    "name_6": "VARCHAR(200)",
    "name_7": "VARCHAR(200)",
    "name_8": "VARCHAR(200)",
    "name_9": "VARCHAR(200)",
    "native_av_morphology": "VARCHAR(100)",
    "optimal_ascvd_risk": "FLOAT",
    "other_co_morbidities_risk_factors_choice_diabetes_mellitus": "BOOLEAN",
    "other_co_morbidities_risk_factors_choice_dyslipidemia": "BOOLEAN",
    "other_co_morbidities_risk_factors_choice_familial_hypercholeste": "BOOLEAN",
    "other_co_morbidities_risk_factors_choice_hypertension": "BOOLEAN",
    "other_co_morbidities_risk_factors_choice_none": "BOOLEAN",
    "other_co_morbidities_risk_factors_choice_other": "BOOLEAN",
    "other_echocardiographic_findings": "TEXT",
    "other_ethnicity": "VARCHAR(100)",
    "other_laboratory_results_to_report": "TEXT",
    "others_imaging_modality_specify": "TEXT",
    "others_lab_work_specify": "TEXT",
    "participant_s_name": "VARCHAR(200)",
    "pasp": "FLOAT",
    "pedigree": "TEXT",
    "pericardium_choice_26_0_acute_rheumatic_pericarditis": "BOOLEAN",
    "pericardium_choice_26_acute_pericarditis": "BOOLEAN",
    "pericardium_choice_27_0_chronic_adhesive_pericarditis": "BOOLEAN",
    "pericardium_choice_27_1_chronic_constrictive_pericarditis": "BOOLEAN",
    "pericardium_choice_27_2_chronic_rheumatic_pericarditis": "BOOLEAN",
    "pericardium_choice_27_chronic_pericarditis": "BOOLEAN",
    "pericardium_choice_28_0_haemopericardium_not_elsewhere_classifi": "BOOLEAN",
    "pericardium_choice_28_1_pericardial_effusion_noninflammatory": "BOOLEAN",
    "pericardium_choice_28_other_diseases_of_pericardium": "BOOLEAN",
    "pericardium_choice_29_0_cardiac_tamponade": "BOOLEAN",
    "pericardium_choice_29_other_specified_diseases_of_pericardium": "BOOLEAN",
    "pericardium_choice_30_pericarditis_in_diseases_classified_elsew": "BOOLEAN",
    "pericardium_choice_calcified": "BOOLEAN",
    "pericardium_choice_effusion": "BOOLEAN",
    "pericardium_choice_normal": "BOOLEAN",
    "platelet_count": "FLOAT",
    "pr": "VARCHAR(50)",
    "prescription_document_by_bhs_clinic": "TEXT",
    "present_or_most_recent_past_occupation": "VARCHAR(200)",
    "previous_patient_at_ahc": "BOOLEAN",
    "ps": "VARCHAR(50)",
    "pulmonary_hypertension": "BOOLEAN",
    "pulmonary_vascular_disease_choice_31_0_pulmonary_arterial_hyper": "BOOLEAN",
    "pulmonary_vascular_disease_choice_31_1_pulmonary_hypertension_d": "BOOLEAN",
    "pulmonary_vascular_disease_choice_31_2_pulmonary_hypertension_a": "BOOLEAN",
    "pulmonary_vascular_disease_choice_31_pulmonary_hypertension": "BOOLEAN",
    "pulmonary_vascular_disease_choice_32_3_chronic_thromboembolic_e": "BOOLEAN",
    "pulmonary_vascular_disease_choice_32_4_pulmonary_hypertension_f": "BOOLEAN",
    "pulmonary_vascular_disease_choice_32_pulmonary_embolism": "BOOLEAN",
    "pulmonary_vascular_disease_choice_chronic_kindey_failure": "BOOLEAN",
    "pulmonary_vascular_disease_choice_congenital_heart_disease": "BOOLEAN",
    "pulmonary_vascular_disease_choice_copd_interstitial_lung_diseas": "BOOLEAN",
    "pulmonary_vascular_disease_choice_idiopathic_primary": "BOOLEAN",
    "pulmonary_vascular_disease_choice_lv_diastolic_dysfunction": "BOOLEAN",
    "pulmonary_vascular_disease_choice_lv_systolic_dysfunction": "BOOLEAN",
    "pulmonary_vascular_disease_choice_metabolic_disorder": "BOOLEAN",
    "pulmonary_vascular_disease_choice_obstructive_sleep_apnea": "BOOLEAN",
    "pulmonary_vascular_disease_choice_secondary_to_systemic_disorde": "BOOLEAN",
    "pulmonary_vascular_disease_choice_systemic_disorder": "BOOLEAN",
    "pulmonary_vascular_disease_choice_valvular_heart_disease": "BOOLEAN",
    "pwt": "FLOAT",
    "qrs_duration": "FLOAT",
    "qrs_width_120_ms": "BOOLEAN",
    "qt_interval": "FLOAT",
    "random_blood_glucose": "FLOAT",
    "rbcs": "FLOAT",
    "rdw": "FLOAT",
    "record_id": "TEXT",
    "refer_to_ahc_clinic_bmv": "TEXT",
    "refer_to_ahc_clinic_ep": "TEXT",
    "refer_to_ahc_clinic_general": "TEXT",
    "refer_to_ahc_clinic_guch": "TEXT",
    "refer_to_ahc_clinic_heart_failure": "TEXT",
    "refer_to_ahc_clinic_lvad": "TEXT",
    "refer_to_ahc_clinic_other_specify": "TEXT",
    "refer_to_ahc_clinic_pulmonary": "TEXT",
    "refer_to_ahc_clinic_tavi": "TEXT",
    "refer_to_another_speciality_clinic_specify": "TEXT",
    "regional_wall_motion_abnormalities": "BOOLEAN",
    "relative_10_age_at_event": "INTEGER",
    "relative_10_event": "VARCHAR(100)",
    "relative_10_gender": "VARCHAR(10)",
    "relative_10_relation": "VARCHAR(100)",
    "relative_1_age_at_event": "INTEGER",
    "relative_1_event": "VARCHAR(100)",
    "relative_1_gender": "VARCHAR(10)",
    "relative_1_relation": "VARCHAR(100)",
    "relative_2_age_at_event": "INTEGER",
    "relative_2_event": "VARCHAR(100)",
    "relative_2_gender": "VARCHAR(10)",
    "relative_2_relation": "VARCHAR(100)",
    "relative_3_age_at_event": "INTEGER",
    "relative_3_event": "VARCHAR(100)",
    "relative_3_gender": "VARCHAR(10)",
    "relative_3_relation": "VARCHAR(100)",
    "relative_4_age_at_event": "INTEGER",
    "relative_4_event": "VARCHAR(100)",
    "relative_4_gender": "VARCHAR(10)",
    "relative_4_relation": "VARCHAR(100)",
    "relative_5_age_at_event": "INTEGER",
    "relative_5_event": "VARCHAR(100)",
    "relative_5_gender": "VARCHAR(10)",
    "relative_5_relation": "VARCHAR(100)",
    "relative_6_age_at_event": "INTEGER",
    "relative_6_event": "VARCHAR(100)",
    "relative_6_gender": "VARCHAR(10)",
    "relative_6_relation": "VARCHAR(100)",
    "relative_7_age_at_event": "INTEGER",
    "relative_7_event": "VARCHAR(100)",
    "relative_7_gender": "VARCHAR(10)",
    "relative_7_relation": "VARCHAR(100)",
    "relative_8_age_at_event": "INTEGER",
    "relative_8_event": "VARCHAR(100)",
    "relative_8_gender": "VARCHAR(10)",
    "relative_8_relation": "VARCHAR(100)",
    "relative_9_age_at_event": "INTEGER",
    "relative_9_event": "VARCHAR(100)",
    "relative_9_gender": "VARCHAR(10)",
    "relative_9_relation": "VARCHAR(100)",
    "renal_duplex": "BOOLEAN",
    "results": "TEXT",
    "rhd_affected_valves_choice_aortic": "BOOLEAN",
    "rhd_affected_valves_choice_mitral": "BOOLEAN",
    "rhd_affected_valves_choice_pulmonary": "BOOLEAN",
    "rhd_affected_valves_choice_tricuspid": "BOOLEAN",
    "rheumatic_valvular_heart_disease": "BOOLEAN",
    "rhythm_in_ecg": "VARCHAR(100)",
    "right_anterior_tibial_abi": "FLOAT",
    "right_anterior_tibial_pressure": "FLOAT",
    "right_posterior_tibial_abi": "FLOAT",
    "right_posterior_tibial_pressure": "FLOAT",
    "route": "VARCHAR(50)",
    "route_1": "VARCHAR(50)",
    "route_10": "VARCHAR(50)",
    "route_11": "VARCHAR(50)",
    "route_12": "VARCHAR(50)",
    "route_13": "VARCHAR(50)",
    "route_14": "VARCHAR(50)",
    "route_2": "VARCHAR(50)",
    "route_3": "VARCHAR(50)",
    "route_4": "VARCHAR(50)",
    "route_5": "VARCHAR(50)",
    "route_6": "VARCHAR(50)",
    "route_7": "VARCHAR(50)",
    "route_8": "VARCHAR(50)",
    "route_9": "VARCHAR(50)",
    "rv_diameters_basal": "FLOAT",
    "rv_diameters_longitudinal": "FLOAT",
    "rv_diameters_mild": "FLOAT",
    "rv_size": "FLOAT",
    "rwma_index": "FLOAT",
    "rwma_score": "FLOAT",
    "serum_triglycerides": "FLOAT",
    "shisha_how_many_minutes_per_session": "FLOAT",
    "shisha_how_many_sessions_per_day": "FLOAT",
    "sino_tubular_junction_end_diastole": "FLOAT",
    "sinus_of_valsalva_end_diastole": "FLOAT",
    "smoking_index_current": "FLOAT",
    "smoking_index_former": "FLOAT",
    "smoking_years": "FLOAT",
    "specify_congenital_defect": "TEXT",
    "specify_ct_scan_region_s_of_interest": "TEXT",
    "specify_degenerated_valve_s_choice_aortic": "TEXT",
    "specify_degenerated_valve_s_choice_mitral": "TEXT",
    "specify_degenerated_valve_s_choice_pulmonary": "TEXT",
    "specify_degenerated_valve_s_choice_tricuspid": "TEXT",
    "specify_mri_scan_region_s_of_interest": "TEXT",
    "specify_other_ahc_clinic_referral": "TEXT",
    "specify_other_lab_work": "TEXT",
    "specify_other_requested_imaging_modality_ies": "TEXT",
    "specify_speciality_clinic_referral": "TEXT",
    "specify_x_ray_region_s_of_interest": "TEXT",
    "status": "VARCHAR(50)",
    "status_1": "VARCHAR(50)",
    "status_10": "VARCHAR(50)",
    "status_11": "VARCHAR(50)",
    "status_12": "VARCHAR(50)",
    "status_13": "VARCHAR(50)",
    "status_14": "VARCHAR(50)",
    "status_2": "VARCHAR(50)",
    "status_3": "VARCHAR(50)",
    "status_4": "VARCHAR(50)",
    "status_5": "VARCHAR(50)",
    "status_6": "VARCHAR(50)",
    "status_7": "VARCHAR(50)",
    "status_8": "VARCHAR(50)",
    "status_9": "VARCHAR(50)",
    "subject_is_on_treatment": "TEXT",
    "swt": "FLOAT",
    "systolic_blood_pressure_right_brachial_measurement_1": "FLOAT",
    "systolic_blood_pressure_right_brachial_measurement_2": "FLOAT",
    "systolic_blood_pressure_right_brachial_measurement_3": "FLOAT",
    "t3": "FLOAT",
    "t4": "FLOAT",
    "tapse": "FLOAT",
    "thyroid_functions": "BOOLEAN",
    "time_unit_for_smoking_cessation_duration": "VARCHAR(20)",
    "tlc": "FLOAT",
    "total_bilirubin": "FLOAT",
    "total_cholesterol": "FLOAT",
    "total_daily_dose": "FLOAT",
    "total_daily_dose_1": "FLOAT",
    "total_daily_dose_10": "FLOAT",
    "total_daily_dose_11": "FLOAT",
    "total_daily_dose_12": "FLOAT",
    "total_daily_dose_13": "FLOAT",
    "total_daily_dose_14": "FLOAT",
    "total_daily_dose_2": "FLOAT",
    "total_daily_dose_3": "FLOAT",
    "total_daily_dose_4": "FLOAT",
    "total_daily_dose_5": "FLOAT",
    "total_daily_dose_6": "FLOAT",
    "total_daily_dose_7": "FLOAT",
    "total_daily_dose_8": "FLOAT",
    "total_daily_dose_9": "FLOAT",
    "tr": "VARCHAR(50)",
    "troponin": "FLOAT",
    "ts": "VARCHAR(50)",
    "tsh": "FLOAT",
    "tubular_ascending_aorta_end_diastole_distance_from_sinotubular_": "FLOAT",
    "tubular_ascending_aorta_end_diastole_max_diameter": "FLOAT",
    "upload_consent_scan_1": "TEXT",
    "upload_consent_scan_2": "TEXT",
    "upper_limb_duplex": "BOOLEAN",
    "urea": "FLOAT",
    "valvular_heart_disease_choice_1_congenital": "BOOLEAN",
    "valvular_heart_disease_choice_2_rheumatic": "BOOLEAN",
    "valvular_heart_disease_choice_3_degenerative": "BOOLEAN",
    "valvular_heart_disease_choice_4_0_mitral_stenosis": "BOOLEAN",
    "valvular_heart_disease_choice_4_1_mitral_insufficiency": "BOOLEAN",
    "valvular_heart_disease_choice_4_2_mitral_stenosis_with_insuffic": "BOOLEAN",
    "valvular_heart_disease_choice_4_3_mitral_valve_prolapse": "BOOLEAN",
    "valvular_heart_disease_choice_4_mitral_valve_diseases": "BOOLEAN",
    "valvular_heart_disease_choice_5_0_aortic_stenosis": "BOOLEAN",
    "valvular_heart_disease_choice_5_1_aortic_insufficiency": "BOOLEAN",
    "valvular_heart_disease_choice_5_2_aortic_stenosis_with_insuffic": "BOOLEAN",
    "valvular_heart_disease_choice_5_3_bicuspid_aortic_valve": "BOOLEAN",
    "valvular_heart_disease_choice_5_aortic_valve_diseases": "BOOLEAN",
    "valvular_heart_disease_choice_6_0_tricuspid_stenosis": "BOOLEAN",
    "valvular_heart_disease_choice_6_1_tricuspid_insufficiency": "BOOLEAN",
    "valvular_heart_disease_choice_6_2_tricuspid_stenosis_with_insuf": "BOOLEAN",
    "valvular_heart_disease_choice_6_tricuspid_valve_diseases": "BOOLEAN",
    "valvular_heart_disease_choice_7_0_pulmonary_stenosis": "BOOLEAN",
    "valvular_heart_disease_choice_7_1_pulmonary_insufficiency": "BOOLEAN",
    "valvular_heart_disease_choice_7_2_pulmonary_stenosis_with_insuf": "BOOLEAN",
    "valvular_heart_disease_choice_7_pulmonary_valve_diseases": "BOOLEAN",
    "valvular_heart_disease_choice_8_0_disorders_of_both_mitral_and_": "BOOLEAN",
    "valvular_heart_disease_choice_8_1_disorders_of_both_mitral_and_": "BOOLEAN",
    "valvular_heart_disease_choice_8_2_disorders_of_both_aortic_and_": "BOOLEAN",
    "valvular_heart_disease_choice_8_3_combined_disorders_of_mitral_": "BOOLEAN",
    "valvular_heart_disease_choice_8_multiple_valve_diseases": "BOOLEAN",
    "ventricular_rate": "FLOAT",
    "vldl": "FLOAT",
    "waist_circumference_in_cm": "FLOAT",
    "waist_hip_ratio": "FLOAT",
    "weight_in_kg": "FLOAT",
    "what_ethnicity_do_you_consider_yourself": "VARCHAR(50)",
    "what_is_the_familial_relationship_between_you_and_your_spouse": "VARCHAR(100)",
    "what_is_the_familial_relationship_between_your_father_and_mothe": "TEXT",
    "what_is_your_current_smoking_status": "TEXT",
    "what_is_your_marital_status": "VARCHAR(50)",
    "what_is_your_occupational_status": "VARCHAR(200)",
    "when_you_get_any_pain_or_discomfort_in_your_chest_what_do_you_d": "TEXT",
    "where": "TEXT",
    "why_there_are_missing_data_that_cannot_be_acquired_in_this_shee": "TEXT",
    "x_ray_specify": "TEXT",
}

# EHVol: pg_col_name -> sql_type
EHVOL_SQL_TYPES = {
    "abnormal_physical_structure": "BOOLEAN",
    "address": "VARCHAR(100)",
    "age": "INTEGER",
    "amount_of_alcohol": "TEXT",
    "anaemia": "BOOLEAN",
    "aortic_regurge": "VARCHAR(50)",
    "aortic_root": "FLOAT",
    "aortic_stenosis": "VARCHAR(50)",
    "are_you_one_of_a_twin_or_triplet": "BOOLEAN",
    "are_your_parents_grandparents_or_great_grandparents_from_non_eg": "BOOLEAN",
    "autoimmune_problems": "BOOLEAN",
    "bmi": "FLOAT",
    "bp": "FLOAT",
    "bsa": "FLOAT",
    "city_of_residence_during_childhood": "VARCHAR(100)",
    "communication_difficulties": "BOOLEAN",
    "complete": "BOOLEAN",
    "complete_1": "BOOLEAN",
    "complete_2": "BOOLEAN",
    "complete_3": "BOOLEAN",
    "complete_4": "BOOLEAN",
    "complete_5": "BOOLEAN",
    "complete_6": "BOOLEAN",
    "complete_7": "BOOLEAN",
    "complete_8": "BOOLEAN",
    "complete_9": "BOOLEAN",
    "consanguinous_marriage": "BOOLEAN",
    "consent_obtained": "TEXT",
    "consent_scan": "TEXT",
    "contraindications_for_mri": "BOOLEAN",
    "current_city_of_residence": "VARCHAR(100)",
    "current_recent_smoker_1_year": "TEXT",
    "date_of_birth": "DATE",
    "date_of_enrolment": "DATE",
    "diabetes_mellitus": "TEXT",
    "diabetes_therapy": "VARCHAR(100)",
    "dna_id": "VARCHAR(50)",
    "do_any_of_your_own_children_parents_or_siblings_have_any_of_the": "BOOLEAN",
    "do_you_drink_alcohol": "BOOLEAN",
    "do_you_take_any_medication_currently": "BOOLEAN",
    "do_you_wish_to_be_informed_if_we_discover_any_abnormality_was_d": "BOOLEAN",
    "does_any_other_non_cardiac_condition_run_in_your_family": "TEXT",
    "dyslipidemia": "TEXT",
    "ecg_conclusion": "TEXT",
    "echo_date": "DATE",
    "ef": "FLOAT",
    "email": "TEXT",
    "examination_date": "DATE",
    "fat_free_mass": "FLOAT",
    "fat_mass": "FLOAT",
    "father_s_city_of_origin": "TEXT",
    "father_s_city_of_origin_1": "TEXT",
    "from_where": "TEXT",
    "fs": "FLOAT",
    "gender": "VARCHAR(10)",
    "have_you_undergone_an_operation_or_any_surgical_procedures": "BOOLEAN",
    "hba1c": "FLOAT",
    "heart_attack_or_angina": "BOOLEAN",
    "heart_rate": "FLOAT",
    "heart_rate_during_mri": "FLOAT",
    "height_cm": "FLOAT",
    "high_blood_pressure": "TEXT",
    "history_of_familial_cardiomyopathies": "BOOLEAN",
    "history_of_premature_cad": "BOOLEAN",
    "history_of_sudden_death_history": "BOOLEAN",
    "home_tel": "VARCHAR(50)",
    "home_tel_2": "VARCHAR(50)",
    "how_long_have_you_been_smoking": "FLOAT",
    "how_many_cigarettes_have_you_been_smoking_a_day": "INTEGER",
    "how_many_cigarettes_have_you_been_smoking_a_day_before_you_quit": "INTEGER",
    "how_many_siblings_you_have": "INTEGER",
    "how_many_years_have_you_been_smoking": "FLOAT",
    "is_there_any_chance_you_might_be_pregnant": "BOOLEAN",
    "ivsd": "FLOAT",
    "ivss": "FLOAT",
    "jvp": "VARCHAR(50)",
    "kidney_problems": "BOOLEAN",
    "known_collagen_disease": "BOOLEAN",
    "known_cvs_disease": "BOOLEAN",
    "left_atrium": "FLOAT",
    "left_ventricular_ef": "FLOAT",
    "left_ventricular_ejection_fraction": "FLOAT",
    "left_ventricular_end_diastolic_volume": "FLOAT",
    "left_ventricular_end_systolic_volume": "FLOAT",
    "left_ventricular_mass": "FLOAT",
    "list_these_medications": "TEXT",
    "liver_problems": "BOOLEAN",
    "lung_problems": "BOOLEAN",
    "lvedd": "FLOAT",
    "lvesd": "FLOAT",
    "lvm": "FLOAT",
    "lvpwd": "FLOAT",
    "lvpws": "FLOAT",
    "malignancy": "BOOLEAN",
    "malignancy_details": "TEXT",
    "marital_status": "VARCHAR(50)",
    "mitral_regurge": "VARCHAR(50)",
    "mitral_stenosis": "VARCHAR(50)",
    "mobile_tel": "VARCHAR(50)",
    "mobile_tel_2": "VARCHAR(50)",
    "mri": "TEXT",
    "mri_date": "DATE",
    "muscloskeletal_problems": "BOOLEAN",
    "name": "VARCHAR(200)",
    "name_1": "VARCHAR(200)",
    "nationality": "VARCHAR(50)",
    "neurological_problems": "BOOLEAN",
    "non_egyptian_parents": "BOOLEAN",
    "notes": "TEXT",
    "number_of_children": "INTEGER",
    "number_of_wives": "INTEGER",
    "offspring_of_consanguinous_marriage": "TEXT",
    "other": "TEXT",
    "other_findings": "TEXT",
    "other_mri_findings": "TEXT",
    "p_wave_abnormality": "VARCHAR(100)",
    "parents_occupation": "VARCHAR(200)",
    "physical_abnormality_details": "TEXT",
    "pr_interval": "FLOAT",
    "pregnant_female": "BOOLEAN",
    "prior_heart_failure_previous_hx": "TEXT",
    "procedure_details": "TEXT",
    "pulmonary_regurge": "VARCHAR(50)",
    "pulmonary_stenosis": "VARCHAR(50)",
    "qrs_abnormalities": "VARCHAR(200)",
    "qrs_duration": "FLOAT",
    "qtc_interval": "FLOAT",
    "rate": "FLOAT",
    "record_id": "TEXT",
    "regularity": "VARCHAR(50)",
    "rheumatic_fever": "BOOLEAN",
    "rhythm": "VARCHAR(100)",
    "right_ventricle": "FLOAT",
    "right_ventricular_ef": "FLOAT",
    "s1": "VARCHAR(50)",
    "s2": "VARCHAR(50)",
    "s3": "BOOLEAN",
    "s4": "BOOLEAN",
    "span_cm": "FLOAT",
    "specifiy_p_wave_abnormality": "TEXT",
    "specifiy_qrs_abnormality": "TEXT",
    "specifiy_st_seg_abnormality": "TEXT",
    "specifiy_t_wave_abnormality": "TEXT",
    "st_segment_abnormalities": "VARCHAR(200)",
    "subaortic_membrane": "BOOLEAN",
    "t_wave_abnormalities": "VARCHAR(200)",
    "tricuspid_regurge": "VARCHAR(50)",
    "tricuspid_stenosis": "VARCHAR(50)",
    "troponin_i": "FLOAT",
    "type": "TEXT",
    "unwilling_to_participate": "BOOLEAN",
    "volunteer_under_18_year_old": "BOOLEAN",
    "we_may_contact_you_yearly_to_follow_up_on_your_health_do_you_ac": "TEXT",
    "weight_kg": "FLOAT",
    "what_is_this_these_condition_s": "TEXT",
    "where_did_you_spend_your_childhood": "TEXT",
    "who_and_what_disease": "TEXT",
}


def _cast_by_type(value, sql_type):
    """Generic type cast for registry passthrough columns."""
    t = (sql_type or "TEXT").strip().upper()
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    if t in ("TEXT",) or t.startswith("VARCHAR"):
        return s
    if t == "INTEGER":
        try:
            return int(float(s.replace(",", "")))
        except (ValueError, TypeError):
            return None
    if t in ("FLOAT", "DOUBLE PRECISION", "NUMERIC", "REAL"):
        try:
            return float(s.replace(",", ""))
        except (ValueError, TypeError):
            return None
    if t == "BOOLEAN":
        sl = s.lower()
        if sl in ("1", "yes", "true", "t", "y"):
            return True
        if sl in ("0", "no", "false", "f", "n"):
            return False
        return None
    if t == "DATE":
        return parse_date(s, "")
    return s

# =============================================================================
# NIFI PROCESSOR CLASS
# =============================================================================

class BiolinkTransformProcessor(FlowFileTransform):
    """
    Apache NiFi 2.x Python processor that transforms raw CSV records
    from BHS or EHVol datasets into the BioLink unified schema.

    Input:  JSON object (one CSV row as key-value pairs)
    Output: JSON object conforming to participant ingestion schema
    """

    class Java:
        implements = ["org.apache.nifi.python.processor.FlowFileTransform"]

    class ProcessorDetails:
        version = "1.0.0"
        description = (
            "Transforms BHS/EHVol CSV records into the BioLink unified "
            "participant schema with field mapping, type conversion, "
            "city homogenization, BP averaging, and quality scoring."
        )
        tags = ["biolink", "etl", "transform", "csv", "healthcare"]

    DATASET_TYPE = PropertyDescriptor(
        name="Dataset Type",
        description="Source dataset type: bhs or ehvol",
        required=True,
        default_value="bhs",
        allowable_values=["bhs", "ehvol"],
        expression_language_scope=ExpressionLanguageScope.FLOWFILE_ATTRIBUTES,
    )

    property_descriptors = [DATASET_TYPE]

    def __init__(self, **kwargs):
        super().__init__()

    def getPropertyDescriptors(self):
        return self.property_descriptors

    # -----------------------------------------------------------------
    # Core transform
    # -----------------------------------------------------------------
    def transform(self, context, flowfile):
        dataset = context.getProperty(self.DATASET_TYPE).evaluateAttributeExpressions(flowfile).getValue()

        try:
            raw = json.loads(flowfile.getContentsAsBytes().decode("utf-8"))
        except Exception as e:
            return FlowFileTransformResult(
                relationship="failure",
                contents=json.dumps({"error": f"Invalid JSON input: {e}"}),
                attributes={"biolink.error": str(e)},
            )

        # Handle batch (array) or single record
        records = raw if isinstance(raw, list) else [raw]
        results = []

        for idx, record in enumerate(records):
            unified, issues = self._transform_record(record, dataset, idx)
            quality_score = self._quality_score(issues)
            unified["data_quality_score"] = round(quality_score, 2)
            results.append(unified)

        output = results if isinstance(raw, list) else results[0]

        return FlowFileTransformResult(
            relationship="success",
            contents=json.dumps(output, default=str),
            attributes={
                "biolink.dataset": dataset,
                "biolink.record_count": str(len(results)),
                "mime.type": "application/json",
            },
        )

    # -----------------------------------------------------------------
    # Record-level transform
    # -----------------------------------------------------------------
    def _transform_record(self, record, dataset, row_idx):
        unified = {
            "source_dataset": dataset,
            "ingested_at": datetime.utcnow().isoformat(),
        }
        issues = []

        # ── Step 1: Smart transforms on 34 key fields (FIELD_MAPPINGS) ────
        for unified_name, mapping in FIELD_MAPPINGS.items():
            source_key = mapping.get(dataset)
            if source_key is None:
                unified[unified_name] = None
                continue
            transform_name = mapping.get("transform")
            validation = mapping.get("validation")
            try:
                value = self._extract_value(record, source_key, unified_name, dataset)
                if value is not None and transform_name:
                    value = self._apply_transform(transform_name, value, dataset, record, source_key)
                if value is not None and validation:
                    issue = self._validate(unified_name, value, validation)
                    if issue:
                        issues.append(issue)
                unified[unified_name] = value
            except Exception as e:
                issues.append({"field": unified_name, "severity": "error", "message": str(e)})
                unified[unified_name] = None

        # ── Step 2: Full registry passthrough for ALL remaining columns ───
        # Collect source keys already handled by FIELD_MAPPINGS
        handled_src_keys: set = set()
        for mapping in FIELD_MAPPINGS.values():
            src = mapping.get(dataset)
            if isinstance(src, list):
                handled_src_keys.update(src)
            elif src:
                handled_src_keys.add(src)

        registry = BHS_REGISTRY if dataset == "bhs" else EHVOL_REGISTRY
        sql_types = BHS_SQL_TYPES if dataset == "bhs" else EHVOL_SQL_TYPES

        for src_col, pg_col in registry.items():
            if src_col in handled_src_keys:
                continue   # already covered by FIELD_MAPPINGS
            if pg_col in unified:
                continue   # already set (guard against duplicate pg_col names)
            raw_val = record.get(src_col)
            if raw_val is None or str(raw_val).strip() == "":
                unified[pg_col] = None
            else:
                unified[pg_col] = _cast_by_type(raw_val, sql_types.get(pg_col, "TEXT"))

        # ── Step 3: Computed metadata ─────────────────────────────────────
        unified["participant_id"] = self._build_participant_id(unified, record, dataset, row_idx)

        compact = {k: v for k, v in record.items()
                   if not k.startswith("_") and v is not None and str(v).strip() != ""}
        raw_json_str = json.dumps(compact, default=str)
        if len(raw_json_str) > 8192:
            mapped_keys: set = set()
            for mapping in FIELD_MAPPINGS.values():
                src = mapping.get(dataset)
                if isinstance(src, list):
                    mapped_keys.update(src)
                elif src:
                    mapped_keys.add(src)
            compact = {k: v for k, v in compact.items() if k in mapped_keys}
        unified["source_raw_json"] = compact

        return unified, issues

    # --------------------------------------------------------------
    # Value extraction  (handles multi-field BP averaging for BHS)
    # -----------------------------------------------------------------
    def _extract_value(self, record, source_key, unified_name, dataset):
        # Multi-field averaging for BHS blood pressure
        if isinstance(source_key, list):
            if dataset == "bhs" and unified_name in ("systolic_bp", "diastolic_bp"):
                values = []
                for field in source_key:
                    v = record.get(field)
                    if v and str(v).strip():
                        try:
                            values.append(float(str(v).strip()))
                        except ValueError:
                            pass
                return sum(values) / len(values) if values else None
            # Fallback: return first non-null
            for field in source_key:
                v = record.get(field)
                if v and str(v).strip():
                    return v
            return None

        return record.get(source_key)

    # -----------------------------------------------------------------
    # Apply named transform
    # -----------------------------------------------------------------
    def _apply_transform(self, transform_name, value, dataset, record, source_key):
        # Special handling for BP from EHVol combined field "120/80"
        if transform_name == "bp_systolic":
            if dataset == "ehvol":
                return extract_systolic_bp(value, dataset)
            return parse_numeric(value, dataset)

        if transform_name == "bp_diastolic":
            if dataset == "ehvol":
                return extract_diastolic_bp(value, dataset)
            return parse_numeric(value, dataset)

        func = TRANSFORM_FUNCTIONS.get(transform_name)
        if func:
            return func(value, dataset)

        return value

    # -----------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------
    @staticmethod
    def _validate(field_name, value, rule):
        if rule.get("type") == "range":
            try:
                num = float(value) if not isinstance(value, (int, float)) else value
                lo, hi = rule.get("min"), rule.get("max")
                if lo is not None and num < lo:
                    return {"field": field_name, "severity": "warning", "message": f"{num} < min {lo}"}
                if hi is not None and num > hi:
                    return {"field": field_name, "severity": "warning", "message": f"{num} > max {hi}"}
            except (ValueError, TypeError):
                pass
        return None

    # -----------------------------------------------------------------
    # Quality score
    # -----------------------------------------------------------------
    @staticmethod
    def _quality_score(issues):
        if not issues:
            return 1.0
        weights = {"critical": 0.5, "error": 0.3, "warning": 0.1, "info": 0.0}
        total = sum(weights.get(i.get("severity", "info"), 0.1) for i in issues)
        return max(0.0, 1.0 - total)

    # -----------------------------------------------------------------
    # Collision-safe participant ID builder
    # -----------------------------------------------------------------
    @staticmethod
    def _build_participant_id(unified, record, dataset, row_idx):
        pid = unified.get("participant_id")
        src = unified.get("source_record_id")

        if pid is None:
            if src not in (None, ""):
                return f"{dataset}_record_{src}"
            return f"{dataset}_row_{row_idx}"

        if dataset == "ehvol":
            if src not in (None, ""):
                return f"{pid}_{src}"
            return f"{pid}_row{row_idx}"

        return pid
