"""
Visualisation helper for matched_pairs_accepted.csv.

Generates:
  outputs/match_heatmap.html  – colour-coded pivot of accepted pairs by category
  outputs/match_scores.html   – ranked bar chart of final_score by column pair

Usage:
  python scripts/_viz_matches.py                  # reads default accepted CSV
  python scripts/_viz_matches.py --csv outputs/matched_pairs_accepted.csv
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    sys.exit("pandas is required: pip install pandas")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
OUTPUTS = Path(__file__).resolve().parent.parent / "outputs"
DEFAULT_CSV = OUTPUTS / "matched_pairs_accepted.csv"


# ---------------------------------------------------------------------------
# Heatmap helper
# ---------------------------------------------------------------------------
def _gradient_bg(val: float, vmax: float) -> str:
    """Linear white → #005f87 fill based on value proportion."""
    if vmax == 0:
        return "background-color:#ffffff"
    ratio = min(val / vmax, 1.0)
    r = int(255 * (1 - ratio * 0.8))
    g = int(255 * (1 - ratio * 0.6))
    b = int(255 * (1 - ratio * 0.4))
    return f"background-color:rgb({r},{g},{b});color:{'#fff' if ratio > 0.5 else '#222'}"


def build_heatmap(df: pd.DataFrame) -> str:
    """Return an HTML table showing accepted-pair counts by (category_a × category_b)."""
    pivot = (
        df.groupby(["category_a", "category_b"])
        .size()
        .reset_index(name="count")
        .pivot(index="category_a", columns="category_b", values="count")
        .fillna(0)
        .astype(int)
    )
    vmax = int(pivot.max().max())
    cats_a = list(pivot.index)
    cats_b = list(pivot.columns)

    rows_html = ""
    for ca in cats_a:
        cells = ""
        for cb in cats_b:
            v = pivot.loc[ca, cb]
            style = _gradient_bg(v, vmax)
            cells += f'<td style="{style};padding:8px 12px;text-align:center">{v if v else ""}</td>'
        rows_html += f"<tr><td style='padding:8px 12px;font-weight:600'>{ca}</td>{cells}</tr>"

    header_cells = "".join(
        f'<th style="padding:8px 12px;text-align:center;background:#005f87;color:#fff">{cb}</th>'
        for cb in cats_b
    )
    return f"""<table border="1" cellspacing="0" style="border-collapse:collapse;font-family:sans-serif;font-size:13px">
  <thead>
    <tr>
      <th style="padding:8px 12px;background:#003e5c;color:#fff">category_a \\ category_b</th>
      {header_cells}
    </tr>
  </thead>
  <tbody>
    {rows_html}
  </tbody>
</table>"""


# ---------------------------------------------------------------------------
# Score bar chart helper
# ---------------------------------------------------------------------------
def build_score_bars(df: pd.DataFrame, top_n: int = 40) -> str:
    """Return an HTML bar chart for the top-N accepted pairs by final_score."""
    top = df.nlargest(top_n, "final_score")
    bar_max = float(top["final_score"].max()) if not top.empty else 1.0
    rows = ""
    for _, r in top.iterrows():
        label = f"{r['name_a']} ↔ {r['name_b']}"
        score = r["final_score"]
        cat_tag = f"[{r['category_a']}]" if r.get("category_a") not in (None, "", "unknown") else ""
        pct = score / bar_max * 100
        rows += (
            f'<tr><td style="padding:3px 8px;font-size:12px;white-space:nowrap">{label} {cat_tag}</td>'
            f'<td style="padding:3px 8px;width:300px">'
            f'<div style="background:#005f87;width:{pct:.1f}%;height:14px;border-radius:2px"></div></td>'
            f'<td style="padding:3px 8px;font-size:12px">{score:.4f}</td></tr>'
        )
    return f"""<table style="font-family:sans-serif;border-collapse:collapse">
  <thead><tr>
    <th style="padding:4px 8px;text-align:left;background:#003e5c;color:#fff">Pair</th>
    <th style="padding:4px 8px;text-align:left;background:#003e5c;color:#fff">Score bar</th>
    <th style="padding:4px 8px;text-align:left;background:#003e5c;color:#fff">Score</th>
  </tr></thead>
  <tbody>{rows}</tbody>
</table>"""


