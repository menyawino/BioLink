"""
Agent Swarm Validation for Step 6 v2 Fuzzy Matching Output.

Checks:
1. No false positives (esna→qena, non-egyptian→egyptian)
2. Known high-frequency values are matched
3. Column classification is correct
4. Confidence scores are reasonable
5. No duplicate canonical mappings for same raw value in same column
"""

import csv
from pathlib import Path


def load_suggestions(dataset: str):
    path = Path(f"{dataset}_step_6_fuzzy_suggestions.csv")
    with open(path) as f:
        return list(csv.DictReader(f))


def validate_no_false_positives(records):
    """Check for known false positive patterns."""
    issues = []
    for r in records:
        raw = r["raw_value"].strip().lower()
        canon = r["canonical_value"].strip().lower()
        if not canon:
            continue

        # Negation false positive
        if raw.startswith("non-") and not canon.startswith("non-"):
            issues.append(f"NEGATION_FP: '{r['raw_value']}' -> '{r['canonical_value']}' in {r['column_name']}")

        # Esna -> Qena (the original bug)
        if raw == "esna" and canon == "qena":
            issues.append(f"ESNA_QENA: '{r['raw_value']}' -> '{r['canonical_value']}'")

        # Aswan should map to aswan
        if raw == "aswan" and canon != "aswan":
            issues.append(f"ASWAN_MISMATCH: '{r['raw_value']}' -> '{r['canonical_value']}'")

        # Cairo should map to cairo
        if raw == "cairo" and canon != "cairo":
            issues.append(f"CAIRO_MISMATCH: '{r['raw_value']}' -> '{r['canonical_value']}'")

    return issues


def validate_high_frequency_matches(records):
    """Check that high-frequency values are matched."""
    issues = []
    high_freq_threshold = 50

    for r in records:
        count = int(r["occurrence_count"])
        canon = r["canonical_value"].strip()
        if count >= high_freq_threshold and not canon:
            issues.append(f"HIGH_FREQ_UNMATCHED: '{r['raw_value']}' (n={count}) in {r['column_name']}")

    return issues


def validate_column_classification(records):
    """Check that nationality values are in nationality columns and city values in city columns."""
    issues = []
    nationality_values = {"egyptian", "non-egyptian", "sudanese", "turkish", "saudi", "libyan",
                          "emirati", "jordanian", "palestinian", "syrian", "lebanese", "iraqi",
                          "kenuzi", "fedutchi", "arab"}
    city_columns = ["if mother is egyptian, please specify city",
                    "if father is egyptian, please specify city",
                    "if mother is egyptian, please specify city/",
                    "mother's gov of origin", "father's gov of origin"]

    for r in records:
        raw = r["raw_value"].strip().lower()
        col = r["column_name"].strip().lower()
        canon = r["canonical_value"].strip().lower()

        if not canon:
            continue

        # Nationality value in city column
        if raw in nationality_values and any(c in col for c in city_columns):
            issues.append(f"NAT_IN_CITY_COL: '{r['raw_value']}' in {r['column_name']}")

    return issues


def validate_confidence_scores(records):
    """Check that confidence scores are consistent with match types."""
    issues = []
    for r in records:
        match_type = r["match_type"]
        score = float(r["similarity_score"])
        action = r["suggested_action"]

        if match_type == "alias_exact" and score < 1.0:
            issues.append(f"LOW_EXACT_SCORE: '{r['raw_value']}' score={score}")

        if action == "auto_accept" and score < 0.95:
            issues.append(f"LOW_AUTO_ACCEPT: '{r['raw_value']}' score={score}")

    return issues


def validate_no_duplicate_mappings(records):
    """Check that same raw value in same column doesn't map to multiple canonicals."""
    issues = []
    mappings = {}
    for r in records:
        key = (r["dataset"], r["column_name"], r["raw_value"])
        canon = r["canonical_value"]
        if key in mappings:
            if mappings[key] != canon:
                issues.append(f"DUPLICATE_MAP: {key} -> '{mappings[key]}' and '{canon}'")
        else:
            mappings[key] = canon
    return issues


def main():
    all_issues = []
    all_records = []

    for dataset in ["BHS", "EHVol"]:
        records = load_suggestions(dataset)
        all_records.extend(records)

        print(f"\n{'='*60}")
        print(f"Validating {dataset}: {len(records)} records")
        print(f"{'='*60}")

        checks = [
            ("False Positives", validate_no_false_positives),
            ("High-Frequency Unmatched", validate_high_frequency_matches),
            ("Column Classification", validate_column_classification),
            ("Confidence Scores", validate_confidence_scores),
            ("Duplicate Mappings", validate_no_duplicate_mappings),
        ]

        for name, check_fn in checks:
            issues = check_fn(records)
            status = "PASS" if not issues else f"FAIL ({len(issues)} issues)"
            print(f"  {name}: {status}")
            for issue in issues[:5]:
                print(f"    - {issue}")
            if len(issues) > 5:
                print(f"    ... and {len(issues) - 5} more")
            all_issues.extend(issues)

    print(f"\n{'='*60}")
    print(f"OVERALL: {len(all_issues)} issues found across {len(all_records)} records")
    if not all_issues:
        print("ALL VALIDATIONS PASSED")
    else:
        print(f"FAILURE RATE: {len(all_issues)/len(all_records)*100:.2f}%")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
