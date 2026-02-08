# BioLink Python Backend

FastAPI backend for BioLink (patients registry + analytics + charts).

## Setup

### 1. Install Dependencies

```bash
cd backend-py
pip install -r requirements.txt
```

### 2. Configure Environment

Create `backend-py/.env` (see `backend-py/.env.example`).

Important:
- Do not commit real credentials; keep `.env` files local.

### 3. Start the Backend

```bash
# Using the start script
./start.sh

# Or manually
python -m uvicorn app.main:app --host 0.0.0.0 --port 3001 --reload
```

Server runs on: `http://localhost:3001`

## API Endpoints

### Chat

- `POST /api/chat` - Send chat message

### Patients

- `GET /api/patients?search=...&gender=...&limit=...` - Search patients

### Health

- `GET /` - API status
- `GET /health` - Database health check

## Key Features

✅ AI-powered chat system  
✅ PostgreSQL database connectivity  
✅ CORS enabled for frontend  
✅ Production-ready error handling  
✅ Structured logging  

## Database

Uses PostgreSQL. Connection string from `DATABASE_URL` env var.

This backend is intentionally streamlined around a single denormalized table with a supporting summary view:
- `patients`: Maintains the full set of clinical, imaging, genomic, and risk-factor fields used by patient detail endpoints and deep analytical queries.
-- `EHVOL`: Curated read-only view exposed to list/search endpoints and availability dashboards; keep queries here focused on counts, filters, and data-availability metrics (data completeness, imaging/genomics flags, geographic categories).

The policy is explicit: target `patients` for heavy clinical/feature processing, and reserve `EHVOL` for the tables/filters that power the registry list, search, and availability metrics.

Schema is auto-bootstrapped on backend startup.

### Importing the CSV dataset

To load the standardized CSV into Postgres:

```bash
cd backend-py
python -m app.scripts.import_patients_csv
```

## Environment Variables

All credentials are in `backend-py/.env` and configured from the main `.env` file.

Key variables:
- `DATABASE_URL` - PostgreSQL connection
- `SQLSERVER_*` - SQL Server connection used for live EHVol registry

## Stage 1: SQL Server Smoke Test (EHVol)

This verifies connectivity, schema, and sample rows from the SQL Server registry.

1) Configure SQL Server credentials in `backend-py/.env` (see `.env.example`).
2) Run the smoke test script:

```bash
cd backend-py
python -m app.scripts.sqlserver_smoke_test
```

Expected output: column list + 10 sample rows (id, age, gender, ef, hypertension) and
`Stage 1 OK` message.

## RAG Pipeline (pgvector + Debezium + Ollama)

### Docker services

From repo root:

```bash
docker compose -f docker-compose.rag.yml up -d
```

### Stage 2: pgvector setup

```bash
cd backend-py
python -m app.scripts.stage2_pgvector_setup
```

### Stage 3: Embed sample notes

```bash
cd backend-py
python -m app.scripts.stage3_embed_sample
```

### Stage 4: CDC consumer (Debezium)

Register connector:

```bash
cd backend-py
./scripts/register_debezium_connector.sh
```

Run the CDC consumer:

```bash
python -m app.scripts.stage4_cdc_consumer
```

### Stage 5: RAG query test

```bash
cd backend-py
python -m app.scripts.stage5_rag_query
```

### Stage 6: End-to-end query

```bash
cd backend-py
python -m app.scripts.stage6_e2e
```

### API

`POST /api/rag` with JSON `{ "question": "..." }`

## Troubleshooting

### Database connection fails

Ensure PostgreSQL is running:

```bash
# Check if running
sudo systemctl status postgresql

# Or test connection
psql -U biolink -d biolink -h localhost
```

## Switching from TypeScript Backend

The old Node.js/TypeScript backend (`backend/`) is still available but superseded by this Python version.

To fully migrate:

1. ✅ Tested: Frontend proxy points to `:3001` (works with both)
2. ✅ Verified: All endpoints maintain same API contract

To remove the old backend:

```bash
# Keep for reference, or:
rm -rf ../backend
```

## Development Tips

- Logging to stdout (check terminal for debug info)
- Hot reload enabled (`--reload` flag)
- Database debug via raw SQL in routes
- Use `.env` for local configuration

## Agent Orchestrator Tests

Run unit tests (routing, tool registry safety, orchestrator flow):

```bash
python -m unittest discover -s backend-py/tests
```
