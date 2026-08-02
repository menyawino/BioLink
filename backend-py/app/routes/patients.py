from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import text
from app.database import get_db
import logging
import hashlib
from typing import List

from app.diagnoses import build_patient_diagnoses
from app.routes._dataset_union import aligned_union_sql

router = APIRouter()
logger = logging.getLogger(__name__)

# Allowed columns for sorting to prevent SQL injection
ALLOWED_SORT_COLUMNS = {
    "dna_id",
    "age",
    "gender",
    "nationality",
    "enrollment_date",
    "data_completeness",
    "systolic_bp",
    "diastolic_bp",
    "bmi",
    "echo_ef",
    "mri_ef",
    "heart_rate",
    "hba1c",
}
ALLOWED_DATASETS = {"all", "ehvol", "bhs"}
DATASET_TABLES = {"ehvol": "ehvol_participants", "bhs": "bhs_participants"}
LEGACY_FALLBACK_VIEW = "ehvol"


def _normalized_dataset(dataset: object) -> str:
    if hasattr(dataset, "default"):
        dataset = getattr(dataset, "default")
    value = str(dataset or "all").lower()
    return value if value in ALLOWED_DATASETS else "all"


def _stable_unit_float(seed: str) -> float:
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF


def _stable_range(seed: str, min_val: float = 0.1, max_val: float = 0.9) -> float:
    return min_val + (max_val - min_val) * _stable_unit_float(seed)


def _normalize(values: List[float]) -> List[float]:
    total = sum(values) or 1.0
    return [v / total for v in values]


def _dataset_table(dataset: str | None) -> str:
    return DATASET_TABLES[_normalized_dataset(dataset)]


def _dataset_tables(dataset: str | None) -> list[str]:
    normalized = _normalized_dataset(dataset)
    if normalized == "all":
        return [DATASET_TABLES["ehvol"], DATASET_TABLES["bhs"]]
    return [DATASET_TABLES[normalized]]


def _table_has_rows(db, table_name: str) -> bool:
    try:
        row = db.execute(text(f"SELECT 1 FROM {table_name} WHERE dna_id IS NOT NULL OR participant_id IS NOT NULL LIMIT 1")).fetchone()
        if row is not None:
            return True
    except Exception:
        pass
    row = db.execute(text(f"SELECT 1 FROM {table_name} LIMIT 1")).fetchone()
    return row is not None


def _table_has_valid_data(db, table_name: str) -> bool:
    try:
        rows = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = :t"), {"t": table_name}).fetchall()
        cols = {r[0] for r in rows}
        id_cols = [c for c in ["dna_id", "participant_id", "record_id", "id"] if c in cols]
        if id_cols:
            where_clause = " OR ".join([f"({c} IS NOT NULL AND TRIM(CAST({c} AS TEXT)) != '')" for c in id_cols])
            row = db.execute(text(f"SELECT 1 FROM {table_name} WHERE {where_clause} LIMIT 1")).fetchone()
            return row is not None
        return False
    except Exception:
        return False


def _registry_source_table(db, dataset: str | None) -> str:
    normalized = _normalized_dataset(dataset)

    if normalized == "all":
        tables = _dataset_tables(normalized)
        if all(_table_has_valid_data(db, table_name) for table_name in tables):
            return aligned_union_sql(db, tables)

        if _table_has_valid_data(db, "patients"):
            logger.warning(
                "Falling back to legacy EHVOL view because participant tables have missing or invalid identifiers"
            )
            return LEGACY_FALLBACK_VIEW

        return aligned_union_sql(db, tables)

    source_table = _dataset_table(normalized)

    if _table_has_valid_data(db, source_table):
        return source_table

    if normalized == "ehvol" and _table_has_valid_data(db, "patients"):
        logger.warning(
            "Falling back to legacy EHVOL view because %s has no valid data",
            source_table,
        )
        return LEGACY_FALLBACK_VIEW

    return source_table


