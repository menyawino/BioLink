"""BioLink Step 7 Unify Datasets Processor for Apache NiFi 2.8.0

Assembles the unified registry wide table snapshot and loads into PostgreSQL.
"""

from __future__ import annotations

import json
from nifiapi.flowfiletransform import FlowFileTransform, FlowFileTransformResult
from nifiapi.properties import PropertyDescriptor, ExpressionLanguageScope

from BiolinkRegistryPipelineProcessor import BiolinkRegistryPipelineProcessor


class BiolinkStep7UnifyDatasetsProcessor(BiolinkRegistryPipelineProcessor):
    class Java:
        implements = ["org.apache.nifi.python.processor.FlowFileTransform"]

    class ProcessorDetails:
        version = "2.8.0"
        description = "Step 7: Assembles unified registry wide table and loads snapshot into PostgreSQL."
        tags = ["biolink", "step7", "unify-datasets", "registry-assembly", "postgresql"]
