variable "vault_name" {
  description = "Name of the Key Vault"
  type        = string
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
}

variable "tenant_id" {
  description = "Azure tenant ID"
  type        = string
}

variable "sku_name" {
  description = "SKU for Key Vault"
  type        = string
  default     = "standard"
}

variable "network_acls_default_action" {
  description = "Default action for network ACLs"
  type        = string
  default     = "Deny"
}

variable "allowed_ip_ranges" {
  description = "Allowed IP ranges for Key Vault access"
  type        = list(string)
  default     = []
}

variable "allowed_subnet_ids" {
  description = "Allowed subnet IDs for Key Vault access"
  type        = list(string)
  default     = []
}

variable "database_url" {
  description = "Database connection string"
  type        = string
  sensitive   = true
}

variable "rag_pg_url" {
  description = "RAG vector database connection string"
  type        = string
  sensitive   = true
}

variable "app_secret_key" {
  description = "Application secret key"
  type        = string
  sensitive   = true
}

variable "superset_secret_key" {
  description = "Superset secret key"
  type        = string
  sensitive   = true
}

variable "superset_admin_password" {
  description = "Superset admin password"
  type        = string
  sensitive   = true
}

variable "postgres_admin_password" {
  description = "PostgreSQL admin password"
  type        = string
  sensitive   = true
}

variable "backend_principal_id" {
  description = "Principal ID of the backend managed identity"
  type        = string
}

variable "frontend_principal_id" {
  description = "Principal ID of the frontend managed identity"
  type        = string
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
