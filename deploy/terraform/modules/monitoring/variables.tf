variable "workspace_name" {
  description = "Name of the Log Analytics workspace"
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

variable "sku" {
  description = "SKU for Log Analytics workspace"
  type        = string
  default     = "PerGB2018"
}

variable "retention_days" {
  description = "Log retention in days"
  type        = number
  default     = 30
}

variable "alert_email_addresses" {
  description = "Email addresses for critical alerts"
  type        = list(string)
  default     = []
}

variable "backend_container_app_id" {
  description = "Resource ID of the backend container app"
  type        = string
}

variable "postgres_server_id" {
  description = "Resource ID of the PostgreSQL server"
  type        = string
}

variable "cpu_threshold" {
  description = "CPU usage threshold for alerts (percentage)"
  type        = number
  default     = 80
}

variable "memory_threshold" {
  description = "Memory usage threshold for alerts (percentage)"
  type        = number
  default     = 85
}

variable "db_connection_threshold" {
  description = "Database connection threshold for alerts"
  type        = number
  default     = 80
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
