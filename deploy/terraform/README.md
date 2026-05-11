# BioLink Azure Infrastructure (Terraform)

Production-grade Infrastructure as Code (IaC) for deploying BioLink on Azure using Terraform.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Azure Cloud                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Frontend  │  │   Backend   │  │     Superset        │  │
│  │  Container  │  │  Container  │  │    Container        │  │
│  │    App      │  │    App      │  │      App            │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
│         │                │                     │             │
│  ┌──────┴────────────────┴─────────────────────┴──────────┐  │
│  │              Container Apps Environment                  │  │
│  │                   (VNet integrated)                      │  │
│  └────────────────────────┬────────────────────────────────┘  │
│                           │                                  │
│  ┌────────────────────────┴────────────────────────────────┐  │
│  │              Azure PostgreSQL Flexible Server             │  │
│  │         (biolink + biolink_vector databases)            │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              Azure Key Vault (secrets)                  │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │     Log Analytics + Application Insights + Alerts       │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
deploy/terraform/
├── modules/
│   ├── container_apps/     # Container Apps for backend, frontend, Superset
│   ├── postgres/           # Azure PostgreSQL Flexible Server
│   ├── monitoring/         # Log Analytics, App Insights, Alerts
│   ├── keyvault/           # Azure Key Vault with RBAC
│   └── network/            # VNet, subnets, NSGs
├── environments/
│   ├── staging/            # Staging environment config
│   └── production/         # Production environment config
└── README.md
```

## Prerequisites

1. **Azure CLI** installed and authenticated
2. **Terraform** >= 1.5.0
3. **Docker** for building images
4. Azure subscription with sufficient quota

## Setup

### 1. Create Terraform Backend Storage

```bash
# Run once to create the state storage account
az group create --name biolink-terraform-state --location westeurope

az storage account create \
  --name biolinktfstate \
  --resource-group biolink-terraform-state \
  --location westeurope \
  --sku Standard_LRS \
  --allow-blob-public-access false

az storage container create \
  --name tfstate \
  --account-name biolinktfstate
```

### 2. Configure Variables

Create a `terraform.tfvars` file in the environment directory:

```hcl
# deploy/terraform/environments/staging/terraform.tfvars
location = "westeurope"

# Images (will be overridden by CI/CD)
backend_image  = "biolinkacr.azurecr.io/biolink-backend:latest"
frontend_image = "biolinkacr.azurecr.io/biolink-frontend:latest"
superset_image = "biolinkacr.azurecr.io/biolink-superset:latest"

# PostgreSQL
postgres_admin_password = "your-secure-password"
allowed_cidrs = ["YOUR_IP/32"]

# Azure Entra
azure_entra_tenant_id         = "your-tenant-id"
azure_entra_backend_client_id = "your-backend-client-id"
azure_entra_frontend_client_id = "your-frontend-client-id"
azure_entra_audience          = "api://your-backend-client-id"
azure_entra_authority         = "https://login.microsoftonline.com/your-tenant-id"
azure_entra_api_scope         = "api://your-backend-client-id/access_as_user"

# Monitoring
alert_email_addresses = ["admin@example.com"]
```

### 3. Deploy

```bash
cd deploy/terraform/environments/staging

terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

## CI/CD Integration

The GitHub Actions workflow `.github/workflows/azure-deploy.yml`:

1. Builds Docker images on every push to `main`
2. Pushes images to Azure Container Registry
3. Runs `terraform apply` to update infrastructure
4. Performs smoke tests
5. Automatically rolls back on failure

### Required GitHub Secrets

| Secret | Description |
|--------|-------------|
| `AZURE_CREDENTIALS` | Azure service principal JSON |
| `AZURE_SUBSCRIPTION_ID` | Azure subscription ID |
| `AZURE_RESOURCE_GROUP` | Target resource group |
| `AZURE_ACR_NAME` | Azure Container Registry name |
| `APP_SECRET_KEY` | Application secret key |
| `SUPERSET_SECRET_KEY` | Superset secret key |
| `SUPERSET_ADMIN_PASSWORD` | Superset admin password |
| `SUPERSET_ADMIN_EMAIL` | Superset admin email |
| `AZURE_POSTGRES_ADMIN_PASSWORD` | PostgreSQL admin password |
| `AZURE_ENTRA_TENANT_ID` | Azure Entra tenant ID |
| `AZURE_ENTRA_BACKEND_CLIENT_ID` | Backend app registration ID |
| `AZURE_ENTRA_FRONTEND_CLIENT_ID` | Frontend app registration ID |
| `AZURE_ENTRA_AUDIENCE` | Token audience |
| `AZURE_ENTRA_AUTHORITY` | Authority URL |
| `AZURE_ENTRA_API_SCOPE` | API scope |
| `ALERT_EMAIL_ADDRESSES` | Comma-separated alert emails |
| `ALLOWED_CIDRS` | Comma-separated allowed CIDRs |

## Environments

### Staging
- Smaller SKUs (B1ms for DB, 0.5 CPU for apps)
- Single replica minimums
- 7-day backup retention
- No geo-redundancy
- Network ACLs allow broader access

### Production
- Larger SKUs (D2s_v3 for DB, 1.0 CPU for apps)
- Multi-replica minimums (2+)
- 30-day backup retention
- Geo-redundant backups enabled
- Strict network ACLs
- Higher monitoring thresholds

## Security Features

- **Managed Identities**: Container apps use system-assigned managed identities
- **Key Vault RBAC**: Secrets stored in Key Vault with role-based access
- **VNet Integration**: Container Apps and PostgreSQL in private VNet
- **NSGs**: Network security groups restrict traffic between subnets
- **SSL Enforcement**: PostgreSQL requires secure transport
- **Private Endpoints**: Ready for private endpoint configuration

## Monitoring

- **Log Analytics**: Centralized logging for all services
- **Application Insights**: Distributed tracing for backend and frontend
- **Metric Alerts**: CPU, memory, and database connection alerts
- **Action Groups**: Email notifications for critical alerts

## Cost Optimization

- Staging uses Burstable SKUs to minimize costs
- Production uses General Purpose SKUs for consistent performance
- Container Apps scale to zero when not in use (staging)
- Log Analytics retention configurable per environment
