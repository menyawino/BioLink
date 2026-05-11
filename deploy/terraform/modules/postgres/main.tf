# Azure PostgreSQL Flexible Server Module for BioLink

terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.100"
    }
  }
}

resource "azurerm_postgresql_flexible_server" "main" {
  name                   = var.server_name
  resource_group_name    = var.resource_group_name
  location               = var.location
  version                = "16"
  sku_name               = var.sku_name
  storage_mb             = var.storage_mb
  backup_retention_days  = var.backup_retention_days
  geo_redundant_backup_enabled = var.geo_redundant_backup_enabled

  administrator_login    = var.admin_username
  administrator_password = var.admin_password

  zone = var.zone

  tags = var.tags
}

# Allow Azure services
resource "azurerm_postgresql_flexible_server_firewall_rule" "allow_azure" {
  name             = "allow-azure-services"
  server_id        = azurerm_postgresql_flexible_server.main.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}

# Allow specific CIDRs
resource "azurerm_postgresql_flexible_server_firewall_rule" "allowed_cidrs" {
  for_each = toset(var.allowed_cidrs)

  name             = "allow-${replace(each.value, "/", "-")}"
  server_id        = azurerm_postgresql_flexible_server.main.id
  start_ip_address = cidrhost(each.value, 0)
  end_ip_address   = cidrhost(each.value, -1)
}

# Main application database
resource "azurerm_postgresql_flexible_server_database" "app" {
  name      = var.app_database_name
  server_id = azurerm_postgresql_flexible_server.main.id
  charset   = "UTF8"
  collation = "en_US.utf8"
}

# Vector/RAG database
resource "azurerm_postgresql_flexible_server_database" "vector" {
  name      = var.vector_database_name
  server_id = azurerm_postgresql_flexible_server.main.id
  charset   = "UTF8"
  collation = "en_US.utf8"
}

# Enable pgvector extension
resource "azurerm_postgresql_flexible_server_configuration" "extensions" {
  name      = "azure.extensions"
  server_id = azurerm_postgresql_flexible_server.main.id
  value     = "VECTOR"
}

# Enable SSL enforcement
resource "azurerm_postgresql_flexible_server_configuration" "ssl" {
  name      = "require_secure_transport"
  server_id = azurerm_postgresql_flexible_server.main.id
  value     = "on"
}
