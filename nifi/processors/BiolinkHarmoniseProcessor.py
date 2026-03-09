"""
BioLink Harmonise Processor for Apache NiFi 2.8.0 — Step 2 of 2

Applies master_schema.csv to an incoming batch of raw JSON records and
remaps dataset-specific column names to canonical master column names.
PII columns are hard-dropped and never appear in the output.

One instance of this processor is deployed per dataset:
  • dataset_type = bhs   → maps source_a_cols → master_col  → bhs_harmonised
  • dataset_type = ehvol → maps source_b_cols → master_col  → ehvol_harmonised

Pipeline position (per-dataset pipeline):
  GetFile → CsvToJson → BiolinkHarmoniseProcessor → BiolinkJsonToSqlProcessor
                                                         → PutSQL(xx_harmonised)

The incoming FlowFile content must be a JSON array of flat record dicts, as
produced by BiolinkCsvToJsonProcessor (snake-cased keys).

Properties:
  Dataset Type   - "bhs" or "ehvol"
  Schema Path    - /opt/nifi/outputs/master_schema.csv  (written by Step 1)
  Batch Size     - max records per output FlowFile (default 0 = all)
"""

import csv
import io
import json
import os
import re
import statistics
from datetime import date, datetime, timezone

from nifiapi.flowfiletransform import FlowFileTransform, FlowFileTransformResult
from nifiapi.properties import PropertyDescriptor, ExpressionLanguageScope

# ─────────────────────────────────────────────────────────────────────────────
# Shared string helper  (must be identical to BiolinkMasterSchemaProcessor)
# ─────────────────────────────────────────────────────────────────────────────

_APOS_RE = re.compile(r"['\u2018\u2019\u0060\u00b4]")
_NON_AZ09 = re.compile(r"[^a-z0-9]+")


def to_snake(name: str) -> str:
    s = _APOS_RE.sub("", str(name).lower())
    s = _NON_AZ09.sub("_", s).strip("_")
    return s or "col"


# ─────────────────────────────────────────────────────────────────────────────
# Schema loader
# ─────────────────────────────────────────────────────────────────────────────

