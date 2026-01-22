import os
import sys
from typing import List

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

REQUIRED_COLUMNS = {"id", "age", "gender", "ef", "hypertension", "notes"}


def get_env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        raise ValueError(f"Missing required env var: {name}")
    return value


def build_connection_url() -> str:
    host = get_env("SQLSERVER_HOST")
    port = get_env("SQLSERVER_PORT", "1433")
    db = get_env("SQLSERVER_DB")
    user = get_env("SQLSERVER_USER")
    password = get_env("SQLSERVER_PASSWORD")
    driver = os.getenv("SQLSERVER_DRIVER", "ODBC Driver 18 for SQL Server")
    trust_raw = os.getenv("SQLSERVER_TRUST_CERT", "true")
    trust_cert = "yes" if str(trust_raw).lower() in {"true", "1", "yes"} else "no"

    return (
        "mssql+pyodbc://"
        f"{user}:{password}@{host}:{port}/{db}"
        f"?driver={driver.replace(' ', '+')}"
        f"&TrustServerCertificate={trust_cert}"
    )


def read_schema(conn) -> List[dict]:
    query = text(
        """
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'patients'
        """
    )
    rows = conn.execute(query).fetchall()
    return [row[0] for row in rows]


def run():
    url = build_connection_url()
    engine = create_engine(url, pool_pre_ping=True)

    with engine.connect() as conn:
        columns = read_schema(conn)
        if not columns:
            raise RuntimeError("No columns found for patients table. Check schema or table name.")

        missing = REQUIRED_COLUMNS.difference({c.lower() for c in columns})
        if missing:
            raise RuntimeError(f"Missing expected columns in patients table: {sorted(missing)}")

        schema_query = text(
            """
            SELECT TOP 10 id, age, gender, ef, hypertension
            FROM patients
            ORDER BY id
            """
        )
        rows = conn.execute(schema_query).fetchall()

    print("SQL Server patients table schema (columns):")
    print(columns)
    print("\nSample rows (id, age, gender, ef, hypertension):")
    for row in rows:
        print(row)

    assert len(rows) > 0, "Expected at least 1 row in patients table"
    print("\nStage 1 OK: SQL Server connection + schema + sample rows")


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        print(f"Stage 1 FAILED: {exc}")
        sys.exit(1)
