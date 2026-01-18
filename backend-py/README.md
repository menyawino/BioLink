# BioLink Python Backend

FastAPI backend for BioLink (patients registry + analytics + charts + optional Azure AI Foundry integration).

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

### 3. Install Python Azure SDKs

The dependencies include:
- `azure-ai-projects==0.15.0` - Azure AI Foundry Agents API SDK
- `azure-identity==1.15.0` - Azure authentication
- `azure-ai-inference==0.16.0` - Azure AI Inference

### 4. Start the Backend

```bash
# Using the start script
./start.sh

# Or manually
python -m uvicorn app.main:app --host 0.0.0.0 --port 3001 --reload
```

Server runs on: `http://localhost:3001`

## API Endpoints

### Foundry Agent Integration

- `POST /api/foundry/thread` - Create conversation thread
- `POST /api/foundry/run` - Run agent with message
- `GET /api/foundry/history?thread_id=...` - Get conversation history
- `GET /api/foundry/health` - Health check

### Chat (Azure OpenAI fallback)

- `POST /api/chat` - Send chat message

### Patients

- `GET /api/patients?search=...&gender=...&limit=...` - Search patients

### Health

- `GET /` - API status
- `GET /health` - Database health check

## Key Features

✅ Azure AI Foundry v2 Agents API integration (using Python SDK)  
✅ Async/await streaming for agent responses  
✅ Azure OpenAI fallback for chat  
✅ PostgreSQL database connectivity  
✅ CORS enabled for frontend  
✅ Production-ready error handling  
✅ Structured logging  

## Database

Uses PostgreSQL. Connection string from `DATABASE_URL` env var.

This backend is intentionally streamlined around a single denormalized table:
- `patients` (single source of truth)
- `patient_summary` view (list/search/analytics/charts)

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
- `AZURE_OPENAI_ENDPOINT` - Azure OpenAI endpoint
- `AZURE_OPENAI_API_KEY` - Azure OpenAI API key
- `AZURE_EXISTING_AIPROJECT_ENDPOINT` - Azure AI Foundry project endpoint
- `AZURE_EXISTING_AGENT_ID` - Agent ID (blnk:8)

## Troubleshooting

### "Azure Foundry endpoint not configured"

Check that `AZURE_EXISTING_AIPROJECT_ENDPOINT` is set in `.env`:

```bash
echo $AZURE_EXISTING_AIPROJECT_ENDPOINT
# Should output: https://omar-ahmed-abdelhamiid-resource.services.ai.azure.com/api/projects/abdelhamiid-1153
```

### "Azure OpenAI is not configured"

Check that both are set:

```bash
echo $AZURE_OPENAI_ENDPOINT
echo $AZURE_OPENAI_API_KEY
```

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
2. ✅ Updated: Azure Foundry endpoints use correct SDK
3. ✅ Verified: All endpoints maintain same API contract

To remove the old backend:

```bash
# Keep for reference, or:
rm -rf ../backend
```

## Development Tips

- Logging to stdout (check terminal for debug info)
- Hot reload enabled (`--reload` flag)
- Database debug via raw SQL in routes
- Use `az login` for Azure credential fallback
