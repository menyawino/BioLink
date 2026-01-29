import pandas as pd
import sqlalchemy as sa
from sqlalchemy import text
from app.config import settings
import logging

logger = logging.getLogger(__name__)


def to_bool(value):
    if pd.isna(value):
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(int(value))
    if isinstance(value, str):
        v = value.strip().lower()
        if v in {"yes", "y", "true", "1"}:
            return True
        if v in {"no", "n", "false", "0"}:
            return False
    return None


def to_float(value):
    if pd.isna(value):
        return None
    try:
        return float(value)
    except Exception:
        return None


def to_int(value):
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        v = value.strip()
        if "-" in v:
            parts = [p for p in v.split("-") if p.strip()]
            try:
                nums = [float(p) for p in parts]
                if nums:
                    return int(sum(nums) / len(nums))
            except Exception:
                return None
        try:
            return int(float(v))
        except Exception:
            return None
    return None


def load_full_data():
    """Load full EHVol CSV into the patients table."""
    try:
        df = pd.read_csv('/app/db/100925_Cleaned_EHVol_Data_STANDARDIZED.csv')
        logger.info(f"Loaded {len(df)} records from full CSV")

        engine = sa.create_engine(settings.database_url)

        # Clear existing data
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM patients"))

        records = []
        for _, row in df.iterrows():
            record = {
                'dna_id': str(row['dna_id']),
                'age': to_int(row.get('age')),
                'gender': row.get('gender'),
                'nationality': row.get('nationality'),
                'current_city': row.get('current_city_of_residence'),
                'enrollment_date': pd.to_datetime(row.get('date_of_enrolment')).date() if pd.notna(row.get('date_of_enrolment')) else None,
                'heart_rate': to_float(row.get('heart_rate')),
                'height_cm': to_float(row.get('height_cm_')),
                'weight_kg': to_float(row.get('weight_kg_')),
                'bmi': to_float(row.get('bmi')),
                'bsa': to_float(row.get('bsa')),
                'hba1c': to_float(row.get('hba1c')),
                'troponin_i': to_float(row.get('troponin_i')),
                'echo_ef': to_float(row.get('ef')),
                'mri_ef': to_float(row.get('left_ventricular_ejection_fraction')),
                'rv_ef': to_float(row.get('right_ventricular_ef')),
                'current_smoker': to_bool(row.get('current_recent_smoker_1_year_')),
                'ever_smoked': to_bool(row.get('ever_smoked')),
                'smoking_years': to_float(row.get('smoking_years')),
                'cigarettes_per_day': to_int(row.get('how_many_cigarettes_have_you_been_smoking_a_day_')),
                'drinks_alcohol': to_bool(row.get('do_you_drink_alcohol_')),
                'takes_medication': to_bool(row.get('do_you_take_any_medication_currently_')),
                'diabetes_mellitus': to_bool(row.get('diabetes_mellitus')),
                'high_blood_pressure': to_bool(row.get('high_blood_pressure')),
                'dyslipidemia': to_bool(row.get('dyslipidemia')),
                'heart_attack_or_angina': to_bool(row.get('heart_attack_or_angina')),
                'prior_heart_failure': to_bool(row.get('prior_heart_failure_previous_hx_')),
                'history_sudden_death': to_bool(row.get('history_of_sudden_death_history')),
                'history_premature_cad': to_bool(row.get('history_of_premature_cad')),
            }

            bp_str = row.get('bp')
            if pd.notna(bp_str) and isinstance(bp_str, str):
                try:
                    systolic, diastolic = bp_str.split('/')
                    record['systolic_bp'] = to_float(systolic.strip())
                    record['diastolic_bp'] = to_float(diastolic.strip())
                except Exception:
                    pass

            records.append(record)

        with engine.begin() as conn:
            for record in records:
                columns = ', '.join(record.keys())
                placeholders = ', '.join([f':{k}' for k in record.keys()])
                sql = f"INSERT INTO patients ({columns}) VALUES ({placeholders})"
                conn.execute(text(sql), record)

        logger.info(f"Inserted {len(records)} records into patients table")

    except Exception as e:
        logger.error(f"Failed to load full data: {e}")
        raise


if __name__ == "__main__":
    load_full_data()
