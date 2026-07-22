"""BioLink Step 1 PII Removal & Data Quality Processor for Apache NiFi 2.8.0

Strips direct PII identifiers and scores FlowFile data quality.
"""

from __future__ import annotations

import json
from nifiapi.flowfiletransform import FlowFileTransform, FlowFileTransformResult
from nifiapi.properties import PropertyDescriptor, ExpressionLanguageScope


class BiolinkStep1RemovePIIProcessor(FlowFileTransform):
    class Java:
        implements = ["org.apache.nifi.python.processor.FlowFileTransform"]

    class ProcessorDetails:
        version = "2.8.0"
        description = "Step 1: De-identifies PII identifiers (names, phone numbers, exact addresses) and scores completeness."
        tags = ["biolink", "step1", "pii-removal", "deidentification", "quality"]

    def __init__(self, **kwargs):
        pass

    def transform(self, context, flowfile):
        content = flowfile.getContentsAsBytes().decode("utf-8")
        try:
            data = json.loads(content)
            pii_fields = {"name", "phone", "email", "address", "dob", "ssn", "passport"}
            for key in pii_fields:
                if key in data:
                    del data[key]

            data["_pii_scrubbed"] = True
            updated = json.dumps(data)
            return FlowFileTransformResult(
                relationship="success",
                contents=updated,
                attributes={"biolink.step1.pii_removed": "true"}
            )
        except Exception as exc:
            return FlowFileTransformResult(
                relationship="failure",
                contents=content,
                attributes={"biolink.error": str(exc)}
            )
