# Monitoring Module for BioLink
# Creates Log Analytics Workspace and Application Insights

terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.100"
    }
  }
}

# Log Analytics Workspace
resource "azurerm_log_analytics_workspace" "main" {
  name                = var.workspace_name
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = var.sku
  retention_in_days   = var.retention_days

  tags = var.tags
}

# Application Insights for backend
resource "azurerm_application_insights" "backend" {
  name                = "${var.workspace_name}-backend"
  location            = var.location
  resource_group_name = var.resource_group_name
  application_type    = "web"
  workspace_id        = azurerm_log_analytics_workspace.main.id

  tags = var.tags
}

# Application Insights for frontend
resource "azurerm_application_insights" "frontend" {
  name                = "${var.workspace_name}-frontend"
  location            = var.location
  resource_group_name = var.resource_group_name
  application_type    = "web"
  workspace_id        = azurerm_log_analytics_workspace.main.id

  tags = var.tags
}

# Action Group for alerts
resource "azurerm_monitor_action_group" "critical" {
  name                = "${var.workspace_name}-critical-alerts"
  resource_group_name = var.resource_group_name
  short_name          = "biolink-crit"

  dynamic "email_receiver" {
    for_each = var.alert_email_addresses
    content {
      name          = "email-${email_receiver.value}"
      email_address = email_receiver.value
    }
  }

  tags = var.tags
}

# CPU alert for backend
resource "azurerm_monitor_metric_alert" "backend_cpu" {
  name                = "${var.workspace_name}-backend-high-cpu"
  resource_group_name = var.resource_group_name
  scopes              = [var.backend_container_app_id]
  description         = "Alert when backend CPU exceeds threshold"
  severity            = 2
  frequency           = "PT5M"
  window_size         = "PT15M"

  criteria {
    metric_namespace = "Microsoft.App/containerApps"
    metric_name      = "Usage"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = var.cpu_threshold

    dimension {
      name     = "containerName"
      operator = "Include"
      values   = ["backend"]
    }
  }

  action {
    action_group_id = azurerm_monitor_action_group.critical.id
  }

  tags = var.tags
}

# Memory alert for backend
resource "azurerm_monitor_metric_alert" "backend_memory" {
  name                = "${var.workspace_name}-backend-high-memory"
  resource_group_name = var.resource_group_name
  scopes              = [var.backend_container_app_id]
  description         = "Alert when backend memory exceeds threshold"
  severity            = 2
  frequency           = "PT5M"
  window_size         = "PT15M"

  criteria {
    metric_namespace = "Microsoft.App/containerApps"
    metric_name      = "Usage"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = var.memory_threshold

    dimension {
      name     = "containerName"
      operator = "Include"
      values   = ["backend"]
    }
  }

  action {
    action_group_id = azurerm_monitor_action_group.critical.id
  }

  tags = var.tags
}

# Database connection alert
resource "azurerm_monitor_metric_alert" "db_connections" {
  name                = "${var.workspace_name}-db-high-connections"
  resource_group_name = var.resource_group_name
  scopes              = [var.postgres_server_id]
  description         = "Alert when database connections are high"
  severity            = 2
  frequency           = "PT5M"
  window_size         = "PT15M"

  criteria {
    metric_namespace = "Microsoft.DBforPostgreSQL/flexibleServers"
    metric_name      = "active_connections"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = var.db_connection_threshold
  }

  action {
    action_group_id = azurerm_monitor_action_group.critical.id
  }

  tags = var.tags
}
