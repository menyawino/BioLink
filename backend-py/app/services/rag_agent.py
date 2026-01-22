from __future__ import annotations

import json
import re
import logging
from typing import Optional

from langchain_ollama import ChatOllama
from fastapi.concurrency import run_in_threadpool

from app.config import settings
from app.rag.embedding import embed_query
from app.rag.vector_store import similarity_search
from app.rag.sqlserver import fetch_patient_ids_by_filters, fetch_patients_by_ids

logger = logging.getLogger(__name__)


class RagAgentService:
    def __init__(self):
        self.llm = ChatOllama(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            temperature=0
        )

    async def _extract_filters(self, question: str) -> dict:
        prompt = (
            "Extract structured filters and a search query from the user question. "
            "Return ONLY JSON with keys: query, age_min, age_max, gender, ef_min, ef_max, city. "
            "If a field is unknown, set it to null. "
            f"Question: {question}"
        )
        response = await self.llm.ainvoke(prompt)
        try:
            return json.loads(response.content)
        except Exception:
            return {
                "query": question,
                "age_min": None,
                "age_max": None,
                "gender": None,
                "ef_min": None,
                "ef_max": None,
                "city": None,
            }

    async def run(self, question: str) -> str:
        filters = await self._extract_filters(question)
        query = filters.get("query") or question
        question_lower = question.lower()
        def _to_int(value):
            try:
                return int(float(value))
            except Exception:
                return None

        def _to_float(value):
            try:
                return float(value)
            except Exception:
                return None

        age_min = _to_int(filters.get("age_min"))
        age_max = _to_int(filters.get("age_max"))
        gender_raw = filters.get("gender")
        gender = None
        if isinstance(gender_raw, str) and gender_raw.strip().lower() in {"male", "female"}:
            gender = gender_raw.strip().lower()

        ef_min = _to_float(filters.get("ef_min"))
        ef_max = _to_float(filters.get("ef_max"))
        city = filters.get("city")
        if isinstance(city, str):
            city = city.strip() or None
        else:
            city = None

        between_match = re.search(r"ef\s*(?:between|from)\s*(\d+(?:\.\d+)?)\s*(?:and|to)\s*(\d+(?:\.\d+)?)", question_lower)
        if between_match:
            ef_min = float(between_match.group(1))
            ef_max = float(between_match.group(2))

        under_match = re.search(r"ef\s*(?:<=|<|under|below)\s*(\d+(?:\.\d+)?)", question_lower)
        if under_match:
            ef_max = float(under_match.group(1))

        over_match = re.search(r"ef\s*(?:>=|>|over|above)\s*(\d+(?:\.\d+)?)", question_lower)
        if over_match:
            ef_min = float(over_match.group(1))

        if ef_min is None and ef_max is None and "low ef" in question_lower:
            ef_max = 40.0

        filters_applied = any(
            value is not None
            for value in [age_min, age_max, gender, ef_min, ef_max, city]
        )

        patient_ids = await run_in_threadpool(
            fetch_patient_ids_by_filters,
            age_min,
            age_max,
            gender,
            ef_min,
            ef_max,
            city,
        )

        if filters_applied and not patient_ids:
            return "No matching patients were found for the requested filters."

        if filters_applied:
            patient_details = await run_in_threadpool(fetch_patients_by_ids, patient_ids)
            ordered_ids = [pid for pid in patient_ids if pid in patient_details]
            sample_ids = ordered_ids[: settings.rag_top_k]
            lines = []
            for pid in sample_ids:
                info = patient_details.get(pid, {})
                lines.append(
                    f"- Patient {pid}: gender={info.get('gender')} | age={info.get('age')} | "
                    f"ef={info.get('ef')} | city={info.get('city')}"
                )

            total = len(ordered_ids)
            header = f"Found {total} patients matching the filters."
            if not lines:
                return header
            return f"{header}\n\nTop matches:\n" + "\n".join(lines)

        query_embedding = await run_in_threadpool(embed_query, query)
        chunks = await run_in_threadpool(
            similarity_search,
            query_embedding,
            settings.rag_top_k,
            patient_ids if filters_applied else None
        )

        if not chunks:
            if filters_applied:
                return "No matching notes were found for the requested filters."
            return "No matching notes were found for the requested criteria."

        unique_ids = list({c["patient_id"] for c in chunks})
        patient_details = await run_in_threadpool(fetch_patients_by_ids, unique_ids)

        context_block = "\n\n".join(
            [
                (
                    f"Patient {c['patient_id']} (score={c['similarity']:.2f}) | "
                    f"gender: {patient_details.get(c['patient_id'], {}).get('gender')} | "
                    f"age: {patient_details.get(c['patient_id'], {}).get('age')} | "
                    f"ef: {patient_details.get(c['patient_id'], {}).get('ef')} | "
                    f"city: {patient_details.get(c['patient_id'], {}).get('city')} | "
                    f"notes: {c['content']}"
                )
                for c in chunks
            ]
        )

        answer_prompt = (
            "You are a clinical research assistant. "
            "Answer strictly using only the provided patient context. "
            "Do not guess or infer values that are not explicitly stated. "
            "If the question asks for criteria (e.g., low EF males), list the matching patients and their EF/city. "
            "If the context does not contain the answer, say that the context is insufficient. "
            f"Question: {question}\n\nContext:\n{context_block}"
        )
        response = await self.llm.ainvoke(answer_prompt)
        snippets = "\n".join(
            [
                (
                    f"- Patient {c['patient_id']}: "
                    f"gender={patient_details.get(c['patient_id'], {}).get('gender')} | "
                    f"age={patient_details.get(c['patient_id'], {}).get('age')} | "
                    f"ef={patient_details.get(c['patient_id'], {}).get('ef')} | "
                    f"city={patient_details.get(c['patient_id'], {}).get('city')} | "
                    f"notes={c['content']}"
                )
                for c in chunks
            ]
        )
        return f"{response.content}\n\nContext snippets:\n{snippets}"


try:
    rag_agent_service = RagAgentService()
except Exception as e:
    logger.error(f"RAG agent initialization failed: {e}")
    rag_agent_service = None
