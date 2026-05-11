#!/bin/sh

set -eu

/app/.venv/bin/python - <<'PY'
import os

from sqlalchemy import create_engine, text

metadata_uri = os.getenv("SUPERSET_METADATA_DATABASE_URI", "").strip()
metadata_schema = os.getenv("SUPERSET_METADATA_SCHEMA", "").strip()

if metadata_uri and metadata_schema:
    engine = create_engine(metadata_uri, pool_pre_ping=True)
    quoted_schema = metadata_schema.replace('"', '""')
    with engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{quoted_schema}"'))
    engine.dispose()
PY

superset db upgrade
superset fab create-admin \
  --username "${SUPERSET_ADMIN_USER}" \
  --firstname "${SUPERSET_ADMIN_FIRSTNAME}" \
  --lastname "${SUPERSET_ADMIN_LASTNAME}" \
  --email "${SUPERSET_ADMIN_EMAIL}" \
  --password "${SUPERSET_ADMIN_PASSWORD}" || true
superset init
/app/.venv/bin/python /app/superset_init.py

exec /app/.venv/bin/gunicorn \
  --bind 0.0.0.0:8088 \
  --workers "${SUPERSET_GUNICORN_WORKERS:-2}" \
  --worker-class gthread \
  --threads "${SUPERSET_GUNICORN_THREADS:-8}" \
  --timeout "${SUPERSET_GUNICORN_TIMEOUT:-120}" \
  "superset.app:create_app()"