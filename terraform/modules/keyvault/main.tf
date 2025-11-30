# =============================================================================
# Key Vault Module - Azure Key Vault
# =============================================================================

terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.80"
    }
  }
}

variable "resource_group_name" { type = string }
variable "location" { type = string }
variable "project_name" { type = string }
variable "environment" { type = string }
variable "sku_name" { type = string }
variable "enable_soft_delete" { type = bool }
variable "soft_delete_retention_days" { type = number }
variable "enable_purge_protection" { type = bool }
variable "enable_rbac_authorization" { type = bool }
variable "public_network_access" { type = bool }
variable "subnet_id" { type = string }
variable "private_dns_zone_ids" { type = list(string) }
variable "aks_principal_id" { type = string }
variable "aks_tenant_id" { type = string }
variable "secrets" { type = map(object({ value = string })) }
variable "tags" { type = map(string) }

data "azurerm_client_config" "current" {}

resource "azurerm_key_vault" "kv" {
  name                          = "${replace(var.project_name, "-", "")}${var.environment}kv"
  location                      = var.location
  resource_group_name           = var.resource_group_name
  tenant_id                     = data.azurerm_client_config.current.tenant_id
  sku_name                      = var.sku_name
  soft_delete_retention_days    = var.soft_delete_retention_days
  purge_protection_enabled      = var.enable_purge_protection
  enable_rbac_authorization     = var.enable_rbac_authorization
  public_network_access_enabled = var.public_network_access

  network_acls {
    bypass         = "AzureServices"
    default_action = var.public_network_access ? "Allow" : "Deny"
  }

  tags = var.tags
}

resource "azurerm_private_endpoint" "kv" {
  count               = !var.public_network_access ? 1 : 0
  name                = "${azurerm_key_vault.kv.name}-pe"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = var.subnet_id

  private_service_connection {
    name                           = "${azurerm_key_vault.kv.name}-psc"
    private_connection_resource_id = azurerm_key_vault.kv.id
    is_manual_connection           = false
    subresource_names              = ["vault"]
  }

  private_dns_zone_group {
    name                 = "keyvault-dns-zone-group"
    private_dns_zone_ids = var.private_dns_zone_ids
  }

  tags = var.tags
}

resource "azurerm_role_assignment" "aks_secrets_user" {
  scope                = azurerm_key_vault.kv.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = var.aks_principal_id
}

resource "azurerm_key_vault_secret" "secrets" {
  for_each     = var.secrets
  name         = each.key
  value        = each.value.value
  key_vault_id = azurerm_key_vault.kv.id

  depends_on = [azurerm_role_assignment.aks_secrets_user]
}

output "keyvault_name" {
  description = "Key Vault name"
  value       = azurerm_key_vault.kv.name
}

output "keyvault_id" {
  description = "Key Vault resource ID"
  value       = azurerm_key_vault.kv.id
}

output "keyvault_uri" {
  description = "Key Vault URI"
  value       = azurerm_key_vault.kv.vault_uri
}
