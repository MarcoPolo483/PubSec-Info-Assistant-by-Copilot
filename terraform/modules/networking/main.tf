# =============================================================================
# Networking Module - VNet, Subnets, NSGs, Private Endpoints
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
variable "vnet_address_space" { type = list(string) }
variable "aks_subnet_cidr" { type = string }
variable "appgw_subnet_cidr" { type = string }
variable "private_endpoint_cidr" { type = string }
variable "database_subnet_cidr" { type = string }
variable "enable_ddos_protection" { type = bool }
variable "enable_private_link" { type = bool }
variable "tags" { type = map(string) }

# Virtual Network
resource "azurerm_virtual_network" "vnet" {
  name                = "${var.project_name}-${var.environment}-vnet"
  location            = var.location
  resource_group_name = var.resource_group_name
  address_space       = var.vnet_address_space
  tags                = var.tags
}

# AKS Subnet
resource "azurerm_subnet" "aks" {
  name                 = "aks-subnet"
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = [var.aks_subnet_cidr]
}

# Application Gateway Subnet
resource "azurerm_subnet" "appgw" {
  name                 = "appgw-subnet"
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = [var.appgw_subnet_cidr]
}

# Private Endpoint Subnet
resource "azurerm_subnet" "private_endpoint" {
  name                 = "private-endpoint-subnet"
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = [var.private_endpoint_cidr]
  private_endpoint_network_policies_enabled = false
}

# Database Subnet
resource "azurerm_subnet" "database" {
  name                 = "database-subnet"
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = [var.database_subnet_cidr]
  service_endpoints    = ["Microsoft.Sql", "Microsoft.Storage"]
}

# Network Security Groups
resource "azurerm_network_security_group" "aks" {
  name                = "${var.project_name}-${var.environment}-aks-nsg"
  location            = var.location
  resource_group_name = var.resource_group_name

  security_rule {
    name                       = "AllowHTTPS"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "443"
    source_address_prefix      = "VirtualNetwork"
    destination_address_prefix = "*"
  }

  tags = var.tags
}

resource "azurerm_subnet_network_security_group_association" "aks" {
  subnet_id                 = azurerm_subnet.aks.id
  network_security_group_id = azurerm_network_security_group.aks.id
}

# Private DNS Zones
resource "azurerm_private_dns_zone" "acr" {
  count               = var.enable_private_link ? 1 : 0
  name                = "privatelink.azurecr.io"
  resource_group_name = var.resource_group_name
  tags                = var.tags
}

resource "azurerm_private_dns_zone_virtual_network_link" "acr" {
  count                 = var.enable_private_link ? 1 : 0
  name                  = "acr-dns-link"
  resource_group_name   = var.resource_group_name
  private_dns_zone_name = azurerm_private_dns_zone.acr[0].name
  virtual_network_id    = azurerm_virtual_network.vnet.id
  tags                  = var.tags
}

resource "azurerm_private_dns_zone" "keyvault" {
  count               = var.enable_private_link ? 1 : 0
  name                = "privatelink.vaultcore.azure.net"
  resource_group_name = var.resource_group_name
  tags                = var.tags
}

resource "azurerm_private_dns_zone_virtual_network_link" "keyvault" {
  count                 = var.enable_private_link ? 1 : 0
  name                  = "keyvault-dns-link"
  resource_group_name   = var.resource_group_name
  private_dns_zone_name = azurerm_private_dns_zone.keyvault[0].name
  virtual_network_id    = azurerm_virtual_network.vnet.id
  tags                  = var.tags
}

resource "azurerm_private_dns_zone" "aks" {
  count               = var.enable_private_link ? 1 : 0
  name                = "privatelink.${var.location}.azmk8s.io"
  resource_group_name = var.resource_group_name
  tags                = var.tags
}

resource "azurerm_private_dns_zone_virtual_network_link" "aks" {
  count                 = var.enable_private_link ? 1 : 0
  name                  = "aks-dns-link"
  resource_group_name   = var.resource_group_name
  private_dns_zone_name = azurerm_private_dns_zone.aks[0].name
  virtual_network_id    = azurerm_virtual_network.vnet.id
  tags                  = var.tags
}

output "vnet_name" { value = azurerm_virtual_network.vnet.name }
output "vnet_id" { value = azurerm_virtual_network.vnet.id }
output "aks_subnet_id" { value = azurerm_subnet.aks.id }
output "appgw_subnet_id" { value = azurerm_subnet.appgw.id }
output "private_endpoint_subnet_id" { value = azurerm_subnet.private_endpoint.id }
output "database_subnet_id" { value = azurerm_subnet.database.id }
output "acr_private_dns_zone_id" { value = var.enable_private_link ? azurerm_private_dns_zone.acr[0].id : null }
output "keyvault_private_dns_zone_id" { value = var.enable_private_link ? azurerm_private_dns_zone.keyvault[0].id : null }
output "aks_private_dns_zone_id" { value = var.enable_private_link ? azurerm_private_dns_zone.aks[0].id : null }
