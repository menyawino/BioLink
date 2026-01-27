import unittest
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = TESTS_DIR.parent
sys.path.insert(0, str(BACKEND_ROOT))

from app.services.audit import redact_payload


class AuditTests(unittest.TestCase):
    def test_redacts_sensitive_fields(self):
        payload = {
            "dna_id": "EHV001",
            "name": "Jane Doe",
            "email": "jane@example.com",
            "message": "safe",
        }
        redacted = redact_payload(payload)
        self.assertEqual(redacted["dna_id"], "[REDACTED]")
        self.assertEqual(redacted["name"], "[REDACTED]")
        self.assertEqual(redacted["email"], "[REDACTED]")
        self.assertEqual(redacted["message"], "safe")


if __name__ == "__main__":
    unittest.main()