# ---------------------------------------------------------------------------
# Category breakdown table
# ---------------------------------------------------------------------------
def build_category_table(df: pd.DataFrame) -> str:
    """Tabulate accepted pair counts per (category_a, category_b) pair, sorted descending."""
    counts = (
        df.groupby(["category_a", "category_b"])
        .agg(count=("final_score", "size"), mean_score=("final_score", "mean"))
        .reset_index()
        .sort_values("count", ascending=False)
    )
    rows = ""
    for _, r in counts.iterrows():
        rows += (
            f"<tr><td style='padding:5px 10px'>{r['category_a']}</td>"
            f"<td style='padding:5px 10px'>{r['category_b']}</td>"
            f"<td style='padding:5px 10px;text-align:center'>{r['count']}</td>"
            f"<td style='padding:5px 10px;text-align:center'>{r['mean_score']:.3f}</td></tr>"
        )
    return f"""<table border="1" cellspacing="0" style="border-collapse:collapse;font-family:sans-serif;font-size:13px">
  <thead><tr style="background:#005f87;color:#fff">
    <th style="padding:6px 10px">Category A</th>
    <th style="padding:6px 10px">Category B</th>
    <th style="padding:6px 10px">Pairs</th>
    <th style="padding:6px 10px">Mean Score</th>
  </tr></thead>
  <tbody>{rows}</tbody>
</table>"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Visualise matched_pairs_accepted.csv")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV,
                        help=f"Path to accepted pairs CSV (default: {DEFAULT_CSV})")
    parser.add_argument("--top", type=int, default=40,
                        help="Number of top pairs in score bar chart (default 40)")
    args = parser.parse_args()

    if not args.csv.exists():
        sys.exit(f"File not found: {args.csv}\nRun two_stage_match.py first.")

    df = pd.read_csv(args.csv)

    # Ensure category columns exist (backwards compat with pre-v3 CSVs)
    if "category_a" not in df.columns:
        df["category_a"] = "unknown"
    if "category_b" not in df.columns:
        df["category_b"] = "unknown"

    # Convert final_score to float (may be string from csv.writer)
    df["final_score"] = pd.to_numeric(df["final_score"], errors="coerce").fillna(0.0)

    heatmap_html    = build_heatmap(df)
    score_bar_html  = build_score_bars(df, top_n=args.top)
    cat_table_html  = build_category_table(df)

    accepted_count = len(df)
    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>BioLink Column Match Report</title>
  <style>
    body  {{ font-family: sans-serif; margin: 32px; background: #f8f9fa; color: #222; }}
    h1   {{ color: #003e5c; }}
    h2   {{ color: #005f87; margin-top: 40px; border-bottom: 2px solid #005f87; padding-bottom: 4px; }}
    p    {{ max-width: 720px; }}
  </style>
</head>
<body>
  <h1>BioLink Column Match Report</h1>
  <p>
    Two-stage pipeline result: <strong>{accepted_count} accepted pairs</strong>
    (BHS × EHVol, TF-IDF + data validation, v3).
  </p>

  <h2>1. Accepted Pairs by Category (heatmap)</h2>
  <p>Cell value = number of accepted column pairs between the two clinical domains.</p>
  {heatmap_html}

  <h2>2. Category-Pair Breakdown</h2>
  {cat_table_html}

  <h2>3. Top-{args.top} Accepted Pairs by Final Score</h2>
  {score_bar_html}
</body>
</html>"""

    out_html = OUTPUTS / "match_heatmap.html"
    out_html.write_text(page, encoding="utf-8")
    print(f"Wrote: {out_html}")


if __name__ == "__main__":
    main()
