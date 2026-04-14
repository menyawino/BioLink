"""
BioLink Master Schema Processor for Apache NiFi 2.8.0 — Step 1 of 2

Reads the full BHS and EHVol CSV files from the shared data directory,
runs the two-stage SapBERT column-matching pipeline,
and writes master_schema.csv to the shared outputs directory.

Pipeline position:
  GenerateFlowFile (run-once) → BiolinkMasterSchemaProcessor
                                    ↳ writes /opt/nifi/outputs/master_schema.csv
                                    ↳ emits schema CSV as FlowFile on success

Step 2 processors (BiolinkHarmoniseProcessor) read master_schema.csv from
the same outputs directory before applying it to individual dataset chunks.

Properties:
  BHS CSV Path        - /opt/nifi/db/BHS_Full.csv
  EHVol CSV Path      - /opt/nifi/db/EHVol_Full.csv
  Schema Output Path  - /opt/nifi/outputs/master_schema.csv
    Match Threshold     - cosine similarity floor (default 0.25)
        Top K               - SapBERT candidates per column (default 20)
    Lexicon Path        - optional clinical lexicon CSV
                                                (default /opt/nifi/biolink_scripts/clinical_lexicon.csv)
"""

import csv
import json
import os
import re
import subprocess
from datetime import datetime, timezone

from nifiapi.flowfiletransform import FlowFileTransform, FlowFileTransformResult
from nifiapi.properties import PropertyDescriptor, ExpressionLanguageScope

# ─────────────────────────────────────────────────────────────────────────────
# Shared string helpers  (mirror nifi/pipeline/two_stage_match.py)
# ─────────────────────────────────────────────────────────────────────────────

_APOS_RE = re.compile(r"['\u2018\u2019\u0060\u00b4]")
_NON_AZ09 = re.compile(r"[^a-z0-9]+")


def to_snake(name: str) -> str:
    s = _APOS_RE.sub("", str(name).lower())
    s = _NON_AZ09.sub("_", s).strip("_")
    return s or "col"


_CL_ABBREV = {
    "hr": "heart_rate", "bp": "blood_pressure", "sbp": "systolic_blood_pressure",
    "dbp": "diastolic_blood_pressure", "bmi": "body_mass_index",
    "egfr": "estimated_glomerular_filtration_rate", "hba1c": "glycated_haemoglobin",
    "dob": "date_of_birth", "dod": "date_of_death", "ht": "height",
    "wt": "weight", "chol": "cholesterol", "tg": "triglycerides",
    "hdl": "high_density_lipoprotein", "ldl": "low_density_lipoprotein",
    "ecg": "electrocardiogram", "ef": "ejection_fraction",
    "lvedd": "left_ventricular_end_diastolic_diameter",
    "lvef": "left_ventricular_ejection_fraction",
    "afib": "atrial_fibrillation", "mi": "myocardial_infarction",
    "lv": "left_ventricle", "rv": "right_ventricle",
    "dm": "diabetes_mellitus", "htn": "hypertension",
}


def expand_name(snake: str) -> str:
    tokens = snake.split("_")
    return " ".join(_CL_ABBREV.get(t, t) for t in tokens)


# ─────────────────────────────────────────────────────────────────────────────
# Clinical lexicon  (loaded once, falls back to built-in mini-lexicon)
# ─────────────────────────────────────────────────────────────────────────────

