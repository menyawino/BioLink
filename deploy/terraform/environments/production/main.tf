# BioLink Production Environment
# Terraform configuration for production deployment on Azure

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.100"
    }
  }

  backend "azurerm" {
    resource_group_name  = "biolink-terraform-state"
    storage_account_name = "biolinktfstate"
    container_name       = "tfstate"
    key                  = "production.terraform.tfstate"
  }
}

provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = true
    }
  }
}

locals {
  environment = "production"
  tags = {
    Environment = local.environment
    Project     = "BioLink"
    ManagedBy   = "Terraform"
    CostCenter  = "Research-IT"
  }
}

# Resource Group
resource "azurerm_resource_group" "main" {
  name     = "biolink-${local.environment}"
  location = var.location
  tags     = local.tags
}

# Network
module "network" {
  source = "../../modules/network"

  vnet_name                       = "biolink-${local.environment}-vnet"
  resource_group_name             = azurerm_resource_group.main.name
  location                        = var.location
  address_space                   = ["10.0.0.0/16"]
  container_apps_subnet_prefix    = "10.0.1.0/24"
  database_subnet_prefix          = "10.0.2.0/24"
  private_endpoints_subnet_prefix = "10.0.3.0/24"
  tags                            = local.tags
}

# PostgreSQL
module "postgres" {
  source = "../../modules/postgres"

  server_name                  = "biolink-${local.environment}-postgres"
  resource_group_name          = azurerm_resource_group.main.name
  location                     = var.location
  sku_name                     = "GP_Standard_D2s_v3"
  storage_mb                   = 65536
  backup_retention_days        = 30
  geo_redundant_backup_enabled = true
  admin_username               = var.postgres_admin_username
  admin_password               = var.postgres_admin_password
  allowed_cidrs                = var.allowed_cidrs
  tags                         = local.tags
}

# Container Apps
module "container_apps" {
  source = "../../modules/container_apps"

  environment_name         = "biolink-${local.environment}"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = var.location
  log_analytics_workspace_id = module.monitoring.log_analytics_workspace_id

  # Backend
  backend_app_name     = "biolink-${local.environment}-backend"
  backend_image        = var.backend_image
  backend_cpu          = 1.0
  backend_memory       = "2.0Gi"
  backend_min_replicas = 2
  backend_max_replicas = 10

  # Frontend
  frontend_app_name     = "biolink-${local.environment}-frontend"
  frontend_image        = var.frontend_image
  frontend_cpu          = 0.5
  frontend_memory       = "1.0Gi"
  frontend_min_replicas = 2
  frontend_max_replicas = 5

  # Superset
  superset_app_name     = "biolink-${local.environment}-superset"
  superset_image        = var.superset_image
  superset_cpu          = 1.0
  superset_memory       = "2.0Gi"
  superset_min_replicas = 1
  superset_max_replicas = 3

  # Stakeholder site
  deploy_stakeholder_site = true
  stakeholder_app_name    = "biolink-${local.environment}-stakeholders"
  stakeholder_image       = var.stakeholder_image

  # Secrets
  database_url                  = module.postgres.connection_string
  rag_pg_url                    = module.postgres.vector_connection_string
  app_secret_key                = var.app_secret_key
  superset_secret_key           = var.superset_secret_key
  superset_admin_password       = var.superset_admin_password
  superset_admin_user           = var.superset_admin_user
  superset_admin_email          = var.superset_admin_email
  superset_metadata_database_uri = module.postgres.connection_string
  superset_url                  = "https://biolink-${local.environment}-superset.${var.container_apps_domain}"
  superset_embedded_allowed_domains = "https://biolink-${local.environment}-frontend.${var.container_apps_domain}"

  # Azure Entra
  azure_entra_tenant_id         = var.azure_entra_tenant_id
  azure_entra_backend_client_id = var.azure_entra_backend_client_id
  azure_entra_frontend_client_id = var.azure_entra_frontend_client_id
  azure_entra_audience          = var.azure_entra_audience
  azure_entra_authority         = var.azure_entra_authority
  azure_entra_api_scope         = var.azure_entra_api_scope

  # Other
  redis_url   = var.redis_url
  ollama_url  = var.ollama_url
  log_level   = "INFO"

  tags = local.tags
}

# Monitoring
module "monitoring" {
  source = "../../modules/monitoring"

  workspace_name           = "biolink-${local.environment}-logs"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = var.location
  retention_days           = 90
  alert_email_addresses    = var.alert_email_addresses
  backend_container_app_id = module.container_apps.backend_fqdn
  postgres_server_id       = module.postgres.server_id
  cpu_threshold            = 75
  memory_threshold         = 80
  db_connection_threshold  = 100
  tags                     = local.tags
}

# Key Vault
module "keyvault" {
  source = "../../modules/keyvault"

  vault_name              = "biolink-${local.environment}-kv"
  resource_group_name     = azurerm_resource_group.main.name
  location                = var.location
  tenant_id               = var.azure_entra_tenant_id
  sku_name                = "standard"
  network_acls_default_action = "Deny"
  allowed_ip_ranges       = var.allowed_cidrs

  database_url            = module.postgres.connection_string
  rag_pg_url              = module.postgres.vector_connection_string
  app_secret_key          = var.app_secret_key
  superset_secret_key     = var.superset_secret_key
  superset_admin_password = var.superset_admin_password
  postgres_admin_password = var.postgres_admin_password

  backend_principal_id  = module.container_apps.backend_principal_id
  frontend_principal_id = module.container_apps.frontend_principal_id

  tags = local.tags
}
