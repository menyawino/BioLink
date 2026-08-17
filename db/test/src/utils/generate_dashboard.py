#!/usr/bin/env python3
"""
Pipeline Visualization Dashboard
Generates a comprehensive multi-panel figure summarizing the entire
BHS + EHVol data-cleaning and unification pipeline.
"""

import json
import csv
import os
from pathlib import Path
from collections import Counter

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import seaborn as sns

# ---------------------------------------------------------------------------
# 1. CONFIGURATION
# ---------------------------------------------------------------------------
OUTPUT_DIR = Path("step_7")
FIGURE_PATH = Path("pipeline_dashboard.png")
DPI = 150

# Colour palette
COL_BHS = "#2E86AB"      # deep blue
COL_EHVOL = "#A23B72"    # magenta
COL_SHARED = "#F18F01"   # amber
COL_NEUTRAL = "#C73E1D"  # red-orange
COL_OK = "#3B1F2B"       # dark plum
COLS = [COL_BHS, COL_EHVOL, COL_SHARED, COL_NEUTRAL, COL_OK]

sns.set_style("whitegrid")
plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["font.size"] = 9

# ---------------------------------------------------------------------------
# 2. LOAD DATA
# ---------------------------------------------------------------------------
print("Loading pipeline outputs...")

# Audit JSON
with open(OUTPUT_DIR / "unification_audit.json") as f:
    audit = json.load(f)

# Column mapping
column_mapping = pd.read_csv(OUTPUT_DIR / "column_mapping.csv")

# Unit mapping
unit_mapping = pd.read_csv(OUTPUT_DIR / "unit_mapping.csv")

# Value set mapping
value_set_mapping = pd.read_csv(OUTPUT_DIR / "value_set_mapping.csv")

# Modality manifest
modality_manifest = pd.read_csv(OUTPUT_DIR / "modality_manifest.csv")

# Medications
medications = pd.read_csv(OUTPUT_DIR / "medications_long.csv")

# Family history
family_history = pd.read_csv(OUTPUT_DIR / "family_history_long.csv")

# Step 2 validation findings
step2_findings = []
if Path("step_2_reduction_audit.csv").exists():
    with open("step_2_reduction_audit.csv") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("validation_findings"):
                step2_findings.append(row)

# Step 4 quarantined
step4_quarantined = []
if Path("step_4_quarantined_values.csv").exists():
    with open("step_4_quarantined_values.csv") as f:
        reader = csv.DictReader(f)
        step4_quarantined = list(reader)

# Step 5 unit suggestions
step5_suggestions = []
if Path("step_5_unit_suggestions.csv").exists():
    with open("step_5_unit_suggestions.csv") as f:
        reader = csv.DictReader(f)
        step5_suggestions = list(reader)

# Step 6 fuzzy matches
step6_matches = []
if Path("step_6_fuzzy_matches.csv").exists():
    with open("step_6_fuzzy_matches.csv") as f:
        reader = csv.DictReader(f)
        step6_matches = list(reader)

# ---------------------------------------------------------------------------
# 3. DERIVED METRICS
# ---------------------------------------------------------------------------
bhs_rows = audit["datasets"]["BHS"]["rows"]
ehvol_rows = audit["datasets"]["EHVol"]["rows"]
bhs_cols = audit["datasets"]["BHS"]["columns"]
ehvol_cols = audit["datasets"]["EHVol"]["columns"]

total_concepts = audit["concepts"]["total"]
shared_concepts = audit["concepts"]["shared"]
bhs_only = audit["concepts"]["bhs_only"]
ehvol_only = audit["concepts"]["ehvol_only"]

# Modality distribution
modality_counts = modality_manifest.groupby(["dataset", "modality"]).size().unstack(fill_value=0)

# Broad family distribution
broad_family_counts = column_mapping.groupby(["dataset", "broad_family"]).size().unstack(fill_value=0)

# Medication categories
med_categories = medications["category"].value_counts().head(10) if "category" in medications.columns else pd.Series()

# Family history events
fh_events = family_history["event"].value_counts().head(10) if "event" in family_history.columns else pd.Series()

# Step 2 validation by dataset
step2_by_dataset = Counter()
for row in step2_findings:
    step2_by_dataset[row.get("dataset", "unknown")] += 1

# Step 4 quarantine by concept
step4_by_concept = Counter()
for row in step4_quarantined:
    step4_by_concept[row.get("concept", "unknown")] += 1

