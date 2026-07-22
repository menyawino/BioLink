"""BioLink Step 3 Profile Normalization Processor for Apache NiFi 2.8.0

Applies demographic & clinical profile normalization to FlowFiles.
"""

from __future__ import annotations

import json
from nifiapi.flowfiletransform import FlowFileTransform, FlowFileTransformResult
from nifiapi.properties import PropertyDescriptor, ExpressionLanguageScope


class BiolinkStep3ProfileNormalizationProcessor(FlowFileTransform):
    class Java:
        implements = ["org.apache.nifi.python.processor.FlowFileTransform"]

    class ProcessorDetails:
        version = "2.8.0"
        description = "Step 3: Normalizes demographic and clinical values across datasets."
        tags = ["biolink", "step3", "profile-normalization", "demographics"]

    def transform(self, context, flowfile):
        content = flowfile.getContentsAsBytes().decode("utf-8")
        try:
            data = json.loads(content)
            # Normalize boolean / clinical flags
            for key, val in list(data.items()):
                if isinstance(val, str):
                    sval = val.strip().lower()
                    if sval in {"yes", "true", "1", "checked", "positive"}:
                        data[key] = True
                    elif sval in {"no", "false", "0", "unchecked", "negative"}:
                        data[key] = False

            updated = json.dumps(data)
            return FlowFileTransformResult(
                relationship="success",
                contents=updated,
                attributes={"biolink.step3.normalized": "true"}
            )
        except Exception as exc:
            return FlowFileTransformResult(
                relationship="failure",
                contents=content,
                attributes={"biolink.error": str(exc)}
            )
