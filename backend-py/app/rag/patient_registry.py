from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import bindparam, text

from app.database import engine

PATIENT_TABLE = "patients"


def _get_patient_columns() -> set[str]:
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = :table_name
                """
            ),
            {"table_name": PATIENT_TABLE},
        ).fetchall()
    return {row[0] for row in rows}


def _first_available(columns: set[str], *candidates: str) -> str | None:
    for candidate in candidates:
        if candidate in columns:
            return candidate
    return None


def _aliased_expr(columns: set[str], alias: str, cast_type: str, *candidates: str) -> str:
    column_name = _first_available(columns, *candidates)
    if column_name:
        return f"{column_name} AS {alias}"
    return f"NULL::{cast_type} AS {alias}"


def _ef_expr(columns: set[str]) -> str:
    candidates = [
        column_name
        for column_name in ("ef", "mri_ef", "echo_ef", "lv_ejection_fraction")
        if column_name in columns
    ]
    if not candidates:
        return "NULL::double precision AS ef"
    if len(candidates) == 1:
        return f"{candidates[0]} AS ef"
    return f"COALESCE({', '.join(candidates)}) AS ef"


def _select_fields(columns: set[str]) -> list[str]:
    id_column = _first_available(columns, "id", "record_id", "dna_id")
    if not id_column:
        raise RuntimeError("No patient identifier column found in Postgres patients table")

    return [
        f"{id_column} AS id",
        _aliased_expr(columns, "age", "integer", "age"),
        _aliased_expr(columns, "gender", "text", "gender"),
        _ef_expr(columns),
        _aliased_expr(
            columns,
            "hypertension",
            "boolean",
            "high_blood_pressure",
            "hypertension",
        ),
        _aliased_expr(
            columns,
            "current_city",
            "text",
            "current_city",
            "current_city_category",
        ),
        _aliased_expr(columns, "hba1c", "double precision", "hba1c"),
        _aliased_expr(columns, "troponin_i", "double precision", "troponin_i"),
        _aliased_expr(columns, "ecg_conclusion", "text", "ecg_conclusion"),
        _aliased_expr(columns, "current_smoker", "boolean", "current_smoker"),
        _aliased_expr(columns, "former_smoker", "boolean", "former_smoker"),
        _aliased_expr(columns, "smoking_years", "double precision", "smoking_years"),
        _aliased_expr(columns, "diabetes_mellitus", "boolean", "diabetes_mellitus"),
        _aliased_expr(columns, "dyslipidemia", "boolean", "dyslipidemia"),
        _aliased_expr(
            columns,
            "heart_attack_or_angina",
            "boolean",
            "heart_attack_or_angina",
        ),
    ]


def _normalize_patient_ids(patient_ids: Iterable[str]) -> list[int | str]:
    normalized: list[int | str] = []
    for patient_id in patient_ids:
        patient_id_str = str(patient_id).strip()
        if not patient_id_str:
            continue
        if patient_id_str.isdigit():
            normalized.append(int(patient_id_str))
        else:
            normalized.append(patient_id_str)
    return normalized


def _build_patient_note(row: dict[str, object]) -> str | None:
    parts: list[str] = []

    current_city = row.get("current_city")
    if current_city:
        parts.append(f"city: {current_city}")

    ef = row.get("ef")
    if ef is not None:
        parts.append(f"ef: {ef}")

    hba1c = row.get("hba1c")
    if hba1c is not None:
        parts.append(f"hba1c: {hba1c}")

    troponin_i = row.get("troponin_i")
    if troponin_i is not None:
        parts.append(f"troponin_i: {troponin_i}")

    ecg_conclusion = row.get("ecg_conclusion")
    if ecg_conclusion:
        parts.append(f"ecg_conclusion: {ecg_conclusion}")

    for field_name, label in (
        ("hypertension", "hypertension"),
        ("diabetes_mellitus", "diabetes"),
        ("dyslipidemia", "dyslipidemia"),
        ("heart_attack_or_angina", "heart_attack_or_angina"),
        ("current_smoker", "current_smoker"),
        ("former_smoker", "former_smoker"),
    ):
        if row.get(field_name) is True:
            parts.append(f"{label}: yes")

    smoking_years = row.get("smoking_years")
    if smoking_years is not None:
        parts.append(f"smoking_years: {smoking_years}")

    return " | ".join(parts) or None


def fetch_patients(limit: int = 10):
    columns = _get_patient_columns()
    select_fields = _select_fields(columns)

    with engine.connect() as conn:
        rows = conn.execute(
            text(
                f"""
                SELECT {', '.join(select_fields)}
                FROM {PATIENT_TABLE}
                ORDER BY id
                LIMIT :limit
                """
            ),
            {"limit": limit},
        ).mappings().all()

    results = []
    for row in rows:
        note_text = _build_patient_note(dict(row))
        if not note_text:
            continue
        results.append(
            (
                row["id"],
                row["age"],
                row["gender"],
                row["ef"],
                row["hypertension"],
                note_text,
            )
        )
    return results


def fetch_patients_by_ids(patient_ids: list[str]):
    normalized_ids = _normalize_patient_ids(patient_ids)
    if not normalized_ids:
        return {}

    columns = _get_patient_columns()
    select_fields = _select_fields(columns)
    query = text(
        f"""
        SELECT {', '.join(select_fields)}
        FROM {PATIENT_TABLE}
        WHERE id IN :patient_ids
        ORDER BY id
        """
    ).bindparams(bindparam("patient_ids", expanding=True))

    with engine.connect() as conn:
        rows = conn.execute(query, {"patient_ids": normalized_ids}).mappings().all()

    results = {}
    for row in rows:
        record = dict(row)
        results[str(record["id"])] = {
            "age": record.get("age"),
            "gender": record.get("gender"),
            "ef": record.get("ef"),
            "city": record.get("current_city"),
            "notes": _build_patient_note(record),
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
    columns = _get_patient_columns()
    id_column = _first_available(columns, "id", "record_id", "dna_id")
    if not id_column:
        raise RuntimeError("No patient identifier column found in Postgres patients table")

    ef_column = _first_available(columns, "ef", "mri_ef", "echo_ef", "lv_ejection_fraction")
    city_column = _first_available(columns, "current_city", "current_city_category")

    clauses: list[str] = []
    params: dict[str, object] = {"limit": limit}

    if age_min is not None and "age" in columns:
        clauses.append("age >= :age_min")
        params["age_min"] = age_min
    if age_max is not None and "age" in columns:
        clauses.append("age <= :age_max")
        params["age_max"] = age_max
    if gender and "gender" in columns:
        clauses.append("LOWER(gender) = LOWER(:gender)")
        params["gender"] = gender
    if ef_min is not None and ef_column:
        clauses.append(f"{ef_column} >= :ef_min")
        params["ef_min"] = ef_min
    if ef_max is not None and ef_column:
        clauses.append(f"{ef_column} <= :ef_max")
        params["ef_max"] = ef_max
    if city and city_column:
        clauses.append(f"LOWER({city_column}) = LOWER(:city)")
        params["city"] = city

    where_clause = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    with engine.connect() as conn:
        rows = conn.execute(
            text(
                f"""
                SELECT {id_column} AS id
                FROM {PATIENT_TABLE}
                {where_clause}
                ORDER BY {id_column}
                LIMIT :limit
                """
            ),
            params,
        ).mappings().all()

    return [str(row["id"]) for row in rows]