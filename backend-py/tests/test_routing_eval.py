import unittest
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = TESTS_DIR.parent
sys.path.insert(0, str(BACKEND_ROOT))

from app.services.intent_router import IntentRouter


class RoutingEvalTests(unittest.TestCase):
    def setUp(self):
        self.router = IntentRouter()

    def test_routing_examples(self):
        samples = [
            ("How many patients are there?", "sql"),
            ("Build a cohort of females with diabetes", "cohort"),
            ("Find mention of hypertension in notes", "rag"),
            ("Open the registry view", "ui"),
            ("Hello there", "general"),
        ]

        for message, expected in samples:
            with self.subTest(message=message):
                self.assertEqual(self.router.classify(message), expected)


if __name__ == "__main__":
    unittest.main()