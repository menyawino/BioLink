#!/usr/bin/env python3
"""Objective column matching analysis between BHS and EHVol."""

import csv
import re
from collections import defaultdict

# ---------------------------------------------------------------------------
# 1. NORMALIZATION (same as step_7)
# ---------------------------------------------------------------------------
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
    name = col_name.lower().strip()
    for pattern in UNIT_SUFFIXES:
        name = re.sub(pattern, "", name, flags=re.IGNORECASE)
    name = re.sub(r"[?*!.,;:]+$", "", name).strip()
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
    tokens = re.findall(r"[a-z0-9_\-]+", name)
    filtered = [t for t in tokens if t not in STOP_WORDS and len(t) > 1]
    if not filtered:
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
# 2. LOAD CLASSIFICATIONS
# ---------------------------------------------------------------------------
bhs_cols = []
ehvol_cols = []

with open("BHS_column_classification.csv") as f:
    for row in csv.DictReader(f):
        bhs_cols.append(row)

with open("EHVol_column_classification.csv") as f:
    for row in csv.DictReader(f):
        ehvol_cols.append(row)

for c in bhs_cols:
    c["normalized"] = normalize_concept_name(c["column_name"])
for c in ehvol_cols:
    c["normalized"] = normalize_concept_name(c["column_name"])

print(f"BHS columns: {len(bhs_cols)}")
print(f"EHVol columns: {len(ehvol_cols)}")

# ---------------------------------------------------------------------------
# 3. EXACT NORMALIZED MATCHES
# ---------------------------------------------------------------------------
bhs_norms = {c["normalized"] for c in bhs_cols}
ehvol_norms = {c["normalized"] for c in ehvol_cols}
shared = bhs_norms & ehvol_norms

print(f"\nExact normalized matches: {len(shared)}")
print(f"BHS unique normalized: {len(bhs_norms)}")
print(f"EHVol unique normalized: {len(ehvol_norms)}")

# ---------------------------------------------------------------------------
# 4. NEAR MISSES (same broad_category, token overlap >= 50%)
# ---------------------------------------------------------------------------
print("\n" + "=" * 80)
print("NEAR MISSES (same broad_category, token overlap >= 50%)")
print("=" * 80)

near_misses = []
for bc in bhs_cols:
    for ec in ehvol_cols:
        if bc["broad_category"] != ec["broad_category"]:
            continue
        if bc["normalized"] == ec["normalized"]:
            continue

        bt = set(bc["normalized"].split("_"))
        et = set(ec["normalized"].split("_"))
        if not bt or not et:
            continue
        overlap = len(bt & et) / max(len(bt), len(et))
        if overlap >= 0.5:
            near_misses.append({
                "bhs_name": bc["column_name"],
                "bhs_norm": bc["normalized"],
                "ehvol_name": ec["column_name"],
                "ehvol_norm": ec["normalized"],
                "category": bc["broad_category"],
                "overlap": overlap,
            })

near_misses.sort(key=lambda x: -x["overlap"])

for nm in near_misses[:50]:
    print(f"\n[{nm['category']}]")
    print(f"  BHS:   '{nm['bhs_name']}' -> {nm['bhs_norm']}")
    print(f"  EHVol: '{nm['ehvol_name']}' -> {nm['ehvol_norm']}")
    print(f"  Overlap: {nm['overlap']:.2f}")

print(f"\n\nTotal near-misses found: {len(near_misses)}")

# ---------------------------------------------------------------------------
# 5. SEMANTIC EQUIVALENCE BY CATEGORY
# ---------------------------------------------------------------------------
print("\n" + "=" * 80)
print("CATEGORY-BY-CATEGORY POTENTIAL MATCHES")
print("=" * 80)

# Group by category
bhs_by_cat = defaultdict(list)
ehvol_by_cat = defaultdict(list)
for c in bhs_cols:
    bhs_by_cat[c["broad_category"]].append(c)
for c in ehvol_cols:
    ehvol_by_cat[c["broad_category"]].append(c)

for cat in sorted(set(bhs_by_cat.keys()) & set(ehvol_by_cat.keys())):
    bhs_norms_cat = {c["normalized"] for c in bhs_by_cat[cat]}
    ehvol_norms_cat = {c["normalized"] for c in ehvol_by_cat[cat]}
    shared_cat = bhs_norms_cat & ehvol_norms_cat
    
    print(f"\n{cat}:")
    print(f"  BHS: {len(bhs_by_cat[cat])} cols, EHVol: {len(ehvol_by_cat[cat])} cols")
    print(f"  Exact matches: {len(shared_cat)}")
    
    # Find near misses in this category
    cat_misses = [nm for nm in near_misses if nm["category"] == cat]
    print(f"  Near misses (>=50% overlap): {len(cat_misses)}")
    if cat_misses:
        print("  Examples:")
        for nm in cat_misses[:5]:
            print(f"    - '{nm['bhs_name']}'  <->  '{nm['ehvol_name']}'")

# ---------------------------------------------------------------------------
# 6. SAVE FULL NEAR-MISS REPORT
# ---------------------------------------------------------------------------
with open("column_matching_analysis.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "category", "bhs_column", "bhs_normalized", 
        "ehvol_column", "ehvol_normalized", "token_overlap"
    ])
    writer.writeheader()
    for nm in near_misses:
        writer.writerow({
            "category": nm["category"],
            "bhs_column": nm["bhs_name"],
            "bhs_normalized": nm["bhs_norm"],
            "ehvol_column": nm["ehvol_name"],
            "ehvol_normalized": nm["ehvol_norm"],
            "token_overlap": f"{nm['overlap']:.2f}",
        })

print(f"\n\nFull report saved to: column_matching_analysis.csv ({len(near_misses)} rows)")
