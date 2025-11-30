# =============================================================================
# Development Environment Configuration
# =============================================================================

environment = "dev"
location    = "eastus"
owner       = "devops@example.com"
cost_center = "IT-Development"

# Networking
vnet_address_space     = ["10.0.0.0/16"]
enable_ddos_protection = false
enable_private_link    = true

# ACR
acr_sku                       = "Premium"
acr_public_network_access     = false
acr_retention_days            = 7
acr_geo_replication_locations = []

# AKS
aks_kubernetes_version        = "1.28.3"
aks_automatic_channel_upgrade = "stable"
aks_sku_tier                  = "Standard"
aks_dns_service_ip            = "10.0.4.10"
aks_service_cidr              = "10.0.4.0/24"
aks_docker_bridge_cidr        = "172.17.0.1/16"

# System node pool (smaller for dev)
aks_system_node_pool_vm_size    = "Standard_D2s_v5"
aks_system_node_pool_node_count = 1
aks_system_node_pool_min_count  = 1
aks_system_node_pool_max_count  = 3

# User node pool (smaller for dev)
aks_user_node_pool_vm_size    = "Standard_D4s_v5"
aks_user_node_pool_node_count = 1
aks_user_node_pool_min_count  = 1
aks_user_node_pool_max_count  = 5

aks_enable_private_cluster = false
enable_azure_defender      = false

# Key Vault
keyvault_sku                   = "standard"
keyvault_public_network_access = true

# Monitoring
log_retention_days              = 30
appinsights_sampling_percentage = 100
enable_monitoring_alerts        = true
alert_email_addresses           = ["devops@example.com"]
alert_webhook_urls              = []

# Application Gateway
enable_application_gateway = false
appgw_sku_name             = "Standard_v2"
appgw_sku_tier             = "Standard_v2"
appgw_capacity             = 1
appgw_enable_autoscaling   = false
appgw_min_capacity         = 1
appgw_max_capacity         = 2
appgw_enable_waf           = false
appgw_waf_mode             = "Detection"

# Tags
tags = {
  Department = "Engineering"
  Purpose    = "Development"
}
