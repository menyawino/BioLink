import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))


def build_db_url():
    host = os.getenv("SQLSERVER_HOST", "localhost")
    port = os.getenv("SQLSERVER_PORT", "1433")
    user = os.getenv("SQLSERVER_USER", "sa")
    password = os.getenv("SQLSERVER_PASSWORD", "Strong!Passw0rd")
    db = os.getenv("SQLSERVER_DB", "EHVol")
    driver = os.getenv("SQLSERVER_DRIVER", "ODBC Driver 18 for SQL Server").replace(" ", "+")
    trust_raw = os.getenv("SQLSERVER_TRUST_CERT", "true")
    trust = "yes" if str(trust_raw).lower() in {"true", "1", "yes"} else "no"
    return f"mssql+pyodbc://{user}:{password}@{host}:{port}/{db}?driver={driver}&TrustServerCertificate={trust}"


def run():
    engine = create_engine(build_db_url(), isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        conn.execute(text("EXEC sys.sp_cdc_enable_db"))
        conn.execute(
            text(
                """
                EXEC sys.sp_cdc_enable_table
                    @source_schema = 'dbo',
                    @source_name = 'patients',
                    @role_name = NULL
                """
            )
        )

    print("Stage 0b OK: CDC enabled for EHVol.dbo.patients")


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        print(f"Stage 0b FAILED: {exc}")
        sys.exit(1)
