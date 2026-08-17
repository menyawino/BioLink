"""
step_7_unify_datasets.py
========================
Cross-dataset unification of BHS and EHVol cardiovascular research data.

Design principles:
  1. Zero data loss — every original column is preserved or mapped.
  2. Modality-awareness — same concept measured by different modalities
     (echo vs MRI vs ECG) is NOT collapsed; modality is explicit.
  3. Semantic layering — raw → canonical concept → harmonized value.
  4. Schema-on-read — produce both wide and long unified tables plus
     companion mapping tables for full transparency.

Inputs (from prior pipeline steps):
  - BHS_step_4_range_cleaned.csv
  - EHVol_step_4_range_cleaned.csv
  - BHS_column_classification.csv
  - EHVol_column_classification.csv
    - BHS_step_6_fuzzy_suggestions.csv
    - EHVol_step_6_fuzzy_suggestions.csv

Outputs:
  - unified_wide_table.csv          → pooled analysis ready
    - column_mapping.csv              → every original column → canonical concept
    - value_set_mapping.csv           → original values → unified values
    - unit_mapping.csv                → concept + dataset → unit
    - modality_manifest.csv           → available modalities per concept per dataset
  - unification_audit.json          → coverage metrics, conflicts, sparsity
"""

import csv
import json
import re
from collections import defaultdict
from pathlib import Path
from datetime import datetime

from src.config import INTERIM_DIR, PROCESSED_DIR

# ---------------------------------------------------------------------------
# Input / Output paths
# ---------------------------------------------------------------------------
INPUTS = {
    "BHS": {
        "data": INTERIM_DIR / "BHS_step_4_range_cleaned.csv",
        "classification": INTERIM_DIR / "BHS_column_classification.csv",
        "step6": INTERIM_DIR / "BHS_step_6_fuzzy_suggestions.csv",
    },
    "EHVol": {
        "data": INTERIM_DIR / "EHVol_step_4_range_cleaned.csv",
        "classification": INTERIM_DIR / "EHVol_column_classification.csv",
        "step6": INTERIM_DIR / "EHVol_step_6_fuzzy_suggestions.csv",
    },
}

OUTPUT_PREFIX = PROCESSED_DIR / "step_7"

# ---------------------------------------------------------------------------
# 1. MODALITY DETECTION
# ---------------------------------------------------------------------------
CATEGORY_TO_MODALITY = {
    "Echocardiography & Vascular Imaging": "echo",
    "ECG & Rhythm": "ecg",
    "MRI / CT & Advanced Imaging": "mri_ct",
    "Vitals & Anthropometrics": "vitals",
    "Laboratory Tests & Biomarkers": "lab",
    "Diagnoses & Medical History": "diagnosis",
    "Medication & Dosing": "medication",
    "Family History & Lineage": "family_history",
    "Lifestyle & Risk Factors": "lifestyle",
    "Procedures & Interventions": "procedure",
    "Questionnaires & Reported Symptoms": "symptom",
    "Administration & Consent": "admin",
    "Timeline & Dates": "timeline",
    "Demographics & Social Context": "demographics",
    "Biobanking & Samples": "biobank",
    "Other / Needs Review": "other",
}

# Override modality based on column-name patterns (higher priority than category)
MODALITY_OVERRIDES = [
    (r"\bmri\b", "mri"),
    (r"\bct\b", "ct"),
    (r"\becho\b|\bechocardiograph", "echo"),
    (r"\becg\b|\belectrocardiogram", "ecg"),
    (r"\bholter\b", "holter"),
    (r"\blab\b|\blaboratory\b", "lab"),
    (r"\babi\b", "vascular"),
    (r"\bimt\b", "vascular"),
    (r"\bcarotid\b", "vascular"),
]


def detect_modality(col_name: str, broad_category: str) -> str:
    """Return the modality for a column."""
    col_lower = col_name.lower()
    for pattern, mod in MODALITY_OVERRIDES:
        if re.search(pattern, col_lower):
            return mod
    return CATEGORY_TO_MODALITY.get(broad_category, "other")


# ---------------------------------------------------------------------------
# 2. COLUMN NAME NORMALISATION → CANONICAL CONCEPT
# ---------------------------------------------------------------------------
# Strip administrative noise, units, and modality hints to get the core concept.
STOP_WORDS = {
    "in", "of", "the", "a", "an", "and", "or", "for", "to", "from",
    "at", "on", "with", "by", "as", "is", "are", "was", "were",
    "be", "been", "being", "have", "has", "had", "do", "does", "did",
    "will", "would", "could", "should", "may", "might", "must",
    "can", "shall", "please", "if", "yes", "no", "other", "specify",
    "details", "detail", "comment", "comments", "finding", "findings",
    "result", "results", "value", "values", "measurement", "measurements",
    "date", "time", "day", "month", "year", "age", "current", "recent",
    "prior", "previous", "history", "known", "do you", "have you",
    "are you", "did you", "was there", "is there", "any", "some",
    "all", "each", "every", "both", "either", "neither", "this",
    "these", "that", "those", "what", "which", "who", "whom",
    "whose", "where", "when", "why", "how", "how many", "how much",
    "how long", "how often", "how far", "how old", "how big",
}

