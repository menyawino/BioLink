#!/usr/bin/env python3
"""
BERT-based semantic column matching between BHS and EHVol.
Uses sentence-transformers (all-mpnet-base-v2) for embedding
and cosine similarity for ranking.
"""

import csv
import json
from pathlib import Path
from collections import defaultdict

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

# ---------------------------------------------------------------------------
# 1. CONFIGURATION
# ---------------------------------------------------------------------------
MODEL_NAME = "NeuML/pubmedbert-base-embeddings"
SIMILARITY_THRESHOLD = 0.65  # Minimum cosine similarity to report
TOP_K = 3  # Top matches per column

# ---------------------------------------------------------------------------
# 2. LOAD DATA
# ---------------------------------------------------------------------------
print(f"Loading {MODEL_NAME}...")
model = SentenceTransformer(MODEL_NAME)

bhs_cols = []
ehvol_cols = []

with open("BHS_column_classification.csv") as f:
    for row in csv.DictReader(f):
        bhs_cols.append(row)

with open("EHVol_column_classification.csv") as f:
    for row in csv.DictReader(f):
        ehvol_cols.append(row)

print(f"BHS columns: {len(bhs_cols)}")
print(f"EHVol columns: {len(ehvol_cols)}")

# ---------------------------------------------------------------------------
# 3. GROUP BY BROAD CATEGORY
# ---------------------------------------------------------------------------
bhs_by_cat = defaultdict(list)
ehvol_by_cat = defaultdict(list)

for c in bhs_cols:
    bhs_by_cat[c["broad_category"]].append(c)
for c in ehvol_cols:
    ehvol_by_cat[c["broad_category"]].append(c)

shared_categories = sorted(set(bhs_by_cat.keys()) & set(ehvol_by_cat.keys()))
print(f"\nShared broad categories: {len(shared_categories)}")
for cat in shared_categories:
    print(f"  {cat}: BHS={len(bhs_by_cat[cat])}, EHVol={len(ehvol_by_cat[cat])}")

# ---------------------------------------------------------------------------
# 4. COMPUTE SEMANTIC SIMILARITY PER CATEGORY
# ---------------------------------------------------------------------------
all_matches = []

for cat in shared_categories:
    bhs_list = bhs_by_cat[cat]
    ehvol_list = ehvol_by_cat[cat]
    
    if len(bhs_list) == 0 or len(ehvol_list) == 0:
        continue
    
    bhs_names = [c["column_name"] for c in bhs_list]
    ehvol_names = [c["column_name"] for c in ehvol_list]
    
    # Encode
    bhs_embeddings = model.encode(bhs_names, convert_to_numpy=True, show_progress_bar=False)
    ehvol_embeddings = model.encode(ehvol_names, convert_to_numpy=True, show_progress_bar=False)
    
    # Cosine similarity matrix: (n_bhs, n_ehvol)
    sim_matrix = cosine_similarity(bhs_embeddings, ehvol_embeddings)
    
    # Find matches above threshold
    for i, bhs_col in enumerate(bhs_list):
        for j, ehvol_col in enumerate(ehvol_list):
            sim = float(sim_matrix[i, j])
            if sim >= SIMILARITY_THRESHOLD:
                all_matches.append({
                    "category": cat,
                    "bhs_column": bhs_col["column_name"],
                    "bhs_normalized": bhs_col.get("normalized", ""),
                    "ehvol_column": ehvol_col["column_name"],
                    "ehvol_normalized": ehvol_col.get("normalized", ""),
                    "similarity": round(sim, 4),
                })

# Sort by similarity descending
all_matches.sort(key=lambda x: -x["similarity"])

print(f"\nTotal matches above threshold {SIMILARITY_THRESHOLD}: {len(all_matches)}")

# ---------------------------------------------------------------------------
# 5. DEDUPLICATE: KEEP BEST MATCH PER COLUMN PAIR
# ---------------------------------------------------------------------------
seen_pairs = set()
deduped = []
for m in all_matches:
    pair = (m["bhs_column"], m["ehvol_column"])
    if pair not in seen_pairs:
        seen_pairs.add(pair)
        deduped.append(m)

