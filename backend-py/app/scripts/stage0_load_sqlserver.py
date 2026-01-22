import csv
import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

CSV_PATH = "/Users/menyawino/Playground/BioLink/Code/db/100925_Cleaned_EHVol_Data_STANDARDIZED.csv"

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))


def build_master_url():
    host = os.getenv("SQLSERVER_HOST", "localhost")
    port = os.getenv("SQLSERVER_PORT", "1433")
    user = os.getenv("SQLSERVER_USER", "sa")
    password = os.getenv("SQLSERVER_PASSWORD", "Strong!Passw0rd")
    driver = os.getenv("SQLSERVER_DRIVER", "ODBC Driver 18 for SQL Server").replace(" ", "+")
    trust_raw = os.getenv("SQLSERVER_TRUST_CERT", "true")
    trust = "yes" if str(trust_raw).lower() in {"true", "1", "yes"} else "no"
    return f"mssql+pyodbc://{user}:{password}@{host}:{port}/master?driver={driver}&TrustServerCertificate={trust}"


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


def ensure_database():
    engine = create_engine(build_master_url(), isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        conn.execute(text("IF DB_ID('EHVol') IS NULL CREATE DATABASE EHVol"))


def ensure_table():
    engine = create_engine(build_db_url())
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                IF OBJECT_ID('patients', 'U') IS NULL
                CREATE TABLE patients (
                    id NVARCHAR(64) NOT NULL PRIMARY KEY,
                    age INT NULL,
                    gender NVARCHAR(32) NULL,
                    ef FLOAT NULL,
                    hypertension BIT NULL,
                    notes NVARCHAR(MAX) NULL
                )
                """
            )
        )


def load_csv(limit: int = 1000):
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"CSV not found: {CSV_PATH}")

    engine = create_engine(build_db_url())

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = []
        for idx, row in enumerate(reader):
            if idx >= limit:
                break

            patient_id = row.get("dna_id") or row.get("id") or str(idx)
            age = row.get("age")
            gender = row.get("gender")
            ef = row.get("ef")
            hypertension = row.get("high_blood_pressure") or row.get("hypertension")

            def safe_int(val):
                try:
                    return int(float(val))
                except Exception:
                    return None

            def safe_float(val):
                try:
                    return float(val)
                except Exception:
                    return None

            def safe_bool(val):
                if val is None:
                    return None
                try:
                    return 1 if float(val) > 0 else 0
                except Exception:
                    return None

            notes_parts = []
            city = row.get("current_city_of_residence") or row.get("current_city_category")
            if city:
                notes_parts.append(f"city: {city}")
            if ef is not None and ef != "":
                notes_parts.append(f"ef: {ef}")
            for key in ["comorbidity", "ecg_conclusion", "procedure_details", "what_is_this_these_condition_s_", "who_and_what_disease_"]:
                if row.get(key):
                    notes_parts.append(f"{key}: {row.get(key)}")
            notes = " | ".join(notes_parts) if notes_parts else None

            rows.append(
                {
                    "id": str(patient_id),
                    "age": safe_int(age),
                    "gender": gender,
                    "ef": safe_float(ef),
                    "hypertension": safe_bool(hypertension),
                    "notes": notes,
                }
            )

    if not rows:
        raise RuntimeError("No rows loaded from CSV")

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM patients"))
        conn.execute(
            text(
                """
                INSERT INTO patients (id, age, gender, ef, hypertension, notes)
                VALUES (:id, :age, :gender, :ef, :hypertension, :notes)
                """
            ),
            rows,
        )

    print(f"Loaded {len(rows)} rows into SQL Server patients table")


def run():
    ensure_database()
    ensure_table()
    load_csv(limit=1000)
    print("Stage 0 OK: SQL Server initialized")


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        print(f"Stage 0 FAILED: {exc}")
        sys.exit(1)
