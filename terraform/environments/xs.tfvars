# =============================================================================
# T-Shirt Size: XS (Demo/POC)
# =============================================================================
# Purpose: Proof of concept, demos, testing, small pilots
# Users: 1-10
# Monthly Cost: $150-300
# Setup Time: 20 minutes
# SLA: 99.5% (best effort)
# =============================================================================

# -----------------------------------------------------------------------------
# General Configuration
# -----------------------------------------------------------------------------

environment = "demo"
location    = "eastus"
cost_center = "IT-Innovation"
owner       = "demo@example.com"

tags = {
  Size        = "XS"
  Purpose     = "Demo"
  CostCenter  = "IT-Innovation"
  AutoShutoff = "true"  # Enable cost-saving auto-shutdown
}

# -----------------------------------------------------------------------------
# Networking Configuration
# -----------------------------------------------------------------------------

vnet_address_space     = ["10.0.0.0/16"]
enable_ddos_protection = false  # Not needed for demo
enable_private_link    = false  # Public endpoints OK for demo

# -----------------------------------------------------------------------------
# Azure Container Registry (ACR)
# -----------------------------------------------------------------------------

acr_sku                       = "Basic"  # Minimal cost
acr_public_network_access     = true     # Simplified access
acr_retention_days            = 7        # Minimal retention
acr_geo_replication_locations = []       # No geo-replication

# -----------------------------------------------------------------------------
# Azure Kubernetes Service (AKS)
# -----------------------------------------------------------------------------

aks_kubernetes_version        = "1.33.5"
aks_automatic_channel_upgrade = "stable"
aks_sku_tier                  = "Free"  # No SLA but cost-effective for demo

# Network configuration
aks_dns_service_ip     = "10.2.0.10"
aks_service_cidr       = "10.2.0.0/16"
aks_docker_bridge_cidr = "172.17.0.1/16"

# System Node Pool (runs all workloads in XS size)
aks_system_node_pool_vm_size    = "Standard_B4ms"  # 4 vCPU, 16GB RAM - Cost-effective
aks_system_node_pool_node_count = 1                # Single node
aks_system_node_pool_min_count  = 1                # No auto-scaling
aks_system_node_pool_max_count  = 1                # Fixed capacity

# User Node Pool - DISABLED for XS (workloads run on system pool)
aks_user_node_pool_vm_size    = "Standard_B4ms"
aks_user_node_pool_node_count = 0  # Disabled
aks_user_node_pool_min_count  = 0  # Disabled
aks_user_node_pool_max_count  = 0  # Disabled

# Security features (minimal for demo)
aks_enable_private_cluster = false  # Public cluster for easy access
enable_azure_defender      = false  # Not needed for demo

# -----------------------------------------------------------------------------
# Azure Key Vault
# -----------------------------------------------------------------------------

keyvault_sku                  = "standard"  # Basic tier
keyvault_public_network_access = true       # Simplified access

# -----------------------------------------------------------------------------
# Monitoring Configuration
# -----------------------------------------------------------------------------

log_retention_days             = 30   # Minimal retention
appinsights_sampling_percentage = 50  # Higher sampling to reduce costs
enable_monitoring_alerts       = false  # No alerts for demo

alert_email_addresses = []
alert_webhook_urls    = []

# -----------------------------------------------------------------------------
# Application Gateway
# -----------------------------------------------------------------------------

enable_application_gateway = false  # Use LoadBalancer instead to save costs

appgw_sku_name          = "Standard_v2"  # If enabled later
appgw_sku_tier          = "Standard_v2"
appgw_capacity          = 1
appgw_enable_autoscaling = false
appgw_min_capacity      = 1
appgw_max_capacity      = 2
appgw_enable_waf        = false  # No WAF needed for demo
appgw_waf_mode          = "Detection"

# -----------------------------------------------------------------------------
# Application Secrets
# -----------------------------------------------------------------------------

# IMPORTANT: Set via environment variable or Azure Key Vault reference
# export TF_VAR_openai_api_key="sk-your-key-here"
openai_api_key = ""  # Set via TF_VAR_openai_api_key environment variable

# -----------------------------------------------------------------------------
# Cost Optimization Notes
# -----------------------------------------------------------------------------

# Expected Monthly Costs:
# - AKS (1x B4ms):        ~$120
# - ACR Basic:            $5
# - Key Vault Standard:   $5
# - VNet:                 $10
# - Log Analytics (5GB):  $10
# - Public IP:            $5
# Total:                  ~$155/month
#
# Additional Savings:
# - Stop AKS cluster outside demo hours: Reduces to ~$50/month
#   az aks stop --resource-group <RG> --name <AKS>
#   az aks start --resource-group <RG> --name <AKS>
#
# - Use deallocate for long periods:
#   terraform destroy (when not needed)
#   terraform apply (when needed again)
