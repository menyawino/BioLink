#!/bin/bash

# Start Python backend
cd "$(dirname "$0")"
source venv/bin/activate 2>/dev/null || python -m venv venv && source venv/bin/activate
pip install -q -r requirements.txt

echo "🚀 Starting BioLink Python Backend..."
python -m uvicorn app.main:app --host 0.0.0.0 --port 3001 --reload
