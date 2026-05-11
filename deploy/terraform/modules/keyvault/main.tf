# Azure Key Vault Module for BioLink
# Centralized secret management with RBAC

terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.100"
    }
  }
}

resource "azurerm_key_vault" "main" {
  name                       = var.vault_name
  location                   = var.location
  resource_group_name        = var.resource_group_name
  tenant_id                  = var.tenant_id
  sku_name                   = var.sku_name
  soft_delete_retention_days = 7
  purge_protection_enabled   = true

  enable_rbac_authorization = true

  network_acls {
    default_action             = var.network_acls_default_action
    bypass                     = "AzureServices"
    ip_rules                   = var.allowed_ip_ranges
    virtual_network_subnet_ids = var.allowed_subnet_ids
  }

  tags = var.tags
}

# Secrets
resource "azurerm_key_vault_secret" "database_url" {
  name         = "database-url"
  value        = var.database_url
  key_vault_id = azurerm_key_vault.main.id
}

resource "azurerm_key_vault_secret" "rag_pg_url" {
  name         = "rag-pg-url"
  value        = var.rag_pg_url
  key_vault_id = azurerm_key_vault.main.id
}

resource "azurerm_key_vault_secret" "app_secret_key" {
  name         = "app-secret-key"
  value        = var.app_secret_key
  key_vault_id = azurerm_key_vault.main.id
}

resource "azurerm_key_vault_secret" "superset_secret_key" {
  name         = "superset-secret-key"
  value        = var.superset_secret_key
  key_vault_id = azurerm_key_vault.main.id
}

resource "azurerm_key_vault_secret" "superset_admin_password" {
  name         = "superset-admin-password"
  value        = var.superset_admin_password
  key_vault_id = azurerm_key_vault.main.id
}

resource "azurerm_key_vault_secret" "postgres_admin_password" {
  name         = "postgres-admin-password"
  value        = var.postgres_admin_password
  key_vault_id = azurerm_key_vault.main.id
}

# Role assignments for container apps to read secrets
resource "azurerm_role_assignment" "backend_secrets" {
  scope                = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = var.backend_principal_id
}

resource "azurerm_role_assignment" "frontend_secrets" {
  scope                = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = var.frontend_principal_id
}
