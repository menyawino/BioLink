variable "location" {
  description = "Azure region for production deployment"
  type        = string
  default     = "westeurope"
}

variable "container_apps_domain" {
  description = "Domain suffix for Container Apps"
  type        = string
  default     = "azurecontainerapps.io"
}

# Images
variable "backend_image" {
  description = "Backend Docker image URI"
  type        = string
}

variable "frontend_image" {
  description = "Frontend Docker image URI"
  type        = string
}

variable "superset_image" {
  description = "Superset Docker image URI"
  type        = string
}

variable "stakeholder_image" {
  description = "Stakeholder site Docker image URI"
  type        = string
  default     = ""
}

# PostgreSQL
variable "postgres_admin_username" {
  description = "PostgreSQL admin username"
  type        = string
  default     = "biolinkadmin"
}

variable "postgres_admin_password" {
  description = "PostgreSQL admin password"
  type        = string
  sensitive   = true
}

variable "allowed_cidrs" {
  description = "Allowed CIDR blocks for database access"
  type        = list(string)
  default     = []
}

# Secrets
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

variable "superset_admin_user" {
  description = "Superset admin username"
  type        = string
  default     = "admin"
}

variable "superset_admin_email" {
  description = "Superset admin email"
  type        = string
}

# Azure Entra
variable "azure_entra_tenant_id" {
  description = "Azure Entra tenant ID"
  type        = string
}

variable "azure_entra_backend_client_id" {
  description = "Azure Entra backend client ID"
  type        = string
}

variable "azure_entra_frontend_client_id" {
  description = "Azure Entra frontend client ID"
  type        = string
}

variable "azure_entra_audience" {
  description = "Azure Entra audience"
  type        = string
}

variable "azure_entra_authority" {
  description = "Azure Entra authority URL"
  type        = string
}

variable "azure_entra_api_scope" {
  description = "Azure Entra API scope"
  type        = string
}

# Infrastructure
variable "redis_url" {
  description = "Redis connection URL"
  type        = string
  default     = ""
}

variable "ollama_url" {
  description = "Ollama API URL"
  type        = string
  default     = ""
}

# Monitoring
variable "alert_email_addresses" {
  description = "Email addresses for critical alerts"
  type        = list(string)
  default     = []
}
