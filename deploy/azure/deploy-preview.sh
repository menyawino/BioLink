#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ENV_FILE="${1:-$SCRIPT_DIR/preview.env}"
REGISTRY_SNAPSHOT_PATH="$REPO_ROOT/outputs/unified_registry.csv"
STANDARDIZED_SCHEMA_PATH="$REPO_ROOT/db/schema_standardized.sql"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Expected env file at $ENV_FILE"
  echo "Copy deploy/azure/preview.env.example to deploy/azure/preview.env and fill it in first."
  exit 1
fi

set -a
source "$ENV_FILE"
set +a

if [[ ! -f "$STANDARDIZED_SCHEMA_PATH" ]]; then
  echo "Missing required schema file: $STANDARDIZED_SCHEMA_PATH"
  echo "The backend image needs db/schema_standardized.sql so participant tables can be created."
  exit 1
fi

if [[ ! -f "$REGISTRY_SNAPSHOT_PATH" ]]; then
  echo "Missing required registry snapshot: $REGISTRY_SNAPSHOT_PATH"
  echo "Generate it before deployment, for example:"
  echo "  python3 db/test/run_pipeline.py"
  exit 1
fi

require_var() {
  local var_name="$1"
  if [[ -z "${!var_name:-}" ]]; then
    echo "Missing required variable: $var_name"
    exit 1
  fi
}

require_var AZURE_LOCATION
require_var AZURE_RESOURCE_GROUP
require_var AZURE_CONTAINERAPPS_ENV
require_var AZURE_ACR_NAME
require_var BACKEND_APP_NAME
require_var FRONTEND_APP_NAME
require_var PREVIEW_ALLOWED_CIDR
require_var AZURE_POSTGRES_SERVER
require_var AZURE_POSTGRES_ADMIN
require_var AZURE_POSTGRES_ADMIN_PASSWORD
require_var AZURE_POSTGRES_DATABASE
require_var AZURE_POSTGRES_VECTOR_DATABASE
require_var APP_SECRET_KEY
require_var BOOTSTRAP_ADMIN_USERNAME
require_var BOOTSTRAP_ADMIN_EMAIL
require_var BOOTSTRAP_ADMIN_FULL_NAME
require_var AZURE_ENTRA_TENANT_ID
require_var AZURE_ENTRA_BACKEND_CLIENT_ID
require_var AZURE_ENTRA_FRONTEND_CLIENT_ID
require_var AZURE_ENTRA_API_SCOPE

POSTGRES_LOCATION="${AZURE_POSTGRES_LOCATION:-$AZURE_LOCATION}"
AZURE_ENTRA_AUTHORITY="${AZURE_ENTRA_AUTHORITY:-https://login.microsoftonline.com/${AZURE_ENTRA_TENANT_ID}}"
AZURE_ENTRA_AUDIENCE="${AZURE_ENTRA_AUDIENCE:-api://${AZURE_ENTRA_BACKEND_CLIENT_ID}}"
AZURE_ENTRA_ALLOWED_EMAILS="${AZURE_ENTRA_ALLOWED_EMAILS:-$BOOTSTRAP_ADMIN_EMAIL}"
AZURE_ENTRA_ADMIN_EMAILS="${AZURE_ENTRA_ADMIN_EMAILS:-$BOOTSTRAP_ADMIN_EMAIL}"
SUPERSET_APP_NAME="${SUPERSET_APP_NAME:-biolink-preview-superset}"
SUPERSET_SECRET_KEY="${SUPERSET_SECRET_KEY:-$APP_SECRET_KEY}"
SUPERSET_ADMIN_USER="${SUPERSET_ADMIN_USER:-${BOOTSTRAP_ADMIN_USERNAME:-admin}}"
SUPERSET_ADMIN_PASSWORD="${SUPERSET_ADMIN_PASSWORD:-${BOOTSTRAP_ADMIN_PASSWORD:-$APP_SECRET_KEY}}"
SUPERSET_ADMIN_EMAIL="${SUPERSET_ADMIN_EMAIL:-$BOOTSTRAP_ADMIN_EMAIL}"
SUPERSET_ADMIN_FIRSTNAME="${SUPERSET_ADMIN_FIRSTNAME:-Bio}"
SUPERSET_ADMIN_LASTNAME="${SUPERSET_ADMIN_LASTNAME:-Link}"
SUPERSET_DATABASE_NAME="${SUPERSET_DATABASE_NAME:-BioLink PostgreSQL}"
SUPERSET_DATABASE_SCHEMA="${SUPERSET_DATABASE_SCHEMA:-public}"
SUPERSET_METADATA_SCHEMA="${SUPERSET_METADATA_SCHEMA:-superset_meta}"
SUPERSET_RATELIMIT_STORAGE_URI="${SUPERSET_RATELIMIT_STORAGE_URI:-memory://}"
SUPERSET_VERIFICATION_DASHBOARD_TITLE="${SUPERSET_VERIFICATION_DASHBOARD_TITLE:-BioLink Verification Dashboard}"
SUPERSET_VERIFICATION_DASHBOARD_SLUG="${SUPERSET_VERIFICATION_DASHBOARD_SLUG:-biolink-verification-dashboard}"

