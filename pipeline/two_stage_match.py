#!/usr/bin/env python3
"""
Two-stage clinical column matching pipeline.

Stage 1 – Candidate generation
  Expands snake_case names via a clinical lexicon CSV (pipeline/clinical_lexicon.csv)
  then embeds with TF-IDF char+word n-grams, or SapBERT when sentence-transformers
  is installed. Keeps pairs with cosine similarity ≥ STAGE1_THRESHOLD (default 0.35).

Stage 2 – Validation via data-level + rule-based filters
  For each candidate pair:
    2a. Rule-based vetoes (contact vs clinical, admin, domain incompatibility, etc.)
    2b. Dtype inference from actual data (numeric, date, binary, categorical,
        multi_cat, text) – pairs whose types are incompatible are rejected.
    2c. Value-range / distribution overlap:
          Numeric  → IQR Jaccard + bootstrap 90% CI (range_ci_low / range_ci_high)
          Date     → Year-set Jaccard overlap
          Categorical/Binary → Jaccard of top-N most-frequent values
    2d. Composite final_score using configurable weights (--weights).
    2e. Reject weak pairs with final_score < --min-final-score.

Score weights (defaults, override with --weights name:0.55,range:0.25,cat:0.10,type:0.10)
  name_score × W_name
  + range_score × W_range           (numeric/date/categorical overlap)
  + type_same_bonus × W_type        (+1 if both columns have identical dtype)
  = final_score  (clipped to [0, 1])

Outputs
  outputs/matched_pairs_validated.csv   – all candidates with verdict + diagnostics
  outputs/matched_pairs_accepted.csv    – accepted pairs only (clean, for downstream)
  outputs/match_validation_report.json  – aggregate stats + top-30 accepted

Usage
  python pipeline/two_stage_match.py [--threshold 0.35] [--top-k 5] [--no-sapbert]
  python pipeline/two_stage_match.py --weights name:0.6,range:0.3,cat:0.05,type:0.05
  python pipeline/two_stage_match.py --cat-threshold 0.3 --n-boot 200
    python pipeline/two_stage_match.py --min-final-score 0.50
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import warnings
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
OUTPUTS = ROOT / "outputs"
DB = ROOT / "db"

BHS_CSV = DB / "BHS_Full.csv"
EHVOL_CSV = DB / "EHVol_Full.csv"
BHS_ONLY = OUTPUTS / "db_only_bhs.csv"
EHVOL_ONLY = OUTPUTS / "db_only_ehvol.csv"

# ---------------------------------------------------------------------------
# Clinical abbreviation / domain expansion lexicon
# Primary source: pipeline/clinical_lexicon.csv (acronym,expansion,category,...)
# Fallback: hardcoded dict below (used when CSV is missing or unreadable).
# ---------------------------------------------------------------------------

LEXICON_CSV = Path(__file__).parent / "clinical_lexicon.csv"

_ABBREV_FALLBACK: Dict[str, str] = {
    "bnp": "B-type natriuretic peptide cardiac biomarker",
    "bp": "blood pressure",
    "bsa": "body surface area",
    "ecg": "electrocardiogram",
    "echo": "echocardiogram cardiac ultrasound",
    "ef": "ejection fraction systolic function",
    "egfr": "estimated glomerular filtration rate kidney",
    "lvh": "left ventricular hypertrophy",
    "lvm": "left ventricular mass",
    "mr": "mitral regurgitation",
    "mri": "magnetic resonance imaging cardiac",
    "mrn": "medical record number identifier",
    "qt": "QT interval ECG",
    "qtc": "corrected QT interval ECG",
    "pr": "PR interval ECG",
    "qrs": "QRS complex ECG",
    "rr": "RR interval heart rate",
    "tapse": "tricuspid annular plane systolic excursion",
    "troponin": "cardiac troponin biomarker",
    "alt": "alanine transaminase liver enzyme",
    "ast": "aspartate transaminase liver enzyme",
    "ar": "aortic regurgitation",
    "as": "aortic stenosis",
    "fs": "fractional shortening",
    "dna": "DNA genetic sample",
    "tel": "telephone contact",
    "cmr": "cardiac magnetic resonance",
    "ct": "computed tomography scan",
    "tte": "transthoracic echocardiography",
    "cabg": "coronary artery bypass grafting surgery",
    "af": "atrial fibrillation arrhythmia",
    "lvef": "left ventricular ejection fraction",
    "rvef": "right ventricular ejection fraction",
    "hb": "haemoglobin blood",
    "wbc": "white blood cell count",
    "rbc": "red blood cell count",
    "crp": "C-reactive protein inflammation",
    "hba1c": "glycated haemoglobin diabetes",
    "ldl": "low-density lipoprotein cholesterol",
    "hdl": "high-density lipoprotein cholesterol",
}

# Loaded at import time; populated by load_lexicon().
ABBREV: Dict[str, str] = {}
# Maps acronym → clinical category tag (ecg, echo, lab, mri, …)
ABBREV_CATEGORY: Dict[str, str] = {}


def load_lexicon(path: Path = LEXICON_CSV) -> None:
    """
    Populate ABBREV and ABBREV_CATEGORY from a CSV with columns:
      acronym, expansion, category  [, loinc, snomed]
    Falls back silently to _ABBREV_FALLBACK when file is absent.
    """
    global ABBREV, ABBREV_CATEGORY
    ABBREV = dict(_ABBREV_FALLBACK)  # start from hardcoded baseline
    if not path.exists():
        print(f"  [lexicon] {path} not found – using built-in abbreviations",
              file=sys.stderr)
        return
    try:
        with path.open() as f:
            reader = csv.DictReader(f)
            for row in reader:
                acronym = row.get("acronym", "").strip().lower()
                expansion = row.get("expansion", "").strip()
                category = row.get("category", "").strip().lower()
                if acronym and expansion:
                    ABBREV[acronym] = expansion
                if acronym and category:
                    ABBREV_CATEGORY[acronym] = category
        print(f"  [lexicon] Loaded {len(ABBREV)} abbreviations from {path.name}",
              file=sys.stderr)
    except Exception as e:
        print(f"  [lexicon] Could not read {path}: {e} – using built-in",
              file=sys.stderr)
        ABBREV = dict(_ABBREV_FALLBACK)


# Eagerly load on import so expand_name() has the full dict available.
load_lexicon()


def _col_category(name: str) -> str:
    """Return the clinical category tag for a column name.

    Lookup order:
    1. Full name (lowercased, underscores stripped) in ABBREV_CATEGORY.
    2. Each underscore-split token in ABBREV_CATEGORY.
    3. First matching DOMAIN_TAGS group keyword.
    4. 'unknown' fallback.
    """
    # 1. Full name without underscores (catches e.g. 'qtcinterval' → 'ecg')
    compact = name.lower().replace("_", "")
    if compact in ABBREV_CATEGORY:
        return ABBREV_CATEGORY[compact]
    # 2. Token-by-token
    for tok in name.lower().split("_"):
        if tok in ABBREV_CATEGORY:
            return ABBREV_CATEGORY[tok]
    # 3. Domain tag keyword scan – reuse DOMAIN_TAGS (populated later in module)
    #    DOMAIN_TAGS may not exist yet during cold-import, so guard with getattr.
    for domain, keywords in globals().get("DOMAIN_TAGS", {}).items():
        if any(kw in name.lower() for kw in keywords):
            return domain
    return "unknown"


# ---------------------------------------------------------------------------
# Composite score weights
# Default: name 55%, range/cat overlap 25%, same-type bonus 10%, extra 10% free.
# Tune by passing --weights name:N,range:N,cat:N,type:N (values must sum to 1.0).
# ---------------------------------------------------------------------------
_DEFAULT_WEIGHTS: Dict[str, float] = {
    "name":  0.55,   # TF-IDF / SapBERT cosine name similarity
    "range": 0.25,   # IQR overlap (numeric) / year Jaccard (date) / val Jaccard (cat)
    "cat":   0.10,   # categorical top-N value Jaccard (separate from range for cat cols)
    "type":  0.10,   # bonus when both columns have identical inferred dtype
}

# Domain group tags – used in rule-based vetoes
DOMAIN_TAGS: Dict[str, List[str]] = {
    "ecg": [
        "ecg", "qtc", "qt_interval", "pr_interval", "qrs", "rhythm", "ventricular_rate",
        "corrected_qt", "rate", "holter", "st_segment", "t_wave", "regional_wall",
        "ecg_conclusion", "ecg_date", "ecg_holter",
    ],
    "echo": [
        "echo", "ef", "ejection_fraction", "tapse", "fs", "left_atrial", "aortic_root",
        "echo_date", "left_ventricular", "right_ventricular", "left_atrium",
        "ventricular_mass", "midventricular", "apical", "basal", "septal",
        "other_echocardiographic",
    ],
    "mri": [
        "mri", "cmr", "mri_date", "heart_rate_during_mri", "other_mri_findings",
        "contraindications_for_mri",
    ],
    "lab": [
        "bnp", "troponin", "albumin", "alt", "ast", "egfr", "creatinine", "hba1c",
        "cholesterol", "hdl", "ldl", "triglycerides", "fasting_blood_sugar",
        "haemoglobin", "platelets", "wbc", "rbc", "urea",
    ],
    "contact": [
        "tel", "mobile_tel", "home_tel", "email", "address", "contact_number",
        "alternate_contact", "complete_12",
    ],
    "admin": [
        "record_id", "mrn", "complete", "upload_consent", "consent_scan",
        "household_identifier",
    ],
    "demographics": [
        "age", "gender", "ethnicity", "marital_status", "education",
        "occupation", "city_of_residence", "nationality", "origin",
    ],
    "family_history": [
        "father_origins", "mother_origins", "father_s_city", "mother_s_city",
        "father_s_gov", "mother_s_gov", "family_history", "parents_occupation",
    ],
    "dates": [
        "date", "ecg_date", "echo_date", "mri_date", "date_of_enrolment",
        "date_consent", "examination_date", "date_of_birth",
    ],
}

# ---------------------------------------------------------------------------
# Helpers: snake_case ↔ natural language
# ---------------------------------------------------------------------------
_SNAKE_RE = re.compile(r"[_\s]+")
_NONWORD = re.compile(r"[^a-z0-9 ]")


def to_snake(name: str) -> str:
    """Normalise an arbitrary column heading to snake_case."""
    name = name.lower().strip()
    name = re.sub(r"['\u2019\u2018]", "", name)     # apostrophes
    name = re.sub(r"[^a-z0-9 _]", " ", name)
    name = re.sub(r"\s+", "_", name.strip())
    name = re.sub(r"_+", "_", name)
    return name.strip("_")


def expand_name(snake: str) -> str:
    """Convert snake_case to words, expand domain abbreviations."""
    tokens = _SNAKE_RE.split(snake.lower())
    expanded = []
    for tok in tokens:
        if tok in ABBREV:
            expanded.append(ABBREV[tok])
        else:
            expanded.append(tok)
    return " ".join(expanded)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_dataframe(path: Path) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """
    Load CSV; return (DataFrame with snake_case columns, mapping snake→original).
    """
    df = pd.read_csv(path, dtype=str, low_memory=False)
    orig_cols = list(df.columns)
    snake_cols = [to_snake(c) for c in orig_cols]
    # Deduplicate: if two headings produce the same snake, append _N
    seen: Dict[str, int] = {}
    final_cols = []
    for sc in snake_cols:
        if sc in seen:
            seen[sc] += 1
            final_cols.append(f"{sc}_{seen[sc]}")
        else:
            seen[sc] = 0
            final_cols.append(sc)
    df.columns = final_cols
    mapping = dict(zip(final_cols, orig_cols))
    return df, mapping


def read_list(path: Path) -> List[str]:
    if not path.exists():
        return []
    return [l.strip() for l in path.read_text().splitlines() if l.strip()]


# ---------------------------------------------------------------------------
# dtype inference
# ---------------------------------------------------------------------------

def infer_dtype(series: pd.Series) -> str:
    """
    Returns one of: 'numeric', 'date', 'binary', 'categorical', 'multi_cat', 'text', 'unknown'.
    """
    s = series.dropna().astype(str).str.strip()
    s = s[s != ""]
    if len(s) == 0:
        return "unknown"

    # Try numeric
    numeric_hits = pd.to_numeric(s, errors="coerce").notna().mean()
    if numeric_hits >= 0.80:
        return "numeric"

    # Try dates
    # Fast check: look for patterns like dd/mm/yyyy, yyyy-mm-dd, mm-dd-yyyy
    date_re = re.compile(
        r"^\d{1,4}[/\-\.]\d{1,2}[/\-\.]\d{1,4}$"
        r"|^\d{4}$"  # year only
    )
    date_hits = s.str.match(date_re).mean()
    if date_hits >= 0.60:
        return "date"

    unique_vals = s.nunique()
    total = len(s)

    if unique_vals <= 2:
        return "binary"
    if unique_vals <= 15 or (total > 0 and unique_vals / total <= 0.05):
        return "categorical"
    if unique_vals <= 50:
        return "multi_cat"
    # Check average token count: many words → free text
    avg_len = s.str.len().mean()
    if avg_len > 40:
        return "text"
    return "categorical"


# ---------------------------------------------------------------------------
# Value-range overlap  +  bootstrap confidence intervals
# ---------------------------------------------------------------------------

def numeric_range_overlap(s_a: pd.Series, s_b: pd.Series) -> float:
    """
    Returns 0-1 overlap score between the IQR-based ranges of two numeric cols.
    """
    def iqr_range(s: pd.Series):
        vals = pd.to_numeric(s.dropna(), errors="coerce").dropna()
        if len(vals) < 5:
            return None
        q1, q3 = vals.quantile(0.10), vals.quantile(0.90)
        return (q1, q3)

    r_a = iqr_range(s_a)
    r_b = iqr_range(s_b)
    if r_a is None or r_b is None:
        return 0.5   # can't tell – neutral

    lo = max(r_a[0], r_b[0])
    hi = min(r_a[1], r_b[1])
    if hi <= lo:
        return 0.0
    span_a = r_a[1] - r_a[0]
    span_b = r_b[1] - r_b[0]
    intersect = hi - lo
    union = max(r_a[1], r_b[1]) - min(r_a[0], r_b[0])
    if union <= 0:
        return 1.0
    iou = intersect / union
    return float(iou)


def date_range_overlap(s_a: pd.Series, s_b: pd.Series) -> float:
    """
    Extracts 4-digit years from both cols and computes Jaccard on year sets.
    """
    year_re = re.compile(r"(19|20)\d{2}")

    def extract_years(s: pd.Series) -> set:
        years = set()
        for v in s.dropna().astype(str):
            m = year_re.search(v)
            if m:
                years.add(int(m.group()))
        return years

    ya = extract_years(s_a)
    yb = extract_years(s_b)
    if not ya or not yb:
        return 0.5
    intersect = len(ya & yb)
    union = len(ya | yb)
    return intersect / union if union else 0.5


def categorical_value_overlap(s_a: pd.Series, s_b: pd.Series, top_n: int = 5) -> float:
    """
    Jaccard similarity on the top-N most-frequent non-null values in each column.
    Normalises values to lowercase stripped strings before comparison.

    Returns a [0, 1] score:
      1.0 → identical most-common values (e.g. both have "yes"/"no"/"unknown")
      0.0 → completely disjoint value sets (likely different concepts)
    """
    def top_vals(s: pd.Series, n: int) -> set:
        vals = s.dropna().astype(str).str.strip().str.lower()
        vals = vals[vals != ""]
        return set(vals.value_counts().head(n).index)

    va = top_vals(s_a, top_n)
    vb = top_vals(s_b, top_n)
    if not va or not vb:
        return 0.5   # can't tell
    intersect = len(va & vb)
    union = len(va | vb)
    return intersect / union if union else 0.0


def bootstrap_numeric_overlap(
    s_a: pd.Series,
    s_b: pd.Series,
    n_boot: int = 100,
    ci: float = 0.90,
) -> Tuple[float, float]:
    """
    Bootstrap the IQR Jaccard overlap to produce a confidence interval.

    Returns (ci_low, ci_high) at the requested CI level (default 90%).
    Each bootstrap iteration resamples both columns (with replacement, up to
    1 000 observations each) and recomputes `numeric_range_overlap`.
    """
    vals_a = pd.to_numeric(s_a.dropna(), errors="coerce").dropna().to_numpy()
    vals_b = pd.to_numeric(s_b.dropna(), errors="coerce").dropna().to_numpy()

    if len(vals_a) < 5 or len(vals_b) < 5:
        point = numeric_range_overlap(s_a, s_b)
        return (round(point, 3), round(point, 3))

    cap_a = min(1000, len(vals_a))
    cap_b = min(1000, len(vals_b))
    rng = np.random.default_rng(42)
    boot_scores = []
    for _ in range(n_boot):
        samp_a = pd.Series(rng.choice(vals_a, size=cap_a, replace=True))
        samp_b = pd.Series(rng.choice(vals_b, size=cap_b, replace=True))
        boot_scores.append(numeric_range_overlap(samp_a, samp_b))

    lo_pct = (1 - ci) / 2 * 100
    hi_pct = (1 + ci) / 2 * 100
    return (
        round(float(np.percentile(boot_scores, lo_pct)), 3),
        round(float(np.percentile(boot_scores, hi_pct)), 3),
    )


# ---------------------------------------------------------------------------
# Rule-based vetoes
# ---------------------------------------------------------------------------

def _domains_of(col: str) -> List[str]:
    """Return all domain tags col belongs to."""
    tags = []
    col_lower = col.lower()
    for tag, keywords in DOMAIN_TAGS.items():
        for kw in keywords:
            if kw in col_lower:
                tags.append(tag)
                break
    return tags


# Columns whose match with certain other domains is always wrong
_INCOMPATIBLE_DOMAIN_PAIRS = {
    ("contact", "ecg"), ("contact", "echo"), ("contact", "mri"),
    ("contact", "lab"), ("contact", "dates"),
    ("admin", "ecg"), ("admin", "echo"), ("admin", "mri"), ("admin", "lab"),
    ("ecg", "lab"), ("ecg", "demographics"), ("echo", "lab"),
    ("mri", "lab"),
}


def rule_veto(col_a: str, col_b: str) -> Optional[str]:
    """
    Returns a rejection reason string if the pair should be vetoed,
    None if the pair survives.
    """
    a, b = col_a.lower(), col_b.lower()

    # ---- contact / admin vs anything clinical ----
    # NOTE: consent scan / upload_consent_scan are medical docs, not contact info.
    contact_kws = {"_tel", "email", "address", "contact", "complete_12"}
    admin_kws = {"mrn", "record_id", "household"}
    a_contact = any(k in a for k in contact_kws)
    b_contact = any(k in b for k in contact_kws)
    if a_contact or b_contact:
        if not (a_contact and b_contact):
            return "contact_field_vs_clinical"

    if any(k in a for k in admin_kws) or any(k in b for k in admin_kws):
        if not (any(k in a for k in admin_kws) and any(k in b for k in admin_kws)):
            return "admin_field_vs_clinical"

    # ---- question slugs: do_you_, are_you_, have_you_, if_yes_ ----
    q_prefixes = ("do_you_", "are_you_", "have_you_", "do_any_", "if_yes_",
                  "has_anyone_", "does_any_")
    a_is_q = any(a.startswith(p) for p in q_prefixes)
    b_is_q = any(b.startswith(p) for p in q_prefixes)
    if a_is_q != b_is_q:
        question, non_q = (a, b) if a_is_q else (b, a)
        # Allow if the non-question column name meaningfully overlaps the question text.
        # E.g. "have_you_been_diagnosed_with_rheumatic_fever" ↔ "rheumatic_fever"
        non_q_tokens = set(_SNAKE_RE.split(non_q)) - {""}
        q_tokens = set(_SNAKE_RE.split(question)) - {"", "do", "you", "have", "are",
                                                       "been", "any", "if", "yes",
                                                       "please", "specify", "does"}
        overlap = non_q_tokens & q_tokens
        if not overlap or len(non_q) < 8:
            return "question_field_vs_short_code"

    # ---- diagnosis vs lab/measurement mismatch ----
    diag_kws = {"angina", "anaemia", "diabetes", "hypertension", "stenosis",
                "regurge", "cardiomyopathy", "rheumatic", "autoimmune",
                "dyslipidemia", "heart_attack"}
    lab_kws = {"bnp", "bp", "troponin", "egfr", "albumin", "alt", "ast",
               "fasting_blood_sugar", "haemoglobin", "cholesterol"}
    a_diag = any(k in a for k in diag_kws)
    b_diag = any(k in b for k in diag_kws)
    a_lab = any(k in a for k in lab_kws)
    b_lab = any(k in b for k in lab_kws)
    if (a_diag and b_lab) or (b_diag and a_lab):
        return "diagnosis_vs_lab_biomarker"

    # ---- domain incompatibility ----
    tags_a = set(_domains_of(col_a))
    tags_b = set(_domains_of(col_b))
    for pa, pb in _INCOMPATIBLE_DOMAIN_PAIRS:
        if (pa in tags_a and pb in tags_b) or (pb in tags_a and pa in tags_b):
            return f"domain_mismatch:{pa}_vs_{pb}"

    # ---- specific known false-positives in the original output ----
    bad_pairs = {
        ("date_medications", "diabetes_mellitus"),
        ("fasting_blood_sugar", "high_blood_pressure"),
        ("ef_class", "fat_mass"),
        ("rate", "route"),
        ("notes", "route"),
        ("tapse", "type"),
        ("marital_status", "status"),   # marital_status vs generic status
    }
    pair = (min(col_a, col_b), max(col_a, col_b))
    norm_pair = (min(a, b), max(a, b))
    if norm_pair in bad_pairs:
        return "known_false_positive"

    return None   # no veto


# ---------------------------------------------------------------------------
# Stage 1: Candidate generation (TF-IDF cosine + optional SapBERT)
# ---------------------------------------------------------------------------

def _tfidf_similarity_matrix(names_a: List[str], names_b: List[str]) -> np.ndarray:
    """Return (len_a × len_b) cosine-similarity matrix using TF-IDF."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    expanded_a = [expand_name(n) for n in names_a]
    expanded_b = [expand_name(n) for n in names_b]

    vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(2, 4),
        min_df=1,
        sublinear_tf=True,
    )
    all_docs = expanded_a + expanded_b
    vectorizer.fit(all_docs)
    vecs_a = vectorizer.transform(expanded_a)
    vecs_b = vectorizer.transform(expanded_b)

    # Also add word-level TF-IDF
    word_vec = TfidfVectorizer(
        analyzer="word",
        ngram_range=(1, 2),
        min_df=1,
        sublinear_tf=True,
    )
    word_vec.fit(all_docs)
    wvecs_a = word_vec.transform(expanded_a)
    wvecs_b = word_vec.transform(expanded_b)

    sim_char = cosine_similarity(vecs_a, vecs_b)
    sim_word = cosine_similarity(wvecs_a, wvecs_b)
    return 0.5 * sim_char + 0.5 * sim_word


