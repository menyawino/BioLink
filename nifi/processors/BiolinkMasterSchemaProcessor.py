"""
BioLink Master Schema Processor for Apache NiFi 2.8.0 — Step 1 of 2

Reads the full BHS and EHVol CSV files from the shared data directory,
runs the two-stage column-matching pipeline (TF-IDF + rule-based validation),
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
  Match Threshold     - cosine similarity floor (default 0.35)
  Top K               - TF-IDF candidates per column (default 5)
  Lexicon Path        - optional clinical lexicon CSV
                        (default /opt/nifi/biolink_scripts/clinical_lexicon.csv)
"""

import csv
import io
import json
import math
import os
import re
import string
from collections import defaultdict
from datetime import datetime, timezone

from nifiapi.flowfiletransform import FlowFileTransform, FlowFileTransformResult
from nifiapi.properties import PropertyDescriptor, ExpressionLanguageScope

# ─────────────────────────────────────────────────────────────────────────────
# Shared string helpers  (mirror scripts/two_stage_match.py)
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
# TF-IDF helpers (no sklearn needed — pure Python implementation)
# ─────────────────────────────────────────────────────────────────────────────

def _ngrams(text: str, n: int) -> list[str]:
    return [text[i:i+n] for i in range(len(text) - n + 1)]


def _tokenize(col: str) -> list[str]:
    """Return a bag of character 2–4-grams + word 1–2-grams from expanded column name."""
    expanded = expand_name(col)
    tokens: list[str] = []
    # word n-grams (1-2)
    words = expanded.split()
    tokens.extend(words)
    for i in range(len(words) - 1):
        tokens.append(f"{words[i]} {words[i+1]}")
    # char n-grams (2-4) on expanded text without spaces
    compact = expanded.replace(" ", "_")
    for n in (2, 3, 4):
        tokens.extend(_ngrams(compact, n))
    return tokens


def _build_tfidf(columns: list[str]):
    """Build TF-IDF vectors for a list of column names.
    Returns (doc_tokens, idf_dict) where doc_tokens[i] is the token freq dict."""
    doc_tokens: list[dict[str, float]] = []
    df: dict[str, int] = defaultdict(int)
    for col in columns:
        toks = _tokenize(col)
        freq: dict[str, float] = defaultdict(float)
        for t in toks:
            freq[t] += 1.0
        # normalize by doc length
        total = sum(freq.values()) or 1.0
        for t in freq:
            freq[t] /= total
            df[t] += 1
        doc_tokens.append(dict(freq))

    N = len(columns)
    idf: dict[str, float] = {t: math.log((N + 1) / (cnt + 1)) + 1.0 for t, cnt in df.items()}
    # apply idf
    for vec in doc_tokens:
        for t in vec:
            vec[t] *= idf.get(t, 1.0)
    # L2-normalize
    for vec in doc_tokens:
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        for t in vec:
            vec[t] /= norm
    return doc_tokens, idf


def _cosine(vec_a: dict[str, float], vec_b: dict[str, float]) -> float:
    common = set(vec_a) & set(vec_b)
    if not common:
        return 0.0
    return sum(vec_a[t] * vec_b[t] for t in common)


def stage1_candidates(
    cols_a: list[str],
    cols_b: list[str],
    top_k: int = 5,
    threshold: float = 0.35,
) -> list[tuple[str, str, float]]:
    """
    Return (col_a, col_b, cosine_score) pairs where score >= threshold.
    Uses a pure-Python TF-IDF to avoid sklearn dependency in the container.
    """
    all_cols = cols_a + cols_b
    vecs, _ = _build_tfidf(all_cols)
    vecs_a = vecs[:len(cols_a)]
    vecs_b = vecs[len(cols_a):]

    candidates: list[tuple[str, str, float]] = []
    for i, ca in enumerate(cols_a):
        scores = [(j, _cosine(vecs_a[i], vecs_b[j])) for j in range(len(cols_b))]
        scores.sort(key=lambda x: x[1], reverse=True)
        for j, score in scores[:top_k]:
            if score >= threshold:
                candidates.append((ca, cols_b[j], round(score, 4)))
    return candidates