UNIT_SUFFIXES = [
    r"\s*\(\s*(?:in\s+)?(?:mm|cm|m|kg|g|lb|oz|ml|l|mg|mcg|ng|pg|iu|%|bpm|cpm|mmhg|years?|months?|weeks?|days?)\s*\)",
    r"\s*-\s*(?:mm|cm|m|kg|g|lb|oz|ml|l|mg|mcg|ng|pg|iu|%|bpm|cpm|mmhg)",
    r"\s+in\s+(?:mm|cm|m|kg|g|lb|oz|ml|l|mg|mcg|ng|pg|iu|%|bpm|cpm|mmhg)",
]


from src.utils.snomed_mapper import get_snomed_mapper

SNOMED_MAPPING = {
    "hypertension": "essential_hypertension",
    "htn": "essential_hypertension",
    "diabetes": "diabetes_mellitus",
    "dm": "diabetes_mellitus",
    "heart_attack": "myocardial_infarction",
    "mi": "myocardial_infarction",
    "stroke": "cerebrovascular_accident",
    "cva": "cerebrovascular_accident",
    "heart_failure": "heart_failure",
    "hf": "heart_failure",
    "chf": "congestive_heart_failure",
    "angina": "angina_pectoris",
    "cad": "coronary_artery_disease",
    "cabg": "coronary_artery_bypass_graft",
    "pci": "percutaneous_coronary_intervention",
    "echo": "echocardiography",
    "ecg": "electrocardiogram",
    "ekg": "electrocardiogram",
    "mri": "magnetic_resonance_imaging",
    "ct": "computed_tomography",
    "bmi": "body_mass_index",
    "sbp": "systolic_blood_pressure",
    "dbp": "diastolic_blood_pressure",
    "hr": "heart_rate",
    "lvef": "left_ventricular_ejection_fraction",
    "ef": "ejection_fraction",
    "weight": "body_weight",
    "height": "body_height",
    "cvs_disease": "cardiovascular_disease",
    "cholesterol": "cholesterol_measurement",
    "tg": "triglyceride_measurement",
    "hdl": "high_density_lipoprotein",
    "ldl": "low_density_lipoprotein",
    "fbs": "fasting_blood_glucose",
    "hba1c": "hemoglobin_a1c",
}


def normalize_concept_name(col_name: str) -> str:
    """
    Convert a raw column name to a canonical concept name.
    Examples:
      'LVEDD' → 'lvedd'
      'Weight in kg' → 'body_weight'
      'Systolic Blood Pressure - Right Brachial - Measurement 1' → 'systolic_blood_pressure'
      'Do you have Hypertension?' → 'essential_hypertension'
    """
    name = col_name.lower().strip()

    # Remove unit suffixes
    for pattern in UNIT_SUFFIXES:
        name = re.sub(pattern, "", name, flags=re.IGNORECASE)

    # Remove trailing punctuation and whitespace
    name = re.sub(r"[?*!.,;:]+$", "", name).strip()

    # Remove common prefixes like "do you have", "have you been diagnosed with"
    name = re.sub(
        r"^(?:do you have|have you (?:been diagnosed with|undergone|had)|"
        r"are you|is there any chance you might be|"
        r"have you experienced|have you ever had|"
        r"have you been|did you|was there|what is your|"
        r"what is the|how many|how long|how much|"
        r"if yes,?\s*please specify|if yes,?\s*and specify|"
        r"if yes,?\s*specify|and specify|please specify|"
        r"specify|if yes,?|if no,?|if other,?\s*specify|"
        r"if other,?|other|details?|comments?|findings?|"
        r"results?|values?|measurements?|"
        r"date\s*\(?|time\s*\(?|day\s*\(?|month\s*\(?|year\s*\(?)",
        "",
        name,
        flags=re.IGNORECASE,
    ).strip()

    # Remove stop words (only as whole words)
    tokens = re.findall(r"[a-z0-9_\-]+", name)
    filtered = [t for t in tokens if t not in STOP_WORDS and len(t) > 1]

    if not filtered:
        # Fallback: keep the original stripped name
        filtered = re.findall(r"[a-z0-9_\-]+", name.lower())
        filtered = [t for t in filtered if len(t) > 1]

    concept = "_".join(filtered) if filtered else "unnamed"
    
    # 1. Check acronym overrides
    if concept in SNOMED_MAPPING:
        return SNOMED_MAPPING[concept]
        
    # 2. Check SNOMED GPS Release for exact matches
    mapper = get_snomed_mapper()
    return mapper.get_snomed_term(concept)


# ---------------------------------------------------------------------------
# 3. VALUE SET HARMONISATION
# ---------------------------------------------------------------------------
# Maps original values → unified values for specific concepts.
# Keys are canonical concept names; values are dicts of {original: unified}.
VALUE_SET_RULES = {
    # Gender
    "gender": {
        "male": "male", "m": "male", "man": "male",
        "female": "female", "f": "female", "woman": "female",
    },
    # Yes/No/Boolean
    "_boolean": {
        "yes": "yes", "y": "yes", "true": "yes", "checked": "yes",
        "no": "no", "n": "no", "false": "no", "unchecked": "no",
        "unknown": "unknown", "unk": "unknown", "na": "unknown",
        "not applicable": "unknown", "n/a": "unknown",
    },
    # Smoking status (BHS has richer vocabulary)
    "smoking_status": {
        "smoker": "current",
        "current smoker": "current",
        "non-smoker": "never",
        "never smoker": "never",
        "ex-smoker": "former",
        "former smoker": "former",
        "yes": "current",
        "no": "never",
    },
    # Consanguinity
    "consanguinity_status": {
        "yes": "yes", "no": "no",
    },
    # Marital status
    "marital_status": {
        "married": "married", "single": "single",
        "divorced": "divorced", "widowed": "widowed",
    },
    # Ethnicity / Nationality (handled by Step 6 fuzzy matching dictionary)
    "nationality": {},
    "ethnicity": {},
}

