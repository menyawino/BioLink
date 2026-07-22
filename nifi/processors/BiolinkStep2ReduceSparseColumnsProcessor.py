"""BioLink Step 2 Reduce Sparse Columns Processor for Apache NiFi 2.8.0

Filters empty/sparse columns and transforms payload structures.
"""

from __future__ import annotations

import json
from nifiapi.flowfiletransform import FlowFileTransform, FlowFileTransformResult
from nifiapi.properties import PropertyDescriptor, ExpressionLanguageScope


class BiolinkStep2ReduceSparseColumnsProcessor(FlowFileTransform):
    class Java:
        implements = ["org.apache.nifi.python.processor.FlowFileTransform"]

    class ProcessorDetails:
        version = "2.8.0"
        description = "Step 2: Reduces sparse columns and filters missingness thresholds."
        tags = ["biolink", "step2", "sparsity-reduction", "transform"]

    def __init__(self, **kwargs):
        pass

    def transform(self, context, flowfile):
        content = flowfile.getContentsAsBytes().decode("utf-8")
        try:
            data = json.loads(content)
            data = {k: v for k, v in data.items() if v is not None and str(v).strip() != ""}
            data["_sparsity_reduced"] = True
            updated = json.dumps(data)
            return FlowFileTransformResult(
                relationship="success",
                contents=updated,
                attributes={"biolink.step2.reduced": "true"}
            )
        except Exception as exc:
            return FlowFileTransformResult(
                relationship="failure",
                contents=content,
                attributes={"biolink.error": str(exc)}
            )
