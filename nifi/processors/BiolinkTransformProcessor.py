"""
BioLink Unified Transform Processor for Apache NiFi 2.8.0

This NiFi Python processor ports the cleaning and transformation logic
from biolink_etl/schema_mappings.py and biolink_etl/transformer.py.

It reads CSV records (as JSON FlowFile content), applies field mappings,
type normalization, city homogenization, BP averaging, and quality scoring,
then outputs records conforming to the unified_participants schema.
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
    formats = [
        "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y",
        "%d-%m-%Y", "%m-%d-%Y", "%d/%m/%y", "%Y/%m/%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


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
    eth = s.lower()
    if eth in ("fedutchi", "fedicci", "fedici"):
        return "Nubian_Fedutchi"
    if eth in ("ballana", "ballena"):
        return "Nubian_Ballana"
    if eth in ("dahmit", "dahmeet"):
        return "Nubian_Dahmit"
    if "nubian" in eth:
        return "Nubian_Other"
    if eth in ("egyptian", "egypt", "egy"):
        return "Egyptian"
    return s.title()


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
# NIFI PROCESSOR CLASS
# =============================================================================

class BiolinkTransformProcessor(FlowFileTransform):
    """
    Apache NiFi 2.x Python processor that transforms raw CSV records
    from BHS or EHVol datasets into the BioLink unified schema.

    Input:  JSON object (one CSV row as key-value pairs)
    Output: JSON object conforming to unified_participants schema
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

        # Build collision-safe participant_id
        unified["participant_id"] = self._build_participant_id(
            unified, record, dataset, row_idx
        )

        # Preserve a compact version of the source record (strip internal
        # bookkeeping keys and limit total size to prevent OOM on PutSQL).
        compact = {k: v for k, v in record.items()
                   if not k.startswith("_") and v is not None and str(v).strip() != ""}
        # Truncate to keep JSONB payload manageable (max ~4 KB serialized)
        raw_json = json.dumps(compact, default=str)
        if len(raw_json) > 4096:
            # Keep only mapped fields from source
            mapped_keys = set()
            for mapping in FIELD_MAPPINGS.values():
                src = mapping.get(dataset)
                if isinstance(src, list):
                    mapped_keys.update(src)
                elif src:
                    mapped_keys.add(src)
            compact = {k: v for k, v in compact.items() if k in mapped_keys}
        unified["source_raw_json"] = compact

        return unified, issues

    # -----------------------------------------------------------------
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