# Concepts that should be treated as boolean regardless of their raw values
BOOLEAN_CONCEPTS = {
    "hypertension", "diabetes", "dyslipidemia", "hyperlipidemia",
    "renal_disease", "respiratory_illnesses", "erectile_dysfunction",
    "rheumatic_fever", "rhd", "pvd", "congenital_heart_disease",
    "mi", "stroke", "tia", "heart_failure", "angina",
    "lung_problems", "kidney_problems", "liver_problems",
    "anaemia", "neurological_problems", "muscloskeletal_problems",
    "autoimmune_problems", "malignancy",
    "known_cvs_disease", "known_collagen_disease",
    "contraindications_for_mri", "pregnant_female",
    "history_of_sudden_death", "history_of_familial_cardiomyopathies",
    "history_of_premature_cad", "offspring_of_consanguinous_marriage",
    "consanguinous_marriage", "non_egyptian_parents",
    "communication_difficulties", "unwilling_to_participate",
    "volunteer_under_18",
    "do_any_of_your_children_have_congenital_malformations_or_diseases",
    "has_anyone_in_your_family_experienced_sudden_death_mi_stroke_or_hospitalization_due_to_heart_failure",
    "moderate_or_severe_valvular_lesion",
    "subaortic_membrane", "mitral_regurge", "mitral_stenosis",
    "tricuspid_regurge", "tricuspid_stenosis", "aortic_regurge",
    "aortic_stenosis", "pulmonary_regurge", "pulmonary_stenosis",
    "rheumatic_valvular_heart_disease", "congenital_heart_defect",
    "myxomatous_valve_disease", "degenerative_valve_disease",
    "pericardium_normal", "pericardium_effusion", "pericardium_calcified",
    "abnormality_none", "abnormality_t_wave_inversion",
    "abnormality_st_seg_elevation", "abnormality_st_seg_depression",
    "abnormality_pathological_q_waves",
    "lvh", "ectopic_beats", "qrs_width_120_ms",
    "p_wave_abnormality", "qrs_abnormalities",
    "st_segment_abnormalities", "t_wave_abnormalities",
    "s3", "s4", "abnormal_physical_structure",
    "regional_wall_motion_abnormalities",
    "pulmonary_hypertension",
    "do_you_drink_alcohol", "do_you_consume_alcohol",
    "do_you_take_any_medication_currently",
    "have_you_undergone_an_operation_or_any_surgical_procedures",
    "does_any_other_non_cardiac_condition_run_in_your_family",
    "are_your_parents_grandparents_or_great_grandparents_from_non_egyptian_origin",
    "are_you_one_of_a_twin_or_triplet",
    "do_you_get_this_pain_or_discomfort_when_you_walk_uphill_or_hurry",
    "do_you_get_it_when_you_walk_at_an_ordinary_pace_on_the_level",
    "does_it_go_away_when_you_stand_still",
    "have_you_ever_had_a_severe_pain_across_the_front_of_your_chest_lasting_for_half_an_hour_or_more",
    "have_you_ever_been_diagnosed_with_mi",
    "have_you_been_hospitalized_due_to_heart_failure",
    "have_you_had_a_prior_stroke_or_tia",
    "have_you_undergone_a_coronary_angioplasty_stent",
    "have_you_undergone_a_prior_cabg",
    "have_you_had_any_other_cardiac_procedures",
    "have_you_received_influenza_immunization_within_a_year",
    "have_you_been_diagnosed_with_renal_disease",
    "have_you_been_diagnosed_with_respiratory_illnesses",
    "have_you_been_diagnosed_with_congenital_heart_disease",
    "have_you_been_diagnosed_with_rheumatic_fever",
    "have_you_been_diagnosed_with_rhd",
    "have_you_been_diagnosed_with_pvd",
    "do_you_have_hypertension",
    "do_you_have_hyperlipidemia",
    "do_you_have_diabetes",
    "do_you_have_erectile_dysfunction",
    "have_you_experienced_shortness_of_breath",
    "have_you_ever_had_any_pain_or_discomfort_in_your_chest",
    "intervention_required", "further_plan",
    "agree_to_consent", "agree_to_provide_family_history",
    "agree_to_undergo_tte", "agree_to_have_an_ecg",
    "agree_to_withdraw_samples_for_lab_workup",
    "agree_to_undergo_carotid_duplex", "agree_to_ct", "agree_to_cmr",
    "current_recent_smoker_1_year",
}


