import csv
from collections import Counter
from pathlib import Path

from src.pipeline.step_0_column_mapping import normalize
from src.config import DATASETS, INTERIM_DIR as ROOT, REFERENCE_DIR


MAPPING_SUFFIX = "_column_classification.csv"
DEIDENTIFIED_SUFFIX = "_step_1_deidentified.csv"
AUDIT_SUFFIX = "_step_1_retention_audit.csv"

ALWAYS_KEEP_PII_LABELS = {"non_pii", "sensitive_health"}

RETAINED_QUASI_IDENTIFIER_REASONS = {
    "gender": "retain sex/gender for study analysis",
    "nationality": "retain coarse nationality for study analysis",
    "what ethnicity do you consider yourself": "retain ethnicity for study analysis",
    "other ethnicity": "retain ethnicity detail for study analysis",
    "current city of residence": "retain city-level residence data for study analysis",
    "city of residence during childhood": "retain city-level childhood residence data for study analysis",
    "can you speak nubian": "retain language background for study analysis",
    "can you read and write in arabic": "retain literacy background for study analysis",
    "if yes please specify the highest degree obtained": "retain education level for study analysis",
    "what is your occupational status": "retain coarse occupational status for study analysis",
    "marital status": "retain marital status for study analysis",
    "what is your marital status": "retain marital status for study analysis",
}

EXPLICITLY_RETAINED_HEADERS = {
    "dna id": "retain identifier by request",
    "date of birth": "retain birth date as requested",
    "date of enrolment": "retain enrollment date as requested",
    "enrollment date": "retain enrollment date as requested",
    "mrn ahc": "retain identifier by request",
    "mrn bu": "retain identifier by request",
    "non egyptian parents": "retain field by request",
    "fathers city of origin": "retain relative city as requested",
    "city of residence during childhood": "retain childhood city as requested",
    "number of wives": "retain field by request",
    "if more than 1 wife how many": "retain field by request",
    "if mother is egyptian please specify city": "retain relative city as requested",
    "if father is egyptian please specify city": "retain relative city as requested",
    "parents occupation": "retain occupation by request",
    "present or most recent past occupation": "retain occupation by request",
    "rwma index": "retain field by request",
    "other laboratory results to report": "retain field by request",
}

CALCULATABLE_COLUMN_REASONS = {
    "age": "drop calculatable age from retained dates",
    "current age": "drop calculatable age from retained dates",
    "age at enrollment": "drop calculatable age from retained dates",
    "smoking index current": "drop derived smoking metric",
    "smoking index former": "drop derived smoking metric",
}


def mapping_path(dataset: str) -> Path:
    return ROOT / f"{dataset}{MAPPING_SUFFIX}"


def deidentified_output_path(dataset: str) -> Path:
    return ROOT / f"{dataset}{DEIDENTIFIED_SUFFIX}"


def audit_output_path(dataset: str) -> Path:
    return ROOT / f"{dataset}{AUDIT_SUFFIX}"


def ensure_mapping_files() -> None:
    missing = [dataset for dataset in DATASETS if not mapping_path(dataset).exists()]
    if not missing:
        return

    from src.pipeline.step_0_column_mapping import main as step_0_main

    print("Missing mapping files detected; running step_0_column_mapping.py first")
    step_0_main()


def read_mapping_rows(dataset: str) -> list[dict[str, str]]:
    with mapping_path(dataset).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def decide_retention(dataset: str, mapping_row: dict[str, str]) -> tuple[bool, str]:
    pii_label = mapping_row["pii_label"]
    header_norm = normalize(mapping_row["column_name"])

    if header_norm in EXPLICITLY_RETAINED_HEADERS:
        return True, EXPLICITLY_RETAINED_HEADERS[header_norm]

    if header_norm in CALCULATABLE_COLUMN_REASONS:
        return False, CALCULATABLE_COLUMN_REASONS[header_norm]

    if pii_label in ALWAYS_KEEP_PII_LABELS:
        return True, f"keep_{pii_label}"

    if pii_label == "direct_identifier":
        return False, "drop_direct_identifier"

    if pii_label == "quasi_identifier":
        if header_norm in RETAINED_QUASI_IDENTIFIER_REASONS:
            return True, RETAINED_QUASI_IDENTIFIER_REASONS[header_norm]
        return False, "drop_high_risk_or_nonessential_quasi_identifier"

    return False, f"drop_unhandled_pii_label_{pii_label}"


def write_audit(dataset: str, audit_rows: list[dict[str, str]]) -> None:
    with audit_output_path(dataset).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "dataset",
                "column_index",
                "column_name",
                "broad_family",
                "broad_category",
                "pii_label",
                "retention_action",
                "retention_reason",
            ],
        )
        writer.writeheader()
        writer.writerows(audit_rows)


def write_deidentified_dataset(dataset: str, mapping_rows: list[dict[str, str]]) -> tuple[int, int]:
    keep_indices: list[int] = []
    audit_rows: list[dict[str, str]] = []
    kept_counter: Counter[str] = Counter()
    dropped_counter: Counter[str] = Counter()
    dropped_calculatable_columns: list[str] = []

    for mapping_row in mapping_rows:
        keep_column, retention_reason = decide_retention(dataset, mapping_row)
        column_index = int(mapping_row["column_index"])
        pii_label = mapping_row["pii_label"]

        if keep_column:
            keep_indices.append(column_index - 1)
            kept_counter[pii_label] += 1
            retention_action = "keep"
        else:
            dropped_counter[pii_label] += 1
            retention_action = "drop"
            if retention_reason in CALCULATABLE_COLUMN_REASONS.values():
                dropped_calculatable_columns.append(mapping_row["column_name"])

        audit_rows.append(
            {
                "dataset": dataset,
                "column_index": mapping_row["column_index"],
                "column_name": mapping_row["column_name"],
                "broad_family": mapping_row["broad_family"],
                "broad_category": mapping_row["broad_category"],
                "pii_label": pii_label,
                "retention_action": retention_action,
                "retention_reason": retention_reason,
            }
        )

    source_path = DATASETS[dataset]
    output_path = deidentified_output_path(dataset)
    with source_path.open("r", encoding="utf-8", newline="") as source_handle, output_path.open(
        "w", encoding="utf-8", newline=""
    ) as output_handle:
        reader = csv.reader(source_handle)
        writer = csv.writer(output_handle)

        for row in reader:
            writer.writerow([row[index] if index < len(row) else "" for index in keep_indices])

    write_audit(dataset, audit_rows)
    print(
        f"{dataset}: kept {len(keep_indices)} columns, dropped {len(mapping_rows) - len(keep_indices)} columns"
    )
    print(f"  kept by pii_label: {dict(sorted(kept_counter.items()))}")
    print(f"  dropped by pii_label: {dict(sorted(dropped_counter.items()))}")
    if dropped_calculatable_columns:
        print(f"  dropped calculatable columns: {dropped_calculatable_columns}")
    print(f"  deidentified output: {output_path.name}")
    print(f"  retention audit: {audit_output_path(dataset).name}")
    return len(keep_indices), len(mapping_rows) - len(keep_indices)


def main() -> None:
    ensure_mapping_files()
    for dataset in DATASETS:
        mapping_rows = read_mapping_rows(dataset)
        write_deidentified_dataset(dataset, mapping_rows)


if __name__ == "__main__":
    main()