print(f"After deduplication: {len(deduped)}")

# ---------------------------------------------------------------------------
# 6. CATEGORIZE BY SIMILARITY TIER
# ---------------------------------------------------------------------------
tier_high = [m for m in deduped if m["similarity"] >= 0.80]
tier_medium = [m for m in deduped if 0.70 <= m["similarity"] < 0.80]
tier_low = [m for m in deduped if 0.65 <= m["similarity"] < 0.70]

print(f"\nHigh confidence (>=0.80): {len(tier_high)}")
print(f"Medium confidence (0.70-0.79): {len(tier_medium)}")
print(f"Low confidence (0.65-0.69): {len(tier_low)}")

# ---------------------------------------------------------------------------
# 7. PRINT TOP MATCHES
# ---------------------------------------------------------------------------
print("\n" + "=" * 90)
print("TOP 30 MATCHES (ALL TIERS)")
print("=" * 90)

for m in deduped[:30]:
    tier = "HIGH" if m["similarity"] >= 0.80 else ("MED" if m["similarity"] >= 0.70 else "LOW")
    print(f"\n[{tier}] {m['category']} | sim={m['similarity']}")
    print(f"  BHS:   '{m['bhs_column']}'")
    print(f"  EHVol: '{m['ehvol_column']}'")

# ---------------------------------------------------------------------------
# 8. COMPARE WITH EXACT NORMALIZED MATCHES
# ---------------------------------------------------------------------------
print("\n" + "=" * 90)
print("COMPARISON WITH EXACT NORMALIZED MATCHES")
print("=" * 90)

# Load exact matches from step_7
with open("step_7/unification_audit.json") as f:
    audit = json.load(f)
exact_shared = set(audit["concepts"]["shared_list"])

# How many BERT matches are NOT in exact matches?
bert_concepts_bhs = {m["bhs_column"] for m in deduped}
bert_concepts_ehvol = {m["ehvol_column"] for m in deduped}

# Check overlap with exact normalized matches
# We need to re-normalize to compare
import re

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

def normalize(col_name):
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
    return "_".join(filtered) if filtered else "unnamed"

# Find BERT matches that are NEW (not in exact shared)
new_matches = []
already_matched = []

for m in deduped:
    b_norm = normalize(m["bhs_column"])
    e_norm = normalize(m["ehvol_column"])
    if b_norm == e_norm:
        already_matched.append(m)
    else:
        new_matches.append(m)

print(f"\nBERT matches already found by exact normalization: {len(already_matched)}")
print(f"BERT matches that are NEW: {len(new_matches)}")

print("\n" + "=" * 90)
print("NEW MATCHES DISCOVERED BY BERT (not found by exact normalization)")
print("=" * 90)

for m in new_matches[:30]:
    tier = "HIGH" if m["similarity"] >= 0.80 else ("MED" if m["similarity"] >= 0.70 else "LOW")
    print(f"\n[{tier}] {m['category']} | sim={m['similarity']}")
    print(f"  BHS:   '{m['bhs_column']}' -> {normalize(m['bhs_column'])}")
    print(f"  EHVol: '{m['ehvol_column']}' -> {normalize(m['ehvol_column'])}")

# ---------------------------------------------------------------------------
# 9. SAVE RESULTS
# ---------------------------------------------------------------------------
with open("bert_column_matches.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "category", "bhs_column", "bhs_normalized", "ehvol_column",
        "ehvol_normalized", "similarity", "is_new_match"
    ])
    writer.writeheader()
    for m in deduped:
        b_norm = normalize(m["bhs_column"])
        e_norm = normalize(m["ehvol_column"])
        writer.writerow({
            **m,
            "is_new_match": "no" if b_norm == e_norm else "yes"
        })

print(f"\n\nFull BERT matching report saved to: bert_column_matches.csv ({len(deduped)} rows)")
print(f"  - Already matched by exact normalization: {len(already_matched)}")
print(f"  - New matches discovered by BERT: {len(new_matches)}")
