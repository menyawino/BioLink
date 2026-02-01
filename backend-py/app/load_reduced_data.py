import pandas as pd
import sqlalchemy as sa
from sqlalchemy import text
from app.config import settings
import logging

logger = logging.getLogger(__name__)

def load_reduced_data():
    """Load 50 records from reduced EHVol CSV into the patients table"""
    try:
        # Locate CSV file (try container path first, then repo paths)
        possible_paths = [
            '/app/db/reduced_ehvol_50.csv',
            str(Path(__file__).resolve().parents[1] / 'db' / 'reduced_ehvol_50.csv'),
            str(Path(__file__).resolve().parents[2] / 'db' / 'reduced_ehvol_50.csv'),
            str(Path(__file__).resolve().parents[3] / 'db' / 'reduced_ehvol_50.csv'),
        ]
        csv_path = None
        for p in possible_paths:
            if Path(p).exists():
                csv_path = p
                break
        if csv_path is None:
            raise FileNotFoundError("Reduced dataset not found. Looked in: " + ", ".join(possible_paths))

        # Read the reduced CSV
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(df)} records from CSV at {csv_path}")

        # Create database engine
        engine = sa.create_engine(settings.database_url)

        # Ensure schema exists before inserting
        from app.db_bootstrap import ensure_schema
        ensure_schema(engine)

        # Clear existing data
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM patients"))

        # Map CSV columns to table columns
        records = []
        for _, row in df.iterrows():
            record = {
                'dna_id': str(row['dna_id']),
                'age': int(row['age']) if pd.notna(row['age']) else None,
                'gender': row['gender'],
                'nationality': row.get('nationality'),
                'current_city': row.get('current_city_of_residence'),
                'enrollment_date': pd.to_datetime(row.get('date_of_enrolment')).date() if pd.notna(row.get('date_of_enrolment')) else None,
                'heart_rate': float(row.get('heart_rate')) if pd.notna(row.get('heart_rate')) else None,
                'height_cm': float(row.get('height_cm_')) if pd.notna(row.get('height_cm_')) else None,
                'weight_kg': float(row.get('weight_kg_')) if pd.notna(row.get('weight_kg_')) else None,
                'bmi': float(row.get('bmi')) if pd.notna(row.get('bmi')) else None,
                'bsa': float(row.get('bsa')) if pd.notna(row.get('bsa')) else None,
                'hba1c': float(row.get('hba1c')) if pd.notna(row.get('hba1c')) else None,
                'troponin_i': float(row.get('troponin_i')) if pd.notna(row.get('troponin_i')) else None,
                'echo_ef': float(row.get('ef')) if pd.notna(row.get('ef')) else None,
                'mri_ef': float(row.get('left_ventricular_ejection_fraction')) if pd.notna(row.get('left_ventricular_ejection_fraction')) else None,
                'rv_ef': float(row.get('right_ventricular_ef')) if pd.notna(row.get('right_ventricular_ef')) else None,
                'current_smoker': bool(row.get('current_recent_smoker_1_year_')) if pd.notna(row.get('current_recent_smoker_1_year_')) else None,
                'ever_smoked': bool(row.get('ever_smoked')) if pd.notna(row.get('ever_smoked')) else None,
                'smoking_years': float(row.get('smoking_years')) if pd.notna(row.get('smoking_years')) else None,
                'cigarettes_per_day': int(row.get('how_many_cigarettes_have_you_been_smoking_a_day_')) if pd.notna(row.get('how_many_cigarettes_have_you_been_smoking_a_day_')) else None,
                'drinks_alcohol': bool(row.get('do_you_drink_alcohol_')) if pd.notna(row.get('do_you_drink_alcohol_')) else None,
                'takes_medication': bool(row.get('do_you_take_any_medication_currently_')) if pd.notna(row.get('do_you_take_any_medication_currently_')) else None,
                'diabetes_mellitus': bool(row.get('diabetes_mellitus')) if pd.notna(row.get('diabetes_mellitus')) else None,
                'high_blood_pressure': bool(row.get('high_blood_pressure')) if pd.notna(row.get('high_blood_pressure')) else None,
                'dyslipidemia': bool(row.get('dyslipidemia')) if pd.notna(row.get('dyslipidemia')) else None,
                'heart_attack_or_angina': bool(row.get('heart_attack_or_angina')) if pd.notna(row.get('heart_attack_or_angina')) else None,
                'prior_heart_failure': bool(row.get('prior_heart_failure_previous_hx_')) if pd.notna(row.get('prior_heart_failure_previous_hx_')) else None,
                'history_sudden_death': bool(row.get('history_of_sudden_death_history')) if pd.notna(row.get('history_of_sudden_death_history')) else None,
                'history_premature_cad': bool(row.get('history_of_premature_cad')) if pd.notna(row.get('history_of_premature_cad')) else None,
            }

            # Parse BP
            bp_str = row.get('bp')
            if pd.notna(bp_str) and isinstance(bp_str, str):
                try:
                    systolic, diastolic = bp_str.split('/')
                    record['systolic_bp'] = float(systolic.strip())
                    record['diastolic_bp'] = float(diastolic.strip())
                except:
                    pass

            records.append(record)

        # Insert records
        with engine.begin() as conn:
            for record in records:
                columns = ', '.join(record.keys())
                placeholders = ', '.join([f':{k}' for k in record.keys()])
                sql = f"INSERT INTO patients ({columns}) VALUES ({placeholders})"
                conn.execute(text(sql), record)

        logger.info(f"Inserted {len(records)} records into patients table")

    except Exception as e:
        logger.error(f"Failed to load reduced data: {e}")
        raise

if __name__ == "__main__":
    load_reduced_data()