_CATEGORY_MAP: dict[str, str] = {}
_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "ecg":          ["ecg", "electrocardiogram", "qtc", "pr_interval", "qrs", "rhythm", "arrhythmia",
                     "atrial", "ventricular", "lbbb", "rbbb", "sinus"],
    "echo":         ["echo", "lvef", "lvedd", "lvesd", "ef", "ejection_fraction", "fractional_shortening",
                     "valve", "mitral", "tricuspid", "aortic", "pericardial"],
    "lab":          ["haemoglobin", "haematocrit", "wbc", "platelet", "creatinine", "urea", "bilirubin",
                     "alt", "ast", "albumin", "hba1c", "glucose", "cholesterol", "ldl", "hdl",
                     "triglyceride", "potassium", "sodium", "tsh", "bnp", "troponin", "ferritin"],
    "mri":          ["mri", "cmr", "cardiac_magnetic", "fibrosis", "gadolinium", "t1", "t2",
                     "mapping", "late_enhancement", "strain"],
    "vitals":       ["heart_rate", "blood_pressure", "systolic", "diastolic", "temperature",
                     "respiratory_rate", "oxygen_saturation", "spo2", "weight", "height", "bmi"],
    "genetics":     ["snp", "variant", "allele", "genotype", "mutation", "gene", "dna", "gwas",
                     "polygenic", "risk_score", "prs"],
    "contact":      ["phone", "email", "address", "postcode", "zip", "mobile", "tel", "contact"],
    "demographics": ["age", "sex", "gender", "ethnicity", "race", "dob", "date_of_birth", "marital",
                     "education", "employment", "smoking", "alcohol"],
}


def _load_lexicon(path: str | None) -> None:
    if not path or not os.path.isfile(path):
        return
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            acronym = (row.get("acronym") or "").strip().lower()
            expansion = (row.get("expansion") or "").strip().lower()
            category = (row.get("category") or "").strip().lower()
            if acronym:
                _CL_ABBREV[acronym] = expansion or acronym
            if expansion and category:
                _CATEGORY_MAP[expansion] = category


def _col_category(col: str) -> str:
    if col in _CATEGORY_MAP:
        return _CATEGORY_MAP[col]
    col_exp = expand_name(col)
    for cat, kws in _CATEGORY_KEYWORDS.items():
        for kw in kws:
            if kw in col or kw in col_exp:
                return cat
    return "clinical"


# ─────────────────────────────────────────────────────────────────────────────
# Dtype inference  (header + optional sample rows)
# ─────────────────────────────────────────────────────────────────────────────

_DATE_RE = re.compile(
    r"\b(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{4})\b"
)
_BOOL_VALS = {"yes", "no", "true", "false", "y", "n", "1", "0", "checked", "unchecked"}


def infer_dtype(values: list[str]) -> str:
    clean = [v.strip() for v in values if v.strip() not in ("", "na", "n/a", "nan", "null", "none", "-")]
    if not clean:
        return "unknown"
    if all(v in _BOOL_VALS for v in (v.lower() for v in clean)):
        return "binary"
    numeric, date = 0, 0
    for v in clean:
        try:
            float(v.replace(",", ""))
            numeric += 1
        except ValueError:
            if _DATE_RE.search(v):
                date += 1
    n = len(clean)
    if numeric / n >= 0.85:
        return "numeric"
    if date / n >= 0.70:
        return "date"
    uniq = len(set(v.lower() for v in clean))
    if uniq <= max(5, int(n * 0.05)):
        return "categorical"
    if uniq <= max(20, int(n * 0.20)):
        return "multi_cat"
    return "text"


# ─────────────────────────────────────────────────────────────────────────────
# PII detection
# ─────────────────────────────────────────────────────────────────────────────

_PII_KEYWORDS = frozenset([
    "_tel", "contact_number", "consent_scan", "mrn", "medical_record_number",
    "national_id", "nin", "nhs_number", "passport", "email", "phone",
    "mobile", "address", "postcode", "zip_code", "ip_address", "mac_address",
    "full_name", "surname", "first_name", "given_name", "family_name",
    "dob", "date_of_birth", "birth_date", "ssn", "social_security",
    "credit_card", "bank_account", "driver_license",
])


def is_pii_column(col: str) -> bool:
    col_l = col.lower()
    return any(kw in col_l for kw in _PII_KEYWORDS)


# ─────────────────────────────────────────────────────────────────────────────
# Coalesce strategy mapping
# ─────────────────────────────────────────────────────────────────────────────