def _sapbert_similarity_matrix(names_a: List[str], names_b: List[str]) -> Optional[np.ndarray]:
    """
    Optional: use SapBERT for clinically-aware embeddings.
    Returns None if sentence-transformers is not installed.
    """
    try:
        from sentence_transformers import SentenceTransformer
        from sklearn.metrics.pairwise import cosine_similarity
    except ImportError:
        return None

    model_name = "cambridgeltl/SapBERT-from-PubMedBERT-fulltext"
    print(f"  [SapBERT] Loading model {model_name} …", file=sys.stderr)
    try:
        model = SentenceTransformer(model_name)
    except Exception as e:
        print(f"  [SapBERT] Load failed: {e}", file=sys.stderr)
        return None

    expanded_a = [expand_name(n) for n in names_a]
    expanded_b = [expand_name(n) for n in names_b]
    emb_a = model.encode(expanded_a, show_progress_bar=False)
    emb_b = model.encode(expanded_b, show_progress_bar=False)
    return cosine_similarity(emb_a, emb_b)


def stage1_candidates(
    names_a: List[str],
    names_b: List[str],
    threshold: float = 0.35,
    top_k: int = 5,
    use_sapbert: bool = True,
) -> List[Tuple[str, str, float]]:
    """
    Returns list of (name_a, name_b, name_score) candidate pairs.
    Attempts SapBERT first; falls back to TF-IDF.
    """
    sim = None
    method = "tfidf"
    if use_sapbert:
        sim = _sapbert_similarity_matrix(names_a, names_b)
        if sim is not None:
            method = "sapbert"

    if sim is None:
        sim = _tfidf_similarity_matrix(names_a, names_b)

    print(f"  Stage 1 ({method}): similarity matrix {sim.shape}", file=sys.stderr)

    candidates = []
    for i, na in enumerate(names_a):
        row = sim[i]
        top_indices = np.argsort(row)[::-1][:top_k]
        for j in top_indices:
            s = float(row[j])
            if s >= threshold:
                candidates.append((na, names_b[j], round(s, 4)))

    # Deduplicate: keep highest score per pair
    best: Dict[tuple, float] = {}
    for a, b, s in candidates:
        key = (min(a, b), max(a, b))
        if s > best.get(key, 0):
            best[key] = s
    result = [(k[0], k[1], best[k]) for k in best]
    result.sort(key=lambda x: -x[2])
    print(f"  Stage 1 produced {len(result)} candidate pairs", file=sys.stderr)
    return result


