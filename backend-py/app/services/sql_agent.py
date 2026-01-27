from __future__ import annotations

import logging
import re
from typing import List, Optional

from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit, create_sql_agent
from fastapi.concurrency import run_in_threadpool

from app.config import settings

logger = logging.getLogger(__name__)


class SafeSQLDatabaseToolkit(SQLDatabaseToolkit):
    def __init__(self, db: SQLDatabase, llm: ChatOllama, default_limit: int):
        super().__init__(db=db, llm=llm)
        self._default_limit = default_limit

    def get_tools(self):
        tools = super().get_tools()
        filtered = [t for t in tools if t.name != "query_sql_db"]
        filtered.append(self._safe_query_tool())
        return filtered

    def _safe_query_tool(self):
        db = self.db
        default_limit = self._default_limit

        @tool("query_sql_safe")
        def query_sql_safe(query: str) -> str:
            """Execute a read-only SQL query (SELECT only)."""
            if not query.strip().upper().startswith("SELECT"):
                raise ValueError("Only SELECT queries are allowed.")
            if "COUNT(" in query.upper() and "LIMIT" not in query.upper():
                # For COUNT queries, don't add LIMIT
                pass
            elif "LIMIT" not in query.upper():
                query = f"{query} LIMIT {default_limit}"
            return db.run(query)

        return query_sql_safe


class SqlAgentService:
    def __init__(self):
        self.db = SQLDatabase.from_uri(
            settings.database_url,
            sample_rows_in_table_info=2,
            include_tables=None
        )
        self.llm = ChatOllama(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            temperature=0
        )

    async def run(self, message: str, history: Optional[List[dict]] = None) -> str:
        table_info = self.db.get_table_info()
        prompt = (
            "You are a SQL assistant for a clinical registry database. "
            "The database schema is:\n"
            f"{table_info}\n\n"
            "Generate only a SELECT SQL query to answer the user's question. "
            "Do not add any explanation, just the SQL query. "
            "For COUNT queries, do not add LIMIT. "
            "For other queries, add LIMIT 200 if not present. "
            f"Question: {message}"
        )
        response = await self.llm.ainvoke(prompt)
        sql = response.content.strip()
        sql = self._rewrite_sql_columns(sql, table_info)
        if not sql.upper().startswith("SELECT"):
            return "Generated query is not a SELECT statement."
        
        # Execute in thread
        result = await run_in_threadpool(self._execute_sql, sql)
        return f"Query executed: {sql}\nResult: {result}"

    def _execute_sql(self, sql: str) -> str:
        try:
            return self.db.run(sql)
        except Exception as e:
            return f"SQL Error: {e}"

    @staticmethod
    def _rewrite_sql_columns(sql: str, table_info: str) -> str:
        if not sql or not table_info:
            return sql

        rewritten = sql
        if "current_city" in table_info and re.search(r"\bcity\b", rewritten, flags=re.IGNORECASE):
            rewritten = re.sub(r"\bcity\b", "current_city", rewritten, flags=re.IGNORECASE)

        if "current_city_category" in table_info and re.search(r"\bcity_category\b", rewritten, flags=re.IGNORECASE):
            rewritten = re.sub(r"\bcity_category\b", "current_city_category", rewritten, flags=re.IGNORECASE)

        return rewritten


try:
    sql_agent_service = SqlAgentService()
except Exception as e:
    logger.error(f"SQL agent initialization failed: {e}")
    sql_agent_service = None
