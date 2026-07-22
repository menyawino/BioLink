"""BioLink Step 5 Extract Units Processor for Apache NiFi 2.8.0

Extracts and standardizes clinical measurement units.
"""

from __future__ import annotations

import json
import re
from nifiapi.flowfiletransform import FlowFileTransform, FlowFileTransformResult
from nifiapi.properties import PropertyDescriptor, ExpressionLanguageScope

UNIT_MAP = {
    "mg/dl": "mg/dL",
    "mmol/l": "mmol/L",
    "mmhg": "mmHg",
    "bpm": "bpm",
    "kg": "kg",
    "cm": "cm",
    "%": "%",
}


class BiolinkStep5ExtractUnitsProcessor(FlowFileTransform):
    class Java:
        implements = ["org.apache.nifi.python.processor.FlowFileTransform"]

    class ProcessorDetails:
        version = "2.8.0"
        description = "Step 5: Extracts and standardizes measurement units for clinical values."
        tags = ["biolink", "step5", "units", "ucum", "standardization"]

    def __init__(self, **kwargs):
        pass

    def transform(self, context, flowfile):
        content = flowfile.getContentsAsBytes().decode("utf-8")
        try:
            data = json.loads(content)
            extracted_units = {}
            for key, val in list(data.items()):
                if isinstance(val, str):
                    match = re.search(r"([0-9.]+)\s*([a-zA-Z%/]+)", val)
                    if match:
                        num, unit = match.groups()
                        norm_unit = UNIT_MAP.get(unit.lower(), unit)
                        extracted_units[f"{key}_unit"] = norm_unit

            data.update(extracted_units)
            updated = json.dumps(data)
            return FlowFileTransformResult(
                relationship="success",
                contents=updated,
                attributes={"biolink.step5.units_extracted": "true"}
            )
        except Exception as exc:
            return FlowFileTransformResult(
                relationship="failure",
                contents=content,
                attributes={"biolink.error": str(exc)}
            )
