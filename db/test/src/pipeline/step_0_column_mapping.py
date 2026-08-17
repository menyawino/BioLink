from __future__ import annotations

import csv
import re
from pathlib import Path


from src.config import INTERIM_DIR, DATASETS

CATEGORY_TO_FAMILY = {
    "Administration & Consent": "Participant Context",
    "Timeline & Dates": "Participant Context",
    "Demographics & Social Context": "Participant Context",
    "Family History & Lineage": "Participant Context",
    "Lifestyle & Risk Factors": "Participant Context",
    "Questionnaires & Reported Symptoms": "Participant Context",
    "Diagnoses & Medical History": "Clinical Profiles",
    "Medication & Dosing": "Clinical Profiles",
    "Procedures & Interventions": "Clinical Profiles",
    "Vitals & Anthropometrics": "Clinical Profiles",
    "Laboratory Tests & Biomarkers": "Clinical Profiles",
    "ECG & Rhythm": "Clinical Profiles",
    "Echocardiography & Vascular Imaging": "Clinical Profiles",
    "MRI / CT & Advanced Imaging": "Clinical Profiles",
    "Biobanking & Samples": "Research Assets",
    "Other / Needs Review": "Needs Review",
}

GENERIC_MEDICATION_FIELDS = {
    "name",
    "category",
    "status",
    "route",
    "total daily dose",
    "frequency",
}

LAB_EXACT_MATCHES = {
    "hba1c",
    "troponin i",
    "urea",
    "creatinine",
    "na",
    "k",
    "ca",
    "mg",
    "alt",
    "ast",
    "albumin",
    "crp",
    "hdl",
    "ldl",
    "vldl",
    "bnp",
    "hemoglobin",
    "hematocrit",
    "rbcs",
    "mcv",
    "mch",
    "mchc",
    "rdw",
    "tlc",
    "t3",
    "t4",
    "tsh",
    "cbc",
    "inr",
    "results",
}

ECHO_EXACT_MATCHES = {
    "lv size",
    "lvedd",
    "lvesd",
    "ivsd",
    "ivss",
    "lvpwd",
    "lvpws",
    "lvm",
    "ef",
    "fs",
    "lvh",
    "swt",
    "pwt",
    "rwma score",
    "rwma index",
    "tapse",
    "pasp",
    "ar",
    "as",
    "mr",
    "ms",
    "tr",
    "ts",
    "pr",
    "ps",
    "aortic root",
    "left atrium",
    "right ventricle",
}

ECHO_KEYWORDS = [
    "echo",
    "echocardiography",
    "echocardiographic",
    "tte",
    "abi",
    "brachial pressure",
    "tibial pressure",
    "imt",
    "atheromatous",
    "carotid",
    "duplex",
    "left atrial",
    "right ventricle",
    "left ventricular",
    "right ventricular",
    "aortic root",
    "aortic annulus",
    "sinus of valsalva",
    "sino tubular",
    "ascending aorta",
    "regional wall motion",
    "rwma",
    "pericardium",
    "valvular",
    "mitral",
    "tricuspid",
    "aortic stenosis",
    "aortic regurge",
    "pulmonary stenosis",
    "pulmonary regurge",
    "myxomatous",
    "degenerative valve",
    "congenital defect",
]

ECG_EXACT_MATCHES = {
    "rate",
    "rhythm",
    "ventricular rate",
    "pr interval",
    "qrs duration",
    "qt interval",
    "corrected qt interval",
    "qrs width 120 ms",
    "lvh",
    "ectopic beats",
    "notes",
}

VITALS_EXACT_MATCHES = {
    "bmi",
    "bp",
    "bsa",
    "jvp",
}

VITALS_KEYWORDS = [
    "heart rate",
    "blood pressure",
    "systolic blood pressure",
    "diastolic blood pressure",
    "weight",
    "height",
    "waist circumference",
    "hip circumference",
    "waist hip ratio",
    "fat mass",
    "fat free mass",
    "span",
]

DEMOGRAPHIC_SOCIAL_EXACT_MATCHES = {
    "parents occupation",
    "marital status",
    "number of wives",
    "non egyptian parents",
    "what is your marital status",
    "do you have more than one wife",
    "if more than 1 wife how many",
    "where did you spend your childhood",
}

MEDICAL_HISTORY_EXACT_MATCHES = {
    "heart attack or angina",
    "high blood pressure",
}

DIAGNOSIS_DETAIL_KEYWORDS = [
    "age of onset",
    "specify type",
    "specify disease",
    "number and date of hospitalizations",
    "specify type and age of onset",
    "and specify age of onset",
]