def _table_columns(db, table_name: str) -> set[str]:
    rows = db.execute(
        text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = :table_name
            """),
        {"table_name": table_name},
    ).fetchall()
    return {row[0] for row in rows}


def _source_columns(db, dataset: str | None, source_table: str) -> set[str]:
    # When source_table is a UNION subquery, aggregate columns from the underlying tables.
    # Otherwise (including legacy fallback views), introspect the actual source_table so
    # that generated SQL only references columns that exist in the table being queried.
    if source_table.startswith("("):
        columns: set[str] = set()
        for table_name in _dataset_tables(dataset):
            columns.update(_table_columns(db, table_name))
        return columns
    return _table_columns(db, source_table)


def _mri_sql_expr(columns: set[str]) -> tuple[str, str]:
    if "mri_ef" in columns:
        return "mri_ef", "(mri_ef IS NOT NULL)"
    return "NULL::double precision", "FALSE"


def _first_column(columns: set[str], *candidates: str) -> str | None:
    for candidate in candidates:
        if candidate in columns:
            return candidate
    return None


def _truthy_column_expr(column: str) -> str:
    return (
        f"LOWER(COALESCE(CAST({column} AS TEXT), 'false')) "
        "IN ('true', 't', '1', 'yes', 'y')"
    )


def _json_text_expr(*keys: str) -> str:
    exprs = [f"NULLIF(BTRIM(clinical_data->>'{key}'), '')" for key in keys]
    return f"COALESCE({', '.join(exprs)})" if exprs else "NULL::text"


def _json_numeric_expr(keys: list[str], sql_type: str) -> str:
    raw = _json_text_expr(*keys)
    return (
        f"CASE WHEN {raw} ~ '^-?[0-9]+(\\.[0-9]+)?$' "
        f"THEN ({raw})::{sql_type} ELSE NULL::{sql_type} END"
    )


def _normalized_nationality_expr(column_expr: str) -> str:
    return (
        "CASE "
        f"WHEN {column_expr} IS NULL OR BTRIM({column_expr}) = '' THEN 'Unknown' "
        f"WHEN LOWER({column_expr}) LIKE '%egypt%' "
        f"  OR LOWER({column_expr}) LIKE '%egyption%' "
        f"  OR LOWER({column_expr}) LIKE '%egyptain%' "
        f"  OR LOWER({column_expr}) LIKE '%egyptien%' "
        f"  OR REGEXP_REPLACE(LOWER({column_expr}), '[^a-z]', '', 'g') IN ("
        "      'egy', 'egyp', 'egp', 'eg', 'eyp',"
        "      'egypt', 'egyptian', 'egyption', 'egyptain', 'egyptien', 'egyptient',"
        "      'egiptian', 'egeptian', 'egyept', 'egytptian', 'egytptan',"
        "      'egyptioan', 'egyptions', 'egyptianj', 'egyptians', 'egptient'"
        "  ) "
        f"  OR {column_expr} ~ 'مصر|مصري|مصرية|مصريه' "
        "THEN 'Egyptian' "
        f"ELSE INITCAP(BTRIM({column_expr})) END"
    )


def _dataset_field_exprs(columns: set[str], dataset: str) -> dict[str, str]:
    normalized_dataset = _normalized_dataset(dataset).upper()
    has_clinical_json = "clinical_data" in columns

    id_cols = [c for c in ["dna_id", "participant_id", "record_id", "id"] if c in columns]
    if not id_cols:
        raise HTTPException(
            status_code=500,
            detail="No identifier column found in participant dataset table",
        )
    id_col = f"COALESCE({', '.join([f'CAST({c} AS TEXT)' for c in id_cols])})"

    source_record_col = _first_column(columns, "source_record_id", "record_id")
    if not source_record_col and has_clinical_json:
        source_record_col = _json_text_expr("source_record_id", "record_id")

    dataset_col = _first_column(columns, "source_dataset", "_source_dataset")
    dataset_expr = dataset_col if dataset_col else f"'{normalized_dataset}'::text"
    if not dataset_col and has_clinical_json:
        dataset_expr = f"COALESCE({_json_text_expr('source_dataset', 'cohort')}, '{normalized_dataset}')"

    enrollment_col = _first_column(columns, "enrollment_date", "date_of_enrolment")
    enrollment_expr = enrollment_col if enrollment_col else "NULL::date"
    if not enrollment_col and has_clinical_json:
        enrollment_expr = (
            f"CASE WHEN {_json_text_expr('enrollment_date', 'date_of_enrolment')} ~ '^\\d{{4}}-\\d{{2}}-\\d{{2}}' "
            f"THEN ({_json_text_expr('enrollment_date', 'date_of_enrolment')})::date ELSE NULL::date END"
        )

    city_col = _first_column(columns, "current_city", "current_city_of_residence")
    city_expr = city_col if city_col else "NULL::text"
    if not city_col and has_clinical_json:
        city_expr = _json_text_expr("current_city", "current_city_of_residence")

    echo_col = _first_column(columns, "echo_ef", "ef", "left_ventricular_ef")
    echo_expr = echo_col if echo_col else "NULL::double precision"
    if not echo_col and has_clinical_json:
        echo_expr = _json_numeric_expr(["echo_ef", "ef", "left_ventricular_ef"], "double precision")

    age_expr = "age" if "age" in columns else "NULL::integer"
    if "age" not in columns and has_clinical_json:
        age_expr = _json_numeric_expr(["age", "current_age", "age_at_enrollment"], "integer")

    gender_expr = "gender" if "gender" in columns else "NULL::text"
    if "gender" not in columns and has_clinical_json:
        gender_expr = _json_text_expr("gender")

    nationality_expr = "nationality" if "nationality" in columns else "NULL::text"
    if "nationality" not in columns and has_clinical_json:
        nationality_expr = _json_text_expr("nationality")

    heart_rate_expr = "heart_rate" if "heart_rate" in columns else "NULL::double precision"
    if "heart_rate" not in columns and has_clinical_json:
        heart_rate_expr = _json_numeric_expr(["heart_rate"], "double precision")

    systolic_expr = (
        "systolic_bp"
        if "systolic_bp" in columns
        else ("bp" if "bp" in columns else "NULL::double precision")
    )
    if "systolic_bp" not in columns and "bp" not in columns and has_clinical_json:
        systolic_expr = _json_numeric_expr(["systolic_bp"], "double precision")

    diastolic_expr = "diastolic_bp" if "diastolic_bp" in columns else "NULL::double precision"
    if "diastolic_bp" not in columns and has_clinical_json:
        diastolic_expr = _json_numeric_expr(["diastolic_bp"], "double precision")

    bmi_expr = "bmi" if "bmi" in columns else "NULL::double precision"
    if "bmi" not in columns and has_clinical_json:
        bmi_expr = _json_numeric_expr(["bmi"], "double precision")

    hba1c_expr = "hba1c" if "hba1c" in columns else "NULL::double precision"
    if "hba1c" not in columns and has_clinical_json:
        hba1c_expr = _json_numeric_expr(["hba1c"], "double precision")

    troponin_expr = "troponin_i" if "troponin_i" in columns else "NULL::double precision"
    if "troponin_i" not in columns and has_clinical_json:
        troponin_expr = _json_numeric_expr(["troponin_i"], "double precision")

    current_city_category_expr = (
        "current_city_category" if "current_city_category" in columns else "NULL::text"
    )
    if "current_city_category" not in columns and has_clinical_json:
        current_city_category_expr = _json_text_expr("current_city_category")

    return {
        "id_col": id_col,
        "source_record_col": source_record_col or "",
        "dataset_expr": dataset_expr,
        "age_expr": age_expr,
        "gender_expr": gender_expr,
        "nationality_expr": nationality_expr,
        "enrollment_expr": enrollment_expr,
        "city_expr": city_expr,
        "heart_rate_expr": heart_rate_expr,
        "systolic_expr": systolic_expr,
        "diastolic_expr": diastolic_expr,
        "bmi_expr": bmi_expr,
        "hba1c_expr": hba1c_expr,
        "echo_expr": echo_expr,
        "troponin_expr": troponin_expr,
        "current_city_category_expr": current_city_category_expr,
    }


@router.get("")
async def get_patients(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=1000),
    search: str | None = None,
    gender: str | None = None,
    ageMin: int = Query(None, alias="ageMin"),
    ageMax: int = Query(None, alias="ageMax"),
    sortBy: str = Query("dna_id", alias="sortBy"),
    sortOrder: str = Query("asc", alias="sortOrder"),
    # Data availability filters
    hasEcho: bool = Query(None, alias="hasEcho"),
    hasMri: bool = Query(None, alias="hasMri"),
    hasGenomics: bool = Query(None, alias="hasGenomics"),
    hasLabs: bool = Query(None, alias="hasLabs"),
    hasImaging: bool = Query(None, alias="hasImaging"),
    minDataCompleteness: int = Query(None, alias="minDataCompleteness"),
    # Geographic filters
    nationality: str | None = None,
    region: str | None = None,
    # Temporal filters
    enrollmentDateFrom: str = Query(None, alias="enrollmentDateFrom"),
    enrollmentDateTo: str = Query(None, alias="enrollmentDateTo"),
    # Clinical/risk factor filters
    hasDiabetes: bool = Query(None, alias="hasDiabetes"),
    hasHypertension: bool = Query(None, alias="hasHypertension"),
    hasDyslipidemia: bool = Query(None, alias="hasDyslipidemia"),
    hasCoronaryDisease: bool = Query(None, alias="hasCoronaryDisease"),
    hasHeartFailure: bool = Query(None, alias="hasHeartFailure"),
    hasSmoking: bool = Query(None, alias="hasSmoking"),
    hasObesity: bool = Query(None, alias="hasObesity"),
    hasFamilyHistory: bool = Query(None, alias="hasFamilyHistory"),
    dataset: str = Query("all"),
    db=Depends(get_db),
):
    """Search and filter patients in the registry"""
    try:
        source_table = _registry_source_table(db, dataset)
        columns = _source_columns(db, dataset, source_table)
        mri_value_expr, mri_present_expr = _mri_sql_expr(columns)
        expr = _dataset_field_exprs(columns, dataset)

        # Build a safe, parameterized filter query
        conditions = ["1=1"]
        params = {}

        completeness_expr = (
            f"((CASE WHEN {expr['heart_rate_expr']} IS NOT NULL THEN 20 ELSE 0 END) "
            f"+ (CASE WHEN {expr['systolic_expr']} IS NOT NULL THEN 20 ELSE 0 END) "
            f"+ (CASE WHEN {expr['bmi_expr']} IS NOT NULL THEN 20 ELSE 0 END) "
            f"+ (CASE WHEN {expr['echo_expr']} IS NOT NULL THEN 20 ELSE 0 END) "
            f"+ (CASE WHEN {mri_present_expr} THEN 20 ELSE 0 END))"
        )

        if search:
            search_conditions = [f"CAST({expr['id_col']} AS TEXT) ILIKE :search"]
            if expr["source_record_col"]:
                search_conditions.append(
                    f"CAST({expr['source_record_col']} AS TEXT) ILIKE :search"
                )
            if "nationality" in columns:
                search_conditions.append("CAST(nationality AS TEXT) ILIKE :search")
            conditions.append(f"({' OR '.join(search_conditions)})")
            params["search"] = f"%{search}%"

        if gender:
            if "gender" in columns:
                conditions.append("gender = :gender")
            params["gender"] = gender

        if ageMin is not None:
            if "age" in columns:
                conditions.append("age >= :age_min")
            params["age_min"] = ageMin

        if ageMax is not None:
            if "age" in columns:
                conditions.append("age <= :age_max")
            params["age_max"] = ageMax

        # Data availability filters
        if hasEcho is not None:
            conditions.append(f"(({expr['echo_expr']} IS NOT NULL) = :has_echo)")
            params["has_echo"] = hasEcho

        if hasMri is not None:
            conditions.append(f"(({mri_present_expr}) = :has_mri)")
            params["has_mri"] = hasMri

        # Imaging (any imaging modality: echo OR mri)
        if hasImaging is not None:
            conditions.append(
                f"(({mri_present_expr} OR {expr['echo_expr']} IS NOT NULL) = :has_imaging)"
            )
            params["has_imaging"] = hasImaging

        # Laboratory data availability (best-effort based on stored lab columns)
        if hasLabs is not None:
            conditions.append(
                f"(({expr['hba1c_expr']} IS NOT NULL OR {expr['troponin_expr']} IS NOT NULL) = :has_labs)"
            )
            params["has_labs"] = hasLabs

        # Family history (derived from available family-history flags)
        if hasFamilyHistory is not None:
            family_history_col = _first_column(
                columns,
                "family_history_cad",
                "history_premature_cad",
                "history_of_premature_cad",
            )
            if family_history_col:
                conditions.append(
                    f"(({_truthy_column_expr(family_history_col)}) = :has_family_history)"
                )
            else:
                conditions.append("(FALSE = :has_family_history)")
            params["has_family_history"] = hasFamilyHistory

        # Genomics availability (check patient_genomic_variants table)
        if hasGenomics is not None:
            genomics_expr = (
                f"EXISTS (SELECT 1 FROM patient_genomic_variants v "
                f"WHERE v.dna_id = CAST({expr['id_col']} AS TEXT))"
            )
            conditions.append(f"(({genomics_expr}) = :has_genomics)")
            params["has_genomics"] = hasGenomics

        if minDataCompleteness is not None:
            conditions.append(f"{completeness_expr} >= :min_data_completeness")
            params["min_data_completeness"] = minDataCompleteness

        # Geographic filters
        if nationality:
            conditions.append(
                f"({_normalized_nationality_expr(expr['nationality_expr'])} = :nationality)"
            )
            params["nationality"] = nationality

        # Region (freeform match against nationality/current_city/current_city_category)
        if region:
            region_conditions: list[str] = []
            if "nationality" in columns:
                region_conditions.append("LOWER(nationality) LIKE :region")
            if "current_city_category" in columns:
                region_conditions.append("LOWER(current_city_category) LIKE :region")
            city_col = _first_column(columns, "current_city", "current_city_of_residence")
            if city_col:
                region_conditions.append(f"LOWER({city_col}) LIKE :region")
            if region_conditions:
                conditions.append(f"({' OR '.join(region_conditions)})")
            params["region"] = f"%{region.lower()}%"

        # Temporal filters
        if enrollmentDateFrom:
            enrollment_col = _first_column(columns, "enrollment_date", "date_of_enrolment")
            if enrollment_col:
                conditions.append(f"{enrollment_col} >= :enrollment_date_from")
            params["enrollment_date_from"] = enrollmentDateFrom

        if enrollmentDateTo:
            enrollment_col = _first_column(columns, "enrollment_date", "date_of_enrolment")
            if enrollment_col:
                conditions.append(f"{enrollment_col} <= :enrollment_date_to")
            params["enrollment_date_to"] = enrollmentDateTo

        # Clinical / risk factor filters (best-effort; nullable columns)
        if hasDiabetes is not None:
            diabetes_col = _first_column(
                columns,
                "has_diabetes",
                "diabetes_mellitus",
                "other_co_morbidities_risk_factors_choice_diabetes_mellitus",
            )
            if diabetes_col:
                conditions.append(
                    f"(({_truthy_column_expr(diabetes_col)}) = :has_diabetes)"
                )
            else:
                conditions.append("FALSE = :has_diabetes")
            params["has_diabetes"] = hasDiabetes

        if hasHypertension is not None:
            hypertension_col = _first_column(
                columns,
                "has_hypertension",
                "high_blood_pressure",
                "do_you_have_hypertension",
                "other_co_morbidities_risk_factors_choice_hypertension",
            )
            if hypertension_col:
                conditions.append(
                    f"(({_truthy_column_expr(hypertension_col)}) = :has_hypertension)"
                )
            else:
                conditions.append("FALSE = :has_hypertension")
            params["has_hypertension"] = hasHypertension

        if hasDyslipidemia is not None:
            dyslipidemia_col = _first_column(
                columns,
                "has_dyslipidemia",
                "dyslipidemia",
            )
            if dyslipidemia_col:
                conditions.append(
                    f"(({_truthy_column_expr(dyslipidemia_col)}) = :has_dyslipidemia)"
                )
            else:
                conditions.append("FALSE = :has_dyslipidemia")
            params["has_dyslipidemia"] = hasDyslipidemia

        if hasCoronaryDisease is not None:
            coronary_disease_col = _first_column(
                columns,
                "heart_attack_or_angina",
            )
            if coronary_disease_col:
                conditions.append(
                    f"(({_truthy_column_expr(coronary_disease_col)}) = :has_coronary_disease)"
                )
            else:
                conditions.append("FALSE = :has_coronary_disease")
            params["has_coronary_disease"] = hasCoronaryDisease

        if hasHeartFailure is not None:
            heart_failure_col = _first_column(
                columns,
                "prior_heart_failure",
                "has_heart_failure",
            )
            if heart_failure_col:
                conditions.append(
                    f"(({_truthy_column_expr(heart_failure_col)}) = :has_heart_failure)"
                )
            else:
                conditions.append("FALSE = :has_heart_failure")
            params["has_heart_failure"] = hasHeartFailure

        if hasSmoking is not None:
            smoking_col = _first_column(
                columns,
                "is_smoker",
                "current_smoker",
                "do_you_smoke_shisha_or_cigarettes_or_both",
            )
            if smoking_col:
                conditions.append(
                    f"(({_truthy_column_expr(smoking_col)}) = :has_smoking)"
                )
            else:
                conditions.append("FALSE = :has_smoking")
            params["has_smoking"] = hasSmoking

        if hasObesity is not None:
            if "bmi" in columns:
                (
                    conditions.append("COALESCE(bmi, 0) >= 30")
                    if hasObesity
                    else conditions.append("(bmi IS NULL OR bmi < 30)")
                )

        # Validate and sanitize sort parameters
        sort_by_str = str(getattr(sortBy, "default", sortBy) or "dna_id")
        sort_order_str = str(getattr(sortOrder, "default", sortOrder) or "asc")

        sort_column_map = {
            "dna_id": expr["id_col"],
            "age": expr["age_expr"],
            "gender": expr["gender_expr"],
            "nationality": expr["nationality_expr"],
            "enrollment_date": expr["enrollment_expr"],
            "data_completeness": completeness_expr,
            "systolic_bp": expr["systolic_expr"],
            "diastolic_bp": expr["diastolic_expr"],
            "bmi": expr["bmi_expr"],
            "echo_ef": expr["echo_expr"],
            "mri_ef": mri_value_expr,
            "heart_rate": expr["heart_rate_expr"],
            "hba1c": expr["hba1c_expr"],
        }
        sort_column = sort_column_map.get(
            sort_by_str if sort_by_str in ALLOWED_SORT_COLUMNS else "dna_id", expr["id_col"]
        )
        sort_direction = "DESC" if sort_order_str.lower() == "desc" else "ASC"

        # Calculate offset for pagination
        offset = (page - 1) * limit
        params["limit"] = limit
        params["offset"] = offset

        # Get total count for pagination
        count_stmt = text(
            f"SELECT COUNT(*) as total FROM {source_table} WHERE {' AND '.join(conditions)}"
        )
        total_result = db.execute(count_stmt, params).fetchone()
        total = total_result[0] if total_result else 0

        # Get paginated results using unified table with compatibility aliases
        stmt = text(
            f"SELECT CAST({expr['id_col']} AS TEXT) AS dna_id, {expr['dataset_expr']} AS source_dataset, "
            f"{expr['age_expr']} AS age, {expr['gender_expr']} AS gender, {expr['nationality_expr']} AS nationality, "
            f"{expr['enrollment_expr']} AS enrollment_date, {expr['city_expr']} AS current_city, "
            f"{expr['heart_rate_expr']} AS heart_rate, {expr['systolic_expr']} AS systolic_bp, {expr['diastolic_expr']} AS diastolic_bp, "
            f"{expr['bmi_expr']} AS bmi, {expr['hba1c_expr']} AS hba1c, {expr['echo_expr']} AS echo_ef, {mri_value_expr} AS mri_ef, "
            f"{expr['current_city_category_expr']} AS current_city_category, "
            f"({mri_present_expr}) AS has_mri, "
            f"({expr['echo_expr']} IS NOT NULL) AS has_echo, "
            f"{completeness_expr} AS data_completeness "
            f"FROM {source_table} "
            f"WHERE {' AND '.join(conditions)} "
            f"ORDER BY {sort_column} {sort_direction} "
            "LIMIT :limit OFFSET :offset"
        )

        patients = db.execute(stmt, params).mappings().fetchall()

        total_pages = (total + limit - 1) // limit if limit > 0 else 1

        return {
            "success": True,
            "data": [dict(row) for row in patients],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "totalPages": total_pages,
            },
        }
    except Exception as e:
        logger.error(f"Error fetching patients: {e}")
        return {"success": False, "error": str(e)}


@router.get("/search/{query}")
async def search_patients(
    query: str,
    limit: int = Query(20, ge=1, le=100),
    dataset: str = Query("all"),
    db=Depends(get_db),
):
    """Search patients by DNA ID or nationality"""
    try:
        source_table = _registry_source_table(db, dataset)
        columns = _source_columns(db, dataset, source_table)
        mri_value_expr, mri_present_expr = _mri_sql_expr(columns)
        expr = _dataset_field_exprs(columns, dataset)

        search_conditions = [f"CAST({expr['id_col']} AS TEXT) ILIKE :search"]
        if expr["source_record_col"]:
            search_conditions.append(
                f"CAST({expr['source_record_col']} AS TEXT) ILIKE :search"
            )
        if "nationality" in columns:
            search_conditions.append("CAST(nationality AS TEXT) ILIKE :search")

        params = {"search": f"%{query}%", "limit": limit}

        completeness_expr = (
            f"((CASE WHEN {expr['heart_rate_expr']} IS NOT NULL THEN 20 ELSE 0 END) "
            f"+ (CASE WHEN {expr['systolic_expr']} IS NOT NULL THEN 20 ELSE 0 END) "
            f"+ (CASE WHEN {expr['bmi_expr']} IS NOT NULL THEN 20 ELSE 0 END) "
            f"+ (CASE WHEN {expr['echo_expr']} IS NOT NULL THEN 20 ELSE 0 END) "
            f"+ (CASE WHEN {mri_present_expr} THEN 20 ELSE 0 END))"
        )
        stmt = text(
            f"SELECT CAST({expr['id_col']} AS TEXT) AS dna_id, {expr['dataset_expr']} AS source_dataset, "
            f"{expr['age_expr']} AS age, {expr['gender_expr']} AS gender, {expr['nationality_expr']} AS nationality, "
            f"{expr['enrollment_expr']} AS enrollment_date, {expr['city_expr']} AS current_city, "
            f"{expr['heart_rate_expr']} AS heart_rate, {expr['systolic_expr']} AS systolic_bp, {expr['diastolic_expr']} AS diastolic_bp, "
            f"{expr['bmi_expr']} AS bmi, {expr['hba1c_expr']} AS hba1c, {expr['echo_expr']} AS echo_ef, {mri_value_expr} AS mri_ef, "
            f"{expr['current_city_category_expr']} AS current_city_category, "
            f"({mri_present_expr}) AS has_mri, "
            f"({expr['echo_expr']} IS NOT NULL) AS has_echo, "
            f"{completeness_expr} AS data_completeness "
            f"FROM {source_table} "
            f"WHERE ({' OR '.join(search_conditions)}) "
            f"ORDER BY {expr['id_col']} ASC "
            "LIMIT :limit"
        )
        patients = db.execute(stmt, params).mappings().fetchall()
        return {"success": True, "data": [dict(row) for row in patients]}
    except Exception as e:
        logger.error(f"Error searching patients: {e}")
        return {"success": False, "error": str(e)}


@router.get("/{dna_id}")
async def get_patient(dna_id: str, db=Depends(get_db)):
    """Get detailed patient information by DNA ID"""
    try:
        normalized_id = (dna_id or "").strip()

        patient_stmt = text("""
            SELECT *
            FROM patients
            WHERE TRIM(dna_id) = :dna_id
        """)
        patient = (
            db.execute(patient_stmt, {"dna_id": normalized_id}).mappings().fetchone()
        )

        if not patient:
            for source_table in DATASET_TABLES.values():
                source_columns = _table_columns(db, source_table)
                source_expr = _dataset_field_exprs(source_columns, source_table)
                fallback_stmt = text(f"""
                    SELECT *, CAST({source_expr['id_col']} AS TEXT) AS dna_id
                    FROM {source_table}
                    WHERE TRIM(CAST({source_expr['id_col']} AS TEXT)) = :dna_id
                    """)
                patient = (
                    db.execute(fallback_stmt, {"dna_id": normalized_id})
                    .mappings()
                    .fetchone()
                )
                if patient:
                    break

        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")

        patient_data = dict(patient)
        diagnoses = build_patient_diagnoses(patient_data)

        # Build nested objects from the denormalized row (keep the frontend contract stable)
        lifestyle = {
            "current_smoker": bool(patient_data.get("current_smoker") or False),
            "smoking_duration": None,
            "cigarettes_per_day": patient_data.get("cigarettes_per_day"),
            "drinks_alcohol": bool(patient_data.get("drinks_alcohol") or False),
            "takes_medication": bool(patient_data.get("takes_medication") or False),
            "ever_smoked": bool(patient_data.get("ever_smoked") or False),
            "smoking_years": patient_data.get("smoking_years"),
        }

        exclusion = None
        family = None

        medical = {
            "heart_attack_or_angina": bool(
                patient_data.get("heart_attack_or_angina") or False
            ),
            "high_blood_pressure": bool(
                patient_data.get("high_blood_pressure") or False
            ),
            "dyslipidemia": bool(patient_data.get("dyslipidemia") or False),
            "rheumatic_fever": False,
            "anaemia": False,
            "lung_problems": False,
            "kidney_problems": False,
            "liver_problems": False,
            "diabetes_mellitus": bool(patient_data.get("diabetes_mellitus") or False),
            "prior_heart_failure": bool(
                patient_data.get("prior_heart_failure") or False
            ),
            "neurological_problems": False,
            "musculoskeletal_problems": False,
            "autoimmune_problems": False,
            "undergone_surgery": False,
            "procedure_details": None,
            "malignancy": False,
            "comorbidity": len(diagnoses),
            "diagnoses": diagnoses,
        }

        physical = {
            "examination_date": patient_data.get("enrollment_date"),
            "examination_type": "Enrollment",
            "heart_rate": patient_data.get("heart_rate"),
            "regularity": None,
            "bp_reading": None,
            "systolic_bp": patient_data.get("systolic_bp"),
            "diastolic_bp": patient_data.get("diastolic_bp"),
            "height_cm": patient_data.get("height_cm"),
            "weight_kg": patient_data.get("weight_kg"),
            "bmi": patient_data.get("bmi"),
            "bsa": patient_data.get("bsa"),
            "jvp": None,
            "abnormal_physical_structure": False,
            "s1": None,
            "s2": None,
            "s3": False,
            "s4": False,
        }

        labs = {
            "hba1c": patient_data.get("hba1c"),
            "troponin_i": patient_data.get("troponin_i"),
            "hba1c_outlier": False,
            "troponin_outlier": False,
            "heart_rate_outlier": False,
        }

        ecg = {
            "rate": None,
            "rate_clean": None,
            "rhythm": None,
            "p_wave_abnormality": False,
            "pr_interval": None,
            "qrs_duration": None,
            "qrs_abnormalities": False,
            "st_segment_abnormalities": False,
            "qtc_interval": None,
            "t_wave_abnormalities": False,
            "ecg_conclusion": None,
            "missing_ecg": True,
        }

        echo = {
            "echo_date": patient_data.get("echo_date"),
            "aortic_root": None,
            "left_atrium": None,
            "right_ventricle": None,
            "lvedd": None,
            "lvesd": None,
            "ivsd": None,
            "ivss": None,
            "lvpwd": None,
            "lvpws": None,
            "ef": patient_data.get("echo_ef"),
            "fs": None,
            "subaortic_membrane": False,
            "mitral_regurge": None,
            "mitral_stenosis": False,
            "tricuspid_regurge": None,
            "tricuspid_stenosis": False,
            "aortic_regurge": None,
            "aortic_stenosis": False,
            "pulmonary_regurge": None,
            "pulmonary_stenosis": False,
            "missing_echo": patient_data.get("echo_ef") is None,
        }

        mri = {
            "mri_performed": patient_data.get("mri_ef") is not None,
            "heart_rate_during_mri": None,
            "mri_date": patient_data.get("mri_date"),
            "lv_ejection_fraction": patient_data.get("mri_ef"),
            "lv_end_diastolic_volume": None,
            "lv_end_systolic_volume": None,
            "lv_mass": None,
            "rv_ejection_fraction": patient_data.get("rv_ef"),
            "missing_mri": patient_data.get("mri_ef") is None,
        }

        # Build response
        result = {
            "id": patient_data.get("id"),
            "dna_id": patient_data.get("dna_id"),
            "age": patient_data.get("age"),
            "gender": patient_data.get("gender"),
            "nationality": patient_data.get("nationality"),
            "enrollment_date": patient_data.get("enrollment_date"),
            "current_city": patient_data.get("current_city"),
            "heart_rate": patient_data.get("heart_rate"),
            "systolic_bp": patient_data.get("systolic_bp"),
            "diastolic_bp": patient_data.get("diastolic_bp"),
            "bmi": patient_data.get("bmi"),
            "hba1c": patient_data.get("hba1c"),
            "echo_ef": patient_data.get("echo_ef"),
            "mri_ef": patient_data.get("mri_ef"),
            "current_city_category": patient_data.get("current_city_category"),
            "has_mri": patient_data.get("mri_ef") is not None,
            "has_echo": patient_data.get("echo_ef") is not None,
            "data_completeness": int(
                (20 if patient_data.get("heart_rate") is not None else 0)
                + (20 if patient_data.get("systolic_bp") is not None else 0)
                + (20 if patient_data.get("bmi") is not None else 0)
                + (20 if patient_data.get("echo_ef") is not None else 0)
                + (20 if patient_data.get("mri_ef") is not None else 0)
            ),
            "date_of_birth": patient_data.get("date_of_birth"),
            "is_pregnant": False,
            "father_city_origin": None,
            "childhood_city": None,
            "consent_obtained": True,
            "lifestyle": lifestyle,
            "exclusion": exclusion,
            "family": family,
            "medical": medical,
            "physical": physical,
            "labs": labs,
            "ecg": ecg,
            "echo": echo,
            "mri": mri,
            "geographic": {
                "current_city_category": patient_data.get("current_city_category"),
                "childhood_city_category": patient_data.get("childhood_city_category"),
                "migration_pattern": patient_data.get("migration_pattern"),
            },
        }

        return {"success": True, "data": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching patient {dna_id}: {e}")
        return {"success": False, "error": str(e)}


@router.get("/{dna_id}/genomics")
async def get_patient_genomics(dna_id: str, db=Depends(get_db)):
    """Get genomic data for a patient based on ingested VCF variants."""
    try:
        normalized_id = (dna_id or "").strip()

        patient_row = db.execute(
            text("SELECT dna_id FROM patients WHERE TRIM(dna_id) = :dna_id"),
            {"dna_id": normalized_id},
        ).fetchone()

        if not patient_row:
            for source_table in DATASET_TABLES.values():
                source_columns = _table_columns(db, source_table)
                source_expr = _dataset_field_exprs(source_columns, source_table)
                patient_row = db.execute(
                    text(
                        f"SELECT CAST({source_expr['id_col']} AS TEXT) AS dna_id FROM {source_table} WHERE TRIM(CAST({source_expr['id_col']} AS TEXT)) = :dna_id"
                    ),
                    {"dna_id": normalized_id},
                ).fetchone()
                if patient_row:
                    break

        if not patient_row:
            raise HTTPException(status_code=404, detail="Patient not found")

        stmt = text("""
            SELECT chrom, pos, ref, alt, variant_id, gene, genotype,
                   clinical_significance, condition, frequency
            FROM patient_genomic_variants
            WHERE dna_id = :dna_id
            ORDER BY gene NULLS LAST, chrom, pos
            LIMIT 500
        """)
        rows = db.execute(stmt, {"dna_id": normalized_id}).mappings().fetchall()

        variants = []
        for row in rows:
            variant_id = row.get("variant_id")
            chrom = row.get("chrom")
            pos = row.get("pos")
            ref = row.get("ref")
            alt = row.get("alt")
            variant_label = (
                variant_id
                if variant_id and variant_id != "."
                else f"{chrom}:{pos}{ref}>{alt}"
            )

            clnsig = (row.get("clinical_significance") or "uncertain").lower()
            if clnsig not in {
                "pathogenic",
                "likely_pathogenic",
                "uncertain",
                "likely_benign",
                "benign",
            }:
                clnsig = "uncertain"

            variants.append(
                {
                    "gene": row.get("gene") or "Unknown",
                    "variant": variant_label,
                    "genotype": row.get("genotype") or "0/0",
                    "clinicalSignificance": clnsig,
                    "condition": row.get("condition") or "Cardiovascular risk",
                    "frequency": (
                        float(row.get("frequency"))
                        if row.get("frequency") is not None
                        else 0.0
                    ),
                }
            )

        pharmacogenomics_map = {
            "CYP2C19": {
                "drug": "Clopidogrel",
                "recommendation": "Consider alternative antiplatelet therapy for poor metabolizers.",
            },
            "CYP2D6": {
                "drug": "Metoprolol",
                "recommendation": "Consider dose adjustment for poor metabolizers.",
            },
            "SLCO1B1": {
                "drug": "Simvastatin",
                "recommendation": "Consider lower dose or alternative statin.",
            },
        }

        pharmacogenomics = []
        seen_genes = set()
        for variant in variants:
            gene = variant["gene"]
            if gene not in pharmacogenomics_map or gene in seen_genes:
                continue
            seen_genes.add(gene)

            genotype = variant["genotype"]
            if genotype in {"0/0", "0|0"}:
                metabolizer = "normal"
            elif genotype in {"0/1", "1/0", "0|1", "1|0"}:
                metabolizer = "intermediate"
            elif genotype in {"1/1", "1|1"}:
                metabolizer = "poor"
            else:
                metabolizer = "normal"

            pharmacogenomics.append(
                {
                    "drug": pharmacogenomics_map[gene]["drug"],
                    "gene": gene,
                    "genotype": genotype,
                    "metabolizer": metabolizer,
                    "recommendation": pharmacogenomics_map[gene]["recommendation"],
                    "confidence": "moderate",
                }
            )

        polygenic = {
            "coronaryArteryDisease": _stable_range(f"{dna_id}:cad"),
            "myocardialInfarction": _stable_range(f"{dna_id}:mi"),
            "strokeRisk": _stable_range(f"{dna_id}:stroke"),
            "atrialFibrillation": _stable_range(f"{dna_id}:afib"),
        }

        ancestry_values = _normalize(
            [
                _stable_unit_float(f"{dna_id}:eu"),
                _stable_unit_float(f"{dna_id}:af"),
                _stable_unit_float(f"{dna_id}:as"),
                _stable_unit_float(f"{dna_id}:na"),
                _stable_unit_float(f"{dna_id}:ot"),
            ]
        )
        ancestry = {
            "european": ancestry_values[0],
            "african": ancestry_values[1],
            "asian": ancestry_values[2],
            "native_american": ancestry_values[3],
            "other": ancestry_values[4],
        }

        return {
            "success": True,
            "data": {
                "polygenic": polygenic,
                "variants": variants,
                "pharmacogenomics": pharmacogenomics,
                "ancestry": ancestry,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching genomics for {dna_id}: {e}")
        return {"success": False, "error": str(e)}


@router.get("/{dna_id}/vitals")
async def get_patient_vitals(dna_id: str, db=Depends(get_db)):
    """Get patient vital signs"""
    try:
        stmt = text("""
            SELECT
                systolic_bp,
                diastolic_bp,
                heart_rate,
                weight_kg,
                height_cm,
                bmi,
                bsa,
                hba1c,
                troponin_i
            FROM patients
            WHERE dna_id = :dna_id
        """)
        row = db.execute(stmt, {"dna_id": dna_id}).mappings().fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Patient not found")

        return {
            "success": True,
            "data": {
                "current": {
                    "systolic": row.get("systolic_bp"),
                    "diastolic": row.get("diastolic_bp"),
                    "heartRate": row.get("heart_rate"),
                    "weight": row.get("weight_kg"),
                    "height": row.get("height_cm"),
                    "bmi": row.get("bmi"),
                    "bsa": row.get("bsa"),
                    "hba1c": row.get("hba1c"),
                    "troponin": row.get("troponin_i"),
                }
            },
        }
    except Exception as e:
        logger.error(f"Error fetching vitals for {dna_id}: {e}")
        return {"success": False, "error": str(e)}


@router.get("/{dna_id}/imaging")
async def get_patient_imaging(dna_id: str, db=Depends(get_db)):
    """Get patient imaging data (Echo and MRI)"""
    try:
        stmt = text("""
            SELECT echo_date, echo_ef, mri_date, mri_ef, rv_ef
            FROM patients
            WHERE dna_id = :dna_id
        """)
        row = db.execute(stmt, {"dna_id": dna_id}).mappings().fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Patient not found")

        echo = None
        if row.get("echo_ef") is not None or row.get("echo_date") is not None:
            echo = {
                "echo_date": row.get("echo_date"),
                "aortic_root": None,
                "left_atrium": None,
                "right_ventricle": None,
                "lvedd": None,
                "lvesd": None,
                "ivsd": None,
                "ivss": None,
                "lvpwd": None,
                "lvpws": None,
                "ef": row.get("echo_ef"),
                "fs": None,
                "subaortic_membrane": False,
                "mitral_regurge": None,
                "mitral_stenosis": False,
                "tricuspid_regurge": None,
                "tricuspid_stenosis": False,
                "aortic_regurge": None,
                "aortic_stenosis": False,
                "pulmonary_regurge": None,
                "pulmonary_stenosis": False,
                "missing_echo": row.get("echo_ef") is None,
            }

        mri = None
        if row.get("mri_ef") is not None or row.get("mri_date") is not None:
            mri = {
                "mri_performed": row.get("mri_ef") is not None,
                "heart_rate_during_mri": None,
                "mri_date": row.get("mri_date"),
                "lv_ejection_fraction": row.get("mri_ef"),
                "lv_end_diastolic_volume": None,
                "lv_end_systolic_volume": None,
                "lv_mass": None,
                "rv_ejection_fraction": row.get("rv_ef"),
                "missing_mri": row.get("mri_ef") is None,
            }

        return {"success": True, "data": {"echo": echo, "mri": mri}}
    except Exception as e:
        logger.error(f"Error fetching imaging for {dna_id}: {e}")
        return {"success": False, "error": str(e)}


@router.get("/{dna_id}/risk-factors")
async def get_patient_risk_factors(dna_id: str, db=Depends(get_db)):
    """Get patient risk factors"""
    try:
        stmt = text("""
            SELECT
                dna_id,
                age,
                bmi,
                COALESCE(diabetes_mellitus, false) AS diabetes_mellitus,
                COALESCE(high_blood_pressure, false) AS high_blood_pressure,
                COALESCE(dyslipidemia, false) AS dyslipidemia,
                COALESCE(current_smoker, false) AS current_smoker,
                COALESCE(ever_smoked, false) AS ever_smoked,
                COALESCE(heart_attack_or_angina, false) AS heart_attack_or_angina,
                COALESCE(history_sudden_death, false) AS history_sudden_death,
                COALESCE(history_premature_cad, false) AS history_premature_cad
            FROM patients
            WHERE dna_id = :dna_id
        """)
        row = db.execute(stmt, {"dna_id": dna_id}).mappings().fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Patient not found")

        obese = (row.get("bmi") or 0) >= 30

        risk_score = 0
        risk_score += 2 if row.get("diabetes_mellitus") else 0
        risk_score += 2 if row.get("high_blood_pressure") else 0
        risk_score += 2 if row.get("dyslipidemia") else 0
        risk_score += 2 if row.get("current_smoker") else 0
        risk_score += 1 if obese else 0
        risk_score += 2 if row.get("heart_attack_or_angina") else 0
        risk_score += 1 if (row.get("age") or 0) >= 55 else 0

        return {
            "success": True,
            "data": {
                "dna_id": row.get("dna_id"),
                "diabetes_mellitus": bool(row.get("diabetes_mellitus")),
                "high_blood_pressure": bool(row.get("high_blood_pressure")),
                "dyslipidemia": bool(row.get("dyslipidemia")),
                "current_smoker": bool(row.get("current_smoker")),
                "ever_smoked": bool(row.get("ever_smoked")),
                "obese": bool(obese),
                "heart_attack_or_angina": bool(row.get("heart_attack_or_angina")),
                "history_sudden_death": bool(row.get("history_sudden_death")),
                "history_premature_cad": bool(row.get("history_premature_cad")),
                "risk_score": int(risk_score),
            },
        }
    except Exception as e:
        logger.error(f"Error fetching risk factors for {dna_id}: {e}")
        return {"success": False, "error": str(e)}