if ! command -v az >/dev/null 2>&1; then
  echo "Azure CLI is not installed. Install it first, then rerun this script."
  exit 1
fi

az account show >/dev/null 2>&1 || {
  echo "Azure CLI is not signed in. Run: az login --use-device-code"
  exit 1
}

if [[ -n "${AZURE_SUBSCRIPTION_ID:-}" ]]; then
  az account set --subscription "$AZURE_SUBSCRIPTION_ID"
fi

IMAGE_TAG="${IMAGE_TAG:-preview}"

echo "Creating resource group and registry..."
az group create \
  --name "$AZURE_RESOURCE_GROUP" \
  --location "$AZURE_LOCATION" \
  --output none

if ! az acr show --resource-group "$AZURE_RESOURCE_GROUP" --name "$AZURE_ACR_NAME" >/dev/null 2>&1; then
  az acr create \
    --resource-group "$AZURE_RESOURCE_GROUP" \
    --name "$AZURE_ACR_NAME" \
    --sku Basic \
    --admin-enabled true \
    --output none
fi

ACR_LOGIN_SERVER="$(az acr show --resource-group "$AZURE_RESOURCE_GROUP" --name "$AZURE_ACR_NAME" --query loginServer -o tsv)"
ACR_USERNAME="$(az acr credential show --name "$AZURE_ACR_NAME" --query username -o tsv)"
ACR_PASSWORD="$(az acr credential show --name "$AZURE_ACR_NAME" --query passwords[0].value -o tsv)"

echo "Creating Container Apps environment..."
if ! az containerapp env show --resource-group "$AZURE_RESOURCE_GROUP" --name "$AZURE_CONTAINERAPPS_ENV" >/dev/null 2>&1; then
  az containerapp env create \
    --resource-group "$AZURE_RESOURCE_GROUP" \
    --name "$AZURE_CONTAINERAPPS_ENV" \
    --location "$AZURE_LOCATION" \
    --output none
fi

ACA_DEFAULT_DOMAIN="$(az containerapp env show --resource-group "$AZURE_RESOURCE_GROUP" --name "$AZURE_CONTAINERAPPS_ENV" --query properties.defaultDomain -o tsv)"

BACKEND_URL="https://${BACKEND_APP_NAME}.${ACA_DEFAULT_DOMAIN}"
FRONTEND_URL="https://${FRONTEND_APP_NAME}.${ACA_DEFAULT_DOMAIN}"
SUPERSET_URL="https://${SUPERSET_APP_NAME}.${ACA_DEFAULT_DOMAIN}"
SUPERSET_EMBEDDED_ALLOWED_DOMAINS="${SUPERSET_EMBEDDED_ALLOWED_DOMAINS:-$FRONTEND_URL}"

echo "Creating PostgreSQL server and databases..."
if ! az postgres flexible-server show --resource-group "$AZURE_RESOURCE_GROUP" --name "$AZURE_POSTGRES_SERVER" >/dev/null 2>&1; then
  az postgres flexible-server create \
    --resource-group "$AZURE_RESOURCE_GROUP" \
    --name "$AZURE_POSTGRES_SERVER" \
    --location "$POSTGRES_LOCATION" \
    --admin-user "$AZURE_POSTGRES_ADMIN" \
    --admin-password "$AZURE_POSTGRES_ADMIN_PASSWORD" \
    --sku-name Standard_B1ms \
    --tier Burstable \
    --version 16 \
    --storage-size 32 \
    --yes \
    --output none
