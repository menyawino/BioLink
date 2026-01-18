from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

from sqlalchemy import text

from app.database import engine
from app.db_bootstrap import ensure_schema


def _to_none(value: Any) -> str | None:
    if value is None:
        return None
    value_str = str(value).strip()
    if value_str == "" or value_str.lower() in {"na", "n/a", "none", "null"}:
        return None
    return value_str


def parse_int(value: Any) -> int | None:
    value_str = _to_none(value)
    if value_str is None:
        return None
    try:
        return int(float(value_str))
    except ValueError:
        return None


def parse_float(value: Any) -> float | None:
    value_str = _to_none(value)
    if value_str is None:
        return None
    try:
        return float(value_str)
    except ValueError:
        return None


def parse_bool(value: Any) -> bool | None:
    value_str = _to_none(value)
    if value_str is None:
        return None

    normalized = value_str.strip().lower()
    if normalized in {"1", "true", "t", "yes", "y"}:
        return True
    if normalized in {"0", "false", "f", "no", "n"}:
        return False

    # Some columns contain labels like "Complete"; treat as unknown.
    return None


def parse_date(value: Any) -> date | None:
    value_str = _to_none(value)
    if value_str is None:
        return None

    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(value_str, fmt).date()
        except ValueError:
            pass

    return None


def parse_bp(value: Any) -> tuple[float | None, float | None]:
    value_str = _to_none(value)
    if value_str is None:
        return (None, None)

    # Common format: "120/80"
    if "/" in value_str:
        left, right = value_str.split("/", 1)
        return (parse_float(left), parse_float(right))

    # Sometimes a single number is present; treat as systolic.
    return (parse_float(value_str), None)


@dataclass(frozen=True)
class ImportStats:
    processed: int
    inserted_or_updated: int


DB_COLUMNS: tuple[str, ...] = (
    "dna_id",
    "date_of_birth",
    "age",
    "gender",
    "nationality",
    "enrollment_date",
    "current_city",
    "current_city_category",
    "childhood_city_category",
    "migration_pattern",
    "heart_rate",
    "systolic_bp",
    "diastolic_bp",
    "height_cm",
    "weight_kg",
    "bmi",
    "bsa",
    "hba1c",
    "troponin_i",
    "echo_date",
    "echo_ef",
    "mri_date",
    "mri_ef",
    "current_smoker",
    "former_smoker",
    "ever_smoked",
    "smoking_years",
    "cigarettes_per_day",
    "drinks_alcohol",
    "takes_medication",
    "diabetes_mellitus",
    "high_blood_pressure",
    "dyslipidemia",
    "heart_attack_or_angina",
    "prior_heart_failure",
    "history_sudden_death",
    "history_premature_cad",
)