def harmonize_value(concept: str, raw_value: str, step6_canonical: str = "") -> str:
    """Return a harmonized value for a given concept."""
    if raw_value is None or raw_value == "":
        return ""

    val_lower = raw_value.strip().lower()

    if step6_canonical:
        return step6_canonical

    # Concept-specific rules
    if concept in VALUE_SET_RULES:
        mapping = VALUE_SET_RULES[concept]
        if val_lower in mapping:
            return mapping[val_lower]

    # Boolean concepts
    if concept in BOOLEAN_CONCEPTS:
        if val_lower in VALUE_SET_RULES["_boolean"]:
            return VALUE_SET_RULES["_boolean"][val_lower]
        # Try to infer from common patterns
        if val_lower in {"yes", "y", "true", "checked", "present", "positive"}:
            return "yes"
        if val_lower in {"no", "n", "false", "unchecked", "absent", "negative", "none"}:
            return "no"
        return val_lower  # preserve unusual values

    # Default: lowercase and strip
    return val_lower


# ---------------------------------------------------------------------------
# 4. UNIT TAGGING
# ---------------------------------------------------------------------------
# Concept + dataset → (unit, conversion_factor_to_standard)
# Standard units: mm for echo linear dims, % for fractions, kg for weight, cm for height,
#                 mmHg for BP, bpm for HR, g for mass, mL for volume, mg/dL for lipids, etc.
UNIT_RULES = {
    # Echo linear dimensions
    ("lvedd", "BHS"): ("mm", 1.0),
    ("lvedd", "EHVol"): ("cm", 10.0),  # 1 cm = 10 mm
    ("lvesd", "BHS"): ("mm", 1.0),
    ("lvesd", "EHVol"): ("cm", 10.0),
    ("swt", "BHS"): ("mm", 1.0),
    ("swt", "EHVol"): ("cm", 10.0),
    ("pwt", "BHS"): ("mm", 1.0),
    ("pwt", "EHVol"): ("cm", 10.0),
    ("ivsd", "BHS"): ("mm", 1.0),
    ("ivsd", "EHVol"): ("cm", 10.0),
    ("ivss", "BHS"): ("mm", 1.0),
    ("ivss", "EHVol"): ("cm", 10.0),
    ("lvpwd", "BHS"): ("mm", 1.0),
    ("lvpwd", "EHVol"): ("cm", 10.0),
    ("lvpws", "BHS"): ("mm", 1.0),
    ("lvpws", "EHVol"): ("cm", 10.0),
    ("la_diameter", "BHS"): ("mm", 1.0),
    ("la_diameter", "EHVol"): ("cm", 10.0),
    ("rv_diameters", "BHS"): ("mm", 1.0),
    ("rv_diameters", "EHVol"): ("cm", 10.0),
    ("aortic_annulus", "BHS"): ("mm", 1.0),
    ("aortic_annulus", "EHVol"): ("cm", 10.0),
    ("sinus_of_valsalva", "BHS"): ("mm", 1.0),
    ("sinus_of_valsalva", "EHVol"): ("cm", 10.0),
    ("sino_tubular_junction", "BHS"): ("mm", 1.0),
    ("sino_tubular_junction", "EHVol"): ("cm", 10.0),
    ("tubular_ascending_aorta", "BHS"): ("mm", 1.0),
    ("tubular_ascending_aorta", "EHVol"): ("cm", 10.0),
    ("tapse", "BHS"): ("mm", 1.0),
    ("tapse", "EHVol"): ("mm", 1.0),
    ("pasp", "BHS"): ("mmhg", 1.0),
    ("pasp", "EHVol"): ("mmhg", 1.0),
    ("aortic_root", "BHS"): ("cm", 1.0),
    ("aortic_root", "EHVol"): ("cm", 1.0),
    ("left_atrium", "BHS"): ("cm", 1.0),
    ("left_atrium", "EHVol"): ("cm", 1.0),
    ("right_ventricle", "BHS"): ("cm", 1.0),
    ("right_ventricle", "EHVol"): ("cm", 1.0),

    # Echo functional
    ("ef", "BHS"): ("%", 1.0),
    ("ef", "EHVol"): ("%", 1.0),
    ("fs", "BHS"): ("%", 1.0),
    ("fs", "EHVol"): ("%", 1.0),
    ("lvef", "BHS"): ("%", 1.0),
    ("lvef", "EHVol"): ("%", 1.0),
    ("left_ventricular_ejection_fraction", "BHS"): ("%", 1.0),
    ("left_ventricular_ejection_fraction", "EHVol"): ("%", 1.0),

    # Echo mass / volume
    ("lvm", "BHS"): ("g", 1.0),
    ("lvm", "EHVol"): ("g", 1.0),
    ("left_ventricular_mass", "BHS"): ("g", 1.0),
    ("left_ventricular_mass", "EHVol"): ("g", 1.0),
    ("la_volume", "BHS"): ("ml", 1.0),
    ("la_volume", "EHVol"): ("ml", 1.0),
    ("left_ventricular_end_diastolic_volume", "EHVol"): ("ml", 1.0),
    ("left_ventricular_end_systolic_volume", "EHVol"): ("ml", 1.0),

    # Vitals
    ("weight", "BHS"): ("kg", 1.0),
    ("weight", "EHVol"): ("kg", 1.0),
    ("height", "BHS"): ("cm", 1.0),
    ("height", "EHVol"): ("cm", 1.0),
    ("bmi", "BHS"): ("kg/m2", 1.0),
    ("bmi", "EHVol"): ("kg/m2", 1.0),
    ("bsa", "BHS"): ("m2", 1.0),
    ("bsa", "EHVol"): ("m2", 1.0),
    ("heart_rate", "BHS"): ("bpm", 1.0),
    ("heart_rate", "EHVol"): ("bpm", 1.0),
    ("systolic_blood_pressure", "BHS"): ("mmhg", 1.0),
    ("systolic_blood_pressure", "EHVol"): ("mmhg", 1.0),
    ("diastolic_blood_pressure", "BHS"): ("mmhg", 1.0),
    ("diastolic_blood_pressure", "EHVol"): ("mmhg", 1.0),
    ("bp", "BHS"): ("mmhg", 1.0),
    ("bp", "EHVol"): ("mmhg", 1.0),
    ("jvp", "BHS"): ("cm_h2o", 1.0),
    ("jvp", "EHVol"): ("cm_h2o", 1.0),
    ("waist_circumference", "BHS"): ("cm", 1.0),
    ("hip_circumference", "BHS"): ("cm", 1.0),
    ("waist_hip_ratio", "BHS"): ("ratio", 1.0),
    ("span", "EHVol"): ("cm", 1.0),

    # ECG
    ("ventricular_rate", "BHS"): ("bpm", 1.0),
    ("rate", "EHVol"): ("bpm", 1.0),
    ("qrs_duration", "BHS"): ("ms", 1.0),
    ("qrs_duration", "EHVol"): ("ms", 1.0),
    ("pr_interval", "EHVol"): ("ms", 1.0),
    ("qt_interval", "BHS"): ("ms", 1.0),
    ("qt_interval", "EHVol"): ("ms", 1.0),
    ("corrected_qt_interval", "BHS"): ("ms", 1.0),
    ("qtc_interval", "EHVol"): ("ms", 1.0),

    # Labs
    ("urea", "BHS"): ("mg/dl", 1.0),
    ("creatinine", "BHS"): ("mg/dl", 1.0),
    ("egfr", "BHS"): ("ml/min/1.73m2", 1.0),
    ("na", "BHS"): ("meq/l", 1.0),
    ("k", "BHS"): ("meq/l", 1.0),
    ("ca", "BHS"): ("mg/dl", 1.0),
    ("mg", "BHS"): ("mg/dl", 1.0),
    ("alt", "BHS"): ("u/l", 1.0),
    ("ast", "BHS"): ("u/l", 1.0),
    ("total_bilirubin", "BHS"): ("mg/dl", 1.0),
    ("direct_bilirubin", "BHS"): ("mg/dl", 1.0),
    ("albumin", "BHS"): ("g/dl", 1.0),
    ("crp", "BHS"): ("mg/l", 1.0),
    ("total_cholesterol", "BHS"): ("mg/dl", 1.0),
    ("serum_triglycerides", "BHS"): ("mg/dl", 1.0),
    ("hdl", "BHS"): ("mg/dl", 1.0),
    ("ldl", "BHS"): ("mg/dl", 1.0),
    ("vldl", "BHS"): ("mg/dl", 1.0),
    ("troponin", "BHS"): ("ng/ml", 1.0),
    ("troponin_i", "EHVol"): ("ng/ml", 1.0),
    ("bnp", "BHS"): ("pg/ml", 1.0),
    ("hemoglobin", "BHS"): ("g/dl", 1.0),
    ("hematocrit", "BHS"): ("%", 1.0),
    ("rbcs", "BHS"): ("million/ul", 1.0),
    ("mcv", "BHS"): ("fl", 1.0),
    ("mch", "BHS"): ("pg", 1.0),
    ("mchc", "BHS"): ("g/dl", 1.0),
    ("rdw", "BHS"): ("%", 1.0),
    ("platelet_count", "BHS"): ("k/ul", 1.0),
    ("tlc", "BHS"): ("k/ul", 1.0),
    ("t3", "BHS"): ("ng/dl", 1.0),
    ("t4", "BHS"): ("ug/dl", 1.0),
    ("tsh", "BHS"): ("uiu/ml", 1.0),
    ("hba1c", "BHS"): ("%", 1.0),
    ("hba1c", "EHVol"): ("%", 1.0),
    ("random_blood_glucose", "BHS"): ("mg/dl", 1.0),
    ("fasting_blood_glucose", "BHS"): ("mg/dl", 1.0),

    # Risk scores
    ("lifetime_ascvd_risk", "BHS"): ("%", 1.0),
    ("current_10_year_ascvd_risk", "BHS"): ("%", 1.0),
    ("optimal_ascvd_risk", "BHS"): ("%", 1.0),

    # Vascular
    ("imt", "BHS"): ("mm", 1.0),
    ("brachial_pressure", "BHS"): ("mmhg", 1.0),
    ("right_anterior_tibial_pressure", "BHS"): ("mmhg", 1.0),
    ("right_posterior_tibial_pressure", "BHS"): ("mmhg", 1.0),
    ("left_anterior_tibial_pressure", "BHS"): ("mmhg", 1.0),
    ("left_posterior_tibial_pressure", "BHS"): ("mmhg", 1.0),
    ("right_anterior_tibial_abi", "BHS"): ("ratio", 1.0),
    ("right_posterior_tibial_abi", "BHS"): ("ratio", 1.0),
    ("left_anterior_tibial_abi", "BHS"): ("ratio", 1.0),
    ("left_posterior_tibial_abi", "BHS"): ("ratio", 1.0),
}


