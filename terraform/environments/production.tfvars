# =============================================================================
# Production Environment Configuration
# =============================================================================

environment = "production"
location    = "eastus"
owner       = "sre@example.com"
cost_center = "IT-Production"

# Networking
vnet_address_space         = ["10.2.0.0/16"]
enable_ddos_protection     = true
enable_private_link        = true

# ACR
acr_sku                       = "Premium"
acr_public_network_access     = false
acr_retention_days            = 30
acr_geo_replication_locations = ["westus", "centralus"]

# AKS
aks_kubernetes_version        = "1.28.3"
aks_automatic_channel_upgrade = "stable"
aks_sku_tier                  = "Premium"
aks_dns_service_ip            = "10.2.4.10"
aks_service_cidr              = "10.2.4.0/24"
aks_docker_bridge_cidr        = "172.17.0.1/16"

# System node pool (production-grade)
aks_system_node_pool_vm_size    = "Standard_D4s_v5"
aks_system_node_pool_node_count = 3
aks_system_node_pool_min_count  = 3
aks_system_node_pool_max_count  = 10

# User node pool (production-grade)
aks_user_node_pool_vm_size    = "Standard_D8s_v5"
aks_user_node_pool_node_count = 5
aks_user_node_pool_min_count  = 3
aks_user_node_pool_max_count  = 20

aks_enable_private_cluster = true
enable_azure_defender      = true

# Key Vault
keyvault_sku                   = "premium"
keyvault_public_network_access = false

# Monitoring
log_retention_days              = 90
appinsights_sampling_percentage = 10
enable_monitoring_alerts        = true
alert_email_addresses           = ["sre@example.com", "oncall@example.com"]
alert_webhook_urls              = ["https://hooks.slack.com/services/YOUR/WEBHOOK/URL"]

# Application Gateway
enable_application_gateway = true
appgw_sku_name             = "WAF_v2"
appgw_sku_tier             = "WAF_v2"
appgw_capacity             = 3
appgw_enable_autoscaling   = true
appgw_min_capacity         = 3
appgw_max_capacity         = 10
appgw_enable_waf           = true
appgw_waf_mode             = "Prevention"

# Tags
tags = {
  Department  = "Engineering"
  Purpose     = "Production"
  Criticality = "High"
  Compliance  = "FedRAMP-High"
}