# ---------------------------------------------------------------------------
# Stage 2: Validate candidates
# ---------------------------------------------------------------------------

_TYPE_COMPAT = {
    # (type_a, type_b): compatible? (keys always sorted alphabetically)
    ("binary",      "binary"):      True,
    ("binary",      "categorical"): True,   # binary can live inside categorical
    ("binary",      "date"):        False,
    ("binary",      "multi_cat"):   True,
    ("binary",      "numeric"):     False,
    ("binary",      "text"):        False,
    ("binary",      "unknown"):     True,
    ("categorical", "categorical"): True,
    ("categorical", "date"):        False,
    ("categorical", "multi_cat"):   True,
    ("categorical", "numeric"):     False,
    ("categorical", "text"):        False,  # categorical vs free-text: incompatible
    ("categorical", "unknown"):     True,
    ("date",        "date"):        True,
    ("date",        "multi_cat"):   False,
    ("date",        "numeric"):     False,
    ("date",        "text"):        False,
    ("date",        "unknown"):     True,
    ("multi_cat",   "multi_cat"):   True,
    ("multi_cat",   "numeric"):     False,
    ("multi_cat",   "text"):        False,
    ("multi_cat",   "unknown"):     True,
    ("numeric",     "numeric"):     True,
    ("numeric",     "text"):        False,
    ("numeric",     "unknown"):     True,
    ("text",        "text"):        True,
    ("text",        "unknown"):     True,
    ("unknown",     "unknown"):     True,   # give benefit of doubt
}