# ─────────────────────────────────────────────────────────────────────────────
# Stage 2 validation
# ─────────────────────────────────────────────────────────────────────────────

_TYPE_COMPAT: dict[str, frozenset[str]] = {
    "numeric":     frozenset(["numeric", "binary"]),
    "binary":      frozenset(["binary", "numeric", "categorical"]),
    "categorical": frozenset(["categorical", "multi_cat", "binary", "text"]),
    "multi_cat":   frozenset(["multi_cat", "categorical", "text"]),
    "text":        frozenset(["text", "categorical", "multi_cat"]),
    "date":        frozenset(["date"]),
    "unknown":     frozenset(["numeric", "binary", "categorical", "multi_cat", "text", "date", "unknown"]),
}

_VETO_PAIRS: frozenset[frozenset[str]] = frozenset([
    frozenset(["numeric", "text"]),
    frozenset(["date", "numeric"]),
    frozenset(["date", "binary"]),
    frozenset(["date", "categorical"]),
])


def _type_compatible(dtype_a: str, dtype_b: str) -> bool:
    if dtype_a == dtype_b:
        return True
    pair = frozenset([dtype_a, dtype_b])
    if pair in _VETO_PAIRS:
        return False
    return dtype_b in _TYPE_COMPAT.get(dtype_a, frozenset())


def _jaccard_sets(set_a: set, set_b: set) -> float:
    if not set_a and not set_b:
        return 1.0
    union = set_a | set_b
    return len(set_a & set_b) / len(union) if union else 0.0


def stage2_validate(
    candidates: list[tuple[str, str, float]],
    dtype_a: dict[str, str],
    dtype_b: dict[str, str],
    cat_vals_a: dict[str, set[str]],
    cat_vals_b: dict[str, set[str]],
    threshold: float = 0.35,
) -> list[dict]:
    """
    Apply rule-based validation to TF-IDF candidates and compute composite score.
    Returns list of accepted match dicts.
    """
    accepted: list[dict] = []
    for col_a, col_b, tfidf_score in candidates:
        da = dtype_a.get(col_a, "unknown")
        db = dtype_b.get(col_b, "unknown")
        cat_a = _col_category(col_a)
        cat_b = _col_category(col_b)

        # Hard veto: incompatible types
        if not _type_compatible(da, db):
            continue

        # Semantic boost for same category
        cat_bonus = 0.10 if cat_a == cat_b and cat_a != "clinical" else 0.0

        # Categorical Jaccard score
        jac = 0.0
        if da in ("categorical", "binary") and db in ("categorical", "binary"):
            va = cat_vals_a.get(col_a, set())
            vb = cat_vals_b.get(col_b, set())
            jac = _jaccard_sets(va, vb)

        # Composite score (weights: tfidf=0.50, cat_bonus=0.20, jaccard=0.30)
        composite = tfidf_score * 0.50 + cat_bonus * 0.20 + jac * 0.30

        if composite < threshold:
            continue

        # Choose master column name (prefer dataset A)
        master_col = col_a

        accepted.append({
            "master_col":    master_col,
            "source_a_cols": col_a,
            "source_b_cols": col_b,
            "category":      cat_a if cat_a != "clinical" else cat_b,
            "final_score":   round(composite, 4),
            "coalesce_strategy": get_default_strategy(cat_a if cat_a != "clinical" else cat_b),
            "pii_flag":      is_pii_column(master_col),
        })

    # Deduplicate: keep best score per (col_a, col_b) pair
    seen: dict[tuple[str, str], dict] = {}
    for m in accepted:
        key = (m["source_a_cols"], m["source_b_cols"])
        if key not in seen or m["final_score"] > seen[key]["final_score"]:
            seen[key] = m

    return sorted(seen.values(), key=lambda x: (-x["final_score"], x["master_col"]))


