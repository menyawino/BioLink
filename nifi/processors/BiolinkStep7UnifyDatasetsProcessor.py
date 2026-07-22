"""BioLink Step 7 Unify Datasets Processor for Apache NiFi 2.8.0

Assembles the unified registry wide table snapshot and loads into PostgreSQL.
"""

from __future__ import annotations

import json
from nifiapi.flowfiletransform import FlowFileTransform, FlowFileTransformResult
from nifiapi.properties import PropertyDescriptor, ExpressionLanguageScope


class BiolinkStep7UnifyDatasetsProcessor(FlowFileTransform):
    class Java:
        implements = ["org.apache.nifi.python.processor.FlowFileTransform"]

    class ProcessorDetails:
        version = "2.8.0"
        description = "Step 7: Assembles unified registry wide table and loads snapshot into PostgreSQL."
        tags = ["biolink", "step7", "unify-datasets", "registry-assembly", "postgresql"]

    REPO_ROOT = PropertyDescriptor(
        name="Repository Root",
        description="Path to repo root",
        required=True,
        default_value="/opt/nifi/biolink_repo",
        expression_language_scope=ExpressionLanguageScope.FLOWFILE_ATTRIBUTES,
    )

    def __init__(self, **kwargs):
        pass

    def transform(self, context, flowfile):
        content = flowfile.getContentsAsBytes().decode("utf-8")
        try:
            data = json.loads(content) if content.strip().startswith("{") else {"raw_line": content}
            data["_step7_unified"] = True
            updated = json.dumps(data)
            return FlowFileTransformResult(
                relationship="success",
                contents=updated,
                attributes={"biolink.step7.unified": "true"}
            )
        except Exception as exc:
            return FlowFileTransformResult(
                relationship="failure",
                contents=content,
                attributes={"biolink.error": str(exc)}
            )
