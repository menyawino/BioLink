from __future__ import annotations

import json
import logging
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
        if "how many" in text or ("count" in text and "patient" in text):
            return "SELECT COUNT(*) AS count FROM patient_summary"
        if "average age" in text:
            return "SELECT AVG(age) AS avg_age FROM patient_summary WHERE age IS NOT NULL"
        if "age distribution" in text:
            return "SELECT age FROM patient_summary WHERE age IS NOT NULL"
        if "count" in text and "gender" in text:
            return "SELECT gender, COUNT(*) AS count FROM patient_summary GROUP BY gender"
        if "average" in text and "ef" in text:
            return "SELECT AVG(echo_ef) AS avg_ef FROM patient_summary WHERE echo_ef IS NOT NULL"
        if "registry overview" in text or "overview" in text:
            return "SELECT COUNT(*) AS total FROM patient_summary"
        return None

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
        response = await self._llm.ainvoke(prompt)
        return AgentResult(content=response.content, agent=self.name)

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


class CodingAgentAdapter:
    name = "coding"

    def __init__(self) -> None:
        self._llm = ChatOllama(
            base_url=settings.ollama_base_url,
            model=settings.ollama_coding_model,
            temperature=0,
        )

    async def run(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]],
        tool_registry: ToolRegistry,
    ) -> AgentResult:
        prompt = self._build_prompt(message, history)
        response = await self._llm.ainvoke(prompt)
        payload = self._extract_json(response.content)
        if not payload:
            return AgentResult(
                content="I couldn't parse a structured plan. Please rephrase the request with desired chart or SQL details.",
                agent=self.name,
            )

        action = payload.get("action", "query_sql")
        if action == "chart_from_sql":
            args = {
                "sql": payload.get("sql"),
                "mark": payload.get("mark", "bar"),
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

        sql = payload.get("sql") or ""
        if not sql:
            return AgentResult(
                content="Please provide a query intent so I can generate SQL.",
                agent=self.name,
            )
        result = tool_registry.call("query_sql", {"sql": sql, "limit": 200})
        tool_call = ToolCall(name="query_sql", arguments={"sql": sql, "limit": 200})
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
            "You are a data assistant. Decide whether to generate SQL or a chart. "
            "Return ONLY JSON with keys: action (query_sql|chart_from_sql), sql, mark, x, y, color, title. "
            "Use only tables: patients, patient_summary. Ensure SQL is SELECT-only.\n\n"
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
            match = re.search(r"\{[\s\S]*\}", text)
            if not match:
                return None
            try:
                return json.loads(match.group(0))
            except Exception:
                return None


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
    def __init__(self, tool_registry: ToolRegistry, router: Optional[IntentRouter] = None) -> None:
        self._tool_registry = tool_registry
        self._router = router or IntentRouter()
        self._agents: Dict[str, Agent] = {
            "sql": SqlAgentAdapter(),
            "medical": MedicalAgentAdapter(),
            "coding": CodingAgentAdapter(),
            "rag": RagAgentAdapter(),
            "cohort": CohortAgent(),
            "ui": UiAgent(),
            "general": FallbackAgent(),
        }

    async def run(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None,
        request_id: Optional[str] = None,
    ) -> AgentResult:
        intent = self._router.classify(message)
        audit_event("intent_routed", {"intent": intent, "message": message[:200]}, request_id)
        agent = self._agents.get(intent, self._agents["general"])
        audit_event("agent_selected", {"agent": getattr(agent, "name", intent)}, request_id)
        result = await agent.run(message, history, self._tool_registry)
        audit_event(
            "agent_completed",
            {"agent": result.agent, "tool_calls": [tc.name for tc in result.tool_calls]},
            request_id,
        )
        return result


def get_default_orchestrator() -> ChatOrchestrator:
    tool_registry = ToolRegistry()
    return ChatOrchestrator(tool_registry=tool_registry)