def type_compatible(ta: str, tb: str) -> bool:
    ordered = (ta, tb) if ta <= tb else (tb, ta)
    return _TYPE_COMPAT.get(ordered, True)   # default: compatible unless explicitly blocked


def stage2_validate(
    candidates: List[Tuple[str, str, float]],
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    weights: Optional[Dict[str, float]] = None,
    cat_threshold: float = 0.30,
    n_boot: int = 100,
    min_final_score: float = 0.50,
) -> List[Dict]:
    """
    For each candidate pair apply dtype checks, range checks, and rule vetoes.

    Args:
        candidates:     Output of stage1_candidates().
        df_a / df_b:    DataFrames for the two column sets (used for data checks).
        weights:        Score weight dict with keys name/range/cat/type.
                        Defaults to _DEFAULT_WEIGHTS.
        cat_threshold:  Minimum categorical/binary value overlap to accept pair.
        n_boot:         Bootstrap iterations for numeric CI computation.
        min_final_score: Minimum final composite score to accept pair.

    Returns list of result dicts.
    """
    W = weights if weights else _DEFAULT_WEIGHTS
    # Pre-compute dtypes once
    dtype_cache_a: Dict[str, str] = {}
    dtype_cache_b: Dict[str, str] = {}
    for col in df_a.columns:
        dtype_cache_a[col] = infer_dtype(df_a[col])
    for col in df_b.columns:
        dtype_cache_b[col] = infer_dtype(df_b[col])

    results = []
    for name_a, name_b, name_score in candidates:
        rec = {
            "name_a": name_a,
            "category_a": _col_category(name_a),
            "name_b": name_b,
            "category_b": _col_category(name_b),
            "name_score": name_score,
            "type_a": "unknown",
            "type_b": "unknown",
            "type_compat": True,
            "range_score": None,
            "range_ci_low": None,
            "range_ci_high": None,
            "cat_overlap": None,
            "final_score": name_score,
            "verdict": "ACCEPTED",
            "reject_reason": "",
        }

        # ---- 2d. Rule-based veto (applied before data checks) ----
        veto = rule_veto(name_a, name_b)
        if veto:
            rec["verdict"] = "REJECTED"
            rec["reject_reason"] = veto
            results.append(rec)
            continue

        # ---- get series if available ----
        col_a = name_a if name_a in df_a.columns else None
        col_b = name_b if name_b in df_b.columns else None

        ta = dtype_cache_a.get(col_a, "unknown") if col_a else "unknown"
        tb = dtype_cache_b.get(col_b, "unknown") if col_b else "unknown"
        rec["type_a"] = ta
        rec["type_b"] = tb

        # ---- 2b. Type compatibility ----
        compat = True   # default: compatible
        if ta != "unknown" and tb != "unknown":
            compat = type_compatible(ta, tb)
            rec["type_compat"] = compat
            if not compat:
                rec["verdict"] = "REJECTED"
                rec["reject_reason"] = f"type_mismatch:{ta}_vs_{tb}"
                results.append(rec)
                continue

        # ---- 2c. Value-range / value-distribution overlap ----
        range_score = None

        if col_a and col_b and ta == "numeric" and tb == "numeric":
            range_score = numeric_range_overlap(df_a[col_a], df_b[col_b])
            rec["range_score"] = round(range_score, 3)
            if range_score < 0.05:
                rec["verdict"] = "REJECTED"
                rec["reject_reason"] = f"numeric_range_no_overlap:score={range_score:.3f}"
                results.append(rec)
                continue
            # Bootstrap CI for numeric overlap
            ci_lo, ci_hi = bootstrap_numeric_overlap(
                df_a[col_a], df_b[col_b], n_boot=n_boot
            )
            rec["range_ci_low"] = ci_lo
            rec["range_ci_high"] = ci_hi

        elif col_a and col_b and ta == "date" and tb == "date":
            range_score = date_range_overlap(df_a[col_a], df_b[col_b])
            rec["range_score"] = round(range_score, 3)
            if range_score < 0.10:
                rec["verdict"] = "REJECTED"
                rec["reject_reason"] = f"date_range_no_overlap:score={range_score:.3f}"
                results.append(rec)
                continue

        elif col_a and col_b and ta in ("binary", "categorical") and tb in ("binary", "categorical"):
            cat_ov = categorical_value_overlap(df_a[col_a], df_b[col_b])
            rec["cat_overlap"] = round(cat_ov, 3)
            if cat_ov < cat_threshold:
                rec["verdict"] = "REJECTED"
                rec["reject_reason"] = f"low_categorical_overlap:score={cat_ov:.3f}"
                results.append(rec)
                continue
            # Use cat_overlap as range_score so the weight formula is unified
            range_score = cat_ov
            rec["range_score"] = round(range_score, 3)

        # ---- Compute final composite score ----
        # W["name"]  × name_score
        # W["range"] × range_score  (0.5 neutral when unavailable)
        # W["type"]  × type_same_bonus  (1.0 when both have identical non-unknown dtype)
        type_same = 1.0 if compat_bonus(ta, tb) else 0.0
        r_score = range_score if range_score is not None else 0.5
        final = (
            W["name"]  * name_score
            + W["range"] * r_score
            + W["type"]  * type_same
        )
        rec["final_score"] = round(min(final, 1.0), 4)

        # Guardrail against semantic overmatching when candidate volume is high.
        if rec["final_score"] < min_final_score:
            rec["verdict"] = "REJECTED"
            rec["reject_reason"] = f"final_score_below_min:{rec['final_score']:.4f}"

        results.append(rec)

    return results


