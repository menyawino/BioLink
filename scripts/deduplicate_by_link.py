#!/usr/bin/env python3
"""
Create a deduplicated unified registry by computing a stable pseudonymous
`link_id` per raw record (from a dataset-specific ID column) and coalescing
rows with the same `link_id`.

Usage:
  python scripts/deduplicate_by_link.py outputs/master_schema.csv db/BHS_Full.csv db/EHVol_Full.csv

The script writes `outputs/unified_registry_dedup.csv` and prints counts.
"""
from __future__ import annotations
import hashlib
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

# Ensure repo root is on sys.path when running as a script
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.apply_schema import _load_csv, process_dataset


def find_id_column(cols: list[str]) -> Optional[str]:
    candidates = [
        'record id', 'record_id', 'mrn', 'dna id', 'dna_id', 'participant id',
        "participant's name", 'participant_name', 'id', 'national id', 'national_id'
    ]
    lower = {c.lower(): c for c in cols}
    for cand in candidates:
        if cand in lower:
            return lower[cand]
    return None


def make_link_id(series: pd.Series) -> pd.Series:
    s = series.fillna('').astype(str)
    return s.apply(lambda v: hashlib.sha256(v.encode('utf-8')).hexdigest())


def first_non_null(s: pd.Series):
    v = s.dropna()
    if v.empty:
        return np.nan
    return v.iloc[0]


def main():
    if len(sys.argv) < 3:
        print("Usage: deduplicate_by_link.py <master_schema.csv> <dataset1.csv> [dataset2.csv ...]")
        sys.exit(2)

    schema = pd.read_csv(sys.argv[1])
    datasets = sys.argv[2:]

    parts = []
    link_counts = {}
    for i, ds in enumerate(datasets):
        p = Path(ds)
        if not p.exists():
            print(f"Skipping missing dataset: {p}")
            continue
        raw = _load_csv(p)
        id_col = find_id_column(list(raw.columns))
        if id_col is None:
            print(f"No ID column found in {p.name}; skipping dedup for this cohort.")
            continue
        link = make_link_id(raw[id_col])
        cohort_label = f'D{i+1}'
        cohort_slice = process_dataset(raw, schema, cohort_label=cohort_label)
        cohort_slice = cohort_slice.copy()
        cohort_slice['link_id'] = link.values
        parts.append(cohort_slice)
        link_counts[cohort_label] = cohort_slice['link_id'].nunique()

    if not parts:
        print('No cohorts processed — aborting.')
        sys.exit(1)

    unified = pd.concat(parts, ignore_index=True)

    before = len(unified)
    # Group by link_id and coalesce by first non-null across rows
    grouped = unified.groupby('link_id', dropna=False).agg(lambda col: first_non_null(col))
    # restore cohort column as the concatenation of cohorts present
    grouped['cohort'] = unified.groupby('link_id')['cohort'].agg(lambda s: ','.join(sorted(set(s))))
    grouped = grouped.reset_index(drop=True)

    out = Path('outputs/unified_registry_dedup.csv')
    out.parent.mkdir(exist_ok=True, parents=True)
    grouped.to_csv(out, index=False)

    print(f"Rows before dedup: {before}")
    print(f"Rows after dedup:  {len(grouped)}")
    print('Unique links per cohort:')
    for k,v in link_counts.items():
        print(f'  {k}: {v}')
    print('Saved →', out)


if __name__ == '__main__':
    main()
