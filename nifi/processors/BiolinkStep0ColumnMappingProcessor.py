"""BioLink Step 0 Column Mapping Processor for Apache NiFi 2.8.0

Standardizes column names and maps terminology (CDISC SDTM / LOINC / UCUM) for raw input rows.
"""

from __future__ import annotations

import json
from nifiapi.flowfiletransform import FlowFileTransform, FlowFileTransformResult
from nifiapi.properties import PropertyDescriptor, ExpressionLanguageScope

from BiolinkSchemaStandardizerProcessor import BiolinkSchemaStandardizerProcessor


class BiolinkStep0ColumnMappingProcessor(BiolinkSchemaStandardizerProcessor):
    class Java:
        implements = ["org.apache.nifi.python.processor.FlowFileTransform"]

    class ProcessorDetails:
        version = "2.8.0"
        description = "Step 0: Maps raw dataset columns to standardized clinical terminology."
        tags = ["biolink", "step0", "column-mapping", "cdisc", "sdtm"]