def get_unit_info(concept: str, dataset: str):
    """Return (unit, conversion_factor) for a concept in a dataset."""
    return UNIT_RULES.get((concept, dataset), ("", 1.0))


# ---------------------------------------------------------------------------
# 5. REPEATING GROUP DETECTION (pre-computed from header sequence)
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# 6. LOAD DATA & CLASSIFICATIONS
# ---------------------------------------------------------------------------
def load_csv_indexed(path: Path) -> tuple[list[str], list[list[str]]]:
    """
    Load CSV using index-based access to handle duplicate column names.
    Returns (header_list, rows_as_lists).
    """
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)
    return header, rows


def load_classifications(path: Path) -> dict[str, dict]:
    """Return {column_name: classification_row}."""
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    result = {}
    for row in rows:
        result[row["column_name"]] = row
    return result


def load_step6_mappings(path: Path) -> dict[tuple[str, str], dict]:
    """Return accepted Step 6 mappings keyed by (column_name, raw_value_lower)."""
    accepted_actions = {"auto_accept", "review_recommended"}
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    result = {}
    for row in rows:
        canonical_value = (row.get("canonical_value") or "").strip().lower()
        suggested_action = (row.get("suggested_action") or "").strip().lower()
        raw_value = (row.get("raw_value") or "").strip().lower()
        column_name = row.get("column_name") or ""

        if not canonical_value or suggested_action not in accepted_actions or not raw_value:
            continue

        result[(column_name, raw_value)] = {
            "canonical_value": canonical_value,
            "match_type": row.get("match_type", ""),
            "suggested_action": suggested_action,
            "dictionary": row.get("dictionary", ""),
            "similarity_score": row.get("similarity_score", ""),
        }
    return result