def compat_bonus(ta: str, tb: str) -> bool:
    """High confidence type match (both same non-unknown type)."""
    return ta == tb and ta not in ("unknown",)


# ---------------------------------------------------------------------------
# Master schema generation
# ---------------------------------------------------------------------------

def is_pii_column(col_name: str) -> bool:
    """
    Return True when a column name contains PII-related tokens.
    Errs on the side of over-flagging; human review before dropping.
    """
    pii_keywords = {
        "patient_id", "mrn", "medical_record", "dob",
        "date_of_birth", "birth_date", "address", "street",
        "_tel", "phone", "mobile", "email", "national_id",
        "ssn", "passport", "consent_scan", "signature", "nationality",
        "contact_number",
    }
    lower = col_name.lower()
    return any(kw in lower for kw in pii_keywords)


def get_default_strategy(category: str) -> str:
    """
    Return the recommended coalesce strategy for a clinical category.

    Strategies understood by apply_schema.py:
      first_non_null | mean_value | max_value | min_value
      any_flag       | mode_value | median_date
    """
    return {
        "date":         "median_date",
        "lab":          "max_value",
        "ecg":          "mean_value",
        "echo":         "mean_value",
        "vitals":       "mean_value",
        "mri":          "first_non_null",
        "binary":       "any_flag",
        "categorical":  "mode_value",
        "genetics":     "first_non_null",
        "demographics": "first_non_null",
        "contact":      "first_non_null",
    }.get(category, "first_non_null")


