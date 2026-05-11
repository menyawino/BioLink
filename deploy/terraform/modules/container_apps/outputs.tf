output "backend_fqdn" {
  description = "FQDN of the backend container app"
  value       = azurerm_container_app.backend.ingress[0].fqdn
}

output "frontend_fqdn" {
  description = "FQDN of the frontend container app"
  value       = azurerm_container_app.frontend.ingress[0].fqdn
}

output "superset_fqdn" {
  description = "FQDN of the Superset container app"
  value       = azurerm_container_app.superset.ingress[0].fqdn
}

output "stakeholder_fqdn" {
  description = "FQDN of the stakeholder container app"
  value       = var.deploy_stakeholder_site ? azurerm_container_app.stakeholders[0].ingress[0].fqdn : null
}

output "backend_principal_id" {
  description = "Principal ID of the backend managed identity"
  value       = azurerm_container_app.backend.identity[0].principal_id
}

output "frontend_principal_id" {
  description = "Principal ID of the frontend managed identity"
  value       = azurerm_container_app.frontend.identity[0].principal_id
}
