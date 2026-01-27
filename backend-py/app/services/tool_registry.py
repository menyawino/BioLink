from __future__ import annotations

import logging
import re
from typing import Any, Dict, Optional

import sqlalchemy as sa

logger = logging.getLogger(__name__)


def _get_engine():
    from app.database import engine
    return engine


class ToolRegistry:
    def __init__(self, engine_override=None) -> None:
        self._handlers = {
            "registry_overview": self.registry_overview,
            "query_sql": self.query_sql,
            "search_patients": self.search_patients,
            "build_cohort": self.build_cohort,
            "chart_from_sql": self.chart_from_sql,
        }
        self._allowed_tables = {"patients", "patient_summary"}
        self._max_limit = 500
        self._engine = engine_override

    def list_tools(self) -> Dict[str, Any]:
        return {"tools": sorted(self._handlers.keys())}

    def call(self, tool: str, arguments: Optional[dict] = None) -> Dict[str, Any]:
        if tool not in self._handlers:
            raise ValueError(f"Unknown tool: {tool}")
        args = arguments or {}
        return self._handlers[tool](args)

    def registry_overview(self, args: dict) -> Dict[str, Any]:
        engine = self._engine or _get_engine()
        query = """
        SELECT
          COUNT(*) AS total,
          COUNT(*) FILTER (WHERE LOWER(gender) IN ('male','m')) AS male,
          COUNT(*) FILTER (WHERE LOWER(gender) IN ('female','f')) AS female,
          ROUND(AVG(age), 1) AS avg_age,
          COUNT(*) FILTER (WHERE echo_ef IS NOT NULL) AS with_echo,
          COUNT(*) FILTER (WHERE mri_ef IS NOT NULL) AS with_mri
        FROM patients
        """
        with engine.connect() as conn:
            result = conn.execute(sa.text(query))
            row = result.fetchone()

        return {
            "total": row[0],
            "male": row[1],
            "female": row[2],
            "avg_age": float(row[3]) if row[3] else None,
            "with_echo": row[4],
            "with_mri": row[5],
        }

    def query_sql(self, args: dict) -> Dict[str, Any]:
        engine = self._engine or _get_engine()
        sql = args.get("sql", "")
        limit = int(args.get("limit", self._max_limit))
        safe_sql = self._sanitize_select_sql(sql, limit)

        with engine.connect() as conn:
            result = conn.execute(sa.text(safe_sql))
            rows = result.fetchall()
            columns = result.keys()

        return {
            "rows": [dict(zip(columns, row)) for row in rows],
            "count": len(rows),
        }

    def search_patients(self, args: dict) -> Dict[str, Any]:
        engine = self._engine or _get_engine()
        conditions = []
        params = {}

        if "search" in args and args["search"]:
            search_term = f"%{args['search']}%"
            conditions.append("(LOWER(name) LIKE :search OR CAST(dna_id AS TEXT) LIKE :search)")
            params["search"] = search_term.lower()

        if "gender" in args and args["gender"]:
            conditions.append("LOWER(gender) = :gender")
            params["gender"] = args["gender"].lower()

        if "age_min" in args and args["age_min"] is not None:
            conditions.append("age >= :age_min")
            params["age_min"] = args["age_min"]

        if "age_max" in args and args["age_max"] is not None:
            conditions.append("age <= :age_max")
            params["age_max"] = args["age_max"]

        where_clause = " AND ".join(conditions) if conditions else "TRUE"
        limit = int(args.get("limit", 50))
        limit = min(limit, self._max_limit)

        query = f"""
        SELECT dna_id, name, age, gender, enrollment_date
        FROM patients
        WHERE {where_clause}
        ORDER BY enrollment_date DESC
        LIMIT {limit}
        """

        with engine.connect() as conn:
            result = conn.execute(sa.text(query), params)
            rows = result.fetchall()
            columns = result.keys()

        return {
            "rows": [dict(zip(columns, row)) for row in rows],
            "count": len(rows),
        }

    def build_cohort(self, args: dict) -> Dict[str, Any]:
        engine = self._engine or _get_engine()
        conditions = []
        params = {}

        if args.get("age_min") is not None:
            conditions.append("age >= :age_min")
            params["age_min"] = args["age_min"]

        if args.get("age_max") is not None:
            conditions.append("age <= :age_max")
            params["age_max"] = args["age_max"]

        if args.get("gender"):
            conditions.append("LOWER(gender) = :gender")
            params["gender"] = args["gender"].lower()

        if args.get("has_diabetes") is not None:
            conditions.append("COALESCE(diabetes_mellitus, false) = :has_diabetes")
            params["has_diabetes"] = bool(args["has_diabetes"])

        if args.get("has_hypertension") is not None:
            conditions.append("COALESCE(high_blood_pressure, false) = :has_hypertension")
            params["has_hypertension"] = bool(args["has_hypertension"])

        if args.get("has_echo") is True:
            conditions.append("echo_ef IS NOT NULL")

        if args.get("has_mri") is True:
            conditions.append("mri_ef IS NOT NULL")

        where_clause = " AND ".join(conditions) if conditions else "TRUE"
        limit = int(args.get("limit", 100))
        limit = min(limit, self._max_limit)

        query = f"""
        SELECT
          dna_id, name, age, gender,
          diabetes_mellitus, high_blood_pressure,
          echo_ef, mri_ef,
          enrollment_date
        FROM patients
        WHERE {where_clause}
        ORDER BY enrollment_date DESC
        LIMIT {limit}
        """

        with engine.connect() as conn:
            result = conn.execute(sa.text(query), params)
            rows = result.fetchall()
            columns = result.keys()

        return {
            "rows": [dict(zip(columns, row)) for row in rows],
            "count": len(rows),
        }

    def chart_from_sql(self, args: dict) -> Dict[str, Any]:
        engine = self._engine or _get_engine()
        sql = args.get("sql", "")
        limit = int(args.get("limit", self._max_limit))
        safe_sql = self._sanitize_select_sql(sql, limit)

        with engine.connect() as conn:
            result = conn.execute(sa.text(safe_sql))
            rows = result.fetchall()
            columns = result.keys()

        data = [dict(zip(columns, row)) for row in rows]

        spec = {
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "description": "Generated chart",
            "title": args.get("title", "Chart"),
            "data": {"values": data},
            "mark": args.get("mark", "bar"),
            "encoding": {
                "x": {"field": args.get("x"), "type": args.get("x_type", "ordinal")},
                "y": {"field": args.get("y"), "type": args.get("y_type", "quantitative")},
            },
        }

        if args.get("color"):
            spec["encoding"]["color"] = {"field": args["color"], "type": "nominal"}

        return {
            "spec": spec,
            "rows": data,
            "count": len(data),
        }

    def _sanitize_select_sql(self, sql: str, limit: int) -> str:
        sql = (sql or "").strip()
        if not sql:
            raise ValueError("SQL must not be empty")

        if ";" in sql:
            raise ValueError("Multiple SQL statements are not allowed")

        normalized = sql.upper()
        if not normalized.startswith("SELECT") and not normalized.startswith("WITH"):
            raise ValueError("Only SELECT queries are allowed")

        forbidden = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "TRUNCATE", "COPY"]
        if any(word in normalized for word in forbidden):
            raise ValueError("Unsafe SQL detected")

        tables = self._extract_tables(sql)
        if tables and not tables.issubset(self._allowed_tables):
            raise ValueError("Query references disallowed tables")

        limit = max(1, min(int(limit), self._max_limit))
        if "LIMIT" not in normalized:
            sql = f"{sql} LIMIT {limit}"
        return sql

    @staticmethod
    def _extract_tables(sql: str) -> set:
        pattern = r"\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)"
        matches = re.findall(pattern, sql, flags=re.IGNORECASE)
        return {m.lower() for m in matches}