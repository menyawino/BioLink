import unittest
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = TESTS_DIR.parent
sys.path.insert(0, str(BACKEND_ROOT))

from app.services.orchestrator import ChatOrchestrator, AgentResult
from app.services.intent_router import IntentRouter


class DummyToolRegistry:
    def __init__(self):
        self.calls = []

    def call(self, tool: str, arguments=None):
        self.calls.append((tool, arguments or {}))
        if tool == "query_sql":
            return {"rows": [{"count": 10}], "count": 1}
        if tool == "build_cohort":
            return {"rows": [{"dna_id": "EHV001"}], "count": 1}
        return {"rows": [], "count": 0}


class DummyAgent:
    name = "rag"

    async def run(self, message, history, tool_registry):
        return AgentResult(content="rag ok", agent=self.name)


class DummyMedicalAgent:
    name = "medical"

    async def run(self, message, history, tool_registry):
        return AgentResult(content="medical ok", agent=self.name)

    async def run_handoff(self, message, history, agent_result):
        return AgentResult(
            content="medical ok",
            agent=self.name,
            tool_calls=agent_result.tool_calls,
            metadata={**agent_result.metadata, "handoff_from": agent_result.agent},
        )


class OrchestratorTests(unittest.IsolatedAsyncioTestCase):
    async def test_routes_to_sql_agent(self):
        registry = DummyToolRegistry()
        orchestrator = ChatOrchestrator(
            tool_registry=registry,
            router=IntentRouter(),
            use_llm_router=False,
        )
        orchestrator._agents["medical"] = DummyMedicalAgent()
        result = await orchestrator.run("How many patients are there?")
        self.assertEqual(result.agent, "medical")
        self.assertEqual(result.metadata.get("handoff_from"), "data")
        self.assertTrue(any(call[0] == "query_sql" for call in registry.calls))

    async def test_routes_to_cohort_agent(self):
        registry = DummyToolRegistry()
        orchestrator = ChatOrchestrator(
            tool_registry=registry,
            router=IntentRouter(),
            use_llm_router=False,
        )
        orchestrator._agents["medical"] = DummyMedicalAgent()
        result = await orchestrator.run("Build a cohort of male patients with diabetes")
        self.assertEqual(result.agent, "medical")
        self.assertEqual(result.metadata.get("handoff_from"), "cohort")
        self.assertTrue(any(call[0] == "build_cohort" for call in registry.calls))

    async def test_routes_to_ui_agent(self):
        registry = DummyToolRegistry()
        orchestrator = ChatOrchestrator(
            tool_registry=registry,
            router=IntentRouter(),
            use_llm_router=False,
        )
        orchestrator._agents["medical"] = DummyMedicalAgent()
        result = await orchestrator.run("Open the analytics dashboard")
        self.assertEqual(result.agent, "medical")
        self.assertEqual(result.metadata.get("handoff_from"), "ui")

    async def test_routes_to_rag_agent(self):
        registry = DummyToolRegistry()
        orchestrator = ChatOrchestrator(
            tool_registry=registry,
            router=IntentRouter(),
            use_llm_router=False,
        )
        orchestrator._agents["rag"] = DummyAgent()
        orchestrator._agents["medical"] = DummyMedicalAgent()
        result = await orchestrator.run("Find mention of hypertension in notes")
        self.assertEqual(result.agent, "medical")
        self.assertEqual(result.metadata.get("handoff_from"), "rag")

    async def test_tool_crosstalk_sql_to_tools(self):
        registry = DummyToolRegistry()
        orchestrator = ChatOrchestrator(
            tool_registry=registry,
            router=IntentRouter(),
            use_llm_router=False,
        )
        orchestrator._agents["medical"] = DummyMedicalAgent()
        result = await orchestrator.run("SELECT COUNT(*) FROM patient_summary")
        self.assertEqual(result.agent, "medical")
        self.assertEqual(result.metadata.get("handoff_from"), "data")
        self.assertTrue(any(call[0] == "query_sql" for call in registry.calls))


if __name__ == "__main__":
    unittest.main()