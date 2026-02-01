from __future__ import annotations

import re
from typing import List


class IntentRouter:
    def __init__(self) -> None:
        self._rag_keywords = [
            "rag",
            "note",
            "notes",
            "document",
            "free text",
            "narrative",
            "mention",
        ]
        self._medical_keywords = [
            "diagnosis",
            "diagnose",
            "treatment",
            "therapy",
            "medication",
            "drug",
            "side effect",
            "contraindication",
            "symptom",
            "risk",
            "risk factor",
            "clinical",
            "cardiology",
            "cardiac",
            "hypertension",
            "diabetes",
            "heart failure",
        ]
        self._cohort_keywords = [
            "cohort",
            "eligible",
            "inclusion",
            "exclusion",
            "filter",
            "criteria",
            "group",
        ]
        self._data_keywords = [
            "join",
            "group by",
            "chart",
            "plot",
            "graph",
            "visualize",
            "visualise",
            "table",
            "dataset",
        ]
        self._ui_keywords = [
            "open",
            "navigate",
            "go to",
            "dashboard",
            "registry",
            "analytics",
            "chart builder",
            "timeline",
            "dictionary",
        ]
        self._sql_keywords = [
            "count",
            "how many",
            "average",
            "mean",
            "median",
            "min",
            "max",
            "list",
            "show",
            "query",
            "sql",
            "age",
            "gender",
        ]

    def classify(self, message: str) -> str:
        text = (message or "").strip().lower()
        if not text:
            return "general"

        if text.startswith("select ") or text.startswith("with "):
            return "data"

        if self._contains_any(text, self._rag_keywords):
            return "rag"
        if self._contains_any(text, self._cohort_keywords):
            return "cohort"
        if self._contains_any(text, self._ui_keywords):
            return "ui"
        if self._contains_any(text, self._sql_keywords):
            return "data"
        if self._contains_any(text, self._data_keywords):
            return "data"
        if self._contains_any(text, self._medical_keywords):
            return "medical"

        return "general"

    @staticmethod
    def _contains_any(text: str, keywords: List[str]) -> bool:
        for keyword in keywords:
            if keyword in text:
                return True
        return False