# Step 5 suggestions by concept
step5_by_concept = Counter()
for row in step5_suggestions:
    step5_by_concept[row.get("concept", "unknown")] += 1

# Step 6 fuzzy match confidence
step6_confidence = Counter()
for row in step6_matches:
    step6_confidence[row.get("match_type", "unknown")] += 1

# ---------------------------------------------------------------------------
# 4. BUILD FIGURE
# ---------------------------------------------------------------------------
fig = plt.figure(figsize=(20, 24))
gs = GridSpec(5, 3, figure=fig, hspace=0.35, wspace=0.3)

# ------------------------------------------------------------------
# Panel 1: Title & Overview (spans top row)
# ------------------------------------------------------------------
ax_title = fig.add_subplot(gs[0, :])
ax_title.axis("off")

title_text = (
    "BHS + EHVol Data Pipeline Dashboard\n"
    "Cross-Dataset Unification & Quality Assurance Summary"
)
ax_title.text(0.5, 0.85, title_text, ha="center", va="top", fontsize=20, fontweight="bold")

# Key metrics boxes
metrics = [
    ("BHS Participants", f"{bhs_rows:,}", COL_BHS),
    ("EHVol Participants", f"{ehvol_rows:,}", COL_EHVOL),
    ("Total Concepts", f"{total_concepts}", COL_SHARED),
    ("Shared Concepts", f"{shared_concepts}", "#2ECC71"),
    ("Medication Records", f"{len(medications):,}", COL_NEUTRAL),
    ("Family History Records", f"{len(family_history):,}", COL_OK),
]

for i, (label, value, color) in enumerate(metrics):
    x = 0.08 + i * 0.15
    rect = mpatches.FancyBboxPatch((x, 0.15), 0.12, 0.45, boxstyle="round,pad=0.02",
                                    facecolor=color, alpha=0.15, edgecolor=color, linewidth=2)
    ax_title.add_patch(rect)
    ax_title.text(x + 0.06, 0.45, value, ha="center", va="center", fontsize=16, fontweight="bold", color=color)
    ax_title.text(x + 0.06, 0.25, label, ha="center", va="center", fontsize=9, color="#333")

# ------------------------------------------------------------------
# Panel 2: Dataset Size Comparison
# ------------------------------------------------------------------
ax1 = fig.add_subplot(gs[1, 0])
categories = ["Participants", "Columns"]
bhs_vals = [bhs_rows, bhs_cols]
ehvol_vals = [ehvol_rows, ehvol_cols]

x = np.arange(len(categories))
width = 0.35
bars1 = ax1.bar(x - width/2, bhs_vals, width, label="BHS", color=COL_BHS, alpha=0.85)
bars2 = ax1.bar(x + width/2, ehvol_vals, width, label="EHVol", color=COL_EHVOL, alpha=0.85)

ax1.set_ylabel("Count")
ax1.set_title("Dataset Scale Comparison", fontweight="bold", fontsize=11)
ax1.set_xticks(x)
ax1.set_xticklabels(categories)
ax1.legend()
ax1.set_yscale("log")
ax1.grid(axis="y", alpha=0.3)

# Add value labels
for bar in bars1:
    h = bar.get_height()
    ax1.annotate(f"{h:,}", xy=(bar.get_x() + bar.get_width()/2, h),
                 xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=8)
for bar in bars2:
    h = bar.get_height()
    ax1.annotate(f"{h:,}", xy=(bar.get_x() + bar.get_width()/2, h),
                 xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=8)

# ------------------------------------------------------------------
# Panel 3: Concept Overlap (Venn-style bar)
# ------------------------------------------------------------------
ax2 = fig.add_subplot(gs[1, 1])
overlap_data = [bhs_only, shared_concepts, ehvol_only]
overlap_labels = [f"BHS Only\n({bhs_only})", f"Shared\n({shared_concepts})", f"EHVol Only\n({ehvol_only})"]
colors_overlap = [COL_BHS, COL_SHARED, COL_EHVOL]

bars = ax2.bar(overlap_labels, overlap_data, color=colors_overlap, alpha=0.85, edgecolor="white", linewidth=2)
ax2.set_ylabel("Number of Concepts")
ax2.set_title("Concept Overlap Across Datasets", fontweight="bold", fontsize=11)
ax2.grid(axis="y", alpha=0.3)

for bar in bars:
    h = bar.get_height()
    ax2.annotate(f"{h}", xy=(bar.get_x() + bar.get_width()/2, h),
                 xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=10, fontweight="bold")

