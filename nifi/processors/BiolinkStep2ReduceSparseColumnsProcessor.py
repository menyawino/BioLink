"""BioLink Step 2 Reduce Sparse Columns Processor for Apache NiFi 2.8.0

Filters empty/sparse columns and transforms payload structures.
"""

from __future__ import annotations

import json
from nifiapi.flowfiletransform import FlowFileTransform, FlowFileTransformResult
from nifiapi.properties import PropertyDescriptor, ExpressionLanguageScope

from BiolinkTransformProcessor import BiolinkTransformProcessor


class BiolinkStep2ReduceSparseColumnsProcessor(BiolinkTransformProcessor):
    class Java:
        implements = ["org.apache.nifi.python.processor.FlowFileTransform"]

    class ProcessorDetails:
        version = "2.8.0"
        description = "Step 2: Reduces sparse columns and filters missingness thresholds."
        tags = ["biolink", "step2", "sparsity-reduction", "transform"]