_STRATEGY_MAP = {
    "ecg":          "first_non_null",
    "echo":         "first_non_null",
    "lab":          "mean_value",
    "mri":          "first_non_null",
    "vitals":       "mean_value",
    "genetics":     "first_non_null",
    "demographics": "mode_value",
    "contact":      "first_non_null",
    "clinical":     "first_non_null",
}


def get_default_strategy(category: str) -> str:
    return _STRATEGY_MAP.get(category, "first_non_null")


# ─────────────────────────────────────────────────────────────────────────────
# NiFi Processor
# ─────────────────────────────────────────────────────────────────────────────

class BiolinkMasterSchemaProcessor(FlowFileTransform):
    """
    NiFi Step 1 — Column-matching pipeline that generates master_schema.csv.
    Triggered once by a GenerateFlowFile processor; writes the schema file
    to the configured output path and echoes it as the FlowFile content.
    """

    class Java:
        implements = ["org.apache.nifi.python.processor.FlowFileTransform"]

    class ProcessorDetails:
        version = "1.0.0"
        description = (
            "Step 1 of the script-aligned ETL: executes nifi/pipeline/two_stage_match.py "
            "inside the NiFi container to generate outputs/master_schema.csv using "
            "the same matching logic documented for the registry pipeline."
        )
        tags = ["biolink", "schema", "matching", "etl", "harmonise", "step1"]

    REPOSITORY_ROOT = PropertyDescriptor(
        name="Repository Root",
        description="Mounted repository root used to execute the script-based ETL.",
        required=True,
        default_value="/opt/nifi/biolink_repo",
        expression_language_scope=ExpressionLanguageScope.FLOWFILE_ATTRIBUTES,
    )

    BHS_CSV_PATH = PropertyDescriptor(
        name="BHS CSV Path",
        description="Absolute path to the full BHS CSV file inside the container.",
        required=True,
        default_value="/opt/nifi/db/BHS_Full.csv",
        expression_language_scope=ExpressionLanguageScope.FLOWFILE_ATTRIBUTES,
    )
    EHVOL_CSV_PATH = PropertyDescriptor(
        name="EHVol CSV Path",
        description="Absolute path to the full EHVol CSV file inside the container.",
        required=True,
        default_value="/opt/nifi/db/EHVol_Full.csv",
        expression_language_scope=ExpressionLanguageScope.FLOWFILE_ATTRIBUTES,
    )
    SCHEMA_OUTPUT_PATH = PropertyDescriptor(
        name="Schema Output Path",
        description="Where to write master_schema.csv (shared with Step 2 processors).",
        required=True,
        default_value="/opt/nifi/outputs/master_schema.csv",
        expression_language_scope=ExpressionLanguageScope.FLOWFILE_ATTRIBUTES,
    )
    MATCH_THRESHOLD = PropertyDescriptor(
        name="Match Threshold",
        description="Composite similarity score floor (0–1). Tuned default: 0.25.",
        required=False,
        default_value="0.25",
        expression_language_scope=ExpressionLanguageScope.FLOWFILE_ATTRIBUTES,
    )
    TOP_K = PropertyDescriptor(
        name="Top K",
        description="Number of SapBERT candidate pairs to evaluate per column.",
        required=False,
        default_value="20",
        expression_language_scope=ExpressionLanguageScope.FLOWFILE_ATTRIBUTES,
    )
    MIN_FINAL_SCORE = PropertyDescriptor(
        name="Min Final Score",
        description="Minimum final composite score to accept a pair (script default 0.50).",
        required=False,
        default_value="0.50",
        expression_language_scope=ExpressionLanguageScope.FLOWFILE_ATTRIBUTES,
    )
    LEXICON_PATH = PropertyDescriptor(
        name="Lexicon Path",
        description=(
            "Optional path to clinical_lexicon.csv for expanded category tagging. "
            "Leave blank to use the built-in mini-lexicon."
        ),
        required=False,
        default_value="/opt/nifi/biolink_scripts/clinical_lexicon.csv",
        expression_language_scope=ExpressionLanguageScope.FLOWFILE_ATTRIBUTES,
    )

    property_descriptors = [
        REPOSITORY_ROOT,
        BHS_CSV_PATH, EHVOL_CSV_PATH, SCHEMA_OUTPUT_PATH,
        MATCH_THRESHOLD, TOP_K, MIN_FINAL_SCORE, LEXICON_PATH,
    ]

    def __init__(self, **kwargs):
        super().__init__()

    def getPropertyDescriptors(self):
        return self.property_descriptors

    def transform(self, context, flowfile):
        repo_root   = context.getProperty(self.REPOSITORY_ROOT).getValue()
        bhs_path    = context.getProperty(self.BHS_CSV_PATH).getValue()
        ehvol_path  = context.getProperty(self.EHVOL_CSV_PATH).getValue()
        out_path    = context.getProperty(self.SCHEMA_OUTPUT_PATH).getValue()
        threshold   = float(context.getProperty(self.MATCH_THRESHOLD).getValue() or "0.25")
        top_k       = int(context.getProperty(self.TOP_K).getValue() or "20")
        min_final   = float(context.getProperty(self.MIN_FINAL_SCORE).getValue() or "0.50")
        lexicon     = (context.getProperty(self.LEXICON_PATH).getValue() or "").strip() or None

        # Validate inputs
        script_path = os.path.join(repo_root, "nifi", "pipeline", "two_stage_match.py")
        if not os.path.isfile(script_path):
            msg = f"BiolinkMasterSchemaProcessor: ETL script not found at '{script_path}'"
            return FlowFileTransformResult(
                relationship="failure",
                contents=json.dumps({"error": msg}),
                attributes={"biolink.error": msg},
            )

        for label, path in [("BHS CSV", bhs_path), ("EHVol CSV", ehvol_path)]:
            if not os.path.isfile(path):
                msg = f"BiolinkMasterSchemaProcessor: {label} not found at '{path}'"
                return FlowFileTransformResult(
                    relationship="failure",
                    contents=json.dumps({"error": msg}),
                    attributes={"biolink.error": msg},
                )

        try:
            command = [
                "python3",
                script_path,
                "--threshold",
                str(threshold),
                "--top-k",
                str(top_k),
                "--min-final-score",
                str(min_final),
            ]

            env = os.environ.copy()
            if lexicon:
                env["BIOLINK_LEXICON_PATH"] = lexicon

            subprocess.run(
                command,
                cwd=repo_root,
                env=env,
                check=True,
                capture_output=True,
                text=True,
            )
        except Exception as exc:
            msg = f"BiolinkMasterSchemaProcessor: schema generation failed — {exc}"
            return FlowFileTransformResult(
                relationship="failure",
                contents=json.dumps({"error": msg}),
                attributes={"biolink.error": str(exc)},
            )

        if not os.path.isfile(out_path):
            msg = f"BiolinkMasterSchemaProcessor: expected schema output missing at '{out_path}'"
            return FlowFileTransformResult(
                relationship="failure",
                contents=json.dumps({"error": msg}),
                attributes={"biolink.error": msg},
            )

        total = 0
        pii_count = 0
        with open(out_path, newline="", encoding="utf-8") as schema_file:
            rows = list(csv.DictReader(schema_file))
            total = len(rows)
            pii_count = sum(
                1
                for row in rows
                if str(row.get("pii_flag", "False")).strip().lower() in ("true", "1", "yes")
            )

        # Echo schema CSV as FlowFile content
        with open(out_path, encoding="utf-8") as f:
            schema_csv = f.read()

        now_iso = datetime.now(timezone.utc).isoformat()
        return FlowFileTransformResult(
            relationship="success",
            contents=schema_csv.encode("utf-8"),
            attributes={
                "biolink.schema.total_matched":  str(total),
                "biolink.schema.pii_columns":    str(pii_count),
                "biolink.schema.clinical_columns": str(total - pii_count),
                "biolink.schema.min_final_score": str(min_final),
                "biolink.schema.output_path":    out_path,
                "biolink.schema.generated_at":   now_iso,
                "mime.type":                     "text/csv",
                "filename":                      "master_schema.csv",
            },
        )
