from __future__ import annotations

import asyncio
import json
import logging
import random
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol

from langchain_ollama import ChatOllama

from app.config import settings
from app.services.audit import audit_event
from app.services.intent_router import IntentRouter
from app.services.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


@dataclass
class ToolCall:
    name: str
    arguments: Dict[str, Any]


@dataclass
class AgentResult:
    content: str
    agent: str
    tool_calls: List[ToolCall] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class Agent(Protocol):
    async def run(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]],
        tool_registry: ToolRegistry,
    ) -> AgentResult:
        ...


async def _ainvoke_with_retries(
    llm: ChatOllama,
    prompt: str,
    timeout_s: float,
    max_retries: int,
) -> Any:
    last_error: Optional[Exception] = None
    for attempt in range(max_retries + 1):
        try:
            return await asyncio.wait_for(llm.ainvoke(prompt), timeout=timeout_s)
        except Exception as exc:  # pragma: no cover - defensive
            last_error = exc
            if attempt >= max_retries:
                break
            backoff = settings.llm_retry_backoff_s * (2 ** attempt)
            jitter = random.random() * settings.llm_retry_jitter_s
            await asyncio.sleep(backoff + jitter)
    raise last_error or RuntimeError("LLM invocation failed")


class SqlAgentAdapter:
    name = "sql"

    async def run(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]],
        tool_registry: ToolRegistry,
    ) -> AgentResult:
        sql = self._heuristic_sql(message)
        if not sql:
            return AgentResult(
                content="Ask about patient counts, averages, or registry statistics.",
                agent=self.name,
            )

        result = tool_registry.call("query_sql", {"sql": sql, "limit": 200})
        tool_call = ToolCall(name="query_sql", arguments={"sql": sql, "limit": 200})
        return AgentResult(
            content=self._format_result(sql, result),
            agent=self.name,
            tool_calls=[tool_call],
            metadata={"count": result.get("count", 0)},
        )

    def _heuristic_sql(self, message: str) -> Optional[str]:
        text = (message or "").lower()
        if "select " in text:
            return text
        city = self._extract_city(text)
        if city and ("count" in text or "how many" in text):
            return (
                "SELECT COUNT(*) AS count FROM patients "
                f"WHERE LOWER(current_city) = LOWER('{city}')"
            )
        if "how many" in text or ("count" in text and "patient" in text):
            return "SELECT COUNT(*) AS count FROM EHVOL"
        if "average age" in text:
            return "SELECT AVG(age) AS avg_age FROM EHVOL WHERE age IS NOT NULL"
        if "age distribution" in text:
            return "SELECT age FROM EHVOL WHERE age IS NOT NULL"
        if "count" in text and "gender" in text:
            return "SELECT gender, COUNT(*) AS count FROM EHVOL GROUP BY gender"
        if "average" in text and "ef" in text:
            return "SELECT AVG(echo_ef) AS avg_ef FROM EHVOL WHERE echo_ef IS NOT NULL"
        if "registry overview" in text or "overview" in text:
            return "SELECT COUNT(*) AS total FROM EHVOL"
        return None

    @staticmethod
    def _extract_city(text: str) -> Optional[str]:
        if not text:
            return None

        match = re.search(r"count\s+of\s+([a-z\s-]+?)\s+people", text)
        if not match:
            match = re.search(r"people\s+(?:in|from)\s+([a-z\s-]+)", text)
        if not match:
            match = re.search(r"count\s+of\s+([a-z\s-]+?)\s+in\s+the\s+dataset", text)
        if not match:
            return None

        raw_city = match.group(1).strip()
        safe_city = re.sub(r"[^a-z\s-]", "", raw_city).strip()
        return safe_city or None

    @staticmethod
    def _format_result(sql: str, result: Dict[str, Any]) -> str:
        rows = result.get("rows", [])
        count = result.get("count", 0)
        if count == 0:
            return "Query executed but returned no results."
        if count == 1:
            return f"Query executed: {sql}\nResult: {rows[0]}"
        return f"Query executed: {sql}\nReturned {count} rows. Sample: {rows[:5]}"


