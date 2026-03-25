#!/usr/bin/env python3
"""
Cohort Comparability Analysis

Runs pre-pooling comparability analyses between cohorts in the unified
registry. Must be run AFTER apply_schema.py produces the harmonized data.

Analyses performed
------------------
1. **Measurement distributions** — per-variable KS test, effect sizes (Cohen's d
   for numeric, Cramér's V for categorical), and distribution summary statistics.
2. **Missingness comparison** — per-variable missingness rates by cohort, with
   chi-squared test for differential missingness.
3. **Protocol differences** — documents mean enrollment date, age distribution,
   gender balance, and sample size per cohort.

Outputs
-------
  outputs/comparability_report.json — full structured report
  stdout — human-readable summary

Usage
-----
  python pipeline/cohort_comparability.py \\
      --registry outputs/unified_registry.csv \\
      --tiers outputs/harmonization_tiers.csv
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

try:
    import pandas as pd
    import numpy as np
    from scipy import stats
except ImportError:
    sys.exit("Required: pip install pandas numpy scipy")


def _cohens_d(a: np.ndarray, b: np.ndarray) -> float:
    """Compute Cohen's d for two arrays (handles unequal sizes)."""
    na, nb = len(a), len(b)
    if na < 2 or nb < 2:
        return float("nan")
    mean_a, mean_b = np.mean(a), np.mean(b)
    # Pooled std
    var_a, var_b = np.var(a, ddof=1), np.var(b, ddof=1)
    pooled_std = np.sqrt(((na - 1) * var_a + (nb - 1) * var_b) / (na + nb - 2))
    if pooled_std == 0:
        return 0.0
    return float((mean_a - mean_b) / pooled_std)


def _cramers_v(x: pd.Series, y: pd.Series) -> float:
    """Compute Cramér's V for two categorical series."""
    ct = pd.crosstab(x, y)
    if ct.size == 0:
        return float("nan")
    n = ct.sum().sum()
    if n == 0:
        return float("nan")
    chi2 = stats.chi2_contingency(ct)[0]
    min_dim = min(ct.shape[0], ct.shape[1]) - 1
    if min_dim == 0:
        return 0.0
    return float(np.sqrt(chi2 / (n * min_dim)))


def analyze_numeric_variable(
    df: pd.DataFrame, col: str, cohort_col: str = "cohort"
) -> Dict[str, Any]:
    """Compare a numeric variable across cohorts."""
    result: Dict[str, Any] = {"variable": col, "type": "numeric", "cohorts": {}}

    cohorts = sorted(df[cohort_col].dropna().unique())
    arrays = {}
    for c in cohorts:
        vals = pd.to_numeric(df.loc[df[cohort_col] == c, col], errors="coerce").dropna()
        arrays[c] = vals.values
        result["cohorts"][c] = {
            "n": int(len(vals)),
            "mean": float(vals.mean()) if len(vals) > 0 else None,
            "std": float(vals.std()) if len(vals) > 1 else None,
            "median": float(vals.median()) if len(vals) > 0 else None,
            "q25": float(np.percentile(vals, 25)) if len(vals) > 0 else None,
            "q75": float(np.percentile(vals, 75)) if len(vals) > 0 else None,
            "min": float(vals.min()) if len(vals) > 0 else None,
            "max": float(vals.max()) if len(vals) > 0 else None,
        }

    # Pairwise tests (for 2 cohorts, just one pair)
    result["pairwise"] = []
    cohort_list = list(arrays.keys())
    for i in range(len(cohort_list)):
        for j in range(i + 1, len(cohort_list)):
            ca, cb = cohort_list[i], cohort_list[j]
            a, b = arrays[ca], arrays[cb]
            pair: Dict[str, Any] = {"cohort_a": ca, "cohort_b": cb}
            if len(a) >= 2 and len(b) >= 2:
                ks_stat, ks_p = stats.ks_2samp(a, b)
                pair["ks_statistic"] = float(ks_stat)
                pair["ks_pvalue"] = float(ks_p)
                pair["cohens_d"] = _cohens_d(a, b)
                pair["interpretation"] = _interpret_effect_size(abs(pair["cohens_d"]))
            else:
                pair["ks_statistic"] = None
                pair["ks_pvalue"] = None
                pair["cohens_d"] = None
                pair["interpretation"] = "insufficient_data"
            result["pairwise"].append(pair)

    return result