# ------------------------------------------------------------------
# Panel 4: Modality Distribution
# ------------------------------------------------------------------
ax3 = fig.add_subplot(gs[1, 2])
if not modality_manifest.empty:
    mod_counts = modality_manifest["modality"].value_counts().head(8)
    colors_mod = plt.cm.Spectral(np.linspace(0.1, 0.9, len(mod_counts)))
    wedges, texts, autotexts = ax3.pie(mod_counts.values, labels=mod_counts.index, autopct="%1.1f%%",
                                        colors=colors_mod, startangle=90, pctdistance=0.75)
    for t in texts:
        t.set_fontsize(8)
    for t in autotexts:
        t.set_fontsize(7)
    ax3.set_title("Modality Distribution\n(All Columns)", fontweight="bold", fontsize=11)
else:
    ax3.text(0.5, 0.5, "No modality data", ha="center", va="center", transform=ax3.transAxes)
    ax3.set_title("Modality Distribution", fontweight="bold", fontsize=11)

# ------------------------------------------------------------------
# Panel 5: Broad Family Distribution (stacked bar)
# ------------------------------------------------------------------
ax4 = fig.add_subplot(gs[2, 0])
if not broad_family_counts.empty:
    broad_family_counts.T.plot(kind="barh", stacked=True, ax=ax4, color=[COL_BHS, COL_EHVOL], alpha=0.85)
    ax4.set_xlabel("Number of Columns")
    ax4.set_title("Columns by Broad Family", fontweight="bold", fontsize=11)
    ax4.legend(title="Dataset", loc="lower right")
    ax4.grid(axis="x", alpha=0.3)
else:
    ax4.text(0.5, 0.5, "No broad family data", ha="center", va="center", transform=ax4.transAxes)

# ------------------------------------------------------------------
# Panel 6: Medication Categories (Top 10)
# ------------------------------------------------------------------
ax5 = fig.add_subplot(gs[2, 1])
if not med_categories.empty:
    med_categories.plot(kind="barh", ax=ax5, color=COL_NEUTRAL, alpha=0.85)
    ax5.set_xlabel("Number of Prescriptions")
    ax5.set_title("Top Medication Categories", fontweight="bold", fontsize=11)
    ax5.grid(axis="x", alpha=0.3)
    ax5.invert_yaxis()
else:
    ax5.text(0.5, 0.5, "No medication data", ha="center", va="center", transform=ax5.transAxes)

# ------------------------------------------------------------------
# Panel 7: Family History Events (Top 10)
# ------------------------------------------------------------------
ax6 = fig.add_subplot(gs[2, 2])
if not fh_events.empty:
    fh_events.plot(kind="barh", ax=ax6, color=COL_OK, alpha=0.85)
    ax6.set_xlabel("Number of Records")
    ax6.set_title("Top Family History Events", fontweight="bold", fontsize=11)
    ax6.grid(axis="x", alpha=0.3)
    ax6.invert_yaxis()
else:
    ax6.text(0.5, 0.5, "No family history data", ha="center", va="center", transform=ax6.transAxes)

# ------------------------------------------------------------------
# Panel 8: Pipeline Step Summary (horizontal timeline)
# ------------------------------------------------------------------
ax7 = fig.add_subplot(gs[3, :])

steps = [
    ("Step 0", "Column Mapping", "Mapped 549 raw columns to canonical names", "#3498DB"),
    ("Step 1", "PII Removal", "De-identified direct identifiers, retained quasi-identifiers", "#9B59B6"),
    ("Step 2", "Sparse Reduction + Validation", f"Found {len(step2_findings):,} validation issues (unrealistic dates, orphans, contradictions)", "#E74C3C"),
    ("Step 3", "Normalization Profiling", "Generated per-column value distributions and examples", "#F39C12"),
    ("Step 4", "Range Rules + Quarantine", f"Quarantined {len(step4_quarantined):,} out-of-range values", "#E67E22"),
    ("Step 5", "Unit Extraction", f"Suggested canonical units for {len(step5_suggestions):,} values", "#1ABC9C"),
    ("Step 6", "Fuzzy Matching", f"Matched {len(step6_matches):,} geographic/nationality values to canonical forms", "#2ECC71"),
    ("Step 7", "Cross-Dataset Unification", f"Unified into {total_concepts} concepts, {shared_concepts} shared", COL_SHARED),
]

