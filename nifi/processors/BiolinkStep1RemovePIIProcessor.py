"""BioLink Step 1 PII Removal & Data Quality Processor for Apache NiFi 2.8.0

Strips direct PII identifiers and scores FlowFile data quality.
"""

from __future__ import annotations

import json
from nifiapi.flowfiletransform import FlowFileTransform, FlowFileTransformResult
from nifiapi.properties import PropertyDescriptor, ExpressionLanguageScope

from BiolinkDataQualityProcessor import BiolinkDataQualityProcessor


class BiolinkStep1RemovePIIProcessor(BiolinkDataQualityProcessor):
    class Java:
        implements = ["org.apache.nifi.python.processor.FlowFileTransform"]

    class ProcessorDetails:
        version = "2.8.0"
        description = "Step 1: De-identifies PII identifiers (names, phone numbers, exact addresses) and scores completeness."
        tags = ["biolink", "step1", "pii-removal", "deidentification", "quality"]
