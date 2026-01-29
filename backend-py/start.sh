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

# Load reduced data if table is empty
python -c "
from sqlalchemy import text, create_engine
from app.config import settings
from pathlib import Path
engine = create_engine(settings.database_url)
with engine.begin() as conn:
    result = conn.execute(text('SELECT COUNT(*) FROM patients'))
    count = result.fetchone()[0]
    if count == 0:
        full_path = Path('/app/db/100925_Cleaned_EHVol_Data_STANDARDIZED.csv')
        if full_path.exists():
            print('Loading full dataset...')
            from app.load_full_data import load_full_data
            load_full_data()
        else:
            print('Full dataset not found, loading reduced data...')
            from app.load_reduced_data import load_reduced_data
            load_reduced_data()
    else:
        print(f'Data already loaded: {count} records')
"

echo "🚀 Starting BioLink Python Backend..."
python -m uvicorn app.main:app --host 0.0.0.0 --port 3001 --reload
