locals {
  prefix = "healthcare-${var.environment}"
  tags = {
    environment = var.environment
    project     = "healthcare-claims-pipeline"
    managed_by  = "terraform"
  }
}

# --- Resource Group ---

resource "azurerm_resource_group" "main" {
  name     = "rg-${local.prefix}"
  location = var.location
  tags     = local.tags
}

# --- Storage Account + Containers ---

resource "azurerm_storage_account" "main" {
  name                     = replace("sa${local.prefix}", "-", "")
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  is_hns_enabled           = true  # ADLS Gen2
  tags                     = local.tags
}

resource "azurerm_storage_container" "raw" {
  name                  = "raw"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "staging" {
  name                  = "staging"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "archive" {
  name                  = "archive"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

# --- Azure Data Factory ---

resource "azurerm_data_factory" "main" {
  name                = "adf-${local.prefix}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  tags                = local.tags

  identity {
    type = "SystemAssigned"
  }
}

# Grant ADF identity access to storage
resource "azurerm_role_assignment" "adf_storage" {
  scope                = azurerm_storage_account.main.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_data_factory.main.identity[0].principal_id
}

# --- Snowflake Warehouse ---

resource "snowflake_warehouse" "claims" {
  name           = "CLAIMS_WH_${upper(var.environment)}"
  warehouse_size = var.environment == "prod" ? "SMALL" : "X-SMALL"
  auto_suspend   = 60
  auto_resume    = true
}

# --- Snowflake Database + Schemas ---

resource "snowflake_database" "healthcare" {
  name                        = "HEALTHCARE_DB_${upper(var.environment)}"
  data_retention_time_in_days = var.environment == "prod" ? 7 : 1
}

resource "snowflake_schema" "raw" {
  database = snowflake_database.healthcare.name
  name     = "RAW"
}

resource "snowflake_schema" "staging" {
  database = snowflake_database.healthcare.name
  name     = "STAGING"
}

resource "snowflake_schema" "intermediate" {
  database = snowflake_database.healthcare.name
  name     = "INTERMEDIATE"
}

resource "snowflake_schema" "marts" {
  database = snowflake_database.healthcare.name
  name     = "MARTS"
}

resource "snowflake_schema" "snapshots" {
  database = snowflake_database.healthcare.name
  name     = "SNAPSHOTS"
}

resource "snowflake_schema" "audit" {
  database = snowflake_database.healthcare.name
  name     = "AUDIT"
}