# ─────────────────────────────────────────────────────────────────────────────
# CSV header + sample reader
# ─────────────────────────────────────────────────────────────────────────────

def _read_csv_headers_and_samples(
    path: str,
    sample_rows: int = 200,
) -> tuple[list[str], dict[str, list[str]], dict[str, set[str]]]:
    """Return (snake_headers, col_samples_dict, cat_values_dict)."""
    headers: list[str] = []
    col_samples: dict[str, list[str]] = {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        raw_headers = next(reader)
        headers = [to_snake(h) for h in raw_headers]
        for h in headers:
            col_samples[h] = []
        for i, row in enumerate(reader):
            if i >= sample_rows:
                break
            for j, val in enumerate(row):
                if j < len(headers):
                    col_samples[headers[j]].append(val)

    # Infer dtypes
    dtype_map: dict[str, str] = {h: infer_dtype(col_samples[h]) for h in headers}

    # Build categorical value sets
    cat_vals: dict[str, set[str]] = {}
    for h in headers:
        if dtype_map[h] in ("categorical", "binary"):
            cat_vals[h] = {v.strip().lower() for v in col_samples[h] if v.strip()}

    return headers, dtype_map, cat_vals


# ─────────────────────────────────────────────────────────────────────────────
# Master schema generation
# ─────────────────────────────────────────────────────────────────────────────

_SCHEMA_HEADER = [
    "master_col", "source_a_cols", "source_b_cols",
    "category", "final_score", "coalesce_strategy", "pii_flag",
]


def generate_master_schema(
    bhs_path: str,
    ehvol_path: str,
    output_path: str,
    threshold: float = 0.35,
    top_k: int = 5,
    lexicon_path: str | None = None,
) -> tuple[int, int]:
    """
    Run full matching pipeline and write master_schema.csv.
    Returns (total_matched, pii_count).
    """
    _load_lexicon(lexicon_path)

    headers_a, dtype_a, cat_a = _read_csv_headers_and_samples(bhs_path)
    headers_b, dtype_b, cat_b = _read_csv_headers_and_samples(ehvol_path)

    candidates = stage1_candidates(headers_a, headers_b, top_k=top_k, threshold=threshold)
    matches = stage2_validate(candidates, dtype_a, dtype_b, cat_a, cat_b, threshold=threshold)

    used_a = {m["source_a_cols"] for m in matches if m.get("source_a_cols")}
    used_b = {m["source_b_cols"] for m in matches if m.get("source_b_cols")}
    used_master = {m["master_col"] for m in matches if m.get("master_col")}

    def _append_passthrough(col: str, source_side: str) -> None:
        base = col
        master_col = base
        suffix = 2
        while master_col in used_master:
            master_col = f"{base}_{suffix}"
            suffix += 1
        used_master.add(master_col)
        category = _col_category(col)
        matches.append({
            "master_col":         master_col,
            "source_a_cols":      col if source_side == "a" else "",
            "source_b_cols":      col if source_side == "b" else "",
            "category":           category,
            "final_score":        0.0,
            "coalesce_strategy":  get_default_strategy(category),
            "pii_flag":           is_pii_column(col),
        })

    for col in headers_a:
        if col not in used_a:
            _append_passthrough(col, "a")

    for col in headers_b:
        if col not in used_b:
            _append_passthrough(col, "b")

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_SCHEMA_HEADER)
        writer.writeheader()
        writer.writerows(sorted(matches, key=lambda x: (-float(x.get("final_score", 0.0)), x.get("master_col", ""))))

    pii_count = sum(1 for m in matches if m["pii_flag"])
    return len(matches), pii_count


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
            "Step 1 of 2-stage harmonisation: runs TF-IDF column matching on "
            "BHS_Full.csv and EHVol_Full.csv headers, writes master_schema.csv "
            "to the outputs directory, and emits the schema CSV as a FlowFile."
        )
        tags = ["biolink", "schema", "matching", "etl", "harmonise", "step1"]

    BHS_CSV_PATH = PropertyDescriptor(
        name="BHS CSV Path",
        description="Absolute path to the full BHS CSV file inside the container.",
        required=True,
        default_value="/opt/nifi/db/BHS_Full.csv",
        expression_language_scope=ExpressionLanguageScope.VARIABLE_REGISTRY,
    )
    EHVOL_CSV_PATH = PropertyDescriptor(
        name="EHVol CSV Path",
        description="Absolute path to the full EHVol CSV file inside the container.",
        required=True,
        default_value="/opt/nifi/db/EHVol_Full.csv",
        expression_language_scope=ExpressionLanguageScope.VARIABLE_REGISTRY,
    )
    SCHEMA_OUTPUT_PATH = PropertyDescriptor(
        name="Schema Output Path",
        description="Where to write master_schema.csv (shared with Step 2 processors).",
        required=True,
        default_value="/opt/nifi/outputs/master_schema.csv",
        expression_language_scope=ExpressionLanguageScope.VARIABLE_REGISTRY,
    )
    MATCH_THRESHOLD = PropertyDescriptor(
        name="Match Threshold",
        description="Composite similarity score floor (0–1). Recommended: 0.35.",
        required=False,
        default_value="0.35",
        expression_language_scope=ExpressionLanguageScope.VARIABLE_REGISTRY,
    )
    TOP_K = PropertyDescriptor(
        name="Top K",
        description="Number of TF-IDF candidate pairs to evaluate per column.",
        required=False,
        default_value="5",
        expression_language_scope=ExpressionLanguageScope.VARIABLE_REGISTRY,
    )
    LEXICON_PATH = PropertyDescriptor(
        name="Lexicon Path",
        description=(
            "Optional path to clinical_lexicon.csv for expanded category tagging. "
            "Leave blank to use the built-in mini-lexicon."
        ),
        required=False,
        default_value="/opt/nifi/biolink_scripts/clinical_lexicon.csv",
        expression_language_scope=ExpressionLanguageScope.VARIABLE_REGISTRY,
    )

    property_descriptors = [
        BHS_CSV_PATH, EHVOL_CSV_PATH, SCHEMA_OUTPUT_PATH,
        MATCH_THRESHOLD, TOP_K, LEXICON_PATH,
    ]

    def __init__(self, **kwargs):
        super().__init__()

    def getPropertyDescriptors(self):
        return self.property_descriptors

    def transform(self, context, flowfile):
        bhs_path    = context.getProperty(self.BHS_CSV_PATH).getValue()
        ehvol_path  = context.getProperty(self.EHVOL_CSV_PATH).getValue()
        out_path    = context.getProperty(self.SCHEMA_OUTPUT_PATH).getValue()
        threshold   = float(context.getProperty(self.MATCH_THRESHOLD).getValue() or "0.35")
        top_k       = int(context.getProperty(self.TOP_K).getValue() or "5")
        lexicon     = (context.getProperty(self.LEXICON_PATH).getValue() or "").strip() or None

        # Validate inputs
        for label, path in [("BHS CSV", bhs_path), ("EHVol CSV", ehvol_path)]:
            if not os.path.isfile(path):
                msg = f"BiolinkMasterSchemaProcessor: {label} not found at '{path}'"
                return FlowFileTransformResult(
                    relationship="failure",
                    contents=json.dumps({"error": msg}),
                    attributes={"biolink.error": msg},
                )

        try:
            total, pii_count = generate_master_schema(
                bhs_path=bhs_path,
                ehvol_path=ehvol_path,
                output_path=out_path,
                threshold=threshold,
                top_k=top_k,
                lexicon_path=lexicon,
            )
        except Exception as exc:
            msg = f"BiolinkMasterSchemaProcessor: schema generation failed — {exc}"
            return FlowFileTransformResult(
                relationship="failure",
                contents=json.dumps({"error": msg}),
                attributes={"biolink.error": str(exc)},
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
                "biolink.schema.output_path":    out_path,
                "biolink.schema.generated_at":   now_iso,
                "mime.type":                     "text/csv",
                "filename":                      "master_schema.csv",
            },
        )