def analyze_categorical_variable(
    df: pd.DataFrame, col: str, cohort_col: str = "cohort"
) -> Dict[str, Any]:
    """Compare a categorical variable across cohorts."""
    result: Dict[str, Any] = {"variable": col, "type": "categorical", "cohorts": {}}

    cohorts = sorted(df[cohort_col].dropna().unique())
    for c in cohorts:
        vals = df.loc[df[cohort_col] == c, col].dropna()
        vc = vals.value_counts().to_dict()
        result["cohorts"][c] = {
            "n": int(len(vals)),
            "value_counts": {str(k): int(v) for k, v in vc.items()},
        }

    # Chi-squared test on cross-tab
    valid = df[[cohort_col, col]].dropna()
    if len(valid) > 0 and valid[cohort_col].nunique() >= 2:
        ct = pd.crosstab(valid[col], valid[cohort_col])
        if ct.size > 0 and ct.shape[0] > 1:
            chi2, p, dof, _ = stats.chi2_contingency(ct)
            result["chi2_statistic"] = float(chi2)
            result["chi2_pvalue"] = float(p)
            result["cramers_v"] = _cramers_v(valid[col], valid[cohort_col])
        else:
            result["chi2_statistic"] = None
            result["chi2_pvalue"] = None
            result["cramers_v"] = None
    else:
        result["chi2_statistic"] = None
        result["chi2_pvalue"] = None
        result["cramers_v"] = None

    return result


def analyze_missingness(
    df: pd.DataFrame, clinical_cols: List[str], cohort_col: str = "cohort"
) -> Dict[str, Any]:
    """Compare missingness patterns across cohorts."""
    cohorts = sorted(df[cohort_col].dropna().unique())
    result: Dict[str, Any] = {"per_variable": [], "summary": {}}

    for col in clinical_cols:
        entry: Dict[str, Any] = {"variable": col, "cohorts": {}}
        total_filled = []
        for c in cohorts:
            subset = df.loc[df[cohort_col] == c, col]
            n_total = len(subset)
            n_missing = int(subset.isna().sum())
            n_filled = n_total - n_missing
            miss_rate = n_missing / n_total if n_total > 0 else 1.0
            entry["cohorts"][c] = {
                "n_total": n_total,
                "n_missing": n_missing,
                "missing_rate": round(miss_rate, 4),
            }
            total_filled.append(n_filled)

        # Chi-squared test for differential missingness
        if len(cohorts) == 2:
            # 2x2: [filled, missing] x [cohort1, cohort2]
            c1, c2 = cohorts
            d1 = entry["cohorts"][c1]
            d2 = entry["cohorts"][c2]
            observed = np.array([
                [d1["n_total"] - d1["n_missing"], d1["n_missing"]],
                [d2["n_total"] - d2["n_missing"], d2["n_missing"]],
            ])
            if observed.min() >= 0 and observed.sum() > 0:
                try:
                    chi2, p, _, _ = stats.chi2_contingency(observed)
                    entry["missingness_chi2"] = float(chi2)
                    entry["missingness_pvalue"] = float(p)
                except ValueError:
                    entry["missingness_chi2"] = None
                    entry["missingness_pvalue"] = None
            else:
                entry["missingness_chi2"] = None
                entry["missingness_pvalue"] = None
        else:
            entry["missingness_chi2"] = None
            entry["missingness_pvalue"] = None

        result["per_variable"].append(entry)

    # Overall missingness summary per cohort
    for c in cohorts:
        subset = df[df[cohort_col] == c][clinical_cols]
        overall_rate = float(subset.isna().mean().mean())
        result["summary"][c] = {
            "overall_missing_rate": round(overall_rate, 4),
            "n_rows": int(len(subset)),
            "n_cols_with_data": int((subset.notna().any()).sum()),
        }

    return result