class MedicalAgentAdapter:
    name = "medical"

    def __init__(self) -> None:
        self._llm = ChatOllama(
            base_url=settings.ollama_base_url,
            model=settings.ollama_medical_model,
            temperature=0.2,
        )

    async def run(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]],
        tool_registry: ToolRegistry,
    ) -> AgentResult:
        prompt = self._build_prompt(message, history)
        response = await _ainvoke_with_retries(
            self._llm,
            prompt,
            timeout_s=settings.medical_llm_timeout_s,
            max_retries=settings.llm_max_retries,
        )
        return AgentResult(content=response.content, agent=self.name)

    async def run_handoff(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]],
        agent_result: AgentResult,
    ) -> AgentResult:
        prompt = self._build_handoff_prompt(message, history, agent_result)
        response = await _ainvoke_with_retries(
            self._llm,
            prompt,
            timeout_s=settings.medical_llm_timeout_s,
            max_retries=settings.llm_max_retries,
        )
        return AgentResult(
            content=response.content,
            agent=self.name,
            tool_calls=agent_result.tool_calls,
            metadata={
                **agent_result.metadata,
                "handoff_from": agent_result.agent,
            },
        )

    @staticmethod
    def _build_prompt(message: str, history: Optional[List[Dict[str, str]]]) -> str:
        history_block = ""
        if history:
            history_block = "\n".join(
                [f"{item.get('role', 'user')}: {item.get('content', '')}" for item in history[-6:]]
            )
        return (
            "You are a careful medical assistant. Provide evidence-based guidance, "
            "be explicit about uncertainty, and avoid giving definitive diagnoses. "
            "If a question requires patient-specific data, ask clarifying questions.\n\n"
            f"Conversation history:\n{history_block}\n\n"
            f"User question: {message}\n"
        )

    @staticmethod
    def _build_handoff_prompt(
        message: str,
        history: Optional[List[Dict[str, str]]],
        agent_result: AgentResult,
    ) -> str:
        history_block = ""
        if history:
            history_block = "\n".join(
                [f"{item.get('role', 'user')}: {item.get('content', '')}" for item in history[-6:]]
            )
        tool_call_block = ""
        if agent_result.tool_calls:
            tool_call_block = "\n".join(
                [f"- {tc.name}: {json.dumps(tc.arguments, ensure_ascii=False)}" for tc in agent_result.tool_calls]
            )
        metadata_block = ""
        if agent_result.metadata:
            metadata_block = json.dumps(agent_result.metadata, ensure_ascii=False, indent=2)
        return (
            "You are a medical reasoning assistant. A specialist agent already executed tools and gathered data. "
            "Use the tool results to provide the final response. Be explicit about uncertainty and avoid definitive diagnoses. "
            "If results are insufficient, ask concise clarifying questions.\n\n"
            f"Conversation history:\n{history_block}\n\n"
            f"User question: {message}\n\n"
            f"Specialist agent: {agent_result.agent}\n"
            f"Specialist summary:\n{agent_result.content}\n\n"
            f"Tool calls:\n{tool_call_block or 'None'}\n\n"
            f"Metadata:\n{metadata_block or 'None'}\n"
        )


