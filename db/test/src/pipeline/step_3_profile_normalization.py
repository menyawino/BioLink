import csv
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

from src.pipeline.step_0_column_mapping import normalize
from src.config import DATASETS, INTERIM_DIR as ROOT, REFERENCE_DIR


STEP_2_SUFFIX = "_step_2_reduced.csv"
STEP_3_PROFILE_SUFFIX = "_step_3_normalization_profile.csv"
STEP_3_EXAMPLES_SUFFIX = "_step_3_value_examples.csv"
MAX_EXAMPLES_PER_COLUMN = 20

BOOLEAN_TRUE_VALUES = {"yes", "true", "checked", "positive", "present", "1", "y"}
BOOLEAN_FALSE_VALUES = {"no", "false", "unchecked", "negative", "absent", "0", "n"}
BOOLEAN_VALUES = BOOLEAN_TRUE_VALUES | BOOLEAN_FALSE_VALUES
DATE_FORMATS = (
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%Y-%m-%d",
    "%d-%m-%Y",
    "%m-%d-%Y",
    "%d/%m/%y",
    "%m/%d/%y",
)
INTEGER_PATTERN = re.compile(r"^[+-]?\d+$")
DECIMAL_PATTERN = re.compile(r"^[+-]?\d+(?:\.\d+)?$")


def step_2_input_path(dataset: str) -> Path:
    return ROOT / f"{dataset}{STEP_2_SUFFIX}"


def step_3_profile_path(dataset: str) -> Path:
    return ROOT / f"{dataset}{STEP_3_PROFILE_SUFFIX}"


def step_3_examples_path(dataset: str) -> Path:
    return ROOT / f"{dataset}{STEP_3_EXAMPLES_SUFFIX}"


def ensure_step_2_artifacts() -> None:
    missing = [dataset for dataset in DATASETS if not step_2_input_path(dataset).exists()]
    if not missing:
        return

    from src.pipeline.step_2_reduce_sparse_columns import main as step_2_main

    print("Missing step-2 artifacts detected; running step_2_reduce_sparse_columns.py first")
    step_2_main()


def read_step_2_dataset(dataset: str) -> tuple[list[str], list[list[str]]]:
    with step_2_input_path(dataset).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        rows = list(reader)

    if not rows:
        raise ValueError(f"{step_2_input_path(dataset).name} is empty")

    return rows[0], rows[1:]


def nonempty_values(data_rows: list[list[str]], column_index: int) -> list[str]:
    values = []
    for row in data_rows:
        if column_index >= len(row):
            continue
        value = row[column_index].strip()
        if value:
            values.append(value)
    return values


def looks_like_date(value: str) -> bool:
    if "/" not in value and "-" not in value:
        return False

    stripped = value.strip()
    for date_format in DATE_FORMATS:
        try:
            datetime.strptime(stripped, date_format)
            return True
        except ValueError:
            continue
    return False


def looks_like_integer(value: str) -> bool:
    return bool(INTEGER_PATTERN.match(value.strip()))


def looks_like_decimal(value: str) -> bool:
    return bool(DECIMAL_PATTERN.match(value.strip()))


def summarize_examples(value_counts: Counter[str]) -> list[tuple[str, int, str]]:
    selected: list[tuple[str, int, str]] = []
    seen_values: set[str] = set()

    for value, count in sorted(value_counts.items(), key=lambda item: (-item[1], len(item[0]), item[0])):
        if value in seen_values:
            continue
        selected.append((value, count, "most_common"))
        seen_values.add(value)
        if len(selected) >= min(10, MAX_EXAMPLES_PER_COLUMN):
            break

    for value, count in sorted(value_counts.items(), key=lambda item: (item[1], -len(item[0]), item[0])):
        if value in seen_values:
            continue
        selected.append((value, count, "rare"))
        seen_values.add(value)
        if len(selected) >= min(15, MAX_EXAMPLES_PER_COLUMN):
            break

    for value, count in sorted(value_counts.items(), key=lambda item: (-len(item[0]), -item[1], item[0])):
        if value in seen_values:
            continue
        selected.append((value, count, "longest"))
        seen_values.add(value)
        if len(selected) >= MAX_EXAMPLES_PER_COLUMN:
            break

    return selected[:MAX_EXAMPLES_PER_COLUMN]


