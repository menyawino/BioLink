# Azure Container Apps Module for BioLink
# Deploys backend, frontend, and Superset container apps

terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.100"
    }
  }
}

# Container Apps Environment
resource "azurerm_container_app_environment" "main" {
  name                       = var.environment_name
  resource_group_name        = var.resource_group_name
  location                   = var.location
  log_analytics_workspace_id = var.log_analytics_workspace_id

  tags = var.tags
}

# Backend Container App
resource "azurerm_container_app" "backend" {
  name                         = var.backend_app_name
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"

  identity {
    type = "SystemAssigned"
  }

  ingress {
    external_enabled = true
    target_port      = 3001
    transport        = "auto"
    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  template {
    min_replicas = var.backend_min_replicas
    max_replicas = var.backend_max_replicas

    container {
      name   = "backend"
      image  = var.backend_image
      cpu    = var.backend_cpu
      memory = var.backend_memory

      env {
        name        = "DATABASE_URL"
        secret_name = "database-url"
      }
      env {
        name        = "RAG_PG_URL"
        secret_name = "rag-pg-url"
      }
      env {
        name        = "APP_SECRET_KEY"
        secret_name = "app-secret-key"
      }
      env {
        name  = "AZURE_ENTRA_TENANT_ID"
        value = var.azure_entra_tenant_id
      }
      env {
        name  = "AZURE_ENTRA_BACKEND_CLIENT_ID"
        value = var.azure_entra_backend_client_id
      }
      env {
        name  = "AZURE_ENTRA_AUDIENCE"
        value = var.azure_entra_audience
      }
      env {
        name  = "AZURE_ENTRA_AUTHORITY"
        value = var.azure_entra_authority
      }
      env {
        name  = "REDIS_URL"
        value = var.redis_url
      }
      env {
        name  = "OLLAMA_URL"
        value = var.ollama_url
      }
      env {
        name  = "LOG_LEVEL"
        value = var.log_level
      }
      env {
        name  = "LOG_JSON_FORMAT"
        value = "true"
      }
    }
  }

  secret {
    name  = "database-url"
    value = var.database_url
  }
  secret {
    name  = "rag-pg-url"
    value = var.rag_pg_url
  }
  secret {
    name  = "app-secret-key"
    value = var.app_secret_key
  }

  tags = var.tags

  lifecycle {
    ignore_changes = [
      template[0].container[0].image,
    ]
  }
}

# Frontend Container App
resource "azurerm_container_app" "frontend" {
  name                         = var.frontend_app_name
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"

  identity {
    type = "SystemAssigned"
  }

  ingress {
    external_enabled = true
    target_port      = 80
    transport        = "auto"
    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  template {
    min_replicas = var.frontend_min_replicas
    max_replicas = var.frontend_max_replicas

    container {
      name   = "frontend"
      image  = var.frontend_image
      cpu    = var.frontend_cpu
      memory = var.frontend_memory

      env {
        name  = "VITE_API_BASE_URL"
        value = "https://${azurerm_container_app.backend.ingress[0].fqdn}"
      }
      env {
        name  = "VITE_AZURE_ENTRA_CLIENT_ID"
        value = var.azure_entra_frontend_client_id
      }
      env {
        name  = "VITE_AZURE_ENTRA_TENANT_ID"
        value = var.azure_entra_tenant_id
      }
      env {
        name  = "VITE_AZURE_ENTRA_API_SCOPE"
        value = var.azure_entra_api_scope
      }
      env {
        name  = "VITE_SUPerset_URL"
        value = var.superset_url
      }
    }
  }

  tags = var.tags

  lifecycle {
    ignore_changes = [
      template[0].container[0].image,
    ]
  }
}

# Superset Container App
resource "azurerm_container_app" "superset" {
  name                         = var.superset_app_name
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"

  identity {
    type = "SystemAssigned"
  }

  ingress {
    external_enabled = true
    target_port      = 8088
    transport        = "auto"
    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  template {
    min_replicas = var.superset_min_replicas
    max_replicas = var.superset_max_replicas

    container {
      name   = "superset"
      image  = var.superset_image
      cpu    = var.superset_cpu
      memory = var.superset_memory

      env {
        name        = "SUPERSET_SECRET_KEY"
        secret_name = "superset-secret-key"
      }
      env {
        name        = "SUPERSET_ADMIN_PASSWORD"
        secret_name = "superset-admin-password"
      }
      env {
        name  = "SUPERSET_ADMIN_USER"
        value = var.superset_admin_user
      }
      env {
        name  = "SUPERSET_ADMIN_EMAIL"
        value = var.superset_admin_email
      }
      env {
        name  = "SUPERSET_METADATA_DATABASE_URI"
        value = var.superset_metadata_database_uri
      }
      env {
        name  = "SUPERSET_DATABASE_NAME"
        value = var.superset_database_name
      }
      env {
        name  = "SUPERSET_EMBEDDED_ALLOWED_DOMAINS"
        value = var.superset_embedded_allowed_domains
      }
    }
  }

  secret {
    name  = "superset-secret-key"
    value = var.superset_secret_key
  }
  secret {
    name  = "superset-admin-password"
    value = var.superset_admin_password
  }

  tags = var.tags

  lifecycle {
    ignore_changes = [
      template[0].container[0].image,
    ]
  }
}

# Stakeholder site Container App
resource "azurerm_container_app" "stakeholders" {
  count                        = var.deploy_stakeholder_site ? 1 : 0
  name                         = var.stakeholder_app_name
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"

  identity {
    type = "SystemAssigned"
  }

  ingress {
    external_enabled = true
    target_port      = 80
    transport        = "auto"
    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  template {
    min_replicas = 1
    max_replicas = 2

    container {
      name   = "stakeholders"
      image  = var.stakeholder_image
      cpu    = 0.5
      memory = "1.0Gi"
    }
  }

  tags = var.tags

  lifecycle {
    ignore_changes = [
      template[0].container[0].image,
    ]
  }
}
