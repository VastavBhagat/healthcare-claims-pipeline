output "resource_group_name" {
  value = azurerm_resource_group.main.name
}

output "storage_account_name" {
  value = azurerm_storage_account.main.name
}

output "storage_account_primary_key" {
  value     = azurerm_storage_account.main.primary_access_key
  sensitive = true
}

output "adf_name" {
  value = azurerm_data_factory.main.name
}

output "snowflake_database" {
  value = snowflake_database.healthcare.name
}

output "snowflake_warehouse" {
  value = snowflake_warehouse.claims.name
}
