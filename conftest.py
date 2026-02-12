import sys
from pathlib import Path

# Ensure repository root and backend-py are on sys.path so tests can import app
ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend-py"
for path in (ROOT, BACKEND):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