PROCEDURE_DETAIL_KEYWORDS = [
    "specify date",
    "type and date",
]

MEDICAL_HISTORY_KEYWORDS = [
    "heart attack",
    "high blood pressure",
    "dyslipidemia",
    "rheumatic fever",
    "anaemia",
    "lung problems",
    "kidney problems",
    "liver problems",
    "diabetes",
    "prior heart failure",
    "neurological problems",
    "muscloskeletal problems",
    "musculoskeletal problems",
    "autoimmune problems",
    "malignancy",
    "known cvs disease",
    "known collagen disease",
    "hypertension",
    "hyperlipidemia",
    "renal disease",
    "respiratory illnesses",
    "mi",
    "stroke",
    "tia",
    "congenital heart disease",
    "rhd",
    "pvd",
    "erectile dysfunction",
    "heart disease",
    "heart failure",
]

MEDICAL_TAXONOMY_PREFIXES = (
    "major category",
    "other co morbidities risk factors",
    "valvular heart disease",
    "ischaemic heart diseases",
    "heart failure",
    "myocardium cardiomyopathy",
    "endocardium",
    "pericardium",
    "pulmonary vascular disease",
    "complications of heart diseases",
    "hypertensive diseases",
    "hypotensive diseases",
    "diseases of arteries arterioles and capillaries",
    "cerebrovascular diseases",
    "acute rheumatic fever",
    "cardiac arrhythmias",
)

HEALTH_CATEGORIES = {
    "Family History & Lineage",
    "Lifestyle & Risk Factors",
    "Questionnaires & Reported Symptoms",
    "Diagnoses & Medical History",
    "Medication & Dosing",
    "Procedures & Interventions",
    "Vitals & Anthropometrics",
    "Laboratory Tests & Biomarkers",
    "ECG & Rhythm",
    "Echocardiography & Vascular Imaging",
    "MRI / CT & Advanced Imaging",
    "Biobanking & Samples",
}

DIRECT_IDENTIFIER_KEYWORDS = [
    "record id",
    "household identifier",
    "mrn",
    "dna id",
    "address",
    "contact number",
    "home tel",
    "mobile tel",
    "email",
    "upload",
    "scan",
    "pdf",
    "xml",
    "document",
    "report",
]

QUASI_IDENTIFIER_KEYWORDS = [
    "date of birth",
    "current age",
    "age at",
    "gender",
    "ethnicity",
    "nationality",
    "occupation",
    "marital status",
    "wives",
    "city",
    "gov of origin",
    "origin",
    "childhood",
    "speak nubian",
    "read and write in arabic",
    "degree obtained",
    "date",
    "enrolment",
    "enrollment",
]

ADVANCED_IMAGING_KEYWORDS = [
    "mri",
    "cmr",
    "ct",
    "x ray",
    "myocardial perfusion",
    "scan region",
    "imaging modality",
]


def normalize(text: str) -> str:
    return re.sub(r"[^\w]+", " ", (text or "").strip().lower()).strip()


def contains_any(text: str, phrases: list[str]) -> bool:
    return any(phrase in text for phrase in phrases)


def contains_whole_phrase(text: str, phrase: str) -> bool:
    pattern = rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])"
    return re.search(pattern, text) is not None


def contains_any_whole_phrase(text: str, phrases: list[str]) -> bool:
    return any(contains_whole_phrase(text, phrase) for phrase in phrases)


def contains_advanced_imaging_keyword(text: str) -> bool:
    return contains_any_whole_phrase(text, ADVANCED_IMAGING_KEYWORDS)


