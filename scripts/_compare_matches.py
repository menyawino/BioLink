#!/usr/bin/env python3
"""Compare original naive match against the new validated output."""
import csv
from pathlib import Path

OUTPUTS = Path(__file__).parent.parent / "outputs"

orig = {}
for r in csv.DictReader(open(OUTPUTS / "llm_matched_pairs.csv")):
    key = (min(r["name_a"], r["name_b"]), max(r["name_a"], r["name_b"]))
    orig[key] = float(r["score"])

new_all = list(csv.DictReader(open(OUTPUTS / "matched_pairs_validated.csv")))

new_acc = {}
new_rej = {}
for r in new_all:
    key = (min(r["name_a"], r["name_b"]), max(r["name_a"], r["name_b"]))
    if r["verdict"] == "ACCEPTED":
        new_acc[key] = float(r["final_score"])
    else:
        new_rej[key] = r["reject_reason"]

# Pairs in original that are now rejected (false positives caught)
caught = [(k, orig[k], new_rej[k]) for k in orig if k in new_rej]
print("=== Originally matched but NOW REJECTED (false positives caught):")
for k, os, rr in sorted(caught, key=lambda x: -x[1]):
    print(f"  {k[0]:<40} <-> {k[1]:<40}  (orig={os:.3f}, reason: {rr})")

# New pairs discovered that were missing from original
new_only = set(new_acc) - set(orig)
print(f"\n=== New pairs found (not in original): {len(new_only)}")
for k in sorted(new_only, key=lambda x: -new_acc[x])[:20]:
    print(f"  {k[0]:<40} <-> {k[1]:<40}  (final={new_acc[k]:.4f})")

print()
print("Summary:")
print(f"  Original pairs:              {len(orig)}")
print(f"  New accepted:                {len(new_acc)}")
print(f"  New rejected:                {len(new_rej)}")
print(f"  Old false positives caught:  {len(caught)}")
print(f"  New pairs discovered:        {len(new_only)}")