def analyze_protocol_context(
    df: pd.DataFrame, cohort_col: str = "cohort"
) -> Dict[str, Any]:
    """Document protocol-level differences between cohorts."""
    cohorts = sorted(df[cohort_col].dropna().unique())
    result: Dict[str, Any] = {"cohorts": {}}

    for c in cohorts:
        sub = df[df[cohort_col] == c]
        info: Dict[str, Any] = {"n_participants": int(len(sub))}

        # Age distribution
        for age_col in ("age", "age_at_enrollment", "current_age"):
            if age_col in sub.columns:
                ages = pd.to_numeric(sub[age_col], errors="coerce").dropna()
                if len(ages) > 0:
                    info["age_mean"] = round(float(ages.mean()), 1)
                    info["age_std"] = round(float(ages.std()), 1)
                    info["age_range"] = [float(ages.min()), float(ages.max())]
                    info["age_column_used"] = age_col
                    break

        # Gender distribution
        for gender_col in ("gender", "gender_2"):
            if gender_col in sub.columns:
                g = sub[gender_col].dropna()
                if len(g) > 0:
                    info["gender_distribution"] = g.value_counts().to_dict()
                    info["gender_column_used"] = gender_col
                    break

        # Enrollment date range
        for date_col in ("enrollment_date", "date_of_enrolment", "date"):
            if date_col in sub.columns:
                dates = pd.to_datetime(sub[date_col], errors="coerce").dropna()
                if len(dates) > 0:
                    info["enrollment_start"] = str(dates.min().date())
                    info["enrollment_end"] = str(dates.max().date())
                    info["enrollment_date_column_used"] = date_col
                    break

        result["cohorts"][c] = info

    return result