UPSERT_SQL = text(
    """
INSERT INTO patients (
    dna_id,
    date_of_birth,
    age,
    gender,
    nationality,
    enrollment_date,
    current_city,
    current_city_category,
    childhood_city_category,
    migration_pattern,
    heart_rate,
    systolic_bp,
    diastolic_bp,
    height_cm,
    weight_kg,
    bmi,
    bsa,
    hba1c,
    troponin_i,
    echo_date,
    echo_ef,
    mri_date,
    mri_ef,
    current_smoker,
    former_smoker,
    ever_smoked,
    smoking_years,
    cigarettes_per_day,
    drinks_alcohol,
    takes_medication,
    diabetes_mellitus,
    high_blood_pressure,
    dyslipidemia,
    heart_attack_or_angina,
    prior_heart_failure,
    history_sudden_death,
    history_premature_cad
) VALUES (
    :dna_id,
    :date_of_birth,
    :age,
    :gender,
    :nationality,
    :enrollment_date,
    :current_city,
    :current_city_category,
    :childhood_city_category,
    :migration_pattern,
    :heart_rate,
    :systolic_bp,
    :diastolic_bp,
    :height_cm,
    :weight_kg,
    :bmi,
    :bsa,
    :hba1c,
    :troponin_i,
    :echo_date,
    :echo_ef,
    :mri_date,
    :mri_ef,
    :current_smoker,
    :former_smoker,
    :ever_smoked,
    :smoking_years,
    :cigarettes_per_day,
    :drinks_alcohol,
    :takes_medication,
    :diabetes_mellitus,
    :high_blood_pressure,
    :dyslipidemia,
    :heart_attack_or_angina,
    :prior_heart_failure,
    :history_sudden_death,
    :history_premature_cad
)
ON CONFLICT (dna_id) DO UPDATE SET
    date_of_birth = EXCLUDED.date_of_birth,
    age = EXCLUDED.age,
    gender = EXCLUDED.gender,
    nationality = EXCLUDED.nationality,
    enrollment_date = EXCLUDED.enrollment_date,
    current_city = EXCLUDED.current_city,
    current_city_category = EXCLUDED.current_city_category,
    childhood_city_category = EXCLUDED.childhood_city_category,
    migration_pattern = EXCLUDED.migration_pattern,
    heart_rate = EXCLUDED.heart_rate,
    systolic_bp = EXCLUDED.systolic_bp,
    diastolic_bp = EXCLUDED.diastolic_bp,
    height_cm = EXCLUDED.height_cm,
    weight_kg = EXCLUDED.weight_kg,
    bmi = EXCLUDED.bmi,
    bsa = EXCLUDED.bsa,
    hba1c = EXCLUDED.hba1c,
    troponin_i = EXCLUDED.troponin_i,
    echo_date = EXCLUDED.echo_date,
    echo_ef = EXCLUDED.echo_ef,
    mri_date = EXCLUDED.mri_date,
    mri_ef = EXCLUDED.mri_ef,
    current_smoker = EXCLUDED.current_smoker,
    former_smoker = EXCLUDED.former_smoker,
    ever_smoked = EXCLUDED.ever_smoked,
    smoking_years = EXCLUDED.smoking_years,
    cigarettes_per_day = EXCLUDED.cigarettes_per_day,
    drinks_alcohol = EXCLUDED.drinks_alcohol,
    takes_medication = EXCLUDED.takes_medication,
    diabetes_mellitus = EXCLUDED.diabetes_mellitus,
    high_blood_pressure = EXCLUDED.high_blood_pressure,
    dyslipidemia = EXCLUDED.dyslipidemia,
    heart_attack_or_angina = EXCLUDED.heart_attack_or_angina,
    prior_heart_failure = EXCLUDED.prior_heart_failure,
    history_sudden_death = EXCLUDED.history_sudden_death,
    history_premature_cad = EXCLUDED.history_premature_cad,
    updated_at = NOW();
"""
)


