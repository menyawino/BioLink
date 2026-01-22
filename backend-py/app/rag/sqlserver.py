from __future__ import annotations

from sqlalchemy import create_engine, text
from app.config import settings


def build_sqlserver_url() -> str:
    driver = settings.sqlserver_driver.replace(" ", "+")
    trust_raw = str(settings.sqlserver_trust_cert)
    trust = "yes" if trust_raw.lower() in {"true", "1", "yes"} else "no"
    return (
        "mssql+pyodbc://"
        f"{settings.sqlserver_user}:{settings.sqlserver_password}"
        f"@{settings.sqlserver_host}:{settings.sqlserver_port}/{settings.sqlserver_db}"
        f"?driver={driver}&TrustServerCertificate={trust}"
    )


def get_engine():
    url = build_sqlserver_url()
    return create_engine(url, pool_pre_ping=True)


def get_patient_columns():
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'patients'
                """
            )
        ).fetchall()
    return {row[0].lower() for row in rows}


def fetch_patients(limit: int = 10):
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT TOP (:limit) id, age, gender, ef, hypertension, notes
                FROM patients
                WHERE notes IS NOT NULL
                ORDER BY id
                """
            ),
            {"limit": limit},
        ).fetchall()
    return rows


def fetch_patients_by_ids(patient_ids: list[str]):
    if not patient_ids:
        return {}

    columns = get_patient_columns()
    select_cols = ["id", "age", "gender", "ef", "notes"]
    if "current_city" in columns:
        select_cols.append("current_city")
    elif "city" in columns:
        select_cols.append("city")

    placeholders = ", ".join([f":id{i}" for i in range(len(patient_ids))])
    params = {f"id{i}": pid for i, pid in enumerate(patient_ids)}

    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                f"""
                SELECT {", ".join(select_cols)}
                FROM patients
                WHERE id IN ({placeholders})
                """
            ),
            params,
        ).fetchall()

    results = {}
    for row in rows:
        data = dict(zip(select_cols, row))
        city = data.pop("current_city", None) or data.pop("city", None)
        notes = data.get("notes")
        if not city and notes:
            for part in str(notes).split("|"):
                part = part.strip()
                if part.lower().startswith("city:"):
                    city = part.split(":", 1)[1].strip() or None
                    break
        results[str(data.get("id"))] = {
            "age": data.get("age"),
            "gender": data.get("gender"),
            "ef": data.get("ef"),
            "city": city,
            "notes": notes,
        }
    return results


def fetch_patient_ids_by_filters(
    age_min: int | None,
    age_max: int | None,
    gender: str | None,
    ef_min: float | None = None,
    ef_max: float | None = None,
    city: str | None = None,
    limit: int = 200,
):
    columns = get_patient_columns()
    clauses = []
    params = {"limit": limit}
    if age_min is not None:
        clauses.append("age >= :age_min")
        params["age_min"] = age_min
    if age_max is not None:
        clauses.append("age <= :age_max")
        params["age_max"] = age_max
    if gender:
        clauses.append("LOWER(gender) = LOWER(:gender)")
        params["gender"] = gender
    if ef_min is not None and "ef" in columns:
        clauses.append("ef >= :ef_min")
        params["ef_min"] = ef_min
    if ef_max is not None and "ef" in columns:
        clauses.append("ef <= :ef_max")
        params["ef_max"] = ef_max
    if city and "current_city" in columns:
        clauses.append("LOWER(current_city) = LOWER(:city)")
        params["city"] = city
    elif city and "city" in columns:
        clauses.append("LOWER(city) = LOWER(:city)")
        params["city"] = city
    elif city and "notes" in columns:
        clauses.append("notes LIKE :city_note")
        params["city_note"] = f"%city: {city}%"

    where = " AND ".join(clauses)
    if where:
        where = f"WHERE {where}"

    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                f"""
                SELECT TOP (:limit) id
                FROM patients
                {where}
                ORDER BY id
                """
            ),
            params,
        ).fetchall()

    return [row[0] for row in rows]