_OMOP_DOMAIN_BY_CATEGORY: Dict[str, str] = {
    "lab": "measurement",
    "ecg": "measurement",
    "echo": "measurement",
    "vitals": "measurement",
    "mri": "measurement",
    "genetics": "measurement",
    "date": "observation",
    "binary": "observation",
    "categorical": "observation",
    "demographics": "person",
    "family_history": "observation",
    "contact": "observation",
    "admin": "observation",
}


_VOCAB_HINTS: Dict[str, str] = {
    "qtc_interval": "LOINC:8639-2",
    "qt_interval": "LOINC:8638-4",
    "pr_interval": "LOINC:8625-1",
    "ventricular_rate": "LOINC:8867-4",
    "left_ventricular_ef": "LOINC:33878-0",
    "lvef": "LOINC:33878-0",
    "troponin": "LOINC:10839-9",
    "troponin_i": "LOINC:10839-9",
    "bnp": "LOINC:30934-4",
    "egfr": "LOINC:98979-8",
    "haemoglobin": "LOINC:718-7",
    "hemoglobin": "LOINC:718-7",
    "hba1c": "LOINC:4548-4",
    "anaemia": "SNOMED:271737000",
    "anemia": "SNOMED:271737000",
    "diabetes": "SNOMED:73211009",
    "hypertension": "SNOMED:38341003",
    "angina": "SNOMED:194828000",
    "atrial_fibrillation": "SNOMED:49436004",
}


def map_to_omop_domain(category: str, master_col: str) -> str:
    """Map local clinical category/name to an OMOP CDM domain/table hint."""
    category_l = (category or "").strip().lower()
    master_l = (master_col or "").strip().lower()

    if any(tok in master_l for tok in [
        "anaemia", "anemia", "diabetes", "hypertension", "angina",
        "fibrillation", "heart_failure", "stenosis", "regurg",
    ]):
        return "condition_occurrence"
    if any(tok in master_l for tok in ["medication", "drug", "dose", "route"]):
        return "drug_exposure"
    if any(tok in master_l for tok in ["ecg_date", "echo_date", "mri_date", "date_"]):
        return "observation"

    return _OMOP_DOMAIN_BY_CATEGORY.get(category_l, "observation")


def infer_standard_vocab(master_col: str, source_cols: List[str]) -> str:
    """Best-effort lookup for LOINC/SNOMED hints based on column tokens."""
    blob = " ".join([master_col] + [c for c in source_cols if c]).lower()
    for token, code in _VOCAB_HINTS.items():
        if token in blob:
            return code
    return ""


def generate_master_schema(
    accepted_csv: Path,
    output_path: Path,
    all_cols_a: Optional[List[str]] = None,
    all_cols_b: Optional[List[str]] = None,
) -> None:
    """
    Convert matched_pairs_accepted.csv → master_schema.csv.

    One row per accepted pair.
    - master_col:        canonical snake-case name (from name_a, de-duplicated)
    - source_a_cols:     matched BHS column
    - source_b_cols:     matched EHVol column
    - category:          clinical domain (category_a, fallback category_b)
    - final_score:       pipeline confidence score
    - coalesce_strategy: how apply_schema.py should merge the two columns
    - pii_flag:          True when either column contains PII-related tokens

        PII columns are flagged here but NOT removed — apply_schema.py enforces
        the hard drop so every downstream consumer sees the same clean view.

        Coverage rule:
            Every column from dataset A and dataset B must appear at least once in
            master_schema.csv. Columns not mapped by the matching guidelines are
            included as passthrough rows (kept as-is, single-sided source mapping).
    """
    df = pd.read_csv(accepted_csv)
    if df.empty:
        print("[master_schema] No accepted pairs — nothing to write.", file=sys.stderr)
        return

    master_rows = []
    seen_master: set = set()

    for _, row in df.sort_values("final_score", ascending=False).iterrows():
        name_a = str(row["name_a"]).strip()
        name_b = str(row["name_b"]).strip()
        cat_a  = str(row.get("category_a", "unknown")).strip()
        cat_b  = str(row.get("category_b", "unknown")).strip()

        # Canonical name: prefer name_a (BHS is the primary schema)
        base = name_a.lower()
        master_col = base
        suffix = 2
        while master_col in seen_master:
            master_col = f"{base}_{suffix}"
            suffix += 1
        seen_master.add(master_col)

        # Use category_a for strategy; fall back to category_b if unknown
        cat = cat_a if cat_a not in ("", "unknown") else cat_b
        pii = is_pii_column(name_a) or is_pii_column(name_b)
        omop_domain = map_to_omop_domain(cat, master_col)
        standard_vocab = infer_standard_vocab(master_col, [name_a, name_b])

        master_rows.append({
            "master_col":        master_col,
            "source_a_cols":     name_a,
            "source_b_cols":     name_b,
            "category":          cat,
            "omop_domain":       omop_domain,
            "standard_vocab":    standard_vocab,
            "final_score":       round(float(row.get("final_score", 0.0)), 4),
            "coalesce_strategy": get_default_strategy(cat),
            "pii_flag":          pii,
        })

    used_a = {str(r["source_a_cols"]).strip() for r in master_rows if str(r["source_a_cols"]).strip()}
    used_b = {str(r["source_b_cols"]).strip() for r in master_rows if str(r["source_b_cols"]).strip()}

    if all_cols_a is None or all_cols_b is None:
        try:
            df_a_all, _ = load_dataframe(BHS_CSV)
            df_b_all, _ = load_dataframe(EHVOL_CSV)
            all_cols_a = list(df_a_all.columns)
            all_cols_b = list(df_b_all.columns)
        except Exception:
            all_cols_a = all_cols_a or []
            all_cols_b = all_cols_b or []

    def _append_passthrough(col: str, source_side: str) -> None:
        base = col.lower().strip()
        master_col = base
        suffix = 2
        while master_col in seen_master:
            master_col = f"{base}_{suffix}"
            suffix += 1
        seen_master.add(master_col)

        category = _col_category(col)
        omop_domain = map_to_omop_domain(category, master_col)
        standard_vocab = infer_standard_vocab(master_col, [col])
        row = {
            "master_col":        master_col,
            "source_a_cols":     col if source_side == "a" else "",
            "source_b_cols":     col if source_side == "b" else "",
            "category":          category,
            "omop_domain":       omop_domain,
            "standard_vocab":    standard_vocab,
            "final_score":       0.0,
            "coalesce_strategy": get_default_strategy(category),
            "pii_flag":          is_pii_column(col),
        }
        master_rows.append(row)

    # Passthrough columns: first handle exact-name matches between the two
    # unmatched pools as paired rows, then add remaining single-sided passthroughs.
    leftover_a = [col for col in (all_cols_a or []) if col and col not in used_a]
    leftover_b = [col for col in (all_cols_b or []) if col and col not in used_b]
    leftover_b_set = set(leftover_b)

    for col in leftover_a:
        if col in leftover_b_set:
            # Same column name exists unmatched in both datasets — pair them.
            base = col.lower().strip()
            master_col = base
            suffix = 2
            while master_col in seen_master:
                master_col = f"{base}_{suffix}"
                suffix += 1
            seen_master.add(master_col)

            category = _col_category(col)
            pii = is_pii_column(col)
            master_rows.append({
                "master_col":        master_col,
                "source_a_cols":     col,
                "source_b_cols":     col,
                "category":          category,
                "omop_domain":       map_to_omop_domain(category, master_col),
                "standard_vocab":    infer_standard_vocab(master_col, [col]),
                "final_score":       1.0,   # exact name match — perfect confidence
                "coalesce_strategy": get_default_strategy(category),
                "pii_flag":          pii,
            })
            used_b.add(col)   # mark so the B pass below skips it
        else:
            _append_passthrough(col, "a")

    for col in leftover_b:
        if col and col not in used_b:
            _append_passthrough(col, "b")

    schema_df = pd.DataFrame(master_rows).sort_values(
        ["category", "master_col"], key=lambda s: s.str.lower()
    )
    schema_df.to_csv(output_path, index=False)
    pii_count = int(schema_df["pii_flag"].sum())
    print(
        f"[master_schema] {len(schema_df)} master columns "
        f"({pii_count} PII-flagged, {len(schema_df) - pii_count} clinical) "
        f"→ {output_path}"
    )


