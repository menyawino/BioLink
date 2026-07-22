"""BioLink Step 4 Apply Range Rules Processor for Apache NiFi 2.8.0

Validates physiological range boundaries and flags outliers.
"""

from __future__ import annotations

import json
from nifiapi.flowfiletransform import FlowFileTransform, FlowFileTransformResult
from nifiapi.properties import PropertyDescriptor, ExpressionLanguageScope

RANGE_RULES = {
    "age": (0, 120),
    "height_cm": (50, 250),
    "weight_kg": (2, 300),
    "bmi": (10, 60),
    "heart_rate": (30, 200),
    "systolic_bp": (60, 250),
    "diastolic_bp": (30, 150),
    "hba1c": (3, 20),
    "troponin_i": (0, 500),
    "echo_lvef": (5, 95),
}


class BiolinkStep4ApplyRangeRulesProcessor(FlowFileTransform):
    class Java:
        implements = ["org.apache.nifi.python.processor.FlowFileTransform"]

    class ProcessorDetails:
        version = "2.8.0"
        description = "Step 4: Validates clinical measurement boundaries and flags out-of-range values."
        tags = ["biolink", "step4", "range-rules", "validation"]

    def __init__(self, **kwargs):
        pass

    def transform(self, context, flowfile):
        content = flowfile.getContentsAsBytes().decode("utf-8")
        try:
            data = json.loads(content)
            outliers = []
            for field, (low, high) in RANGE_RULES.items():
                if field in data and data[field] is not None:
                    try:
                        val = float(data[field])
                        if val < low or val > high:
                            outliers.append(f"{field}={val}")
                    except ValueError:
                        pass

            data["_range_outliers"] = outliers
            updated = json.dumps(data)
            return FlowFileTransformResult(
                relationship="success",
                contents=updated,
                attributes={"biolink.step4.range_checked": "true", "biolink.outliers": str(len(outliers))}
            )
        except Exception as exc:
            return FlowFileTransformResult(
                relationship="failure",
                contents=content,
                attributes={"biolink.error": str(exc)}
            )