def row_to_record(row: dict[str, str]) -> dict[str, Any] | None:
    dna_id = _to_none(row.get("dna_id"))
    if dna_id is None:
        return None

    systolic_bp, diastolic_bp = parse_bp(row.get("bp"))

    current_smoker = parse_bool(row.get("current_recent_smoker_1_year_"))
    ever_smoked = parse_bool(row.get("ever_smoked"))
    former_smoker: bool | None
    if current_smoker is False and ever_smoked is True:
        former_smoker = True
    elif current_smoker is True:
        former_smoker = False
    else:
        former_smoker = None

    record: dict[str, Any] = {
        "dna_id": dna_id,
        "date_of_birth": parse_date(row.get("date_of_birth")),
        "age": parse_int(row.get("age")),
        "gender": _to_none(row.get("gender")),
        "nationality": _to_none(row.get("nationality")),
        "enrollment_date": parse_date(row.get("date_of_enrolment")),
        "current_city": _to_none(row.get("current_city_of_residence")),
        "current_city_category": _to_none(row.get("current_city_category")),
        "childhood_city_category": _to_none(row.get("childhood_city_category")),
        "migration_pattern": _to_none(row.get("migration_pattern")),
        "heart_rate": parse_float(row.get("heart_rate")),
        "systolic_bp": systolic_bp,
        "diastolic_bp": diastolic_bp,
        "height_cm": parse_float(row.get("height_cm_")),
        "weight_kg": parse_float(row.get("weight_kg_")),
        "bmi": parse_float(row.get("bmi")),
        "bsa": parse_float(row.get("bsa")),
        "hba1c": parse_float(row.get("hba1c")),
        "troponin_i": parse_float(row.get("troponin_i")),
        "echo_date": parse_date(row.get("echo_date")),
        "echo_ef": parse_float(row.get("ef")),
        "mri_date": parse_date(row.get("mri_date")),
        "mri_ef": parse_float(row.get("left_ventricular_ejection_fraction")),
        "current_smoker": current_smoker,
        "former_smoker": former_smoker,
        "ever_smoked": ever_smoked,
        "smoking_years": parse_float(row.get("smoking_years"))
        or parse_float(row.get("how_long_have_you_been_smoking_")),
        "cigarettes_per_day": parse_int(row.get("how_many_cigarettes_have_you_been_smoking_a_day_")),
        "drinks_alcohol": parse_bool(row.get("do_you_drink_alcohol_")),
        "takes_medication": parse_bool(row.get("do_you_take_any_medication_currently_")),
        "diabetes_mellitus": parse_bool(row.get("diabetes_mellitus")),
        "high_blood_pressure": parse_bool(row.get("high_blood_pressure")),
        "dyslipidemia": parse_bool(row.get("dyslipidemia")),
        "heart_attack_or_angina": parse_bool(row.get("heart_attack_or_angina")),
        "prior_heart_failure": parse_bool(row.get("prior_heart_failure_previous_hx_")),
        "history_sudden_death": parse_bool(row.get("history_of_sudden_death_history")),
        "history_premature_cad": parse_bool(row.get("history_of_premature_cad")),
    }

    # Ensure keys exist for executemany
    for col in DB_COLUMNS:
        record.setdefault(col, None)

    return record


def chunks(items: Iterable[dict[str, Any]], batch_size: int) -> Iterable[list[dict[str, Any]]]:
    batch: list[dict[str, Any]] = []
    for item in items:
        batch.append(item)
        if len(batch) >= batch_size:
            yield batch
            batch = []
    if batch:
        yield batch


def import_csv(csv_path: Path, *, batch_size: int, limit: int | None, dry_run: bool) -> ImportStats:
    ensure_schema(engine)

    processed = 0
    inserted_or_updated = 0

    def iter_records() -> Iterable[dict[str, Any]]:
        nonlocal processed
        with csv_path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rec = row_to_record(row)
                processed += 1
                if rec is None:
                    continue
                yield rec
                if limit is not None and processed >= limit:
                    break

    with engine.begin() as conn:
        for batch in chunks(iter_records(), batch_size=batch_size):
            if dry_run:
                continue
            result = conn.execute(UPSERT_SQL, batch)
            # For executemany, rowcount is driver-dependent; treat as best-effort.
            if result.rowcount is not None and result.rowcount > 0:
                inserted_or_updated += result.rowcount
            else:
                inserted_or_updated += len(batch)

    return ImportStats(processed=processed, inserted_or_updated=inserted_or_updated)


def main() -> None:
    parser = argparse.ArgumentParser(description="Import the standardized CSV into Postgres patients table")
    parser.add_argument(
        "--csv",
        default="../db/100925_Cleaned_EHVol_Data_STANDARDIZED.csv",
        help="Path to CSV file (default: ../db/100925_Cleaned_EHVol_Data_STANDARDIZED.csv)",
    )
    parser.add_argument("--batch-size", type=int, default=1000)
    parser.add_argument("--limit", type=int, default=None, help="Only import first N rows")
    parser.add_argument("--dry-run", action="store_true", help="Parse rows but do not write to DB")

    args = parser.parse_args()
    csv_path = Path(args.csv).expanduser().resolve()

    if not csv_path.exists():
        raise SystemExit(f"CSV not found: {csv_path}")

    stats = import_csv(csv_path, batch_size=args.batch_size, limit=args.limit, dry_run=args.dry_run)

    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM patients"))
        total = count.scalar_one()

    print(
        f"Imported {stats.processed} rows (upserted ~{stats.inserted_or_updated}). "
        f"patients table now has {total} rows."
    )


if __name__ == "__main__":
    main()