fi

az postgres flexible-server firewall-rule create \
  --resource-group "$AZURE_RESOURCE_GROUP" \
  --name "$AZURE_POSTGRES_SERVER" \
  --rule-name allow-azure-services \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0 \
  --output none

az postgres flexible-server db create \
  --resource-group "$AZURE_RESOURCE_GROUP" \
  --server-name "$AZURE_POSTGRES_SERVER" \
  --database-name "$AZURE_POSTGRES_DATABASE" \
  --output none

az postgres flexible-server db create \
  --resource-group "$AZURE_RESOURCE_GROUP" \
  --server-name "$AZURE_POSTGRES_SERVER" \
  --database-name "$AZURE_POSTGRES_VECTOR_DATABASE" \
  --output none

POSTGRES_HOST="$(az postgres flexible-server show --resource-group "$AZURE_RESOURCE_GROUP" --name "$AZURE_POSTGRES_SERVER" --query fullyQualifiedDomainName -o tsv)"
PG_USERNAME_FULL="${AZURE_POSTGRES_ADMIN}"
DATABASE_URL="postgresql+psycopg2://${PG_USERNAME_FULL}:${AZURE_POSTGRES_ADMIN_PASSWORD}@${POSTGRES_HOST}:5432/${AZURE_POSTGRES_DATABASE}?sslmode=require"
RAG_PG_URL="postgresql://${PG_USERNAME_FULL}:${AZURE_POSTGRES_ADMIN_PASSWORD}@${POSTGRES_HOST}:5432/${AZURE_POSTGRES_VECTOR_DATABASE}?sslmode=require"
SUPERSET_METADATA_DATABASE_URI="${SUPERSET_METADATA_DATABASE_URI:-$DATABASE_URL}"

echo "Building Superset image in ACR..."
az acr build \
  --registry "$AZURE_ACR_NAME" \
  --image "biolink-superset:${IMAGE_TAG}" \
  --file docker/Dockerfile.superset \
  "$REPO_ROOT"

echo "Deploying Superset preview app..."
az containerapp create \
  --resource-group "$AZURE_RESOURCE_GROUP" \
  --name "$SUPERSET_APP_NAME" \
  --environment "$AZURE_CONTAINERAPPS_ENV" \
  --image "${ACR_LOGIN_SERVER}/biolink-superset:${IMAGE_TAG}" \
  --registry-server "$ACR_LOGIN_SERVER" \
  --registry-username "$ACR_USERNAME" \
  --registry-password "$ACR_PASSWORD" \
  --ingress external \
  --target-port 8088 \
  --min-replicas 1 \
  --max-replicas 1 \
  --cpu 1.0 \
  --memory 2.0Gi \
  --secrets \
    superset-secret-key="$SUPERSET_SECRET_KEY" \
    superset-admin-password="$SUPERSET_ADMIN_PASSWORD" \
  --env-vars \
    SUPERSET_CONFIG_PATH=/app/superset_config.py \
    SUPERSET_SECRET_KEY=secretref:superset-secret-key \
    SUPERSET_ADMIN_USER="$SUPERSET_ADMIN_USER" \
    SUPERSET_ADMIN_PASSWORD=secretref:superset-admin-password \
    SUPERSET_ADMIN_EMAIL="$SUPERSET_ADMIN_EMAIL" \
    SUPERSET_ADMIN_FIRSTNAME="$SUPERSET_ADMIN_FIRSTNAME" \
    SUPERSET_ADMIN_LASTNAME="$SUPERSET_ADMIN_LASTNAME" \
    BIOLINK_PG_HOST="$POSTGRES_HOST" \
    BIOLINK_PG_PORT=5432 \
    BIOLINK_PG_DB="$AZURE_POSTGRES_DATABASE" \
    BIOLINK_PG_USER="$PG_USERNAME_FULL" \
    BIOLINK_PG_PASSWORD="$AZURE_POSTGRES_ADMIN_PASSWORD" \
    CORS_ALLOWED_ORIGINS="$FRONTEND_URL" \
    SUPERSET_EMBEDDED_ALLOWED_DOMAINS="$SUPERSET_EMBEDDED_ALLOWED_DOMAINS" \
    SUPERSET_METADATA_DATABASE_URI="$SUPERSET_METADATA_DATABASE_URI" \
    SUPERSET_METADATA_SCHEMA="$SUPERSET_METADATA_SCHEMA" \
    SUPERSET_RATELIMIT_STORAGE_URI="$SUPERSET_RATELIMIT_STORAGE_URI" \
    SUPERSET_DATABASE_NAME="$SUPERSET_DATABASE_NAME" \
    SUPERSET_DATABASE_SCHEMA="$SUPERSET_DATABASE_SCHEMA" \
    SUPERSET_VERIFICATION_DASHBOARD_TITLE="$SUPERSET_VERIFICATION_DASHBOARD_TITLE" \
    SUPERSET_VERIFICATION_DASHBOARD_SLUG="$SUPERSET_VERIFICATION_DASHBOARD_SLUG"