class DataAgentAdapter:
    name = "data"

    _allowed_marks = {"bar", "line", "area", "point", "tick", "boxplot"}

    def __init__(self) -> None:
        self._llm = ChatOllama(
            base_url=settings.ollama_base_url,
            model=settings.ollama_data_model,
            temperature=0,
        )

    async def run(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]],
        tool_registry: ToolRegistry,
    ) -> AgentResult:
        prompt = self._build_prompt(message, history)
        try:
            response = await _ainvoke_with_retries(
                self._llm,
                prompt,
                timeout_s=settings.data_llm_timeout_s,
                max_retries=settings.llm_max_retries,
            )
        except Exception as exc:
            logger.warning("Data agent LLM unavailable, falling back to heuristic SQL: %s", exc)
            sql = SqlAgentAdapter()._heuristic_sql(message)
            if not sql:
                return AgentResult(
                    content="Ask about patient counts, averages, or registry statistics.",
                    agent=self.name,
                )
            sql = self._ensure_limit(sql, settings.sql_agent_default_limit)
            result = tool_registry.call(
                "query_sql",
                {"sql": sql, "limit": settings.sql_agent_default_limit},
            )
            tool_call = ToolCall(
                name="query_sql",
                arguments={"sql": sql, "limit": settings.sql_agent_default_limit},
            )
            return AgentResult(
                content=SqlAgentAdapter._format_result(sql, result),
                agent=self.name,
                tool_calls=[tool_call],
                metadata={"count": result.get("count", 0), "fallback": "heuristic"},
            )

        payload = self._extract_json(response.content)
        if not payload:
            return AgentResult(
                content="I couldn't parse a structured plan. Please rephrase the request with desired chart or SQL details.",
                agent=self.name,
            )

        action = payload.get("action", "query_sql")
        if action == "chart_from_sql":
            args = {
                "sql": self._sanitize_sql(payload.get("sql") or ""),
                "mark": self._sanitize_mark(payload.get("mark", "bar")),
                "x": payload.get("x"),
                "y": payload.get("y"),
                "color": payload.get("color"),
                "title": payload.get("title", "Chart"),
            }
            if not args.get("sql") or not args.get("x") or not args.get("y"):
                return AgentResult(
                    content="Chart requests need sql, x, and y fields. Please clarify.",
                    agent=self.name,
                )
            result = tool_registry.call("chart_from_sql", args)
            tool_call = ToolCall(name="chart_from_sql", arguments=args)
            summary = f"Generated chart '{args.get('title')}' with {result.get('count', 0)} rows."
            return AgentResult(
                content=summary,
                agent=self.name,
                tool_calls=[tool_call],
                metadata={"chart": result.get("spec")},
            )

        sql = self._sanitize_sql(payload.get("sql") or "")
        if not sql:
            return AgentResult(
                content="Please provide a query intent so I can generate SQL.",
                agent=self.name,
            )
        sql = self._ensure_limit(sql, settings.sql_agent_default_limit)
        result = tool_registry.call(
            "query_sql",
            {"sql": sql, "limit": settings.sql_agent_default_limit},
        )
        tool_call = ToolCall(
            name="query_sql",
            arguments={"sql": sql, "limit": settings.sql_agent_default_limit},
        )
        return AgentResult(
            content=SqlAgentAdapter._format_result(sql, result),
            agent=self.name,
            tool_calls=[tool_call],
            metadata={"count": result.get("count", 0)},
        )

    @staticmethod
    def _build_prompt(message: str, history: Optional[List[Dict[str, str]]]) -> str:
        history_block = ""
        if history:
            history_block = "\n".join(
                [f"{item.get('role', 'user')}: {item.get('content', '')}" for item in history[-6:]]
            )
        return (
            "You are a data agent. Decide whether to generate SQL or a chart. "
            "Return ONLY JSON with keys: action (query_sql|chart_from_sql), sql, mark, x, y, color, title. "
            "Use only tables: patients, EHVOL. Ensure SQL is SELECT-only.\n\n"
            f"Conversation history:\n{history_block}\n\n"
            f"User request: {message}\n"
        )

    @staticmethod
    def _extract_json(text: str) -> Optional[Dict[str, Any]]:
        if not text:
            return None
        try:
            return json.loads(text)
        except Exception:
            cleaned = re.sub(r"```json|```", "", text, flags=re.IGNORECASE).strip()
            try:
                return json.loads(cleaned)
            except Exception:
                pass
            match = re.search(r"\{[\s\S]*\}", text)
            if not match:
                return None
            try:
                return json.loads(match.group(0))
            except Exception:
                return None

    @staticmethod
    def _sanitize_sql(sql: str) -> str:
        if not sql:
            return ""
        lowered = sql.strip().lower()
        if not (lowered.startswith("select ") or lowered.startswith("with ")):
            return ""
        forbidden = [";", "insert ", "update ", "delete ", "drop ", "alter ", "create "]
        if any(token in lowered for token in forbidden):
            return ""
        return sql.strip()

    @staticmethod
    def _ensure_limit(sql: str, limit: int) -> str:
        if re.search(r"\blimit\b", sql, flags=re.IGNORECASE):
            return sql
        return f"{sql.rstrip()} LIMIT {int(limit)}"

    def _sanitize_mark(self, mark: str) -> str:
        cleaned = (mark or "").strip().lower()
        return cleaned if cleaned in self._allowed_marks else "bar"


class RagAgentAdapter:
    name = "rag"

    async def run(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]],
        tool_registry: ToolRegistry,
    ) -> AgentResult:
        from app.services.rag_agent import rag_agent_service
        if rag_agent_service is None:
            return AgentResult(
                content="RAG service is unavailable. Please try again later.",
                agent=self.name,
            )
        response = await rag_agent_service.run(message)
        return AgentResult(content=response, agent=self.name)


class CohortAgent:
    name = "cohort"

    async def run(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]],
        tool_registry: ToolRegistry,
    ) -> AgentResult:
        args = self._extract_filters(message)
        result = tool_registry.call("build_cohort", args)
        tool_call = ToolCall(name="build_cohort", arguments=args)
        summary = f"Built cohort with {result.get('count', 0)} patients."
        return AgentResult(content=summary, agent=self.name, tool_calls=[tool_call])

    def _extract_filters(self, message: str) -> Dict[str, Any]:
        text = (message or "").lower()
        args: Dict[str, Any] = {}

        age_match = re.search(r"(\d{1,3})\s*[-–]\s*(\d{1,3})\s*years?", text)
        if age_match:
            args["age_min"] = int(age_match.group(1))
            args["age_max"] = int(age_match.group(2))

        if "male" in text:
            args["gender"] = "male"
        if "female" in text:
            args["gender"] = "female"

        if "diabetes" in text:
            args["has_diabetes"] = True
        if "hypertension" in text:
            args["has_hypertension"] = True
        if "echo" in text:
            args["has_echo"] = True
        if "mri" in text:
            args["has_mri"] = True

        args.setdefault("limit", 100)
        return args