# ---------------------------------------------------------------------------
# 7. BUILD CONCEPT REGISTRY
# ---------------------------------------------------------------------------
def build_concept_registry(datasets: dict) -> dict:
    """
    Build a registry of all canonical concepts across datasets.
    Returns:
      {
        concept_name: {
          "modality": str,
          "datasets": {dataset: [column_names]},
          "broad_family": str,
          "broad_category": str,
        }
      }
    """
    registry = defaultdict(lambda: {
        "modality": "",
        "datasets": defaultdict(list),
        "broad_family": "",
        "broad_category": "",
    })

    for dataset_name, info in datasets.items():
        classifications = info["classifications"]
        for col_name in info["header"]:
            cls = classifications.get(col_name, {})
            if not cls and " - selected_" in col_name:
                parent_name = col_name.split(" - selected_")[0]
                cls = classifications.get(parent_name, {})
                if not cls:
                    for k in classifications.keys():
                        k_clean = k.replace("  ", " ")
                        p_clean = parent_name.replace("  ", " ").strip()
                        if k_clean.startswith(p_clean + " (choice="):
                            cls = classifications[k]
                            break
                
            concept = normalize_concept_name(col_name)
            modality = detect_modality(col_name, cls.get("broad_category", ""))
            
            if concept in ["type", "unnamed", "disease", "other"]:
                concept = f"{concept}_{modality}"
                
            if concept == "hba1c":
                modality = "lab"

            entry = registry[concept]
            entry["datasets"][dataset_name].append(col_name)
            entry["modality"] = modality
            entry["broad_family"] = cls.get("broad_family", "")
            entry["broad_category"] = cls.get("broad_category", "")

    return dict(registry)


