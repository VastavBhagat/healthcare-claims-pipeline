variable "location" {
  description = "Azure region"
  type        = string
  default     = "australiaeast"
}

variable "environment" {
  description = "Deployment environment (dev or prod)"
  type        = string
  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "environment must be dev or prod"
  }
}

variable "snowflake_account" {
  description = "Snowflake account identifier"
  type        = string
  sensitive   = true
}

variable "snowflake_user" {
  description = "Snowflake admin username"
  type        = string
  sensitive   = true
}

variable "snowflake_password" {
  description = "Snowflake admin password"
  type        = string
  sensitive   = true
}

variable "alert_email" {
  description = "Email address for ADF failure alerts"
  type        = string
}
