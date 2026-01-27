import unittest
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = TESTS_DIR.parent
sys.path.insert(0, str(BACKEND_ROOT))

from app.services.tool_registry import ToolRegistry


class ToolRegistrySafetyTests(unittest.TestCase):
    def setUp(self):
        self.registry = ToolRegistry()

    def test_rejects_non_select(self):
        with self.assertRaises(ValueError):
            self.registry._sanitize_select_sql("DELETE FROM patients", 100)

    def test_rejects_multiple_statements(self):
        with self.assertRaises(ValueError):
            self.registry._sanitize_select_sql("SELECT * FROM patients; DROP TABLE patients", 100)

    def test_rejects_disallowed_tables(self):
        with self.assertRaises(ValueError):
            self.registry._sanitize_select_sql("SELECT * FROM secret_table", 100)

    def test_rejects_copy(self):
        with self.assertRaises(ValueError):
            self.registry._sanitize_select_sql("COPY patients TO '/tmp/out.csv'", 100)

    def test_adds_limit_when_missing(self):
        sql = self.registry._sanitize_select_sql("SELECT * FROM patients", 50)
        self.assertTrue(sql.upper().endswith("LIMIT 50"))


if __name__ == "__main__":
    unittest.main()