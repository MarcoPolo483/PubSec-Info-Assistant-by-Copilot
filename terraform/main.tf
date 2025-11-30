# =============================================================================
# PubSec Info Assistant - Azure Infrastructure (Terraform)
# =============================================================================
# Production-ready Infrastructure-as-Code for Azure deployment
# Supports: AKS, ACR, Key Vault, Application Gateway, Monitoring
# =============================================================================

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.80"
    }
    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 2.45"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }

  # Azure Storage backend for remote state
  backend "azurerm" {
    resource_group_name  = "pubsec-terraform-state-rg"
    storage_account_name = "pubsecterraformstate"
    container_name       = "tfstate"
    key                  = "pubsec-info-assistant.tfstate"
  }
}

provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = true
    }
    key_vault {
      purge_soft_delete_on_destroy    = false
      recover_soft_deleted_key_vaults = true
    }
  }
}

provider "azuread" {}

# =============================================================================
# Local Variables
# =============================================================================

locals {
  project_name = "pubsec-info-assistant"
  environment  = var.environment
  location     = var.location

  # Naming convention: {project}-{environment}-{resource}
  resource_group_name = "${local.project_name}-${local.environment}-rg"

  # Common tags for all resources
  common_tags = merge(
    var.tags,
    {
      Project     = local.project_name
      Environment = local.environment
      ManagedBy   = "Terraform"
      CostCenter  = var.cost_center
      Owner       = var.owner
      Compliance  = "FedRAMP-High"
    }
  )

  # Network configuration
  vnet_address_space    = var.vnet_address_space
  aks_subnet_cidr       = cidrsubnet(local.vnet_address_space[0], 4, 0)
  appgw_subnet_cidr     = cidrsubnet(local.vnet_address_space[0], 4, 1)
  private_endpoint_cidr = cidrsubnet(local.vnet_address_space[0], 4, 2)
  database_subnet_cidr  = cidrsubnet(local.vnet_address_space[0], 4, 3)
}

# =============================================================================
# Resource Group
# =============================================================================

resource "azurerm_resource_group" "main" {
  name     = local.resource_group_name
  location = local.location
  tags     = local.common_tags
}

# =============================================================================
# Networking Module
# =============================================================================

module "networking" {
  source = "./modules/networking"

  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  project_name        = local.project_name
  environment         = local.environment

  vnet_address_space    = local.vnet_address_space
  aks_subnet_cidr       = local.aks_subnet_cidr
  appgw_subnet_cidr     = local.appgw_subnet_cidr
  private_endpoint_cidr = local.private_endpoint_cidr
  database_subnet_cidr  = local.database_subnet_cidr

  enable_ddos_protection = var.enable_ddos_protection
  enable_private_link    = var.enable_private_link

  tags = local.common_tags
}

# =============================================================================
# Azure Container Registry (ACR)
# =============================================================================

module "acr" {
  source = "./modules/acr"

  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  project_name        = local.project_name
  environment         = local.environment

  sku                       = var.acr_sku
  admin_enabled             = false
  public_network_access     = var.acr_public_network_access
  quarantine_policy         = true
  retention_days            = var.acr_retention_days
  geo_replication_locations = var.acr_geo_replication_locations

  # Private endpoint integration
  subnet_id            = module.networking.private_endpoint_subnet_id
  private_dns_zone_ids = [module.networking.acr_private_dns_zone_id]

  tags = local.common_tags

  depends_on = [module.networking]
}

# =============================================================================
# Azure Kubernetes Service (AKS)
# =============================================================================

module "aks" {
  source = "./modules/aks"

  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  project_name        = local.project_name
  environment         = local.environment

  # Network configuration
  vnet_id            = module.networking.vnet_id
  subnet_id          = module.networking.aks_subnet_id
  dns_service_ip     = var.aks_dns_service_ip
  docker_bridge_cidr = var.aks_docker_bridge_cidr
  service_cidr       = var.aks_service_cidr

  # Cluster configuration
  kubernetes_version        = var.aks_kubernetes_version
  automatic_channel_upgrade = var.aks_automatic_channel_upgrade
  sku_tier                  = var.aks_sku_tier

  # System node pool
  system_node_pool_vm_size    = var.aks_system_node_pool_vm_size
  system_node_pool_node_count = var.aks_system_node_pool_node_count
  system_node_pool_min_count  = var.aks_system_node_pool_min_count
  system_node_pool_max_count  = var.aks_system_node_pool_max_count

  # User node pool (application workloads)
  user_node_pool_vm_size    = var.aks_user_node_pool_vm_size
  user_node_pool_node_count = var.aks_user_node_pool_node_count
  user_node_pool_min_count  = var.aks_user_node_pool_min_count
  user_node_pool_max_count  = var.aks_user_node_pool_max_count

  # Security features
  enable_azure_policy        = true
  enable_azure_defender      = var.enable_azure_defender
  enable_pod_security_policy = true
  enable_secret_rotation     = true
  enable_workload_identity   = true

  # Monitoring
  log_analytics_workspace_id = module.monitoring.log_analytics_workspace_id

  # ACR integration
  acr_id = module.acr.acr_id

  # Private cluster
  enable_private_cluster = var.aks_enable_private_cluster
  private_dns_zone_id    = var.aks_enable_private_cluster ? module.networking.aks_private_dns_zone_id : null

  tags = local.common_tags

  depends_on = [module.networking, module.acr, module.monitoring]
}