def _load_schema(path: str) -> list[dict]:
    """
    Load master_schema.csv.
    Returns list of row dicts with keys:
      master_col, source_a_cols, source_b_cols,
      category, final_score, coalesce_strategy, pii_flag
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"master_schema.csv not found at '{path}'")
    rows: list[dict] = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows


# ─────────────────────────────────────────────────────────────────────────────
# Value coercions
# ─────────────────────────────────────────────────────────────────────────────

def _to_float(v) -> float | None:
    if v is None:
        return None
    try:
        return float(str(v).replace(",", "").strip())
    except (ValueError, TypeError):
        return None


def _is_empty(v) -> bool:
    if v is None:
        return True
    if isinstance(v, float):
        import math
        return math.isnan(v)
    return str(v).strip() in ("", "nan", "none", "null", "n/a", "na", "-")


# ─────────────────────────────────────────────────────────────────────────────
# Coalesce strategies  (applied across multiple source columns for one record)
# ─────────────────────────────────────────────────────────────────────────────

def _apply_strategy(values: list, strategy: str):
    """
    Collapse a list of candidate values from multiple source columns into one.
    `values` may include None / empty strings — these are treated as missing.
    """
    non_null = [v for v in values if not _is_empty(v)]
    if not non_null:
        return None

    if strategy == "first_non_null":
        return non_null[0]

    if strategy == "mean_value":
        nums = [_to_float(v) for v in non_null]
        nums = [n for n in nums if n is not None]
        if not nums:
            return non_null[0]
        return round(sum(nums) / len(nums), 6)

    if strategy in ("max_value", "min_value"):
        nums = [_to_float(v) for v in non_null]
        nums = [n for n in nums if n is not None]
        if not nums:
            return non_null[0]
        return max(nums) if strategy == "max_value" else min(nums)

    if strategy == "any_flag":
        for v in non_null:
            s = str(v).strip().lower()
            if s in ("1", "true", "yes", "y", "checked"):
                return True
        return False

    if strategy == "all_flag":
        for v in non_null:
            s = str(v).strip().lower()
            if s in ("0", "false", "no", "n", "unchecked"):
                return False
        return True

    if strategy == "mode_value":
        try:
            return statistics.mode(non_null)
        except statistics.StatisticsError:
            return non_null[0]

    if strategy == "median_date":
        # Return the middle date string by sorted order
        sorted_vals = sorted(str(v) for v in non_null)
        return sorted_vals[len(sorted_vals) // 2]

    # Fallback
    return non_null[0]


# ─────────────────────────────────────────────────────────────────────────────
# Per-record schema application
# ─────────────────────────────────────────────────────────────────────────────

def _normalise_record_keys(record: dict) -> dict:
    """Return a new dict with all keys snake-cased."""
    return {to_snake(k): v for k, v in record.items()}


def apply_schema_to_record(
    record: dict,
    schema_rows: list[dict],
    dataset_type: str,      # "bhs" or "ehvol"
) -> dict:
    """
    Remap a single raw record using master_schema.csv rows.
    PII rows are silently skipped.
    Returns a flat dict with master_col keys.
    """
    norm = _normalise_record_keys(record)
    out: dict = {}

    for row in schema_rows:
        # Skip PII columns
        if str(row.get("pii_flag", "False")).strip().lower() in ("true", "1", "yes"):
            continue

        master_col = row["master_col"]
        strategy   = row.get("coalesce_strategy") or "first_non_null"

        # Determine which source column(s) to look at for this dataset
        if dataset_type == "bhs":
            primary_col   = row.get("source_a_cols", "").strip()
            secondary_col = row.get("source_b_cols", "").strip()
        else:
            primary_col   = row.get("source_b_cols", "").strip()
            secondary_col = row.get("source_a_cols", "").strip()

        # Collect candidate values (primary first, then secondary as fallback)
        candidates: list = []
        for col_name in [primary_col, secondary_col]:
            if col_name and col_name in norm:
                candidates.append(norm[col_name])

        out[master_col] = _apply_strategy(candidates, strategy)

    return out


# ─────────────────────────────────────────────────────────────────────────────
# NiFi Processor
# ─────────────────────────────────────────────────────────────────────────────

class BiolinkHarmoniseProcessor(FlowFileTransform):
    """
    NiFi Step 2 — Applies master_schema.csv to one dataset's JSON records.
    Deploy one instance per dataset (set Dataset Type to 'bhs' or 'ehvol').
    Output is compatible with the existing BiolinkJsonToSqlProcessor.
    """

    class Java:
        implements = ["org.apache.nifi.python.processor.FlowFileTransform"]

    class ProcessorDetails:
        version = "1.0.0"
        description = (
            "Step 2 of 2-stage harmonisation: remaps raw dataset JSON records "
            "to canonical master column names defined in master_schema.csv. "
            "PII columns are hard-dropped. Deploy one instance per dataset "
            "(bhs → bhs_harmonised, ehvol → ehvol_harmonised)."
        )
        tags = ["biolink", "schema", "harmonise", "etl", "step2"]

    DATASET_TYPE = PropertyDescriptor(
        name="Dataset Type",
        description="Which dataset this processor instance handles: 'bhs' or 'ehvol'.",
        required=True,
        default_value="bhs",
        allowable_values=["bhs", "ehvol"],
        expression_language_scope=ExpressionLanguageScope.FLOWFILE_ATTRIBUTES,
    )
    SCHEMA_PATH = PropertyDescriptor(
        name="Schema Path",
        description=(
            "Absolute path to master_schema.csv produced by BiolinkMasterSchemaProcessor. "
            "Must be on a shared volume accessible to both Step 1 and Step 2 processors."
        ),
        required=True,
        default_value="/opt/nifi/outputs/master_schema.csv",
        expression_language_scope=ExpressionLanguageScope.FLOWFILE_ATTRIBUTES,
    )

    property_descriptors = [DATASET_TYPE, SCHEMA_PATH]

    def __init__(self, **kwargs):
        super().__init__()
        self._cached_schema_path: str | None = None
        self._cached_schema: list[dict] | None = None
        self._cached_schema_mtime: float = 0.0

    def getPropertyDescriptors(self):
        return self.property_descriptors

    def _get_schema(self, schema_path: str) -> list[dict]:
        """Load and cache master_schema.csv; reload if file has changed on disk."""
        try:
            mtime = os.path.getmtime(schema_path)
        except OSError:
            mtime = 0.0

        if (
            self._cached_schema is None
            or self._cached_schema_path != schema_path
            or mtime > self._cached_schema_mtime
        ):
            self._cached_schema       = _load_schema(schema_path)
            self._cached_schema_path  = schema_path
            self._cached_schema_mtime = mtime

        return self._cached_schema

    def transform(self, context, flowfile):
        dataset_type = (
            context.getProperty(self.DATASET_TYPE)
            .evaluateAttributeExpressions(flowfile)
            .getValue()
            or "bhs"
        ).strip().lower()
        schema_path = context.getProperty(self.SCHEMA_PATH).getValue()

        # ── Load schema (cached) ──────────────────────────────────────────────
        try:
            schema_rows = self._get_schema(schema_path)
        except FileNotFoundError as exc:
            msg = str(exc)
            return FlowFileTransformResult(
                relationship="failure",
                contents=json.dumps({"error": msg}),
                attributes={"biolink.error": msg},
            )

        # ── Parse incoming JSON records ───────────────────────────────────────
        try:
            raw_bytes = flowfile.getContentsAsBytes()
            raw = json.loads(raw_bytes.decode("utf-8"))
        except Exception as exc:
            msg = f"BiolinkHarmoniseProcessor: failed to parse incoming JSON — {exc}"
            return FlowFileTransformResult(
                relationship="failure",
                contents=json.dumps({"error": msg}),
                attributes={"biolink.error": str(exc)},
            )

        records = raw if isinstance(raw, list) else [raw]
        if not records:
            return FlowFileTransformResult(
                relationship="failure",
                contents=json.dumps({"error": "No records in FlowFile"}),
                attributes={"biolink.error": "No records in FlowFile"},
            )

        # ── Harmonise ─────────────────────────────────────────────────────────
        now_iso = datetime.now(timezone.utc).isoformat()
        harmonised: list[dict] = []

        for record in records:
            clinical = apply_schema_to_record(record, schema_rows, dataset_type)
            if not clinical:
                continue
            # Pack clinical columns into JSONB field; metadata stays as top-level cols
            # so BiolinkJsonToSqlProcessor maps them naturally to the harmonised table.
            harmonised.append({
                "_source_dataset": dataset_type,
                "_ingested_at":    now_iso,
                "clinical_data":   clinical,   # → JSONB in PostgreSQL
            })

        if not harmonised:
            return FlowFileTransformResult(
                relationship="failure",
                contents=json.dumps({"error": "All records produced empty harmonised output"}),
                attributes={"biolink.error": "All records produced empty harmonised output"},
            )

        # ── Non-PII clinical column count (schema minus PII rows) ──────────────
        clinical_cols = sum(
            1 for r in schema_rows
            if str(r.get("pii_flag", "False")).strip().lower() not in ("true", "1", "yes")
        )

        return FlowFileTransformResult(
            relationship="success",
            contents=json.dumps(harmonised).encode("utf-8"),
            attributes={
                "biolink.harmonise.dataset":        dataset_type,
                "biolink.harmonise.record_count":   str(len(harmonised)),
                "biolink.harmonise.clinical_cols":  str(clinical_cols),
                "biolink.harmonise.schema_path":    schema_path,
                "biolink.harmonise.processed_at":   now_iso,
                "mime.type":                        "application/json",
            },
        )
