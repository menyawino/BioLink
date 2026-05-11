# Azure Preview Deployment

This folder contains the first-pass Azure preview deployment scaffold for BioLink.

Current scope:
- Deploy the FastAPI backend to Azure Container Apps.
- Deploy the main frontend to Azure Container Apps.
- Deploy Superset to Azure Container Apps for the embedded Chart Builder workspace.
- Provision Azure Database for PostgreSQL Flexible Server for the main app database and the vector database.
- Lock preview access to specific Microsoft Entra identities and disable the old local signup path.

Not included in this first pass:
- NiFi
- Ollama

This preview is still locked down at the network edge:
- Container Apps ingress is restricted to `PREVIEW_ALLOWED_CIDR`

## Why the cloud backend image is separate

The normal backend image in [backend-py/Dockerfile](/Users/menyawino/Playground/BioLink/Code/backend-py/Dockerfile) expects local bind mounts for `db/` and `outputs/`.
The preview deploy uses [docker/Dockerfile.backend.cloud](/Users/menyawino/Playground/BioLink/Code/docker/Dockerfile.backend.cloud) so those seed artifacts are packaged into the image for the first Azure preview.

## Before you run it

1. Install Azure CLI.
2. Sign in with `az login --use-device-code`.
3. Copy `deploy/azure/preview.env.example` to `deploy/azure/preview.env`.
4. Fill in at minimum:

```env
AZURE_SUBSCRIPTION_ID=<your-subscription-id>
AZURE_ACR_NAME=<globally-unique-acr-name>
PREVIEW_ALLOWED_CIDR=<your-public-ip>/32
AZURE_POSTGRES_LOCATION=<optional-separate-postgres-region>
AZURE_POSTGRES_ADMIN_PASSWORD=<strong-db-password>
APP_SECRET_KEY=<strong-random-secret>
BOOTSTRAP_ADMIN_USERNAME=<your-username>
BOOTSTRAP_ADMIN_EMAIL=<your-email>
BOOTSTRAP_ADMIN_FULL_NAME=<your-name>
AZURE_ENTRA_TENANT_ID=<your-tenant-id>
AZURE_ENTRA_BACKEND_CLIENT_ID=<backend-api-app-registration-client-id>
AZURE_ENTRA_FRONTEND_CLIENT_ID=<spa-app-registration-client-id>
AZURE_ENTRA_API_SCOPE=api://<backend-api-app-registration-client-id>/access_as_user
AZURE_ENTRA_ALLOWED_EMAILS=<comma-separated-preview-emails>
AZURE_ENTRA_ADMIN_EMAILS=<comma-separated-admin-emails>
SUPERSET_ADMIN_PASSWORD=<optional-direct-login-password>
```

## Run the preview deploy

```bash
chmod +x deploy/azure/deploy-preview.sh
./deploy/azure/deploy-preview.sh ./deploy/azure/preview.env
```

## Access control in this first pass

This preview is locked down by application auth:
- Azure Entra is the only supported sign-in path
- no self-registration
- only emails listed in `AZURE_ENTRA_ALLOWED_EMAILS` can sign in
- emails listed in `AZURE_ENTRA_ADMIN_EMAILS` are elevated to BioLink admin on first sign-in

This preview is also locked down at the network edge:
- Container Apps ingress is restricted to `PREVIEW_ALLOWED_CIDR`

The bootstrap admin fields remain in the env file so BioLink can seed a matching admin profile, but the deployed preview no longer exposes the temporary local username/password login.

Superset is still a separate service in this preview. The embedded dashboard uses backend-issued guest tokens, while direct access to the full Superset UI uses the `SUPERSET_ADMIN_*` credentials from the preview env file.