def read_dataset(path: Path) -> tuple[list[str], list[list[str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        rows = []
        for index, row in enumerate(reader):
            rows.append(row)
            if index >= 2:
                break
    if len(rows) < 2:
        raise ValueError(f"Expected at least one header row and one data row in {path.name}")
    headers = rows[0]
    samples = rows[1:3]
    return headers, samples


def value_at(samples: list[list[str]], row_index: int, column_index: int) -> str:
    if row_index >= len(samples):
        return ""
    row = samples[row_index]
    return row[column_index].strip() if column_index < len(row) else ""


def infer_anchor_context(dataset: str, header_norm: str, current_context: str) -> str:
    if current_context == "plan" and header_norm != "complete" and not header_norm.startswith(MEDICAL_TAXONOMY_PREFIXES):
        return "plan"
    if header_norm in {"hba1c", "troponin i", "date labs", "agree to withdraw samples for lab workup"}:
        return "labs"
    if header_norm in {"echo date", "date echocardiography", "agree to undergo tte", "date abi", "agree to undergo carotid duplex"}:
        return "echo"
    if header_norm in {"ecg date", "agree to have an ecg"}:
        return "ecg"
    if header_norm in {"date medications", "subject is on treatment", "do you take any medication currently", "list these medications"}:
        return "medications"
    if header_norm in {"intervention required", "date plan"}:
        return "plan"
    if header_norm in {"mri", "mri date", "agree to ct", "agree to cmr", "cardiac ct", "cardiac mri", "date of cardiac ct", "date of cardiac mri"}:
        return "imaging"
    if header_norm in {"date consent", "agree to consent", "consent obtained", "consent obtained yes", "consent obtained no"}:
        return "consent"
    if header_norm in {"agree to provide family history", "date family history", "pedigree", "offspring of consanguinous marriage"}:
        return "family"
    if header_norm in {"current recent smoker 1 year", "what is your current smoking status", "date risk factors"}:
        return "lifestyle"
    if header_norm in {"in general how would you rate your health today", "have you experienced shortness of breath", "have you ever had any pain or discomfort in your chest"}:
        return "symptoms"
    if header_norm in {"heart attack or angina", "high blood pressure", "known cvs disease", "major category choice none"}:
        return "medical"
    if header_norm in {"examination date", "date clinical exam"}:
        return "vitals"
    if header_norm.startswith(MEDICAL_TAXONOMY_PREFIXES) and current_context not in {
        "echo",
        "imaging",
        "ecg",
        "labs",
        "medications",
        "family",
        "lifestyle",
        "symptoms",
        "vitals",
        "consent",
    }:
        return "medical_taxonomy"
    if header_norm == "lifetime ascvd risk":
        return "risk_scores"
    if dataset == "EHVol" and header_norm == "rate":
        return "ecg"
    if dataset == "BHS" and header_norm == "date":
        return "timeline"
    return current_context


def classify_column(
    dataset: str,
    header: str,
    header_norm: str,
    current_context: str,
) -> tuple[str, str]:
    if header_norm == "complete":
        return "Administration & Consent", "form_completion"

    if header_norm.startswith("agree to "):
        return "Administration & Consent", "agreement_prompt"

    if header_norm == "dna id" or contains_any(header_norm, ["biobank", "sample", "re sampling"]):
        return "Biobanking & Samples", "sample_or_biobank_keyword"

    if current_context == "medical_taxonomy":
        return "Diagnoses & Medical History", "diagnosis_taxonomy_context"
    if current_context == "plan":
        return "Procedures & Interventions", "plan_context"
    if current_context == "imaging":
        return "MRI / CT & Advanced Imaging", "imaging_context"
    if current_context == "medications":
        if header_norm in GENERIC_MEDICATION_FIELDS:
            return "Medication & Dosing", "medication_context_generic_field"
        return "Medication & Dosing", "medication_context"
    if current_context == "labs":
        return "Laboratory Tests & Biomarkers", "lab_context"
    if current_context == "echo":
        if header_norm in ECHO_EXACT_MATCHES:
            return "Echocardiography & Vascular Imaging", "echo_context_exact_match"
        return "Echocardiography & Vascular Imaging", "echo_context"
    if current_context == "ecg":
        if header_norm in ECG_EXACT_MATCHES:
            return "ECG & Rhythm", "ecg_context_exact_match"
        return "ECG & Rhythm", "ecg_context"
    if current_context == "vitals":
        if header_norm in VITALS_EXACT_MATCHES:
            return "Vitals & Anthropometrics", "vitals_exact_match"
        return "Vitals & Anthropometrics", "vitals_context"

    if contains_any(
        header_norm,
        [
            "consent",
            "record id",
            "household identifier",
            "mrn",
            "previous patient at ahc",
            "contact number",
            "alternate contact",
            "address",
            "home tel",
            "mobile tel",
            "email",
            "follow up on your health",
            "wish to be informed",
            "volunteer under 18",
            "communication difficulties",
            "unwilling to participate",
            "upload",
        ],
    ):
        return "Administration & Consent", "administrative_or_consent_keyword"

    if header_norm in DEMOGRAPHIC_SOCIAL_EXACT_MATCHES:
        return "Demographics & Social Context", "demographic_exact_match"

    if header_norm.startswith("do any of your own children parents or siblings have any of the following health conditions"):
        return "Family History & Lineage", "family_history_household_condition"

    if header_norm in MEDICAL_HISTORY_EXACT_MATCHES:
        return "Diagnoses & Medical History", "medical_history_exact_match"

    if current_context == "symptoms" and contains_any(header_norm, PROCEDURE_DETAIL_KEYWORDS):
        return "Procedures & Interventions", "procedure_detail_context"

    if current_context in {"lifestyle", "symptoms"} and contains_any(header_norm, DIAGNOSIS_DETAIL_KEYWORDS):
        return "Diagnoses & Medical History", "diagnosis_detail_context"

    if contains_any(
        header_norm,
        [
            "ecg",
            "ventricular rate",
            "p wave",
            "pr interval",
            "qrs",
            "qt interval",
            "corrected qt interval",
            "st seg",
            "st segment",
            "t wave",
            "ectopic beats",
            "pathological q waves",
            "rhythm in ecg",
        ],
    ):
        return "ECG & Rhythm", "ecg_keyword"

    if header_norm in VITALS_EXACT_MATCHES or contains_any_whole_phrase(header_norm, VITALS_KEYWORDS):
        return "Vitals & Anthropometrics", "vitals_keyword"

    if contains_any_whole_phrase(header_norm, ECHO_KEYWORDS):
        return "Echocardiography & Vascular Imaging", "echo_or_vascular_keyword"

    if header_norm in ECHO_EXACT_MATCHES:
        return "Echocardiography & Vascular Imaging", "echo_exact_match"

    if contains_advanced_imaging_keyword(header_norm):
        return "MRI / CT & Advanced Imaging", "advanced_imaging_keyword"

    if header_norm in LAB_EXACT_MATCHES or contains_any(
        header_norm,
        [
            "laboratory",
            "bilirubin",
            "cholesterol",
            "triglycerides",
            "troponin",
            "platelet count",
            "glucose",
            "egfr",
            "kidney functions",
            "liver functions",
            "lipid profile",
            "thyroid functions",
            "electrolytes",
            "fasting blood sugar",
            "random blood glucose",
        ],
    ):
        return "Laboratory Tests & Biomarkers", "lab_keyword"

    if contains_any(
        header_norm,
        [
            "medication",
            "therapy",
            "route",
            "dose",
            "frequency",
            "subject is on treatment",
            "treatment",
        ],
    ):
        return "Medication & Dosing", "medication_keyword"

    if contains_any(
        header_norm,
        [
            "operation",
            "surgical",
            "procedure",
            "angioplasty",
            "stent",
            "cabg",
            "intervention",
            "angiography",
            "clinical follow up",
            "holter",
            "refer to",
            "clinic",
            "ambulatory bp monitoring",
            "bp chart",
            "further plan",
        ],
    ):
        return "Procedures & Interventions", "procedure_keyword"

    if contains_any(
        header_norm,
        [
            "mother",
            "father",
            "parents",
            "grandparents",
            "siblings",
            "children",
            "spouse",
            "relative",
            "pedigree",
            "consanguin",
            "twin",
            "familial",
            "family",
            "offspring",
            "origins",
            "origin",
            "premature cad",
            "sudden death history",
        ],
    ):
        return "Family History & Lineage", "family_keyword"

    if contains_any(
        header_norm,
        [
            "shortness of breath",
            "chest",
            "pain",
            "discomfort",
            "angina",
            "how soon",
            "rate your health",
            "health today",
            "exertion",
        ],
    ):
        return "Questionnaires & Reported Symptoms", "symptom_keyword"

    if contains_any(
        header_norm,
        [
            "smoker",
            "smoking",
            "cigarette",
            "cigarettes",
            "shisha",
            "alcohol",
            "influenza immunization",
            "ascvd risk",
        ],
    ):
        return "Lifestyle & Risk Factors", "risk_factor_keyword"

    if contains_any_whole_phrase(header_norm, MEDICAL_HISTORY_KEYWORDS) or header_norm.startswith(MEDICAL_TAXONOMY_PREFIXES):
        return "Diagnoses & Medical History", "medical_history_keyword"

    if current_context == "medications":
        return "Medication & Dosing", "medication_context_fallback"
    if current_context == "labs":
        return "Laboratory Tests & Biomarkers", "lab_context_fallback"
    if current_context == "echo":
        return "Echocardiography & Vascular Imaging", "echo_context_fallback"
    if current_context == "ecg":
        return "ECG & Rhythm", "ecg_context_fallback"
    if current_context == "imaging":
        return "MRI / CT & Advanced Imaging", "imaging_context_fallback"
    if current_context == "family":
        return "Family History & Lineage", "family_context_fallback"
    if current_context == "symptoms":
        return "Questionnaires & Reported Symptoms", "symptom_context_fallback"
    if current_context == "lifestyle" or current_context == "risk_scores":
        return "Lifestyle & Risk Factors", "lifestyle_context_fallback"
    if current_context == "medical":
        return "Diagnoses & Medical History", "medical_context_fallback"
    if current_context == "vitals":
        return "Vitals & Anthropometrics", "vitals_context_fallback"
    if current_context == "consent":
        return "Administration & Consent", "consent_context_fallback"

    if contains_any(
        header_norm,
        [
            "date of birth",
            "current age",
            "age at enrollment",
            "age",
            "gender",
            "nationality",
            "ethnicity",
            "occupational status",
            "occupation",
            "marital status",
            "wives",
            "childhood",
            "city of residence",
            "speak nubian",
            "read and write in arabic",
            "degree obtained",
            "participant s name",
            "name",
            "pregnant",
        ],
    ):
        return "Demographics & Social Context", "demographic_keyword"

    if contains_any(header_norm, ["date", "enrolment", "enrollment"]):
        return "Timeline & Dates", "timeline_keyword"

    return "Other / Needs Review", "no_rule_matched"


def classify_pii_label(header: str, header_norm: str, broad_category: str) -> str:
    if "pregnant" in header_norm or "pregnancy" in header_norm:
        return "sensitive_health"

    if header_norm == "name":
        if broad_category == "Medication & Dosing":
            return "sensitive_health"
        return "direct_identifier"

    if contains_any(header_norm, ["participant s name", "alternate contact", "contact 1 name", "contact 2 name"]):
        return "direct_identifier"

    if contains_any(header_norm, DIRECT_IDENTIFIER_KEYWORDS):
        return "direct_identifier"

    if broad_category in HEALTH_CATEGORIES:
        return "sensitive_health"

    if broad_category == "Demographics & Social Context" or broad_category == "Timeline & Dates":
        return "quasi_identifier"

    if contains_any(header_norm, QUASI_IDENTIFIER_KEYWORDS):
        return "quasi_identifier"

    return "non_pii"


def classify_dataset(dataset: str, path: Path) -> list[dict[str, str | int]]:
    headers, samples = read_dataset(path)
    current_context = "demographics"
    results = []
    for index, header in enumerate(headers, start=1):
        header_norm = normalize(header)
        current_context = infer_anchor_context(dataset, header_norm, current_context)
        broad_category, rule = classify_column(dataset, header, header_norm, current_context)
        results.append(
            {
                "dataset": dataset,
                "column_index": index,
                "column_name": header,
                "sample_row_1": value_at(samples, 0, index - 1),
                "sample_row_2": value_at(samples, 1, index - 1),
                "broad_family": CATEGORY_TO_FAMILY[broad_category],
                "broad_category": broad_category,
                "pii_label": classify_pii_label(header, header_norm, broad_category),
                "rule": rule,
            }
        )
        if header_norm == "complete":
            current_context = ""
    return results


def write_results(dataset: str, rows: list[dict[str, str | int]]) -> None:
    output_path = INTERIM_DIR / f"{dataset}_column_classification.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "dataset",
                "column_index",
                "column_name",
                "sample_row_1",
                "sample_row_2",
                "broad_family",
                "broad_category",
                "pii_label",
                "rule",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def write_combined(results_by_dataset: dict[str, list[dict[str, str | int]]]) -> None:
    output_path = INTERIM_DIR / "column_classification_combined.csv"
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "dataset",
                "column_index",
                "column_name",
                "sample_row_1",
                "sample_row_2",
                "broad_family",
                "broad_category",
                "pii_label",
                "rule",
            ],
        )
        writer.writeheader()
        for dataset_rows in results_by_dataset.values():
            writer.writerows(dataset_rows)


def print_summary(results_by_dataset: dict[str, list[dict[str, str | int]]]) -> None:
    for dataset, rows in results_by_dataset.items():
        total = len(rows)
        needs_review = [row for row in rows if row["broad_category"] == "Other / Needs Review"]
        print(f"{dataset}: {total} columns, {len(needs_review)} need review")
        if needs_review:
            preview = ", ".join(
                f"#{row['column_index']} {row['column_name']}" for row in needs_review[:15]
            )
            print(f"  Review preview: {preview}")


def main() -> None:
    results_by_dataset = {
        dataset: classify_dataset(dataset, path)
        for dataset, path in DATASETS.items()
    }
    for dataset, rows in results_by_dataset.items():
        write_results(dataset, rows)
    write_combined(results_by_dataset)
    print_summary(results_by_dataset)


if __name__ == "__main__":
    main()