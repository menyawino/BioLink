#!/bin/bash

# Start Python backend
cd "$(dirname "$0")"

# Prefer the active environment (conda/mamba or an existing venv).
# Only create/use a local ./venv if nothing is active.
if [ -n "${VIRTUAL_ENV:-}" ] || [ -n "${CONDA_PREFIX:-}" ]; then
	echo "Using active Python environment"
else
	if [ ! -d "venv" ]; then
		python -m venv venv
	fi
	# shellcheck disable=SC1091
	source venv/bin/activate
fi

pip install -q -r requirements.txt

echo "🚀 Starting BioLink Python Backend..."
python -m uvicorn app.main:app --host 0.0.0.0 --port 3001 --reload
