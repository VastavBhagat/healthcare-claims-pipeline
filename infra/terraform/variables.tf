variable "resource_group_name" {
  default = "rg-healthcare-pipeline"
}

variable "location" {
  default = "australiaeast"
}

variable "storage_account_name" {
  description = "Must be globally unique, lowercase, 3-24 chars, no hyphens"
}

variable "adf_name" {
  default = "adf-healthcare-vastav"
}

variable "environment" {
  default = "dev"
}