def infer_strategy(header: str, values: list[str]) -> tuple[str, str, str, str]:
    if not values:
        return (
            "preserve_blank_only",
            "high",
            "blank_only",
            "Column is blank after step 2 and should remain untouched unless upstream steps change.",
        )

    normalized_values = [normalize(value) for value in values]
    nonempty_count = len(values)
    boolean_ratio = sum(value in BOOLEAN_VALUES for value in normalized_values) / nonempty_count
    integer_ratio = sum(looks_like_integer(value) for value in values) / nonempty_count
    decimal_ratio = sum(looks_like_decimal(value) for value in values) / nonempty_count
    date_ratio = sum(looks_like_date(value) for value in values) / nonempty_count
    pipe_ratio = sum("|" in value for value in values) / nonempty_count
    unique_count = len(set(values))
    unique_ratio = unique_count / nonempty_count
    max_length = max(len(value) for value in values)
    header_norm = normalize(header)

    pattern_tags: list[str] = []
    if boolean_ratio >= 0.8:
        pattern_tags.append(f"boolean_like={boolean_ratio:.2f}")
    if integer_ratio >= 0.8:
        pattern_tags.append(f"integer_like={integer_ratio:.2f}")
    if decimal_ratio >= 0.8:
        pattern_tags.append(f"decimal_like={decimal_ratio:.2f}")
    if date_ratio >= 0.5:
        pattern_tags.append(f"date_like={date_ratio:.2f}")
    if pipe_ratio >= 0.2:
        pattern_tags.append(f"pipe_delimited={pipe_ratio:.2f}")
    if unique_ratio >= 0.8:
        pattern_tags.append(f"high_cardinality={unique_ratio:.2f}")
    if max_length >= 40:
        pattern_tags.append(f"long_text_max={max_length}")

    patterns = " | ".join(pattern_tags) if pattern_tags else "mixed_or_unclear"

    if "selected_" in header:
        return (
            "split_pipe_delimited_multiselect_preserve_raw",
            "high",
            patterns,
            "This is a step-2 collapsed checkbox summary column; safest next move is to split on ' | ' while preserving the original raw summary column.",
        )

    if "date" in header_norm and date_ratio >= 0.9:
        return (
            "parse_date_preserve_raw_backup",
            "high",
            patterns,
            "Values are consistently date-like; normalize only into a parallel parsed date field and keep the raw source unchanged.",
        )

    if boolean_ratio >= 0.98:
        return (
            "normalize_boolean_tokens_preserve_raw_backup",
            "high",
            patterns,
            "Values are almost entirely boolean-like; map to a canonical yes/no representation only in a new field while preserving raw values.",
        )

    if integer_ratio >= 0.98:
        return (
            "parse_integer_preserve_raw_backup",
            "high",
            patterns,
            "Values are consistently integer-like; normalize only into a parallel numeric field and retain the raw column.",
        )

    if decimal_ratio >= 0.98:
        return (
            "parse_decimal_preserve_raw_backup",
            "high",
            patterns,
            "Values are consistently numeric; normalize only into a parallel numeric field and retain the raw column.",
        )

    if date_ratio >= 0.85:
        return (
            "parse_probable_date_preserve_raw_backup",
            "medium",
            patterns,
            "Most values look date-like, but there is enough variation that raw values should be reviewed before any parsing rule is applied.",
        )

    if unique_count <= 20 and max_length <= 40:
        return (
            "review_for_controlled_vocabulary_mapping",
            "medium",
            patterns,
            "This looks like a compact categorical field; normalize only after reviewing the sampled raw values and defining an explicit mapping table.",
        )

    if pipe_ratio >= 0.8:
        return (
            "split_pipe_delimited_values_preserve_raw",
            "medium",
            patterns,
            "Values often contain pipe-delimited lists; split carefully into lists or linked tables while preserving the raw string.",
        )

    if unique_ratio >= 0.8 or max_length > 80:
        return (
            "preserve_verbatim_trim_whitespace_only",
            "low",
            patterns,
            "This field is high-cardinality or free-text-like; only whitespace cleanup is safe until a manual normalization rule is approved.",
        )

    return (
        "preserve_verbatim_pending_manual_review",
        "low",
        patterns,
        "This field mixes multiple raw forms; do not normalize automatically until the sampled values have been reviewed and a surgical rule is defined.",
    )