# ---------------------------------------------------------------------------
# Auto-threshold tuning
# ---------------------------------------------------------------------------

def auto_tune_threshold(
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    names_a: List[str],
    names_b: List[str],
    use_sapbert: bool = False,
    weights: Optional[Dict[str, float]] = None,
    cat_threshold: float = 0.30,
    n_boot: int = 0,
    gold_path: Optional[Path] = None,
) -> float:
    """
    Binary search for the Stage 1 threshold that maximises F1 on a gold label set.

    Gold labels file: outputs/gold_labels.csv
      Columns: name_a, name_b, label   (label: 1 = true match, 0 = false positive)

    If the file doesn't exist, writes a seed annotation CSV of top-20 accepts +
    10 mid-score pairs and prints instructions, then exits with code 0.
    """
    if gold_path is None:
        gold_path = OUTPUTS / "gold_labels.csv"

    if not gold_path.exists():
        print("\n[auto-threshold] 'gold_labels.csv' not found – generating seed file …")
        seed_cands = stage1_candidates(
            names_a, names_b, threshold=0.35, top_k=5, use_sapbert=use_sapbert
        )
        seed_sorted = sorted(seed_cands, key=lambda x: -x[2])
        high = seed_sorted[:20]
        mid  = [c for c in seed_sorted if 0.40 <= c[2] <= 0.58][:10]
        seed = {(a, b): s for a, b, s in high + mid}  # deduplicate
        with gold_path.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["name_a", "name_b", "name_score", "label"])
            for (a, b), s in seed.items():
                w.writerow([a, b, round(s, 4), ""])
        print(f"[auto-threshold] Wrote {len(seed)} pairs → {gold_path}")
        print("[auto-threshold] Fill in the 'label' column (1 = true match, 0 = false positive)")
        print("[auto-threshold] Then re-run with --auto-threshold.")
        sys.exit(0)

    gold_df = pd.read_csv(gold_path)
    labelled = gold_df[gold_df["label"].notna() & (gold_df["label"].astype(str) != "")]
    gold_pairs: Dict[Tuple[str, str], int] = {
        (r["name_a"], r["name_b"]): int(float(r["label"]))
        for _, r in labelled.iterrows()
    }
    if len(gold_pairs) < 5:
        print(f"[auto-threshold] Need ≥ 5 labelled rows in {gold_path}. Got {len(gold_pairs)}.")
        sys.exit(1)
    n_pos = sum(gold_pairs.values())
    print(f"[auto-threshold] Gold set: {len(gold_pairs)} pairs  "
          f"({n_pos} positive, {len(gold_pairs) - n_pos} negative)")

    thresholds = [round(t / 100, 2) for t in range(25, 71, 5)]
    best_thresh, best_f1 = thresholds[0], -1.0
    print(f"{'Thresh':>8}  {'TP':>4}  {'FP':>4}  {'FN':>4}  {'Prec':>6}  {'Rec':>6}  {'F1':>6}")
    for thresh in thresholds:
        cands = stage1_candidates(
            names_a, names_b, threshold=thresh, top_k=5, use_sapbert=use_sapbert
        )
        validated = stage2_validate(
            cands, df_a, df_b,
            weights=weights, cat_threshold=cat_threshold, n_boot=n_boot,
        )
        accepted_set = {(r["name_a"], r["name_b"]) for r in validated if r["verdict"] == "ACCEPTED"}
        tp = sum(1 for (a, b), lbl in gold_pairs.items() if lbl == 1 and (a, b) in accepted_set)
        fp = sum(1 for (a, b), lbl in gold_pairs.items() if lbl == 0 and (a, b) in accepted_set)
        fn = sum(1 for (a, b), lbl in gold_pairs.items() if lbl == 1 and (a, b) not in accepted_set)
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec  = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1   = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
        print(f"  {thresh:.2f}   {tp:>4}  {fp:>4}  {fn:>4}  {prec:>6.3f}  {rec:>6.3f}  {f1:>6.3f}")
        if f1 > best_f1:
            best_f1, best_thresh = f1, thresh

    print(f"\n[auto-threshold] Best threshold = {best_thresh:.2f}  (F1 = {best_f1:.3f})")
    return best_thresh


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Two-stage clinical column matcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--threshold", type=float, default=0.35,
                        help="Stage 1 cosine similarity threshold (default 0.35)")
    parser.add_argument("--top-k", type=int, default=5,
                        help="Max candidates per column in Stage 1 (default 5)")
    parser.add_argument("--no-sapbert", action="store_true",
                        help="Skip SapBERT and use TF-IDF only")
    parser.add_argument(
        "--weights",
        type=str,
        default=None,
        help=(
            "Comma-separated key:value pairs overriding score weights. "
            "Keys: name, range, cat, type. Values must sum to 1.0. "
            "E.g. --weights name:0.6,range:0.3,cat:0.05,type:0.05"
        ),
    )
    parser.add_argument(
        "--cat-threshold",
        type=float,
        default=0.30,
        help="Min categorical/binary value Jaccard to accept a pair (default 0.30)",
    )
    parser.add_argument(
        "--n-boot",
        type=int,
        default=100,
        help="Bootstrap iterations for numeric CI (default 100; 0 to disable)",
    )
    parser.add_argument(
        "--min-final-score",
        type=float,
        default=0.50,
        help="Minimum final composite score to accept a pair (default 0.50)",
    )
    parser.add_argument(
        "--auto-threshold",
        action="store_true",
        help=(
            "Binary-search for the best Stage 1 threshold using outputs/gold_labels.csv. "
            "If the file does not exist, generates a seed annotation CSV and exits."
        ),
    )
    args = parser.parse_args()

    # ---- Parse custom weights ----
    weights = dict(_DEFAULT_WEIGHTS)
    if args.weights:
        try:
            for part in args.weights.split(","):
                k, v = part.strip().split(":")
                weights[k.strip()] = float(v.strip())
            total = sum(weights.values())
            if abs(total - 1.0) > 0.01:
                print(f"WARNING: weights sum to {total:.3f}, not 1.0", file=sys.stderr)
        except Exception as e:
            print(f"ERROR parsing --weights: {e}", file=sys.stderr)
            sys.exit(1)
    print(f"Score weights: {weights}")

    OUTPUTS.mkdir(exist_ok=True)

    # ---- Load column name lists ----
    bhs_names = read_list(BHS_ONLY)
    ehvol_names = read_list(EHVOL_ONLY)
    print(f"BHS-only columns: {len(bhs_names)}")
    print(f"EHVol-only columns: {len(ehvol_names)}")

    # ---- Load full DataFrames for data-level checks ----
    print("Loading DataFrames for data-level checks …")
    df_bhs, _map_bhs = load_dataframe(BHS_CSV)
    df_ehvol, _map_ehvol = load_dataframe(EHVOL_CSV)
    print(f"  BHS: {df_bhs.shape}  |  EHVol: {df_ehvol.shape}")

    # Filter to only-columns present in the schema (the unmatched ones)
    # (BHS df may contain ALL columns incl. shared; we only want to match unmatched)
    df_bhs_sub = df_bhs[[c for c in bhs_names if c in df_bhs.columns]]
    df_ehvol_sub = df_ehvol[[c for c in ehvol_names if c in df_ehvol.columns]]
    print(f"  Subset BHS: {df_bhs_sub.shape}  |  Subset EHVol: {df_ehvol_sub.shape}")

    # ---- Auto-threshold tuning (runs then overrides args.threshold) ----
    if args.auto_threshold:
        args.threshold = auto_tune_threshold(
            df_bhs_sub, df_ehvol_sub,
            bhs_names, ehvol_names,
            use_sapbert=not args.no_sapbert,
            weights=weights,
            cat_threshold=args.cat_threshold,
            n_boot=0,   # skip bootstrap during scan for speed
        )
        print(f"[auto-threshold] Using tuned threshold: {args.threshold:.2f}")

    # ---- Stage 1 ----
    print("\n=== Stage 1: Candidate generation ===")
    candidates = stage1_candidates(
        names_a=bhs_names,
        names_b=ehvol_names,
        threshold=args.threshold,
        top_k=args.top_k,
        use_sapbert=not args.no_sapbert,
    )

    # ---- Stage 2 ----
    print("\n=== Stage 2: Validation ===")
    results = stage2_validate(
        candidates,
        df_bhs_sub,
        df_ehvol_sub,
        weights=weights,
        cat_threshold=args.cat_threshold,
        n_boot=args.n_boot,
        min_final_score=args.min_final_score,
    )

    # ---- Summary ----
    accepted = [r for r in results if r["verdict"] == "ACCEPTED"]
    rejected = [r for r in results if r["verdict"] == "REJECTED"]
    reject_reasons: Dict[str, int] = defaultdict(int)
    for r in rejected:
        reject_reasons[r["reject_reason"]] += 1

    print(f"\n  Total candidates:  {len(results)}")
    print(f"  Accepted:          {len(accepted)}")
    print(f"  Rejected:          {len(rejected)}")
    print("  Rejection reasons:")
    for reason, count in sorted(reject_reasons.items(), key=lambda x: -x[1]):
        print(f"    {reason}: {count}")

    # ---- Write outputs ----
    out_csv = OUTPUTS / "matched_pairs_validated.csv"
    fieldnames = [
        "name_a", "category_a", "name_b", "category_b", "name_score",
        "type_a", "type_b", "type_compat",
        "range_score", "range_ci_low", "range_ci_high",
        "cat_overlap",
        "final_score", "verdict", "reject_reason",
    ]
    with out_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in sorted(results, key=lambda x: -x["final_score"]):
            w.writerow(r)

    # accepted-only CSV mirrors the original format + new diagnostic columns
    # Summarise accepted pairs by category pair for reporting
    from collections import Counter
    cat_counts: Counter = Counter(
        (r["category_a"], r["category_b"]) for r in accepted
    )
    category_summary = [
        {"category_a": ca, "category_b": cb, "count": cnt}
        for (ca, cb), cnt in cat_counts.most_common()
    ]

    out_accepted = OUTPUTS / "matched_pairs_accepted.csv"
    with out_accepted.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name_a", "category_a", "name_b", "category_b",
                    "name_score", "type_a", "type_b",
                    "range_score", "range_ci_low", "range_ci_high",
                    "cat_overlap", "final_score"])
        for r in sorted(accepted, key=lambda x: -x["final_score"]):
            w.writerow([
                r["name_a"], r["category_a"], r["name_b"], r["category_b"],
                r["name_score"], r["type_a"], r["type_b"],
                r["range_score"], r["range_ci_low"], r["range_ci_high"],
                r["cat_overlap"], r["final_score"],
            ])

    # Category breakdown summary
    print("\n  Category-pair breakdown (top-10):")
    for entry in category_summary[:10]:
        print(f"    {entry['category_a']:12} ↔ {entry['category_b']:12}: {entry['count']}")

    # ---- Generate master schema ----
    out_master = OUTPUTS / "master_schema.csv"
    generate_master_schema(
        out_accepted,
        output_path=out_master,
        all_cols_a=list(df_bhs.columns),
        all_cols_b=list(df_ehvol.columns),
    )

    report = {
        "total_candidates": len(results),
        "accepted": len(accepted),
        "rejected": len(rejected),
        "rejection_reasons": dict(reject_reasons),
        "stage1_threshold": args.threshold,
        "top_k": args.top_k,
        "score_weights": weights,
        "cat_threshold": args.cat_threshold,
        "n_boot": args.n_boot,
        "min_final_score": args.min_final_score,
        "category_summary": category_summary,
        "top_accepted": [
            {k: r[k] for k in ("name_a", "category_a", "name_b", "category_b",
                                "name_score", "type_a", "type_b",
                                "range_score", "range_ci_low", "range_ci_high",
                                "cat_overlap", "final_score")}
            for r in sorted(accepted, key=lambda x: -x["final_score"])[:30]
        ],
    }
    out_report = OUTPUTS / "match_validation_report.json"
    with out_report.open("w") as f:
        json.dump(report, f, indent=2)

    print(f"\nWrote:")
    print(f"  {out_csv}")
    print(f"  {out_accepted}")
    print(f"  {out_master}")
    print(f"  {out_report}")


if __name__ == "__main__":
    main()