def _interpret_effect_size(d: float) -> str:
    if np.isnan(d):
        return "unknown"
    if d < 0.2:
        return "negligible"
    if d < 0.5:
        return "small"
    if d < 0.8:
        return "medium"
    return "large"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Cohort comparability analysis for BioLink unified registry",
    )
    parser.add_argument(
        "--registry", default="outputs/unified_registry.csv",
        help="Path to unified_registry.csv (from apply_schema.py)",
    )
    parser.add_argument(
        "--tiers", default="outputs/harmonization_tiers.csv",
        help="Path to harmonization_tiers.csv (from apply_schema.py)",
    )
    parser.add_argument(
        "--output", "-o", default="outputs/comparability_report.json",
        help="Output path for comparability report JSON",
    )
    parser.add_argument(
        "--top-n", type=int, default=50,
        help="Analyze the top-N variables by fill rate (default: 50)",
    )
    args = parser.parse_args()

    reg_path = Path(args.registry)
    if not reg_path.exists():
        sys.exit(f"Registry not found: {reg_path}\nRun apply_schema.py first.")

    print("Loading unified registry …")
    df = pd.read_csv(reg_path, dtype=str, low_memory=False)
    print(f"  {len(df):,} rows × {len(df.columns)} columns")

    if "cohort" not in df.columns:
        sys.exit("No 'cohort' column found — cannot compare cohorts.")

    clinical_cols = [c for c in df.columns if c != "cohort"]

    # Load tiers if available
    tiers_info = {}
    tiers_path = Path(args.tiers)
    if tiers_path.exists():
        tdf = pd.read_csv(tiers_path)
        for _, tr in tdf.iterrows():
            tiers_info[tr["master_col"]] = {
                "tier": tr.get("tier", "schema_aligned"),
                "data_type": tr.get("data_type", "string"),
                "unit": tr.get("unit", ""),
            }

    # Select top-N variables by fill rate for detailed analysis
    fill_rates = df[clinical_cols].notna().mean().sort_values(ascending=False)
    top_cols = list(fill_rates.head(args.top_n).index)
    print(f"  Analyzing top {len(top_cols)} variables by fill rate …")

    report: Dict[str, Any] = {
        "metadata": {
            "registry_path": str(reg_path),
            "n_rows": len(df),
            "n_cohorts": int(df["cohort"].nunique()),
            "cohort_labels": sorted(df["cohort"].unique().tolist()),
            "n_clinical_cols": len(clinical_cols),
            "n_analyzed": len(top_cols),
        },
        "protocol_context": analyze_protocol_context(df),
        "distributions": [],
        "missingness": analyze_missingness(df, clinical_cols),
    }

    # Distribution analysis
    print("\n  Distribution analysis:")
    for col in top_cols:
        tier_entry = tiers_info.get(col, {})
        dtype = tier_entry.get("data_type", "string")

        if dtype in ("numeric",):
            result = analyze_numeric_variable(df, col)
        elif dtype in ("categorical", "boolean"):
            result = analyze_categorical_variable(df, col)
        else:
            # Try numeric first, fall back to categorical
            numeric_series = pd.to_numeric(df[col], errors="coerce")
            if numeric_series.notna().sum() > numeric_series.isna().sum():
                result = analyze_numeric_variable(df, col)
            else:
                result = analyze_categorical_variable(df, col)

        result["tier"] = tier_entry.get("tier", "schema_aligned")
        result["unit"] = tier_entry.get("unit", "")
        report["distributions"].append(result)

    # Save report
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    # ---- Print summary ----
    print(f"\nComparability report → {out_path}")
    print(f"\n{'='*60}")
    print("COHORT COMPARABILITY SUMMARY")
    print(f"{'='*60}")

    # Protocol context
    ctx = report["protocol_context"]
    for c, info in ctx["cohorts"].items():
        print(f"\n  Cohort {c}: {info['n_participants']} participants")
        if "age_mean" in info:
            print(f"    Age: {info['age_mean']} ± {info['age_std']} "
                  f"(range: {info['age_range'][0]}-{info['age_range'][1]})")
        if "gender_distribution" in info:
            g = info["gender_distribution"]
            print(f"    Gender: {g}")
        if "enrollment_start" in info:
            print(f"    Enrollment: {info['enrollment_start']} to {info['enrollment_end']}")

    # Flag large effect sizes
    print(f"\n  Variables with LARGE effect size (|d| >= 0.8):")
    large_effects = []
    for dist in report["distributions"]:
        for pw in dist.get("pairwise", []):
            if pw.get("interpretation") == "large":
                large_effects.append((dist["variable"], pw.get("cohens_d", 0)))
    if large_effects:
        for var, d in sorted(large_effects, key=lambda x: abs(x[1]), reverse=True)[:15]:
            print(f"    {var}: d={d:.2f}")
    else:
        print("    (none)")

    # Differential missingness
    print(f"\n  Variables with significant differential missingness (p < 0.01):")
    diff_miss = []
    for entry in report["missingness"]["per_variable"]:
        p = entry.get("missingness_pvalue")
        if p is not None and p < 0.01:
            rates = {c: entry["cohorts"][c]["missing_rate"] for c in entry["cohorts"]}
            diff = max(rates.values()) - min(rates.values())
            if diff > 0.1:  # only flag >10% difference
                diff_miss.append((entry["variable"], diff, p))
    if diff_miss:
        for var, diff, p in sorted(diff_miss, key=lambda x: x[1], reverse=True)[:15]:
            print(f"    {var}: Δ={diff:.1%}  p={p:.2e}")
    else:
        print("    (none)")

    print(f"\n{'='*60}")


if __name__ == "__main__":
    main()
