# =============================================================================
# Staging Environment Configuration
# =============================================================================

environment = "staging"
location    = "eastus"
owner       = "devops@example.com"
cost_center = "IT-Staging"

# Networking
vnet_address_space     = ["10.1.0.0/16"]
enable_ddos_protection = false
enable_private_link    = true

# ACR
acr_sku                       = "Premium"
acr_public_network_access     = false
acr_retention_days            = 14
acr_geo_replication_locations = []

# AKS
aks_kubernetes_version        = "1.33.5"
aks_automatic_channel_upgrade = "stable"
aks_sku_tier                  = "Standard"
aks_dns_service_ip            = "10.3.0.10"
aks_service_cidr              = "10.3.0.0/16"
aks_docker_bridge_cidr        = "172.17.0.1/16"

# System node pool
aks_system_node_pool_vm_size    = "Standard_D4s_v5"
aks_system_node_pool_node_count = 2
aks_system_node_pool_min_count  = 2
aks_system_node_pool_max_count  = 5

# User node pool
aks_user_node_pool_vm_size    = "Standard_D8s_v5"
aks_user_node_pool_node_count = 2
aks_user_node_pool_min_count  = 2
aks_user_node_pool_max_count  = 10

aks_enable_private_cluster = true
enable_azure_defender      = true

# Key Vault
keyvault_sku                   = "premium"
keyvault_public_network_access = false

# Monitoring
log_retention_days              = 60
appinsights_sampling_percentage = 50
enable_monitoring_alerts        = true
alert_email_addresses           = ["devops@example.com", "staging-alerts@example.com"]
alert_webhook_urls              = []

# Application Gateway
enable_application_gateway = true
appgw_sku_name             = "WAF_v2"
appgw_sku_tier             = "WAF_v2"
appgw_capacity             = 2
appgw_enable_autoscaling   = true
appgw_min_capacity         = 2
appgw_max_capacity         = 5
appgw_enable_waf           = true
appgw_waf_mode             = "Detection"

# Tags
tags = {
  Department = "Engineering"
  Purpose    = "Staging"
}