az containerapp ingress access-restriction set \
  --resource-group "$AZURE_RESOURCE_GROUP" \
  --name "$SUPERSET_APP_NAME" \
  --rule-name allow-preview-ip \
  --description "Restrict preview access to the current operator IP." \
  --ip-address "$PREVIEW_ALLOWED_CIDR" \
  --action Allow \
  --output none

echo "Building backend image in ACR..."
az acr build \
  --registry "$AZURE_ACR_NAME" \
  --image "biolink-backend:${IMAGE_TAG}" \
  --file docker/Dockerfile.backend.cloud \
  "$REPO_ROOT"

echo "Deploying backend preview app..."
az containerapp create \
  --resource-group "$AZURE_RESOURCE_GROUP" \
  --name "$BACKEND_APP_NAME" \
  --environment "$AZURE_CONTAINERAPPS_ENV" \
  --image "${ACR_LOGIN_SERVER}/biolink-backend:${IMAGE_TAG}" \
  --registry-server "$ACR_LOGIN_SERVER" \
  --registry-username "$ACR_USERNAME" \
  --registry-password "$ACR_PASSWORD" \
  --ingress external \
  --target-port 3001 \
  --min-replicas 1 \
  --max-replicas 1 \
  --cpu 1.0 \
  --memory 2.0Gi \
  --secrets \
    app-secret-key="$APP_SECRET_KEY" \
    superset-admin-password="$SUPERSET_ADMIN_PASSWORD" \
  --env-vars \
    ENVIRONMENT=production \
    SECRET_KEY=secretref:app-secret-key \
    DATABASE_URL="$DATABASE_URL" \
    RAG_PG_URL="$RAG_PG_URL" \
    RATE_LIMIT_STORAGE_URL="${RATE_LIMIT_STORAGE_URL:-memory://}" \
    CORS_ALLOWED_ORIGINS="$FRONTEND_URL" \
    SUPERSET_URL="$SUPERSET_URL" \
    SUPERSET_PUBLIC_URL="$SUPERSET_URL" \
    SUPERSET_ADMIN_USER="$SUPERSET_ADMIN_USER" \
    SUPERSET_ADMIN_PASSWORD=secretref:superset-admin-password \
    SUPERSET_ADMIN_EMAIL="$SUPERSET_ADMIN_EMAIL" \
    SUPERSET_DATABASE_NAME="$SUPERSET_DATABASE_NAME" \
    SUPERSET_DATABASE_URI="$DATABASE_URL" \
    SUPERSET_DEFAULT_DASHBOARD_REF="$SUPERSET_VERIFICATION_DASHBOARD_SLUG" \
    SUPERSET_EMBEDDED_ALLOWED_DOMAINS="$SUPERSET_EMBEDDED_ALLOWED_DOMAINS" \
    BOOTSTRAP_ADMIN_USERNAME="$BOOTSTRAP_ADMIN_USERNAME" \
    BOOTSTRAP_ADMIN_EMAIL="$BOOTSTRAP_ADMIN_EMAIL" \
    BOOTSTRAP_ADMIN_FULL_NAME="$BOOTSTRAP_ADMIN_FULL_NAME" \
    AZURE_ENTRA_ENABLED=true \
    AZURE_ENTRA_TENANT_ID="$AZURE_ENTRA_TENANT_ID" \
    AZURE_ENTRA_CLIENT_ID="$AZURE_ENTRA_BACKEND_CLIENT_ID" \
    AZURE_ENTRA_AUDIENCE="$AZURE_ENTRA_AUDIENCE" \
    AZURE_ENTRA_ALLOWED_EMAILS="$AZURE_ENTRA_ALLOWED_EMAILS" \
    AZURE_ENTRA_ADMIN_EMAILS="$AZURE_ENTRA_ADMIN_EMAILS" \
    ALLOW_SELF_REGISTRATION="${ALLOW_SELF_REGISTRATION:-false}" \
    BOOTSTRAP_DEMO_USERS="${BOOTSTRAP_DEMO_USERS:-false}"