y_positions = np.arange(len(steps))
for i, (step_num, step_name, desc, color) in enumerate(steps):
    ax7.barh(i, 1, color=color, alpha=0.2, height=0.6)
    ax7.barh(i, 0.05, color=color, alpha=0.9, height=0.6)
    ax7.text(0.02, i, f"{step_num}: {step_name}", va="center", ha="left", fontsize=10, fontweight="bold")
    ax7.text(0.25, i, desc, va="center", ha="left", fontsize=9, color="#444")

ax7.set_xlim(0, 1)
ax7.set_ylim(-0.5, len(steps) - 0.5)
ax7.set_yticks([])
ax7.set_xticks([])
ax7.set_title("Pipeline Execution Summary", fontweight="bold", fontsize=12, pad=10)
ax7.spines["top"].set_visible(False)
ax7.spines["right"].set_visible(False)
ax7.spines["bottom"].set_visible(False)
ax7.spines["left"].set_visible(False)

# ------------------------------------------------------------------
# Panel 9: Data Quality Findings (Step 2 breakdown)
# ------------------------------------------------------------------
ax8 = fig.add_subplot(gs[4, 0])
if step2_by_dataset:
    labels_s2 = list(step2_by_dataset.keys())
    values_s2 = list(step2_by_dataset.values())
    colors_s2 = [COL_BHS if "BHS" in l else COL_EHVOL for l in labels_s2]
    ax8.bar(labels_s2, values_s2, color=colors_s2, alpha=0.85)
    ax8.set_ylabel("Number of Findings")
    ax8.set_title("Step 2: Validation Findings", fontweight="bold", fontsize=11)
    ax8.grid(axis="y", alpha=0.3)
    for i, v in enumerate(values_s2):
        ax8.text(i, v + max(values_s2)*0.01, f"{v:,}", ha="center", va="bottom", fontsize=9, fontweight="bold")
else:
    ax8.text(0.5, 0.5, "No Step 2 audit data", ha="center", va="center", transform=ax8.transAxes)

# ------------------------------------------------------------------
# Panel 10: Step 4 Quarantine by Concept (Top 10)
# ------------------------------------------------------------------
ax9 = fig.add_subplot(gs[4, 1])
if step4_by_concept:
    top_quarantine = pd.Series(step4_by_concept).sort_values(ascending=False).head(10)
    top_quarantine.plot(kind="barh", ax=ax9, color=COL_NEUTRAL, alpha=0.85)
    ax9.set_xlabel("Quarantined Values")
    ax9.set_title("Step 4: Top Quarantined Concepts", fontweight="bold", fontsize=11)
    ax9.grid(axis="x", alpha=0.3)
    ax9.invert_yaxis()
else:
    ax9.text(0.5, 0.5, "No quarantine data", ha="center", va="center", transform=ax9.transAxes)

# ------------------------------------------------------------------
# Panel 11: Step 5 + Step 6 Summary
# ------------------------------------------------------------------
ax10 = fig.add_subplot(gs[4, 2])
quality_metrics = {
    "Unit Suggestions": len(step5_suggestions),
    "Fuzzy Matches": len(step6_matches),
    "Quarantined": len(step4_quarantined),
    "Validations": len(step2_findings),
}
if any(quality_metrics.values()):
    colors_qm = ["#1ABC9C", "#2ECC71", COL_NEUTRAL, "#E74C3C"]
    bars = ax10.bar(quality_metrics.keys(), quality_metrics.values(), color=colors_qm, alpha=0.85)
    ax10.set_ylabel("Count")
    ax10.set_title("Quality Assurance Actions", fontweight="bold", fontsize=11)
    ax10.grid(axis="y", alpha=0.3)
    for bar in bars:
        h = bar.get_height()
        if h > 0:
            ax10.annotate(f"{h:,}", xy=(bar.get_x() + bar.get_width()/2, h),
                          xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=9, fontweight="bold")
    plt.setp(ax10.xaxis.get_majorticklabels(), rotation=30, ha="right")
else:
    ax10.text(0.5, 0.5, "No quality data", ha="center", va="center", transform=ax10.transAxes)

# ------------------------------------------------------------------
# Save
# ------------------------------------------------------------------
plt.savefig(FIGURE_PATH, dpi=DPI, bbox_inches="tight", facecolor="white")
plt.close()

print(f"\nDashboard saved to: {FIGURE_PATH.resolve()}")
print(f"Figure size: 20 x 24 inches at {DPI} DPI")
