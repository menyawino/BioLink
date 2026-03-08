"""
BioLink Data Quality Validator Processor for Apache NiFi 2.8.0

Validates transformed unified records against data quality rules.
Ported from biolink_etl/data_quality.py validation framework.

Routes records to 'success' (valid) or 'failure' (critical issues).
Attaches quality report as FlowFile attributes.
"""

import json
from nifiapi.flowfiletransform import FlowFileTransform, FlowFileTransformResult
from nifiapi.properties import PropertyDescriptor, ExpressionLanguageScope


# =============================================================================
# VALIDATION RULES
# =============================================================================

# Fields guaranteed to exist after BiolinkSchemaStandardizerProcessor runs.
# (participant_id does not exist as a unified field in wide tables — BHS uses
# record_id, EHVol uses dna_id; both are validated by the standardizer itself.)
REQUIRED_FIELDS = [
    "_source_dataset",
]

DATASET_REQUIRED_KEY = {
    "BHS": "record_id",
    "EHVOL": "dna_id",
}

TYPE_RULES = {
    "age":                 "integer",
    "age_at_enrollment":   "integer",
    "height_cm":           "numeric",
    "weight_kg":           "numeric",
    "bmi":                 "numeric",
    "heart_rate":          "numeric",
    "systolic_bp":         "numeric",
    "diastolic_bp":        "numeric",
    "hba1c":               "numeric",
    "troponin_i":          "numeric",
    "echo_lvef":           "numeric",   # BHS standardized name
    "echo_ef":             "numeric",   # EHVol standardized name
    "smoking_pack_years":  "numeric",
    "_data_quality_score": "numeric",
    "has_diabetes":        "boolean",
    "has_hypertension":    "boolean",
    "has_dyslipidemia":    "boolean",
    "has_heart_failure":   "boolean",
    "is_smoker":           "boolean",
}

RANGE_RULES = {
    "age":               (0, 120),
    "age_at_enrollment": (0, 120),
    "height_cm":         (50, 250),
    "weight_kg":         (2, 300),
    "bmi":               (10, 60),
    "heart_rate":        (30, 200),
    "systolic_bp":       (70, 250),
    "diastolic_bp":      (40, 150),
    "hba1c":             (3, 20),
    "echo_lvef":         (10, 80),
    "echo_ef":           (10, 80),
}

# Cross-field consistency rules
BP_CONSISTENCY = {
    "description": "Systolic BP must be greater than diastolic BP",
    "fields": ["systolic_bp", "diastolic_bp"],
}