class UiAgent:
    name = "ui"

    async def run(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]],
        tool_registry: ToolRegistry,
    ) -> AgentResult:
        return AgentResult(
            content="I can navigate you to the requested view. Try: open registry, open analytics, or open cohort builder.",
            agent=self.name,
        )


class FallbackAgent:
    name = "general"

    async def run(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]],
        tool_registry: ToolRegistry,
    ) -> AgentResult:
        return AgentResult(
            content="I can help with registry questions, cohorts, or notes. Ask about counts, cohorts, or clinical notes.",
            agent=self.name,
        )


class ChatOrchestrator:
    def __init__(
        self,
        tool_registry: ToolRegistry,
        router: Optional[IntentRouter] = None,
        use_llm_router: bool = True,
    ) -> None:
        self._tool_registry = tool_registry
        self._router = router or IntentRouter()
        self._use_llm_router = use_llm_router
        self._orchestrator_llm = (
            ChatOllama(
                base_url=settings.ollama_base_url,
                model=settings.ollama_orchestrator_model,
                temperature=0,
            )
            if use_llm_router
            else None
        )
        self._allowed_intents = {
            "data",
            "medical",
            "rag",
            "cohort",
            "ui",
            "general",
        }
        self._agents: Dict[str, Agent] = {
            "data": DataAgentAdapter(),
            "medical": MedicalAgentAdapter(),
            "rag": RagAgentAdapter(),
            "cohort": CohortAgent(),
            "ui": UiAgent(),
            "general": FallbackAgent(),
        }
        self._agents["sql"] = self._agents["data"]
        self._agents["coding"] = self._agents["data"]

    async def _route_with_llm(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]],
    ) -> Optional[str]:
        if not self._orchestrator_llm:
            return None

        history_block = ""
        if history:
            history_block = "\n".join(
                [f"{item.get('role', 'user')}: {item.get('content', '')}" for item in history[-6:]]
            )
        prompt = (
            "You are an orchestrator. Route the user request to exactly one intent from: "
            "data, medical, rag, cohort, ui, general. "
            "Return ONLY the intent string.\n\n"
            f"Conversation history:\n{history_block}\n\n"
            f"User request: {message}\n"
        )
        response = await _ainvoke_with_retries(
            self._orchestrator_llm,
            prompt,
            timeout_s=settings.orchestrator_llm_timeout_s,
            max_retries=settings.llm_max_retries,
        )
        intent = (response.content or "").strip().lower()
        intent = re.sub(r"[^a-z]", "", intent)
        if intent in {"sql", "coding"}:
            intent = "data"
        return intent if intent in self._allowed_intents else None

    def _should_use_llm_router(self, intent: str) -> bool:
        return self._use_llm_router and intent == "general"

    def _normalize_intent(self, intent: str) -> str:
        if intent in {"sql", "coding"}:
            return "data"
        return intent

    async def run(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None,
        request_id: Optional[str] = None,
    ) -> AgentResult:
        intent = self._router.classify(message)
        if self._should_use_llm_router(intent):
            llm_intent = await self._route_with_llm(message, history)
            if llm_intent:
                intent = llm_intent
        intent = self._normalize_intent(intent)
        audit_event("intent_routed", {"intent": intent, "message": message[:200]}, request_id)
        agent = self._agents.get(intent, self._agents["general"])
        audit_event("agent_selected", {"agent": getattr(agent, "name", intent)}, request_id)
        result = await agent.run(message, history, self._tool_registry)
        audit_event(
            "agent_completed",
            {"agent": result.agent, "tool_calls": [tc.name for tc in result.tool_calls]},
            request_id,
        )
        if result.agent != "medical":
            medical_agent = self._agents["medical"]
            audit_event(
                "agent_handoff",
                {"from": result.agent, "to": "medical"},
                request_id,
            )
            if hasattr(medical_agent, "run_handoff"):
                return await medical_agent.run_handoff(message, history, result)
            combined_message = (
                f"User question: {message}\n\n"
                f"Specialist agent ({result.agent}) summary:\n{result.content}"
            )
            return await medical_agent.run(combined_message, history, self._tool_registry)
        return result


def get_default_orchestrator() -> ChatOrchestrator:
    tool_registry = ToolRegistry()
    return ChatOrchestrator(tool_registry=tool_registry)