output "log_analytics_workspace_id" {
  description = "ID of the Log Analytics workspace"
  value       = azurerm_log_analytics_workspace.main.id
}

output "log_analytics_workspace_name" {
  description = "Name of the Log Analytics workspace"
  value       = azurerm_log_analytics_workspace.main.name
}

output "application_insights_backend_key" {
  description = "Instrumentation key for backend Application Insights"
  value       = azurerm_application_insights.backend.instrumentation_key
  sensitive   = true
}

output "application_insights_frontend_key" {
  description = "Instrumentation key for frontend Application Insights"
  value       = azurerm_application_insights.frontend.instrumentation_key
  sensitive   = true
}
