variable "environment_name" {
  description = "Name of the Container Apps environment"
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

variable "log_analytics_workspace_id" {
  description = "Log Analytics Workspace ID for monitoring"
  type        = string
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}

# Backend
variable "backend_app_name" {
  description = "Name of the backend container app"
  type        = string
}

variable "backend_image" {
  description = "Docker image for backend"
  type        = string
}

variable "backend_cpu" {
  description = "CPU cores for backend"
  type        = number
  default     = 1.0
}

variable "backend_memory" {
  description = "Memory for backend"
  type        = string
  default     = "2.0Gi"
}

variable "backend_min_replicas" {
  description = "Minimum replicas for backend"
  type        = number
  default     = 1
}

variable "backend_max_replicas" {
  description = "Maximum replicas for backend"
  type        = number
  default     = 5
}

# Frontend
variable "frontend_app_name" {
  description = "Name of the frontend container app"
  type        = string
}

variable "frontend_image" {
  description = "Docker image for frontend"
  type        = string
}

variable "frontend_cpu" {
  description = "CPU cores for frontend"
  type        = number
  default     = 0.5
}

variable "frontend_memory" {
  description = "Memory for frontend"
  type        = string
  default     = "1.0Gi"
}

variable "frontend_min_replicas" {
  description = "Minimum replicas for frontend"
  type        = number
  default     = 1
}

variable "frontend_max_replicas" {
  description = "Maximum replicas for frontend"
  type        = number
  default     = 3
}

# Superset
variable "superset_app_name" {
  description = "Name of the Superset container app"
  type        = string
}

variable "superset_image" {
  description = "Docker image for Superset"
  type        = string
}

variable "superset_cpu" {
  description = "CPU cores for Superset"
  type        = number
  default     = 1.0
}

variable "superset_memory" {
  description = "Memory for Superset"
  type        = string
  default     = "2.0Gi"
}

variable "superset_min_replicas" {
  description = "Minimum replicas for Superset"
  type        = number
  default     = 1
}

variable "superset_max_replicas" {
  description = "Maximum replicas for Superset"
  type        = number
  default     = 2
}

# Stakeholder site
variable "deploy_stakeholder_site" {
  description = "Whether to deploy the stakeholder site"
  type        = bool
  default     = false
}

variable "stakeholder_app_name" {
  description = "Name of the stakeholder container app"
  type        = string
  default     = "biolink-stakeholders"
}

variable "stakeholder_image" {
  description = "Docker image for stakeholder site"
  type        = string
  default     = ""
}

# Secrets / Connection strings
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

variable "superset_admin_user" {
  description = "Superset admin username"
  type        = string
  default     = "admin"
}

variable "superset_admin_email" {
  description = "Superset admin email"
  type        = string
}

variable "superset_metadata_database_uri" {
  description = "Superset metadata database URI"
  type        = string
  sensitive   = true
}

variable "superset_database_name" {
  description = "Superset database display name"
  type        = string
  default     = "BioLink PostgreSQL"
}

variable "superset_embedded_allowed_domains" {
  description = "Domains allowed to embed Superset"
  type        = string
}

variable "superset_url" {
  description = "Superset URL for frontend"
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

# Other
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

variable "log_level" {
  description = "Application log level"
  type        = string
  default     = "INFO"
}