def write_profile(dataset: str, rows: list[dict[str, str]]) -> None:
    with step_3_profile_path(dataset).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "dataset",
                "column_index",
                "column_name",
                "total_rows",
                "nonempty_count",
                "nonempty_ratio",
                "unique_nonempty_count",
                "unique_nonempty_ratio",
                "proposed_strategy",
                "confidence",
                "observed_patterns",
                "guardrail",
                "example_preview",
                "requires_manual_review",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def write_examples(dataset: str, rows: list[dict[str, str]]) -> None:
    with step_3_examples_path(dataset).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "dataset",
                "column_index",
                "column_name",
                "example_rank",
                "example_value",
                "value_count",
                "selection_reason",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def profile_dataset(dataset: str) -> None:
    headers, data_rows = read_step_2_dataset(dataset)
    total_rows = len(data_rows)
    profile_rows: list[dict[str, str]] = []
    example_rows: list[dict[str, str]] = []

    for column_index, header in enumerate(headers, start=1):
        values = nonempty_values(data_rows, column_index - 1)
        value_counts = Counter(values)
        selected_examples = summarize_examples(value_counts)
        proposed_strategy, confidence, observed_patterns, guardrail = infer_strategy(header, values)
        nonempty_count = len(values)
        unique_count = len(value_counts)
        example_preview = " || ".join(
            f"{value} ({count})" for value, count, _ in selected_examples[:8]
        )

        profile_rows.append(
            {
                "dataset": dataset,
                "column_index": str(column_index),
                "column_name": header,
                "total_rows": str(total_rows),
                "nonempty_count": str(nonempty_count),
                "nonempty_ratio": f"{(nonempty_count / total_rows) if total_rows else 0:.4f}",
                "unique_nonempty_count": str(unique_count),
                "unique_nonempty_ratio": f"{(unique_count / nonempty_count) if nonempty_count else 0:.4f}",
                "proposed_strategy": proposed_strategy,
                "confidence": confidence,
                "observed_patterns": observed_patterns,
                "guardrail": guardrail,
                "example_preview": example_preview,
                "requires_manual_review": "yes",
            }
        )

        for example_rank, (value, count, selection_reason) in enumerate(selected_examples, start=1):
            example_rows.append(
                {
                    "dataset": dataset,
                    "column_index": str(column_index),
                    "column_name": header,
                    "example_rank": str(example_rank),
                    "example_value": value,
                    "value_count": str(count),
                    "selection_reason": selection_reason,
                }
            )

    write_profile(dataset, profile_rows)
    write_examples(dataset, example_rows)
    print(
        f"{dataset}: profiled {len(headers)} columns, wrote {len(profile_rows)} profile rows and {len(example_rows)} example rows"
    )
    print(f"  profile output: {step_3_profile_path(dataset).name}")
    print(f"  example output: {step_3_examples_path(dataset).name}")


def main() -> None:
    ensure_step_2_artifacts()
    for dataset in DATASETS:
        profile_dataset(dataset)


if __name__ == "__main__":
    main()