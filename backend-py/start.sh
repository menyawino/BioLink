#!/bin/bash

# Start Python backend
cd "$(dirname "$0")"

echo "🚀 Starting BioLink Python Backend..."
python -m uvicorn app.main:app --host 0.0.0.0 --port 3001 --reload
