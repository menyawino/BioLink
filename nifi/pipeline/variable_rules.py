#!/usr/bin/env python3
"""
Variable-level transformation rules for BioLink harmonization.

Each rule defines:
  - master_col: the harmonized column name
  - data_type: expected output type (numeric, boolean, categorical, date, string)
  - unit: SI/standard unit for the harmonized value
  - allowable_range: (min, max) for numeric; list for categorical
  - transform: normalization function name
  - loinc: LOINC code if applicable
  - snomed: SNOMED CT concept if applicable
  - phenotype_definition: clinical definition for derived phenotypes
  - timing_window: acceptable measurement timing relative to enrollment
  - tier: harmonization tier (schema_aligned | semantically_harmonized | analysis_ready)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class VariableRule:
    master_col: str
    data_type: str  # numeric, boolean, categorical, date, string
    unit: Optional[str] = None
    allowable_range: Optional[Tuple[float, float]] = None
    allowable_values: Optional[List[str]] = None
    transform: Optional[str] = None
    loinc: Optional[str] = None
    snomed: Optional[str] = None
    phenotype_definition: Optional[str] = None
    timing_window: Optional[str] = None
    tier: str = "schema_aligned"
    source_a_transform: Optional[str] = None  # BHS-specific transform
    source_b_transform: Optional[str] = None  # EHVol-specific transform


# ---------------------------------------------------------------------------
# Value normalization maps (used by transforms)
# ---------------------------------------------------------------------------

GENDER_MAP = {
    "male": "Male", "m": "Male", "1": "Male", "boy": "Male", "man": "Male",
    "female": "Female", "f": "Female", "2": "Female", "girl": "Female", "woman": "Female",
}

BOOLEAN_TRUE = {"yes", "y", "true", "t", "1", "checked", "check"}
BOOLEAN_FALSE = {"no", "n", "false", "f", "0", "unchecked", "uncheck"}

SMOKING_STATUS_MAP = {
    "smoker": "current", "current smoker": "current", "active smoker": "current",
    "cigarettes": "current", "shisha": "current", "both": "current",
    "non-smoker": "never", "non smoker": "never", "never": "never",
    "never smoked": "never", "no": "never",
    "ex-smoker": "former", "former smoker": "former", "former": "former",
    "quit": "former", "stopped": "former", "ex smoker": "former",
}

MARITAL_STATUS_MAP = {
    "single": "Single", "married": "Married", "divorced": "Divorced",
    "widowed": "Widowed", "separated": "Separated",
}

SEVERITY_MAP = {
    "none": "none", "no": "none", "absent": "none",
    "trivial": "trivial", "trace": "trivial", "normal/trivial": "trivial",
    "mild": "mild", "mild-moderate": "mild",
    "moderate": "moderate",
    "moderate-severe": "severe", "severe": "severe",
}

RHYTHM_MAP = {
    "normal": "sinus_rhythm", "normal sinus rhythm": "sinus_rhythm",
    "nsr": "sinus_rhythm", "sinus": "sinus_rhythm", "regular": "sinus_rhythm",
    "sinus rhythm": "sinus_rhythm",
    "af": "atrial_fibrillation", "atrial fibrillation": "atrial_fibrillation",
    "a fib": "atrial_fibrillation", "afib": "atrial_fibrillation",
    "atrial flutter": "atrial_flutter", "a flutter": "atrial_flutter",
    "irregular": "irregular",
}


# ---------------------------------------------------------------------------
# VARIABLE RULES REGISTRY
# ---------------------------------------------------------------------------

VARIABLE_RULES: Dict[str, VariableRule] = {}


def _r(
    master_col: str,
    data_type: str,
    unit: str | None = None,
    rng: tuple | None = None,
    vals: list | None = None,
    transform: str | None = None,
    loinc: str | None = None,
    snomed: str | None = None,
    phenotype: str | None = None,
    timing: str | None = None,
    tier: str = "schema_aligned",
    sa_transform: str | None = None,
    sb_transform: str | None = None,
) -> None:
    """Register a variable rule."""
    VARIABLE_RULES[master_col] = VariableRule(
        master_col=master_col,
        data_type=data_type,
        unit=unit,
        allowable_range=rng,
        allowable_values=vals,
        transform=transform,
        loinc=loinc,
        snomed=snomed,
        phenotype_definition=phenotype,
        timing_window=timing,
        tier=tier,
        source_a_transform=sa_transform,
        source_b_transform=sb_transform,
    )


# =====================================================================
# DEMOGRAPHICS
# =====================================================================
_r("age", "numeric", "years", (0, 120), transform="parse_numeric",
   loinc="30525-0", timing="baseline",
   tier="semantically_harmonized")

_r("age_at_enrollment", "numeric", "years", (0, 120), transform="parse_numeric",
   loinc="30525-0", timing="baseline",
   tier="semantically_harmonized")

_r("current_age", "numeric", "years", (0, 120), transform="parse_numeric",
   loinc="30525-0", timing="baseline",
   tier="schema_aligned")

_r("gender", "categorical", vals=["Male", "Female"],
   transform="normalize_gender", snomed="263495000",
   timing="baseline", tier="semantically_harmonized")

_r("gender_2", "categorical", vals=["Male", "Female"],
   transform="normalize_gender", snomed="263495000",
   timing="baseline", tier="semantically_harmonized")

_r("marital_status", "categorical",
   vals=["Single", "Married", "Divorced", "Widowed", "Separated"],
   transform="normalize_marital_status", timing="baseline",
   tier="semantically_harmonized")

_r("marital_status_2", "categorical",
   vals=["Single", "Married", "Divorced", "Widowed", "Separated"],
   transform="normalize_marital_status", timing="baseline",
   tier="semantically_harmonized")

# =====================================================================
# VITALS / ANTHROPOMETRIC
# =====================================================================
_r("height_cm", "numeric", "cm", (50, 250), transform="parse_numeric",
   loinc="8302-2", snomed="50373000", timing="baseline",
   tier="semantically_harmonized")

_r("height_cm_2", "numeric", "cm", (50, 250), transform="parse_numeric",
   loinc="8302-2", timing="baseline", tier="schema_aligned")

_r("height_in_cm", "numeric", "cm", (50, 250), transform="parse_numeric",
   loinc="8302-2", timing="baseline", tier="schema_aligned")

_r("weight_in_kg", "numeric", "kg", (2, 300), transform="parse_numeric",
   loinc="29463-7", snomed="27113001", timing="baseline",
   tier="semantically_harmonized")

_r("bmi", "numeric", "kg/m2", (10, 70), transform="parse_numeric",
   loinc="39156-5", snomed="60621009", timing="baseline",
   tier="semantically_harmonized",
   phenotype="Overweight: BMI 25-29.9; Obese: BMI >=30")

_r("bmi_2", "numeric", "kg/m2", (10, 70), transform="parse_numeric",
   loinc="39156-5", timing="baseline", tier="schema_aligned")

_r("bsa", "numeric", "m2", (0.5, 3.0), transform="parse_numeric",
   loinc="8277-6", snomed="301898006", timing="baseline",
   tier="semantically_harmonized")

_r("heart_rate", "numeric", "bpm", (20, 300), transform="parse_numeric",
   loinc="8867-4", snomed="364075005", timing="baseline",
   tier="semantically_harmonized")

_r("heart_rate_2", "numeric", "bpm", (20, 300), transform="parse_numeric",
   loinc="8867-4", timing="baseline", tier="schema_aligned")

_r("ventricular_rate", "numeric", "bpm", (20, 300), transform="parse_numeric",
   loinc="8867-4", timing="baseline", tier="schema_aligned")

# Blood pressure
_r("systolic_blood_pressure_right_brachial_measurement_1", "numeric", "mmHg",
   (50, 300), transform="parse_numeric",
   loinc="8480-6", snomed="271649006", timing="baseline",
   tier="semantically_harmonized")

_r("systolic_blood_pressure_right_brachial_measurement_2", "numeric", "mmHg",
   (50, 300), transform="parse_numeric", loinc="8480-6", timing="baseline",
   tier="schema_aligned")

_r("systolic_blood_pressure_right_brachial_measurement_3", "numeric", "mmHg",
   (50, 300), transform="parse_numeric", loinc="8480-6", timing="baseline",
   tier="schema_aligned")

_r("diastolic_blood_pressure_right_brachial_measurement_1", "numeric", "mmHg",
   (20, 200), transform="parse_numeric",
   loinc="8462-4", snomed="271650006", timing="baseline",
   tier="semantically_harmonized")

_r("diastolic_blood_pressure_right_brachial_measurement_2", "numeric", "mmHg",
   (20, 200), transform="parse_numeric", loinc="8462-4", timing="baseline",
   tier="schema_aligned")

_r("diastolic_blood_pressure_right_brachial_measurement_3", "numeric", "mmHg",
   (20, 200), transform="parse_numeric", loinc="8462-4", timing="baseline",
   tier="schema_aligned")

_r("bp", "string", "mmHg", transform="extract_bp",
   loinc="55284-4", snomed="75367002", timing="baseline",
   tier="semantically_harmonized")

_r("waist_circumference_in_cm", "numeric", "cm", (40, 200),
   transform="parse_numeric", loinc="8280-0", timing="baseline",
   tier="semantically_harmonized")

_r("hip_circumference_in_cm", "numeric", "cm", (40, 200),
   transform="parse_numeric", loinc="62409-8", timing="baseline",
   tier="semantically_harmonized")

_r("waist_hip_ratio", "numeric", None, (0.5, 1.5),
   transform="parse_numeric", timing="baseline",
   tier="semantically_harmonized")

_r("span_cm", "numeric", "cm", (100, 250),
   transform="parse_numeric", timing="baseline", tier="schema_aligned")

# =====================================================================
# LABORATORY
# =====================================================================
_r("hemoglobin", "numeric", "g/dL", (3, 25), transform="parse_numeric",
   loinc="718-7", snomed="59827004", timing="baseline",
   tier="analysis_ready")

_r("hematocrit", "numeric", "%", (10, 70), transform="parse_numeric",
   loinc="4544-3", timing="baseline", tier="analysis_ready")

_r("platelet_count", "numeric", "10^3/uL", (10, 1500), transform="parse_numeric",
   loinc="777-3", timing="baseline", tier="analysis_ready")

_r("tlc", "numeric", "10^3/uL", (0.5, 50), transform="parse_numeric",
   loinc="6690-2", timing="baseline", tier="analysis_ready")

_r("rbcs", "numeric", "10^6/uL", (1, 10), transform="parse_numeric",
   loinc="789-8", timing="baseline", tier="analysis_ready")

_r("mcv", "numeric", "fL", (50, 130), transform="parse_numeric",
   loinc="787-2", timing="baseline", tier="analysis_ready")

_r("mch", "numeric", "pg", (15, 45), transform="parse_numeric",
   loinc="785-6", timing="baseline", tier="analysis_ready")

_r("mchc", "numeric", "g/dL", (25, 40), transform="parse_numeric",
   loinc="786-4", timing="baseline", tier="analysis_ready")

_r("rdw", "numeric", "%", (10, 25), transform="parse_numeric",
   loinc="788-0", timing="baseline", tier="analysis_ready")

_r("hba1c", "numeric", "%", (3, 20), transform="parse_numeric",
   loinc="4548-4", snomed="43396009", timing="baseline",
   tier="analysis_ready",
   phenotype="Normal: <5.7%; Pre-diabetes: 5.7-6.4%; Diabetes: >=6.5% (ADA criteria)")

_r("hba1c_1", "numeric", "%", (3, 20), transform="parse_numeric",
   loinc="4548-4", timing="baseline", tier="schema_aligned")

_r("hba1c_2", "numeric", "%", (3, 20), transform="parse_numeric",
   loinc="4548-4", timing="baseline", tier="schema_aligned")

_r("fasting_blood_glucose", "numeric", "mg/dL", (20, 600),
   transform="parse_numeric", loinc="1558-6", timing="baseline_fasting",
   tier="analysis_ready",
   phenotype="Normal: <100 mg/dL; Impaired: 100-125; Diabetes: >=126 (ADA)")

_r("fasting_blood_sugar", "numeric", "mg/dL", (20, 600),
   transform="parse_numeric", loinc="1558-6", timing="baseline_fasting",
   tier="schema_aligned")

_r("random_blood_glucose", "numeric", "mg/dL", (20, 600),
   transform="parse_numeric", loinc="2345-7", timing="baseline",
   tier="analysis_ready")

_r("total_cholesterol", "numeric", "mg/dL", (50, 500),
   transform="parse_numeric", loinc="2093-3", snomed="77068002",
   timing="baseline_fasting", tier="analysis_ready")

_r("ldl", "numeric", "mg/dL", (10, 400), transform="parse_numeric",
   loinc="2089-1", timing="baseline_fasting", tier="analysis_ready",
   phenotype="Optimal: <100; Near-optimal: 100-129; Borderline: 130-159; High: 160-189; Very-high: >=190 (ATP-III)")

_r("hdl", "numeric", "mg/dL", (5, 150), transform="parse_numeric",
   loinc="2085-9", timing="baseline_fasting", tier="analysis_ready",
   phenotype="Low (risk): <40 men/<50 women; Protective: >=60")

_r("serum_triglycerides", "numeric", "mg/dL", (10, 2000),
   transform="parse_numeric", loinc="2571-8", timing="baseline_fasting",
   tier="analysis_ready")

_r("vldl", "numeric", "mg/dL", (1, 200), transform="parse_numeric",
   loinc="13458-5", timing="baseline_fasting", tier="analysis_ready")

_r("creatinine", "numeric", "mg/dL", (0.1, 20), transform="parse_numeric",
   loinc="2160-0", snomed="70901006", timing="baseline",
   tier="analysis_ready")

_r("urea", "numeric", "mg/dL", (1, 200), transform="parse_numeric",
   loinc="3091-6", timing="baseline", tier="analysis_ready")

_r("egfr_male", "numeric", "mL/min/1.73m2", (1, 200),
   transform="parse_numeric", loinc="33914-3", timing="baseline",
   tier="analysis_ready",
   phenotype="G1: >=90 normal; G2: 60-89 mild; G3a: 45-59; G3b: 30-44; G4: 15-29; G5: <15 (KDIGO)")

_r("egfr_female", "numeric", "mL/min/1.73m2", (1, 200),
   transform="parse_numeric", loinc="33914-3", timing="baseline",
   tier="analysis_ready")

_r("alt", "numeric", "U/L", (1, 2000), transform="parse_numeric",
   loinc="1742-6", snomed="34608000", timing="baseline",
   tier="analysis_ready")

_r("ast", "numeric", "U/L", (1, 2000), transform="parse_numeric",
   loinc="1920-8", snomed="45803000", timing="baseline",
   tier="analysis_ready")

_r("albumin", "numeric", "g/dL", (1, 7), transform="parse_numeric",
   loinc="1751-7", timing="baseline", tier="analysis_ready")

_r("total_bilirubin", "numeric", "mg/dL", (0.01, 30),
   transform="parse_numeric", loinc="1975-2", timing="baseline",
   tier="analysis_ready")

_r("direct_bilirubin", "numeric", "mg/dL", (0.01, 15),
   transform="parse_numeric", loinc="1968-7", timing="baseline",
   tier="analysis_ready")

_r("inr", "numeric", None, (0.5, 10), transform="parse_numeric",
   loinc="6301-6", timing="baseline", tier="analysis_ready")

_r("na", "numeric", "mmol/L", (100, 170), transform="parse_numeric",
   loinc="2951-2", timing="baseline", tier="analysis_ready")

_r("k", "numeric", "mmol/L", (2, 8), transform="parse_numeric",
   loinc="2823-3", timing="baseline", tier="analysis_ready")

_r("ca", "numeric", "mg/dL", (5, 15), transform="parse_numeric",
   loinc="17861-6", timing="baseline", tier="analysis_ready")

_r("mg", "numeric", "mg/dL", (0.5, 5), transform="parse_numeric",
   loinc="2601-3", timing="baseline", tier="analysis_ready")

_r("troponin", "numeric", "ng/mL", (0, 100), transform="parse_numeric",
   loinc="6598-7", snomed="105011006", timing="baseline",
   tier="analysis_ready",
   phenotype="Normal: <0.04 ng/mL; Elevated: >=0.04 (assay-dependent)")

_r("bnp", "numeric", "pg/mL", (0, 50000), transform="parse_numeric",
   loinc="42637-9", snomed="55283-6", timing="baseline",
   tier="analysis_ready",
   phenotype="Normal: <100 pg/mL; Grey zone: 100-400; HF likely: >400")

_r("crp", "numeric", "mg/L", (0, 200), transform="parse_numeric",
   loinc="1988-5", timing="baseline", tier="analysis_ready")

_r("crp_1", "numeric", "mg/L", (0, 200), transform="parse_numeric",
   loinc="1988-5", timing="baseline", tier="schema_aligned")

_r("tsh", "numeric", "uIU/mL", (0.01, 100), transform="parse_numeric",
   loinc="3016-3", timing="baseline", tier="analysis_ready")

_r("t3", "numeric", "ng/dL", (0.1, 10), transform="parse_numeric",
   loinc="3053-6", timing="baseline", tier="analysis_ready")

_r("t4", "numeric", "ng/dL", (0.1, 15), transform="parse_numeric",
   loinc="3026-2", timing="baseline", tier="analysis_ready")

# =====================================================================
# ECG
# =====================================================================
_r("corrected_qt_interval", "numeric", "ms", (200, 700),
   transform="parse_numeric", loinc="8633-0", snomed="251226000",
   timing="baseline", tier="analysis_ready",
   phenotype="Prolonged QTc: >450ms men / >460ms women")

_r("qt_interval", "numeric", "ms", (200, 700), transform="parse_numeric",
   loinc="8634-8", timing="baseline", tier="analysis_ready")

_r("pr_interval", "numeric", "ms", (80, 400), transform="parse_numeric",
   loinc="8622-3", snomed="251213003", timing="baseline",
   tier="analysis_ready",
   phenotype="1st-degree AV block: PR >200ms")

_r("pr_interval_2", "numeric", "ms", (80, 400), transform="parse_numeric",
   loinc="8622-3", timing="baseline", tier="schema_aligned")

_r("qrs_duration", "numeric", "ms", (40, 250), transform="parse_numeric",
   loinc="8625-6", snomed="251208003", timing="baseline",
   tier="analysis_ready",
   phenotype="Wide QRS: >=120ms; Bundle branch block criterion")

_r("qrs_duration_2", "numeric", "ms", (40, 250), transform="parse_numeric",
   loinc="8625-6", timing="baseline", tier="schema_aligned")

_r("rate", "numeric", "bpm", (20, 300), transform="parse_numeric",
   loinc="8867-4", timing="baseline", tier="schema_aligned")

_r("rhythm", "categorical",
   vals=["sinus_rhythm", "atrial_fibrillation", "atrial_flutter", "irregular"],
   transform="normalize_rhythm", loinc="8884-9", timing="baseline",
   tier="semantically_harmonized")

_r("rhythm_in_ecg", "categorical",
   vals=["sinus_rhythm", "atrial_fibrillation", "atrial_flutter", "irregular"],
   transform="normalize_rhythm", loinc="8884-9", timing="baseline",
   tier="semantically_harmonized")

_r("ecg_conclusion", "string", transform="passthrough",
   timing="baseline", tier="schema_aligned")

# =====================================================================
# ECHOCARDIOGRAPHY
# =====================================================================
_r("ef", "numeric", "%", (5, 85), transform="parse_numeric",
   loinc="10230-1", snomed="250908004", timing="baseline",
   tier="analysis_ready",
   phenotype="HFrEF: EF<40%; HFmrEF: 40-49%; HFpEF: EF>=50% (ESC 2021)")

_r("ef_2", "numeric", "%", (5, 85), transform="parse_numeric",
   loinc="10230-1", timing="baseline", tier="schema_aligned")

_r("fs", "numeric", "%", (10, 60), transform="parse_numeric",
   loinc="10230-1", timing="baseline", tier="analysis_ready")

_r("lvedd", "numeric", "mm", (20, 90), transform="parse_numeric",
   loinc="18026-6", timing="baseline", tier="analysis_ready")

_r("lvedd_2", "numeric", "mm", (20, 90), transform="parse_numeric",
   loinc="18026-6", timing="baseline", tier="schema_aligned")

_r("lvesd", "numeric", "mm", (10, 70), transform="parse_numeric",
   loinc="18150-4", timing="baseline", tier="analysis_ready")

_r("lvesd_2", "numeric", "mm", (10, 70), transform="parse_numeric",
   loinc="18150-4", timing="baseline", tier="schema_aligned")

_r("ivsd", "numeric", "mm", (3, 25), transform="parse_numeric",
   loinc="18087-8", timing="baseline", tier="analysis_ready")

_r("ivss", "numeric", "mm", (3, 25), transform="parse_numeric",
   timing="baseline", tier="schema_aligned")

_r("lvpwd", "numeric", "mm", (3, 25), transform="parse_numeric",
   loinc="18090-2", timing="baseline", tier="analysis_ready")

_r("lvpws", "numeric", "mm", (3, 25), transform="parse_numeric",
   timing="baseline", tier="schema_aligned")

_r("left_ventricular_mass", "numeric", "g", (30, 500),
   transform="parse_numeric", loinc="75994-8", timing="baseline",
   tier="analysis_ready",
   phenotype="LVH: LVM >115g/m2 men / >95g/m2 women (ASE)")

_r("lvm", "numeric", "g", (30, 500), transform="parse_numeric",
   loinc="75994-8", timing="baseline", tier="schema_aligned")

_r("lvh", "boolean", transform="normalize_boolean",
   snomed="55827005", timing="baseline", tier="semantically_harmonized",
   phenotype="Left ventricular hypertrophy present/absent")

_r("lvh_1", "string", timing="baseline", tier="schema_aligned")

_r("left_atrium", "numeric", "cm", (1, 8), transform="parse_numeric",
   timing="baseline", tier="analysis_ready")

_r("left_atrial_size", "numeric", "mm", (10, 80), transform="parse_numeric",
   timing="baseline", tier="analysis_ready")

_r("la_diameter_plax", "numeric", "mm", (10, 80), transform="parse_numeric",
   loinc="18035-7", timing="baseline", tier="analysis_ready")

_r("aortic_root", "numeric", "cm", (1, 6), transform="parse_numeric",
   timing="baseline", tier="analysis_ready")

_r("right_ventricle", "numeric", "mm", (10, 60), transform="parse_numeric",
   timing="baseline", tier="analysis_ready")

_r("tapse", "numeric", "mm", (5, 40), transform="parse_numeric",
   loinc="80059-1", timing="baseline", tier="analysis_ready",
   phenotype="RV dysfunction: TAPSE <17mm (ASE)")

_r("pasp", "numeric", "mmHg", (10, 120), transform="parse_numeric",
   loinc="33453-2", timing="baseline", tier="analysis_ready",
   phenotype="Pulmonary hypertension: PASP >35mmHg")

_r("left_ventricular_end_diastolic_volume", "numeric", "mL", (20, 500),
   transform="parse_numeric", timing="baseline", tier="analysis_ready")

_r("left_ventricular_end_systolic_volume", "numeric", "mL", (5, 300),
   transform="parse_numeric", timing="baseline", tier="analysis_ready")

# Valve severity
for valve in ("mr", "ar", "tr", "pr", "ms", "as", "ts", "ps"):
    _r(valve, "categorical",
       vals=["none", "trivial", "mild", "moderate", "severe"],
       transform="normalize_severity", timing="baseline",
       tier="semantically_harmonized")

_r("mitral_regurge", "categorical",
   vals=["none", "trivial", "mild", "moderate", "severe"],
   transform="normalize_severity", timing="baseline",
   tier="semantically_harmonized")

_r("aortic_regurge", "categorical",
   vals=["none", "trivial", "mild", "moderate", "severe"],
   transform="normalize_severity", timing="baseline",
   tier="semantically_harmonized")

_r("tricuspid_regurge", "categorical",
   vals=["none", "trivial", "mild", "moderate", "severe"],
   transform="normalize_severity", timing="baseline",
   tier="semantically_harmonized")

_r("aortic_stenosis", "categorical",
   vals=["none", "trivial", "mild", "moderate", "severe"],
   transform="normalize_severity", timing="baseline",
   tier="semantically_harmonized")

_r("aortic_stenosis_2", "categorical",
   vals=["none", "trivial", "mild", "moderate", "severe"],
   transform="normalize_severity", timing="baseline",
   tier="schema_aligned")

_r("pulmonary_regurge", "categorical",
   vals=["none", "trivial", "mild", "moderate", "severe"],
   transform="normalize_severity", timing="baseline",
   tier="semantically_harmonized")

_r("pulmonary_stenosis", "categorical",
   vals=["none", "trivial", "mild", "moderate", "severe"],
   transform="normalize_severity", timing="baseline",
   tier="semantically_harmonized")

_r("mitral_stenosis", "categorical",
   vals=["none", "trivial", "mild", "moderate", "severe"],
   transform="normalize_severity", timing="baseline",
   tier="semantically_harmonized")

_r("tricuspid_stenosis", "categorical",
   vals=["none", "trivial", "mild", "moderate", "severe"],
   transform="normalize_severity", timing="baseline",
   tier="semantically_harmonized")

_r("tricuspid_stenosis_2", "categorical",
   vals=["none", "trivial", "mild", "moderate", "severe"],
   transform="normalize_severity", timing="baseline",
   tier="schema_aligned")

# Wall motion segments (1-7 AHA scoring)
for seg in ("apical_anterior", "apical_inferior", "apical_lateral",
            "apical_septal", "basal_anterior", "basal_anterolateral",
            "basal_anteroseptal", "basal_inferior", "basal_inferolateral",
            "basal_inferoseptal", "midventricular_anterior",
            "midventricular_anterolateral", "midventricular_anteroseptal",
            "midventricular_inferior", "midventricular_inferolateral",
            "midventricular_inferoseptal"):
    _r(seg, "numeric", None, (1, 7), transform="parse_numeric",
       timing="baseline", tier="analysis_ready")

# =====================================================================
# ABI
# =====================================================================
for side in ("left", "right"):
    for loc in ("anterior_tibial", "posterior_tibial"):
        _r(f"{side}_{loc}_abi", "numeric", None, (0, 2),
           transform="parse_numeric", loinc="37399-3",
           timing="baseline", tier="analysis_ready",
           phenotype="PAD: ABI <0.9; Normal: 0.9-1.3; Non-compressible: >1.3")
        _r(f"{side}_{loc}_pressure", "numeric", "mmHg", (0, 300),
           transform="parse_numeric", timing="baseline", tier="analysis_ready")

_r("brachial_pressure_highest_side", "numeric", "mmHg", (40, 300),
   transform="parse_numeric", timing="baseline", tier="schema_aligned")

# =====================================================================
# CAROTID
# =====================================================================
_r("imt_left_in_mm", "numeric", "mm", (0.1, 3), transform="parse_numeric",
   loinc="24889-5", timing="baseline", tier="analysis_ready",
   phenotype="Abnormal IMT: >=0.9mm; Plaque: IMT >=1.5mm")

_r("imt_right_in_mm", "numeric", "mm", (0.1, 3), transform="parse_numeric",
   loinc="24890-3", timing="baseline", tier="analysis_ready")

# =====================================================================
# RISK SCORES
# =====================================================================
_r("current_10_year_ascvd_risk", "numeric", "%", (0, 100),
   transform="parse_numeric", timing="baseline", tier="analysis_ready",
   phenotype="Low: <5%; Borderline: 5-7.4%; Intermediate: 7.5-19.9%; High: >=20% (ACC/AHA)")

_r("lifetime_ascvd_risk", "numeric", "%", (0, 100),
   transform="parse_numeric", timing="baseline", tier="analysis_ready")

_r("optimal_ascvd_risk", "numeric", "%", (0, 100),
   transform="parse_numeric", timing="baseline", tier="analysis_ready")

# =====================================================================
# SMOKING / LIFESTYLE
# =====================================================================
_r("what_is_your_current_smoking_status", "categorical",
   vals=["current", "former", "never"],
   transform="normalize_smoking_status", timing="baseline",
   tier="semantically_harmonized")

_r("do_you_smoke_shisha_or_cigarettes_or_both", "categorical",
   vals=["cigarettes", "shisha", "both", "none"],
   transform="normalize_smoking_type", timing="baseline",
   tier="semantically_harmonized")

_r("smoking_years", "numeric", "years", (0, 80), transform="parse_numeric",
   timing="baseline", tier="semantically_harmonized")

_r("smoking_index_current", "numeric", "pack-years", (0, 200),
   transform="parse_numeric", timing="baseline", tier="analysis_ready")

_r("smoking_index_former", "numeric", "pack-years", (0, 200),
   transform="parse_numeric", timing="baseline", tier="analysis_ready")

_r("average_no_of_cigarettes_per_day", "numeric", "cigarettes/day", (0, 100),
   transform="parse_numeric", timing="baseline",
   tier="semantically_harmonized")

# =====================================================================
# MEDICAL HISTORY (boolean conditions)
# =====================================================================
_boolean_conditions = {
    "do_you_have_diabetes": ("diabetes_mellitus", "Diabetes"),
    "do_you_have_hypertension": ("hypertension", "Hypertension"),
    "do_you_have_hyperlipidemia": ("hyperlipidemia", "Hyperlipidemia"),
    "have_you_been_hospitalized_due_to_heart_failure": ("heart_failure_hx", "Heart Failure History"),
    "have_you_ever_been_diagnosed_with_mi": ("mi_hx", "Myocardial Infarction History"),
    "have_you_had_a_prior_stroke_or_tia": ("stroke_tia_hx", "Stroke/TIA History"),
    "have_you_been_diagnosed_with_rheumatic_fever": ("rheumatic_fever_hx", "Rheumatic Fever History"),
    "have_you_been_diagnosed_with_congenital_heart_disease": ("chd_hx", "CHD History"),
    "have_you_been_diagnosed_with_renal_disease": ("renal_disease_hx", "Renal Disease"),
    "have_you_been_diagnosed_with_respiratory_illnesses": ("resp_illness_hx", "Respiratory Illness"),
    "have_you_been_diagnosed_with_pvd": ("pvd_hx", "PVD History"),
    "diabetes_mellitus": ("diabetes_mellitus", "Diabetes"),
    "high_blood_pressure": ("hypertension", "High Blood Pressure"),
    "dyslipidemia": ("dyslipidemia", "Dyslipidemia"),
    "heart_attack_or_angina": ("mi_angina", "MI or Angina"),
    "angina": ("angina", "Angina"),
    "pulmonary_hypertension": ("pulm_htn", "Pulmonary Hypertension"),
    "congenital_heart_defect": ("congenital_hd", "Congenital Heart Defect"),
    "degenerative_valve_disease": ("degen_valve", "Degenerative Valve Disease"),
    "rheumatic_valvular_heart_disease": ("rheumatic_vhd", "Rheumatic VHD"),
    "anaemia": ("anaemia", "Anaemia"),
    "kidney_problems": ("kidney_problems", "Kidney Problems"),
    "liver_problems": ("liver_problems", "Liver Problems"),
    "lung_problems": ("lung_problems", "Lung Problems"),
    "neurological_problems": ("neuro_problems", "Neurological Problems"),
    "autoimmune_problems": ("autoimmune", "Autoimmune Problems"),
    "malignancy": ("malignancy", "Malignancy"),
    "known_cvs_disease": ("cvs_disease", "Known CVS Disease"),
    "known_collagen_disease": ("collagen_disease", "Collagen Disease"),
    "pregnant_female": ("pregnant", "Pregnancy"),
}

for col, (_, desc) in _boolean_conditions.items():
    _r(col, "boolean", transform="normalize_boolean",
       timing="baseline", tier="semantically_harmonized",
       phenotype=f"Self-reported or clinician-confirmed {desc}")

# =====================================================================
# DATES
# =====================================================================
_date_cols = [
    "date", "date_abi", "date_clinical_exam", "date_consent",
    "date_demographic_data", "date_labs", "date_medications",
    "date_of_cardotid_duplex", "date_of_coronary_intervention",
    "date_of_enrolment", "date_plan", "date_risk_factors",
    "enrollment_date", "date_echocardiography", "echo_date",
    "date_family_history", "ecg_date", "date_of_cardiac_ct",
    "date_of_cardiac_mri", "mri_date",
]

for dc in _date_cols:
    _r(dc, "date", transform="parse_date", timing="baseline",
       tier="semantically_harmonized")

# =====================================================================
# ADMIN / IDs
# =====================================================================
_r("record_id", "string", tier="schema_aligned", timing="baseline")
_r("record_id_2", "string", tier="schema_aligned", timing="baseline")
_r("household_identifier", "string", tier="schema_aligned", timing="baseline")
_r("dna_id", "string", tier="schema_aligned", timing="baseline")

# For all "complete" status fields
for i in ["", "_1", "_2", "_3", "_4", "_5", "_6", "_7", "_8", "_9",
          "_10", "_11", "_12", "_13", "_14",
          "_1_2", "_2_2", "_3_2", "_4_2", "_5_2", "_6_2", "_7_2", "_8_2", "_9_2"]:
    _r(f"complete{i}", "categorical",
       vals=["Complete", "Incomplete", "Unverified", ""],
       timing="baseline", tier="schema_aligned")


# =====================================================================
# CATEGORY-LEVEL CHOICE BOOLEANS (ICD-coded disease checklist items)
# =====================================================================
# These are "Checked"/"Unchecked" REDCap choice columns that are
# structurally passthrough and require only boolean normalization.
# They are bulk-registered as schema_aligned with boolean transform.


def get_default_rule(master_col: str) -> VariableRule:
    """Return a default schema_aligned passthrough rule for unknown columns."""
    return VariableRule(
        master_col=master_col,
        data_type="string",
        tier="schema_aligned",
    )


def get_rule(master_col: str) -> VariableRule:
    """Retrieve the rule for a column, or return a default."""
    return VARIABLE_RULES.get(master_col, get_default_rule(master_col))
