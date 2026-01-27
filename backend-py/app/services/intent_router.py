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
        self._cohort_keywords = [
            "cohort",
            "eligible",
            "inclusion",
            "exclusion",
            "filter",
            "criteria",
            "group",
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
            "patient",
            "patients",
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
            "ef",
            "ejection fraction",
            "hypertension",
            "diabetes",
        ]

    def classify(self, message: str) -> str:
        text = (message or "").strip().lower()
        if not text:
            return "general"

        if self._contains_any(text, self._rag_keywords):
            return "rag"
        if self._contains_any(text, self._cohort_keywords):
            return "cohort"
        if self._contains_any(text, self._ui_keywords):
            return "ui"
        if self._contains_any(text, self._sql_keywords):
            return "sql"

        return "general"

    @staticmethod
    def _contains_any(text: str, keywords: List[str]) -> bool:
        for keyword in keywords:
            if keyword in text:
                return True
        return False