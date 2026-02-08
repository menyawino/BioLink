from __future__ import annotations

import json
import logging
import os
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

try:
    import langextract as lx
except Exception:  # pragma: no cover - missing optional dependency
    lx = None


class LangExtractWrapper:
    """Thin wrapper around Google LangExtract.

    Uses Ollama/local provider by default. Returns JSON-serializable results
    for each input text.
    """

    def __init__(self, model_id: Optional[str] = None, model_url: Optional[str] = None):
        # sensible defaults: use Ollama gemma model if available
        self.model_id = model_id or "gemma2:2b"
        self.model_url = model_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

    def extract_notes(
        self,
        texts: List[str],
        prompt_description: str,
        examples: Optional[List[Any]] = None,
        fence_output: bool = False,
    ) -> List[Dict[str, Any]]:
        """Run LangExtract on each text and return list of dicts.

        If `langextract` is not installed, returns an empty list and logs a warning.
        """
        if lx is None:
            logger.warning("langextract not installed; skipping extraction")
            return []

        results: List[Dict[str, Any]] = []
        for i, txt in enumerate(texts):
            try:
                res = lx.extract(
                    text_or_documents=txt,
                    prompt_description=prompt_description,
                    examples=examples or [],
                    model_id=self.model_id,
                    model_url=self.model_url,
                    fence_output=fence_output,
                )

                # Attempt to convert to JSON-serializable form
                serializable = None
                if hasattr(res, "json"):
                    try:
                        serializable = json.loads(res.json())
                    except Exception:
                        serializable = {"raw": str(res)}
                else:
                    try:
                        serializable = json.loads(json.dumps(res))
                    except Exception:
                        serializable = {"raw": str(res)}

                results.append({"text_index": i, "result": serializable})
            except Exception as e:
                logger.exception("LangExtract failed on text index %s: %s", i, e)
                results.append({"text_index": i, "result": {"error": str(e)}})

        return results


def default_wrapper() -> LangExtractWrapper:
    return LangExtractWrapper()
