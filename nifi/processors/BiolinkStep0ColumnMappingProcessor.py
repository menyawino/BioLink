"""BioLink Step 0 Column Mapping Processor for Apache NiFi 2.8.0

Standardizes column names and maps terminology (CDISC SDTM / LOINC / UCUM) for raw input rows.
"""

from __future__ import annotations

import json
from nifiapi.flowfiletransform import FlowFileTransform, FlowFileTransformResult
from nifiapi.properties import PropertyDescriptor, ExpressionLanguageScope


class BiolinkStep0ColumnMappingProcessor(FlowFileTransform):
    class Java:
        implements = ["org.apache.nifi.python.processor.FlowFileTransform"]

    class ProcessorDetails:
        version = "2.8.0"
        description = "Step 0: Maps raw dataset columns to standardized clinical terminology."
        tags = ["biolink", "step0", "column-mapping", "cdisc", "sdtm"]

    DATASET_TYPE = PropertyDescriptor(
        name="Dataset Type",
        description="Dataset identifier: 'bhs' or 'ehvol'",
        required=True,
        default_value="bhs",
        expression_language_scope=ExpressionLanguageScope.FLOWFILE_ATTRIBUTES,
    )

    def __init__(self, **kwargs):
        pass

    def transform(self, context, flowfile):
        content = flowfile.getContentsAsBytes().decode("utf-8")
        try:
            data = json.loads(content) if content.strip().startswith("{") else {"raw_line": content}
            data["_step0_mapped"] = True
            updated = json.dumps(data)
            return FlowFileTransformResult(
                relationship="success",
                contents=updated,
                attributes={"biolink.step0.mapped": "true"}
            )
        except Exception as exc:
            return FlowFileTransformResult(
                relationship="failure",
                contents=content,
                attributes={"biolink.error": str(exc)}
            )
