# BioLink Agent Integration

Connect your existing Microsoft Foundry (Azure AI) agent with BioLink API tools.

## Setup

1. **Install dependencies** (--pre flag is required):
```bash
cd agent
pip install agent-framework-azure-ai --pre httpx azure-identity
```

Or use requirements file:
```bash
pip install -r requirements.txt
```

2. **Configure your agent details** in `biolink_agent.py`:
```python
PROJECT_ENDPOINT = "https://omar-ahmed-abdelhamiid-resource.cognitiveservices.azure.com/openai/deployments/gpt-5-nano/chat/completions?api-version=2025-01-01-preview"
MODEL_DEPLOYMENT = "gpt-5-nano"  # Your model deployment name
AGENT_NAME = "BioLinkAgent"  # Your agent name
```

3. **Find your configuration**:
   - Open Microsoft Foundry portal (ai.azure.com)
   - Go to your project
   - Copy the Project Endpoint from project settings
   - Copy your Model Deployment name from the Deployments section
   - Note your Agent name if you already created one

4. **Ensure BioLink is running**:
```bash
# From the main Code directory
./start-all.sh
```

5. **Run the agent**:
```bash
cd agent
python biolink_agent.py
```

## Available Tools

The agent has access to these BioLink functions:

### 1. `search_patients`
Search and filter patients by demographics
- Parameters: search, gender, age_min, age_max, limit

### 2. `get_patient_details`
Get complete clinical data for a specific patient
- Parameters: dna_id

### 3. `build_cohort`
Build patient cohorts with clinical criteria
- Parameters: age_min, age_max, gender, has_diabetes, has_hypertension, has_echo, has_mri, limit

### 4. `get_registry_statistics`
Get comprehensive registry analytics
- No parameters

## Example Queries

```
You: Find me 5 patients with diabetes over age 60

You: Get details for patient EHV001

You: Build a cohort of hypertensive females with MRI data

You: Show me registry statistics

You: Find all patients from Egypt with heart conditions
```

## Authentication

The script uses `DefaultAzureCredential` which tries multiple authentication methods:
1. Environment variables
2. Managed Identity
3. Azure CLI (`az login`)
4. Visual Studio Code
5. Azure PowerShell

Make sure you're logged in via one of these methods:
```bash
az login
```

## Troubleshooting

**Connection Error**: Make sure BioLink backend is running on http://localhost:3001
```bash
curl http://localhost:3001/health
```

**Authentication Error**: Login to Azure CLI
```bash
az login
```

**Agent Not Found**: The agent will be created automatically if it doesn't exist with the specified name

**Module Not Found**: Install with --pre flag
```bash
pip install agent-framework-azure-ai --pre
```