# =============================================================================
# Azure Key Vault
# =============================================================================

module "keyvault" {
  source = "./modules/keyvault"

  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  project_name        = local.project_name
  environment         = local.environment

  sku_name                   = var.keyvault_sku
  enable_soft_delete         = true
  soft_delete_retention_days = 90
  enable_purge_protection    = var.environment == "production"
  enable_rbac_authorization  = true

  # Network configuration
  public_network_access = var.keyvault_public_network_access
  subnet_id             = module.networking.private_endpoint_subnet_id
  private_dns_zone_ids  = [module.networking.keyvault_private_dns_zone_id]

  # AKS integration (for workload identity)
  aks_principal_id = module.aks.kubelet_identity_object_id
  aks_tenant_id    = data.azurerm_client_config.current.tenant_id

  # Secrets to create
  secrets = {
    openai-api-key = {
      value = var.openai_api_key
    }
    redis-password = {
      value = random_password.redis_password.result
    }
    qdrant-api-key = {
      value = random_password.qdrant_api_key.result
    }
    app-secret-key = {
      value = random_password.app_secret_key.result
    }
  }

  tags = local.common_tags

  depends_on = [module.networking, module.aks]
}

# =============================================================================
# Monitoring & Observability
# =============================================================================

module "monitoring" {
  source = "./modules/monitoring"

  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  project_name        = local.project_name
  environment         = local.environment

  # Log Analytics
  log_retention_days = var.log_retention_days

  # Application Insights
  application_type    = "web"
  sampling_percentage = var.appinsights_sampling_percentage

  # Alerts
  enable_alerts         = var.enable_monitoring_alerts
  alert_email_addresses = var.alert_email_addresses
  alert_webhook_urls    = var.alert_webhook_urls

  # AKS integration - disabled to avoid circular dependency
  # AKS alerts can be added separately after both modules are created
  # aks_cluster_id = module.aks.aks_cluster_id

  tags = local.common_tags
}

# =============================================================================
# Application Gateway (L7 Load Balancer)
# =============================================================================

module "application_gateway" {
  source = "./modules/application-gateway"
  count  = var.enable_application_gateway ? 1 : 0

  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  project_name        = local.project_name
  environment         = local.environment

  # Network configuration
  subnet_id = module.networking.appgw_subnet_id

  # SKU configuration
  sku_name = var.appgw_sku_name
  sku_tier = var.appgw_sku_tier
  capacity = var.appgw_capacity

  # Autoscaling
  enable_autoscaling = var.appgw_enable_autoscaling
  min_capacity       = var.appgw_min_capacity
  max_capacity       = var.appgw_max_capacity

  # WAF configuration
  enable_waf           = var.appgw_enable_waf
  waf_mode             = var.appgw_waf_mode
  waf_rule_set_type    = "OWASP"
  waf_rule_set_version = "3.2"

  # SSL/TLS
  ssl_certificate_data     = var.ssl_certificate_data
  ssl_certificate_password = var.ssl_certificate_password

  # Backend configuration
  backend_address_pool_fqdns = [
    "${local.project_name}-${local.environment}.${local.location}.cloudapp.azure.com"
  ]

  # Monitoring
  log_analytics_workspace_id = module.monitoring.log_analytics_workspace_id

  tags = local.common_tags

  depends_on = [module.networking, module.monitoring]
}

# =============================================================================
# Supporting Resources
# =============================================================================

# Current Azure client configuration
data "azurerm_client_config" "current" {}

# Random passwords for services
resource "random_password" "redis_password" {
  length  = 32
  special = true
}

resource "random_password" "qdrant_api_key" {
  length  = 64
  special = false
}

resource "random_password" "app_secret_key" {
  length  = 64
  special = true
}

# =============================================================================
# Outputs
# =============================================================================

output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.main.name
}

output "aks_cluster_name" {
  description = "Name of the AKS cluster"
  value       = module.aks.aks_cluster_name
}

output "aks_cluster_id" {
  description = "ID of the AKS cluster"
  value       = module.aks.aks_cluster_id
}

output "acr_login_server" {
  description = "ACR login server URL"
  value       = module.acr.acr_login_server
}

output "acr_id" {
  description = "ID of the Azure Container Registry"
  value       = module.acr.acr_id
}

output "keyvault_uri" {
  description = "URI of the Key Vault"
  value       = module.keyvault.keyvault_uri
}

output "keyvault_id" {
  description = "ID of the Key Vault"
  value       = module.keyvault.keyvault_id
}

output "application_insights_connection_string" {
  description = "Application Insights connection string"
  value       = module.monitoring.application_insights_connection_string
  sensitive   = true
}

output "application_insights_instrumentation_key" {
  description = "Application Insights instrumentation key"
  value       = module.monitoring.application_insights_instrumentation_key
  sensitive   = true
}

output "log_analytics_workspace_id" {
  description = "Log Analytics workspace ID"
  value       = module.monitoring.log_analytics_workspace_id
}

output "application_gateway_public_ip" {
  description = "Public IP address of Application Gateway"
  value       = var.enable_application_gateway ? module.application_gateway[0].public_ip_address : null
}

output "vnet_id" {
  description = "ID of the virtual network"
  value       = module.networking.vnet_id
}

output "aks_get_credentials_command" {
  description = "Command to configure kubectl"
  value       = "az aks get-credentials --resource-group ${azurerm_resource_group.main.name} --name ${module.aks.aks_cluster_name}"
}
