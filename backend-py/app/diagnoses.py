from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Mapping, Sequence


class DiagnosisDefinition(Dict[str, Any]):
    key: str
    id: str
    column: str
    condition: str
    icd10Code: str
    category: str
    status: str
    severity: str
    clinicalNotes: str


class DiagnosisSummary(Dict[str, Any]):
    id: str
    condition: str
    icd10Code: str
    category: str
    diagnosedDate: str
    status: str
    severity: str
    clinicalNotes: str


DIAGNOSIS_DEFINITIONS: Sequence[DiagnosisDefinition] = [
    {
        "key": "hypertension",
        "id": "D001",
        "column": "high_blood_pressure",
        "condition": "Hypertension",
        "icd10Code": "I10",
        "category": "Cardiovascular",
        "status": "treated",
        "severity": "Present",
        "clinicalNotes": "Recorded in medical history",
    },
    {
        "key": "diabetes",
        "id": "D002",
        "column": "diabetes_mellitus",
        "condition": "Diabetes Mellitus",
        "icd10Code": "E11",
        "category": "Metabolic",
        "status": "treated",
        "severity": "Present",
        "clinicalNotes": "Recorded in medical history",
    },
    {
        "key": "dyslipidemia",
        "id": "D003",
        "column": "dyslipidemia",
        "condition": "Dyslipidemia",
        "icd10Code": "E78.5",
        "category": "Metabolic",
        "status": "treated",
        "severity": "Present",
        "clinicalNotes": "Recorded in medical history",
    },
    {
        "key": "cad",
        "id": "D004",
        "column": "heart_attack_or_angina",
        "condition": "Coronary Heart Disease / Angina",
        "icd10Code": "I25.1",
        "category": "Cardiovascular",
        "status": "symptomatic",
        "severity": "Present",
        "clinicalNotes": "History of heart attack or angina",
    },
    {
        "key": "heart_failure",
        "id": "D005",
        "column": "prior_heart_failure",
        "condition": "Heart Failure",
        "icd10Code": "I50",
        "category": "Cardiovascular",
        "status": "treated",
        "severity": "Present",
        "clinicalNotes": "Prior heart failure",
    },
]


def _format_date(value: Any) -> str:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, str) and value:
        return value
    return "Not recorded"


def build_patient_diagnoses(row: Mapping[str, Any]) -> List[DiagnosisSummary]:
    diagnosed_date = _format_date(row.get("enrollment_date"))
    diagnoses: List[DiagnosisSummary] = []

    for definition in DIAGNOSIS_DEFINITIONS:
        if row.get(definition["column"]):
            diagnoses.append({
                "id": definition["id"],
                "condition": definition["condition"],
                "icd10Code": definition["icd10Code"],
                "category": definition["category"],
                "diagnosedDate": diagnosed_date,
                "status": definition["status"],
                "severity": definition["severity"],
                "clinicalNotes": definition["clinicalNotes"],
            })

    return diagnoses


def build_comorbidity_counts_sql(table: str = "patients") -> str:
    columns = [
        f"COUNT(*) FILTER (WHERE COALESCE({definition['column']}, false)) AS {definition['key']}"
        for definition in DIAGNOSIS_DEFINITIONS
    ]
    return f"SELECT {', '.join(columns)} FROM {table}"


def build_comorbidity_distribution_sql(table: str = "patients") -> str:
    expression = " + ".join(
        f"CASE WHEN COALESCE({definition['column']}, false) THEN 1 ELSE 0 END"
        for definition in DIAGNOSIS_DEFINITIONS
    )
    return (
        "SELECT comorbidity_count, COUNT(*) AS patient_count\n"
        f"FROM (SELECT ({expression}) AS comorbidity_count FROM {table}) AS c\n"
        "GROUP BY comorbidity_count\n"
        "ORDER BY comorbidity_count"
    )


def get_diagnosis_definitions() -> Sequence[DiagnosisDefinition]:
    return DIAGNOSIS_DEFINITIONS
