# =============================================================================
# T-Shirt Size: S (Development)
# =============================================================================
# Purpose: Development, staging, QA testing, small production workloads
# Users: 10-50
# Monthly Cost: $400-600
# Setup Time: 30 minutes
# SLA: 99.9%
# =============================================================================

# -----------------------------------------------------------------------------
# General Configuration
# -----------------------------------------------------------------------------

environment = "dev"
location    = "eastus"
cost_center = "IT-Development"
owner       = "devops@example.com"

tags = {
  Size       = "S"
  Purpose    = "Development"
  CostCenter = "IT-Development"
  Backup     = "daily"
}

# -----------------------------------------------------------------------------
# Networking Configuration
# -----------------------------------------------------------------------------

vnet_address_space     = ["10.0.0.0/16"]
enable_ddos_protection = false  # Not needed for dev
enable_private_link    = true   # Optional private endpoints

# -----------------------------------------------------------------------------
# Azure Container Registry (ACR)
# -----------------------------------------------------------------------------

acr_sku                       = "Standard"  # Better performance than Basic
acr_public_network_access     = true        # Can be set to false for private endpoint
acr_retention_days            = 14          # 2-week retention
acr_geo_replication_locations = []          # No geo-replication for dev

# -----------------------------------------------------------------------------
# Azure Kubernetes Service (AKS)
# -----------------------------------------------------------------------------

aks_kubernetes_version        = "1.28.3"
aks_automatic_channel_upgrade = "stable"
aks_sku_tier                  = "Standard"  # 99.9% SLA

# Network configuration
aks_dns_service_ip     = "10.0.4.10"
aks_service_cidr       = "10.0.4.0/24"
aks_docker_bridge_cidr = "172.17.0.1/16"

# System Node Pool (Kubernetes system components)
aks_system_node_pool_vm_size    = "Standard_D2s_v5"  # 2 vCPU, 8GB RAM
aks_system_node_pool_node_count = 2                  # High availability
aks_system_node_pool_min_count  = 2                  # Fixed size (no auto-scaling)
aks_system_node_pool_max_count  = 2

# User Node Pool (Application workloads)
aks_user_node_pool_vm_size    = "Standard_D4s_v5"  # 4 vCPU, 16GB RAM
aks_user_node_pool_node_count = 2                  # Initial capacity
aks_user_node_pool_min_count  = 2                  # Minimum for HA
aks_user_node_pool_max_count  = 5                  # Scale up during load testing

# Security features
aks_enable_private_cluster = false  # Can be enabled if needed
enable_azure_defender      = false  # Optional for dev

# -----------------------------------------------------------------------------
# Azure Key Vault
# -----------------------------------------------------------------------------

keyvault_sku                   = "standard"  # Standard tier sufficient for dev
keyvault_public_network_access = true        # Can be set to false for private endpoint

# -----------------------------------------------------------------------------
# Monitoring Configuration
# -----------------------------------------------------------------------------

log_retention_days              = 30   # 1-month retention
appinsights_sampling_percentage = 25   # Moderate sampling
enable_monitoring_alerts        = true  # Basic alerts enabled

# Email notifications for dev team
alert_email_addresses = [
  "devops@example.com",
  "sre-team@example.com"
]

# Optional webhook for Slack/Teams
alert_webhook_urls = []

# -----------------------------------------------------------------------------
# Application Gateway
# -----------------------------------------------------------------------------

# Application Gateway is optional for dev - use LoadBalancer to save costs
enable_application_gateway = false

# If enabled, use minimal configuration
appgw_sku_name           = "Standard_v2"
appgw_sku_tier           = "Standard_v2"
appgw_capacity           = 1
appgw_enable_autoscaling = false
appgw_min_capacity       = 1
appgw_max_capacity       = 3
appgw_enable_waf         = false  # WAF not needed for dev
appgw_waf_mode           = "Detection"

# -----------------------------------------------------------------------------
# Application Secrets
# -----------------------------------------------------------------------------

# IMPORTANT: Set via environment variable or Azure Key Vault reference
# export TF_VAR_openai_api_key="sk-your-key-here"
openai_api_key = ""  # Set via TF_VAR_openai_api_key environment variable

# -----------------------------------------------------------------------------
# Performance & Capacity Notes
# -----------------------------------------------------------------------------

# Expected Performance:
# - Concurrent Users: 10-50
# - Documents: Up to 10,000
# - Embedding Vectors: Up to 5 million
# - Query Response Time: 1-3 seconds
# - Ingestion Rate: 50 docs/min
# - Availability: 99.9% SLA

# Expected Monthly Costs:
# - AKS System (2x D2s_v5):       ~$140
# - AKS User (2-5x D4s_v5):       $280-$700
# - ACR Standard (100GB):         $20
# - Key Vault Standard:           $10
# - VNet:                         $15
# - Log Analytics (20GB):         $50
# - Public IP:                    $5
# Total:                          $520-$940/month
# Average:                        ~$600/month

# Cost Optimization Tips:
# - Use auto-scaling to scale down during off-hours
# - Stop/deallocate for weekends if not needed 24/7
# - Monitor actual resource usage and right-size VMs