az containerapp ingress access-restriction set \
  --resource-group "$AZURE_RESOURCE_GROUP" \
  --name "$BACKEND_APP_NAME" \
  --rule-name allow-preview-ip \
  --description "Restrict preview access to the current operator IP." \
  --ip-address "$PREVIEW_ALLOWED_CIDR" \
  --action Allow \
  --output none

echo "Building frontend image in ACR..."
az acr build \
  --registry "$AZURE_ACR_NAME" \
  --image "biolink-frontend:${IMAGE_TAG}" \
  --file docker/Dockerfile.frontend \
  --build-arg VITE_BACKEND_URL="$BACKEND_URL" \
  --build-arg VITE_SQL_AGENT_ENABLED=true \
  --build-arg VITE_SUPERSET_URL="${VITE_SUPERSET_URL:-$SUPERSET_URL}" \
  --build-arg VITE_SUPERSET_DASHBOARD_ID="${VITE_SUPERSET_DASHBOARD_ID:-$SUPERSET_VERIFICATION_DASHBOARD_SLUG}" \
  --build-arg VITE_NIFI_URL="${VITE_NIFI_URL:-}" \
  --build-arg VITE_AZURE_ENTRA_ENABLED=true \
  --build-arg VITE_AZURE_ENTRA_CLIENT_ID="$AZURE_ENTRA_FRONTEND_CLIENT_ID" \
  --build-arg VITE_AZURE_ENTRA_TENANT_ID="$AZURE_ENTRA_TENANT_ID" \
  --build-arg VITE_AZURE_ENTRA_AUTHORITY="$AZURE_ENTRA_AUTHORITY" \
  --build-arg VITE_AZURE_ENTRA_API_SCOPE="$AZURE_ENTRA_API_SCOPE" \
  --build-arg VITE_OLLAMA_BASE_URL="${VITE_OLLAMA_BASE_URL:-}" \
  "$REPO_ROOT"

echo "Deploying frontend preview app..."
az containerapp create \
  --resource-group "$AZURE_RESOURCE_GROUP" \
  --name "$FRONTEND_APP_NAME" \
  --environment "$AZURE_CONTAINERAPPS_ENV" \
  --image "${ACR_LOGIN_SERVER}/biolink-frontend:${IMAGE_TAG}" \
  --registry-server "$ACR_LOGIN_SERVER" \
  --registry-username "$ACR_USERNAME" \
  --registry-password "$ACR_PASSWORD" \
  --ingress external \
  --target-port 80 \
  --min-replicas 1 \
  --max-replicas 1 \
  --cpu 0.5 \
  --memory 1.0Gi

az containerapp ingress access-restriction set \
  --resource-group "$AZURE_RESOURCE_GROUP" \
  --name "$FRONTEND_APP_NAME" \
  --rule-name allow-preview-ip \
  --description "Restrict preview access to the current operator IP." \
  --ip-address "$PREVIEW_ALLOWED_CIDR" \
  --action Allow \
  --output none

echo
echo "Preview deployment complete."
echo "Backend:      $BACKEND_URL"
echo "Frontend:     $FRONTEND_URL"
echo "Superset:     $SUPERSET_URL"