# ---------------------------------------------------------------------------
# 8. UNIFICATION ENGINE
# ---------------------------------------------------------------------------
def unify_datasets():
    print("=" * 70)
    print("STEP 7: Cross-Dataset Unification")
    print("=" * 70)

    # ------------------------------------------------------------------
    # 8.1 Load everything (index-based to handle duplicate column names)
    # ------------------------------------------------------------------
    datasets = {}
    for name, paths in INPUTS.items():
        print(f"\nLoading {name}...")
        header, rows = load_csv_indexed(paths["data"])
        classifications = load_classifications(paths["classification"])
        step6_mappings = load_step6_mappings(paths["step6"])
        datasets[name] = {
            "header": header,
            "rows": rows,
            "classifications": classifications,
            "step6_mappings": step6_mappings,
            "columns": header,
        }
        print(f"  Rows: {len(rows)}, Columns: {len(header)}")
        print(f"  Step 6 accepted mappings: {len(step6_mappings)}")

    # ------------------------------------------------------------------
    # 8.2 Build concept registry
    # ------------------------------------------------------------------
    print("\nBuilding concept registry...")
    registry = build_concept_registry(datasets)
    print(f"  Total canonical concepts: {len(registry)}")

    # Categorize concepts
    shared_concepts = []
    bhs_only = []
    ehvol_only = []
    for concept, info in registry.items():
        ds = set(info["datasets"].keys())
        if ds == {"BHS", "EHVol"}:
            shared_concepts.append(concept)
        elif ds == {"BHS"}:
            bhs_only.append(concept)
        elif ds == {"EHVol"}:
            ehvol_only.append(concept)

    print(f"  Shared concepts: {len(shared_concepts)}")
    print(f"  BHS-only concepts: {len(bhs_only)}")
    print(f"  EHVol-only concepts: {len(ehvol_only)}")

    # ------------------------------------------------------------------
    # 8.3 Prepare output structures
    # ------------------------------------------------------------------
    column_mapping = []       # original_col → canonical_concept + modality
    value_set_mapping = []    # concept + original_value → unified_value
    unit_mapping = []         # concept + dataset → unit + conversion
    modality_manifest = []    # concept + dataset → modality

    unified_wide_rows = []
    step6_applied_rows = 0
    step6_applied_unique = set()

    # ------------------------------------------------------------------
    # 8.5 Process each dataset row-by-row
    # ------------------------------------------------------------------
    for dataset_name, info in datasets.items():
        header = info["header"]
        rows = info["rows"]
        classifications = info["classifications"]
        step6_mappings = info["step6_mappings"]

        for row_idx, row in enumerate(rows):
            # Synthetic participant ID
            if dataset_name == "BHS":
                pid = f"BHS_{row[header.index('MRN (BU)')] if 'MRN (BU)' in header else f'row_{row_idx}'}"
            else:
                pid = f"EHVol_{row[header.index('DNA ID')] if 'DNA ID' in header else f'row_{row_idx}'}"

            wide_row = {
                "dataset_source": dataset_name,
                "participant_id": pid,
            }

            # --- Process regular columns ---
            for col_idx, col_name in enumerate(header):
                raw_value = row[col_idx]
                raw_value_stripped = raw_value.strip() if isinstance(raw_value, str) else raw_value

                # Get classification
                cls = classifications.get(col_name, {})
                if not cls and " - selected_" in col_name:
                    parent_name = col_name.split(" - selected_")[0]
                    cls = classifications.get(parent_name, {})
                    if not cls:
                        for k in classifications.keys():
                            k_clean = k.replace("  ", " ")
                            p_clean = parent_name.replace("  ", " ").strip()
                            if k_clean.startswith(p_clean + " (choice="):
                                cls = classifications[k]
                                break
                    
                concept = normalize_concept_name(col_name)
                modality = detect_modality(col_name, cls.get("broad_category", ""))
                
                if concept in ["type", "unnamed", "disease", "other"]:
                    concept = f"{concept}_{modality}"
                    
                if concept == "hba1c":
                    modality = "lab"

                step6_match = None
                if isinstance(raw_value_stripped, str) and raw_value_stripped:
                    step6_match = step6_mappings.get((col_name, raw_value_stripped.lower()))

                # Harmonize value
                unified_value = harmonize_value(
                    concept,
                    raw_value,
                    step6_canonical=step6_match["canonical_value"] if step6_match else "",
                )

                if step6_match:
                    step6_applied_rows += 1
                    step6_applied_unique.add((dataset_name, col_name, raw_value_stripped.lower(), unified_value))

                # Get unit info
                unit, conversion = get_unit_info(concept, dataset_name)

                # Column mapping record
                column_mapping.append({
                    "dataset": dataset_name,
                    "original_column": col_name,
                    "canonical_concept": concept,
                    "modality": modality,
                    "broad_family": cls.get("broad_family", ""),
                    "broad_category": cls.get("broad_category", ""),
                    "pii_label": cls.get("pii_label", ""),
                })

                # Unit mapping record
                if unit:
                    unit_mapping.append({
                        "concept": concept,
                        "dataset": dataset_name,
                        "unit": unit,
                        "conversion_factor": conversion,
                    })

                # Modality manifest record
                modality_manifest.append({
                    "concept": concept,
                    "dataset": dataset_name,
                    "modality": modality,
                    "original_column": col_name,
                })

                # Value set mapping (only for non-empty, transformed values)
                if raw_value and raw_value.strip() and raw_value.strip().lower() != unified_value:
                    value_set_mapping.append({
                        "concept": concept,
                        "dataset": dataset_name,
                        "original_value": raw_value.strip(),
                        "unified_value": unified_value,
                    })

                # Build wide table column name
                if concept in shared_concepts:
                    # Check if same concept has different modalities in different datasets
                    bhs_modality = ""
                    ehvol_modality = ""
                    if "BHS" in registry[concept]["datasets"]:
                        bhs_modality = detect_modality(
                            registry[concept]["datasets"]["BHS"][0],
                            classifications.get(registry[concept]["datasets"]["BHS"][0], {}).get("broad_category", "")
                        )
                    if "EHVol" in registry[concept]["datasets"]:
                        ehvol_modality = detect_modality(
                            registry[concept]["datasets"]["EHVol"][0],
                            classifications.get(registry[concept]["datasets"]["EHVol"][0], {}).get("broad_category", "")
                        )

                    if bhs_modality and ehvol_modality and bhs_modality != ehvol_modality:
                        wide_col = f"{concept}_{modality}"
                    else:
                        wide_col = concept
                else:
                    wide_col = f"{concept}_{modality}" if modality else concept

                wide_row[wide_col] = unified_value
                if unit:
                    wide_row[f"{wide_col}_unit"] = unit

            unified_wide_rows.append(wide_row)

    # ------------------------------------------------------------------
    # 8.6 Deduplicate mapping tables
    # ------------------------------------------------------------------
    def dedupe(rows: list[dict], keys: list[str]) -> list[dict]:
        seen = set()
        result = []
        for r in rows:
            key = tuple(r.get(k, "") for k in keys)
            if key not in seen:
                seen.add(key)
                result.append(r)
        return result

    column_mapping = dedupe(column_mapping, ["dataset", "original_column"])
    value_set_mapping = dedupe(value_set_mapping, ["concept", "dataset", "original_value"])
    unit_mapping = dedupe(unit_mapping, ["concept", "dataset"])
    modality_manifest = dedupe(modality_manifest, ["concept", "dataset", "modality"])

    # ------------------------------------------------------------------
    # 8.7 Write outputs
    # ------------------------------------------------------------------
    print("\nWriting outputs...")

    # Unified wide table
    if unified_wide_rows:
        all_wide_cols = set()
        for r in unified_wide_rows:
            all_wide_cols.update(r.keys())
        all_wide_cols = sorted(all_wide_cols, key=lambda c: (
            0 if c in {"dataset_source", "participant_id"} else 1,
            c,
        ))
        wide_path = OUTPUT_PREFIX / "unified_wide_table.csv"
        wide_path.parent.mkdir(parents=True, exist_ok=True)
        with open(wide_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=all_wide_cols)
            w.writeheader()
            w.writerows(unified_wide_rows)
        print(f"  Unified wide table: {wide_path} ({len(unified_wide_rows)} rows, {len(all_wide_cols)} cols)")

    # Column mapping
    if column_mapping:
        cm_path = OUTPUT_PREFIX / "column_mapping.csv"
        with open(cm_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=[
                "dataset", "original_column", "canonical_concept", "modality",
                "broad_family", "broad_category", "pii_label",
            ])
            w.writeheader()
            w.writerows(column_mapping)
        print(f"  Column mapping: {cm_path} ({len(column_mapping)} entries)")

    # Value set mapping
    if value_set_mapping:
        vsm_path = OUTPUT_PREFIX / "value_set_mapping.csv"
        with open(vsm_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=[
                "concept", "dataset", "original_value", "unified_value",
            ])
            w.writeheader()
            w.writerows(value_set_mapping)
        print(f"  Value set mapping: {vsm_path} ({len(value_set_mapping)} entries)")

    # Unit mapping
    if unit_mapping:
        um_path = OUTPUT_PREFIX / "unit_mapping.csv"
        with open(um_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=[
                "concept", "dataset", "unit", "conversion_factor",
            ])
            w.writeheader()
            w.writerows(unit_mapping)
        print(f"  Unit mapping: {um_path} ({len(unit_mapping)} entries)")

    # Modality manifest
    if modality_manifest:
        mm_path = OUTPUT_PREFIX / "modality_manifest.csv"
        with open(mm_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=[
                "concept", "dataset", "modality", "original_column",
            ])
            w.writeheader()
            w.writerows(modality_manifest)
        print(f"  Modality manifest: {mm_path} ({len(modality_manifest)} entries)")

    # ------------------------------------------------------------------
    # 8.8 Generate audit report
    # ------------------------------------------------------------------
    audit = {
        "timestamp": datetime.now().isoformat(),
        "datasets": {
            "BHS": {"rows": len(datasets["BHS"]["rows"]), "columns": len(datasets["BHS"]["header"])},
            "EHVol": {"rows": len(datasets["EHVol"]["rows"]), "columns": len(datasets["EHVol"]["header"])},
        },
        "concepts": {
            "total": len(registry),
            "shared": len(shared_concepts),
            "bhs_only": len(bhs_only),
            "ehvol_only": len(ehvol_only),
            "shared_list": sorted(shared_concepts),
            "bhs_only_list": sorted(bhs_only),
            "ehvol_only_list": sorted(ehvol_only),
        },
        "outputs": {
            "unified_wide_rows": len(unified_wide_rows),
            "column_mapping_entries": len(column_mapping),
            "value_set_mapping_entries": len(value_set_mapping),
            "unit_mapping_entries": len(unit_mapping),
            "modality_manifest_entries": len(modality_manifest),
        },
        "step6_integration": {
            "accepted_mapping_entries": sum(len(info["step6_mappings"]) for info in datasets.values()),
            "applied_rows": step6_applied_rows,
            "applied_unique_value_mappings": len(step6_applied_unique),
        },
        "coverage": {
            "bhs_columns_mapped": len([c for c in column_mapping if c["dataset"] == "BHS"]),
            "ehvol_columns_mapped": len([c for c in column_mapping if c["dataset"] == "EHVol"]),
        },
        "modality_distribution": {},
    }

    # Modality distribution
    modality_counts = defaultdict(lambda: {"BHS": 0, "EHVol": 0})
    for entry in modality_manifest:
        modality_counts[entry["modality"]][entry["dataset"]] += 1
    audit["modality_distribution"] = dict(modality_counts)

    audit_path = OUTPUT_PREFIX / "unification_audit.json"
    with open(audit_path, "w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2)
    print(f"  Audit report: {audit_path}")

    print("\n" + "=" * 70)
    print("Unification complete!")
    print("=" * 70)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    unify_datasets()