class BiolinkDataQualityProcessor(FlowFileTransform):
    """
    Validates unified BioLink records for data quality.
    
    - Required field checks (critical severity)
    - Type checks (error severity)
    - Range checks (warning severity)
    - Cross-field consistency (warning severity)
    - Computes quality report in FlowFile attributes
    """

    class Java:
        implements = ["org.apache.nifi.python.processor.FlowFileTransform"]

    class ProcessorDetails:
        version = "1.0.0"
        description = (
            "Validates transformed BioLink records against data quality rules "
            "including required fields, type checks, range validation, and "
            "cross-field consistency. Routes to success or failure."
        )
        tags = ["biolink", "validation", "quality", "healthcare"]

    MIN_QUALITY_SCORE = PropertyDescriptor(
        name="Minimum Quality Score",
        description="Records below this quality score are routed to failure (0.0-1.0)",
        required=False,
        default_value="0.3",
        expression_language_scope=ExpressionLanguageScope.FLOWFILE_ATTRIBUTES,
    )

    property_descriptors = [MIN_QUALITY_SCORE]

    def __init__(self, **kwargs):
        super().__init__()

    def getPropertyDescriptors(self):
        return self.property_descriptors

    def transform(self, context, flowfile):
        min_score_str = context.getProperty(self.MIN_QUALITY_SCORE).evaluateAttributeExpressions(flowfile).getValue()
        min_score = float(min_score_str) if min_score_str else 0.3

        try:
            raw = json.loads(flowfile.getContentsAsBytes().decode("utf-8"))
        except Exception as e:
            return FlowFileTransformResult(
                relationship="failure",
                contents=json.dumps({"error": f"Invalid JSON: {e}"}),
                attributes={"biolink.error": str(e)},
            )

        records = raw if isinstance(raw, list) else [raw]
        valid_records = []
        rejected_records = []
        all_issues = []

        for record in records:
            issues = self._validate_record(record)
            score = self._compute_score(issues)
            record["_data_quality_score"] = round(score, 2)

            if score >= min_score:
                valid_records.append(record)
            else:
                record["_rejection_reasons"] = issues
                rejected_records.append(record)

            all_issues.extend(issues)

        # Summarize
        issue_counts = {}
        for issue in all_issues:
            sev = issue.get("severity", "info")
            issue_counts[sev] = issue_counts.get(sev, 0) + 1

        attrs = {
            "biolink.quality.total_records": str(len(records)),
            "biolink.quality.valid_records": str(len(valid_records)),
            "biolink.quality.rejected_records": str(len(rejected_records)),
            "biolink.quality.critical_issues": str(issue_counts.get("critical", 0)),
            "biolink.quality.error_issues": str(issue_counts.get("error", 0)),
            "biolink.quality.warning_issues": str(issue_counts.get("warning", 0)),
            "mime.type": "application/json",
        }

        if rejected_records:
            attrs["biolink.quality.has_rejections"] = "true"

        output = valid_records if isinstance(raw, list) else (valid_records[0] if valid_records else {})
        relationship = "success" if valid_records else "failure"

        return FlowFileTransformResult(
            relationship=relationship,
            contents=json.dumps(output, default=str),
            attributes=attrs,
        )

    def _validate_record(self, record):
        issues = []

        # Required field checks
        for field in REQUIRED_FIELDS:
            val = record.get(field)
            if val is None or (isinstance(val, str) and val.strip() == ""):
                issues.append({
                    "field": field,
                    "severity": "critical",
                    "message": f"Required field '{field}' is missing or empty",
                })

        dataset = (record.get("_source_dataset") or "").upper()
        key_field = DATASET_REQUIRED_KEY.get(dataset)
        if key_field:
            key_val = record.get(key_field)
            if key_val is None or (isinstance(key_val, str) and key_val.strip() == ""):
                issues.append({
                    "field": key_field,
                    "severity": "critical",
                    "message": f"Required dataset key '{key_field}' is missing or empty for dataset {dataset}",
                })

        # Type checks
        for field, expected_type in TYPE_RULES.items():
            val = record.get(field)
            if val is None:
                continue
            if not self._check_type(val, expected_type):
                issues.append({
                    "field": field,
                    "severity": "error",
                    "message": f"Expected {expected_type}, got {type(val).__name__}: {val}",
                })

        # Range checks
        for field, (lo, hi) in RANGE_RULES.items():
            val = record.get(field)
            if val is None:
                continue
            try:
                num = float(val) if not isinstance(val, (int, float)) else val
                if num < lo:
                    issues.append({
                        "field": field,
                        "severity": "warning",
                        "message": f"Value {num} below minimum {lo}",
                    })
                elif num > hi:
                    issues.append({
                        "field": field,
                        "severity": "warning",
                        "message": f"Value {num} above maximum {hi}",
                    })
            except (ValueError, TypeError):
                pass

        # Cross-field: BP consistency
        sys_bp = record.get("systolic_bp")
        dia_bp = record.get("diastolic_bp")
        if sys_bp is not None and dia_bp is not None:
            try:
                if float(sys_bp) <= float(dia_bp):
                    issues.append({
                        "field": "systolic_bp/diastolic_bp",
                        "severity": "warning",
                        "message": f"Systolic ({sys_bp}) <= Diastolic ({dia_bp})",
                    })
            except (ValueError, TypeError):
                pass

        return issues

    @staticmethod
    def _check_type(value, expected):
        if expected == "numeric":
            if isinstance(value, (int, float)):
                return True
            try:
                float(value)
                return True
            except (ValueError, TypeError):
                return False
        if expected == "integer":
            if isinstance(value, int):
                return True
            try:
                int(value)
                return True
            except (ValueError, TypeError):
                return False
        if expected == "boolean":
            return isinstance(value, bool)
        return True

    @staticmethod
    def _compute_score(issues):
        if not issues:
            return 1.0
        weights = {"critical": 0.5, "error": 0.3, "warning": 0.1, "info": 0.0}
        total = sum(weights.get(i.get("severity", "info"), 0.1) for i in issues)
        return max(0.0, 1.0 - total)
