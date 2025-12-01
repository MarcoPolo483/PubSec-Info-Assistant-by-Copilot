# =============================================================================
# ACR Module - Azure Container Registry
# =============================================================================

terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}

variable "resource_group_name" { type = string }
variable "location" { type = string }
variable "project_name" { type = string }
variable "environment" { type = string }
variable "sku" { type = string }
variable "admin_enabled" { type = bool }
variable "public_network_access" { type = bool }
variable "quarantine_policy" { type = bool }
variable "retention_days" { type = number }
variable "geo_replication_locations" { type = list(string) }
variable "subnet_id" { type = string }
variable "private_dns_zone_ids" { type = list(string) }
variable "tags" { type = map(string) }

resource "azurerm_container_registry" "acr" {
  name                          = "${replace(var.project_name, "-", "")}${var.environment}acr"
  resource_group_name           = var.resource_group_name
  location                      = var.location
  sku                           = var.sku
  admin_enabled                 = var.admin_enabled
  public_network_access_enabled = var.public_network_access

  identity {
    type = "SystemAssigned"
  }

  dynamic "georeplications" {
    for_each = var.sku == "Premium" ? var.geo_replication_locations : []
    content {
      location                = georeplications.value
      zone_redundancy_enabled = true
    }
  }

  retention_policy_in_days = var.retention_days
  trust_policy_enabled     = var.quarantine_policy

  network_rule_set {
    default_action = var.public_network_access ? "Allow" : "Deny"
  }

  tags = var.tags
}

resource "azurerm_private_endpoint" "acr" {
  count               = var.sku == "Premium" && !var.public_network_access ? 1 : 0
  name                = "${azurerm_container_registry.acr.name}-pe"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = var.subnet_id

  private_service_connection {
    name                           = "${azurerm_container_registry.acr.name}-psc"
    private_connection_resource_id = azurerm_container_registry.acr.id
    is_manual_connection           = false
    subresource_names              = ["registry"]
  }

  private_dns_zone_group {
    name                 = "acr-dns-zone-group"
    private_dns_zone_ids = var.private_dns_zone_ids
  }

  tags = var.tags
}

output "acr_name" {
  description = "ACR name"
  value       = azurerm_container_registry.acr.name
}

output "acr_id" {
  description = "ACR resource ID"
  value       = azurerm_container_registry.acr.id
}

output "acr_login_server" {
  description = "ACR login server URL"
  value       = azurerm_container_registry.acr.login_server
}
