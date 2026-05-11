output "server_fqdn" {
  description = "Fully qualified domain name of the PostgreSQL server"
  value       = azurerm_postgresql_flexible_server.main.fqdn
}

output "server_id" {
  description = "ID of the PostgreSQL server"
  value       = azurerm_postgresql_flexible_server.main.id
}

output "app_database_name" {
  description = "Name of the application database"
  value       = azurerm_postgresql_flexible_server_database.app.name
}

output "vector_database_name" {
  description = "Name of the vector database"
  value       = azurerm_postgresql_flexible_server_database.vector.name
}

output "connection_string" {
  description = "PostgreSQL connection string"
  value       = "postgresql://${var.admin_username}:${var.admin_password}@${azurerm_postgresql_flexible_server.main.fqdn}:5432/${var.app_database_name}?sslmode=require"
  sensitive   = true
}

output "vector_connection_string" {
  description = "Vector database connection string"
  value       = "postgresql://${var.admin_username}:${var.admin_password}@${azurerm_postgresql_flexible_server.main.fqdn}:5432/${var.vector_database_name}?sslmode=require"
  sensitive   = true
}
