import unittest
import sys
from pathlib import Path
TESTS_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = TESTS_DIR.parent
sys.path.insert(0, str(BACKEND_ROOT))

import sqlalchemy as sa
from app.services.tool_registry import ToolRegistry


class ToolRegistryFilterTests(unittest.TestCase):
    def setUp(self):
        # Use an in-memory sqlite engine for safety
        self.engine = sa.create_engine("sqlite:///:memory:")
        with self.engine.begin() as conn:
            conn.execute(sa.text("""
                CREATE TABLE patients (
                    dna_id TEXT PRIMARY KEY,
                    name TEXT,
                    age INTEGER,
                    gender TEXT,
                    echo_ef DOUBLE,
                    mri_ef DOUBLE,
                    hba1c DOUBLE,
                    troponin_i DOUBLE,
                    history_sudden_death BOOLEAN,
                    history_premature_cad BOOLEAN,
                    diabetes_mellitus BOOLEAN,
                    high_blood_pressure BOOLEAN,
                    nationality TEXT,
                    current_city_category TEXT,
                    current_city TEXT,
                    enrollment_date DATE
                )
            """))
            # Insert two rows: one with imaging/labs/family history, one without
            conn.execute(sa.text("INSERT INTO patients (dna_id, age, gender, echo_ef, hba1c, history_sudden_death, nationality, current_city_category, current_city) VALUES ('dna1', 50, 'female', 55.0, 6.1, 1, 'Africa', 'Urban', 'Cairo')"))
            conn.execute(sa.text("INSERT INTO patients (dna_id, age, gender) VALUES ('dna2', 40, 'male')"))

        self.registry = ToolRegistry(engine_override=self.engine)

    def test_has_imaging_filter(self):
        res = self.registry.build_cohort({"has_imaging": True, "limit": 10})
        self.assertEqual(res["count"], 1)

    def test_has_labs_filter(self):
        res = self.registry.build_cohort({"has_labs": True, "limit": 10})
        self.assertEqual(res["count"], 1)

    def test_has_family_history_filter(self):
        res = self.registry.build_cohort({"has_family_history": True, "limit": 10})
        self.assertEqual(res["count"], 1)

    def test_region_filter(self):
        res = self.registry.build_cohort({"region": "Africa", "limit": 10})
        self.assertEqual(res["count"], 1)

    def test_has_genomics_filter_true_returns_empty(self):
        res = self.registry.build_cohort({"has_genomics": True, "limit": 10})
        self.assertEqual(res["count"], 0)


if __name__ == "__main__":
    unittest.main()
