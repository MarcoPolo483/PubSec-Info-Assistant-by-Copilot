# =============================================================================
# T-Shirt Size: M (Production)
# =============================================================================
# Purpose: Production workloads, business-critical applications
# Users: 50-500
# Monthly Cost: $1,500-2,500 (without DDoS), $5,000+ (with DDoS)
# Setup Time: 45 minutes
# SLA: 99.95% (with Availability Zones)
# =============================================================================

# -----------------------------------------------------------------------------
# General Configuration
# -----------------------------------------------------------------------------

environment = "production"
location    = "eastus"
cost_center = "IT-Operations"
owner       = "sre@example.com"

tags = {
  Size            = "M"
  Purpose         = "Production"
  CostCenter      = "IT-Operations"
  Backup          = "continuous"
  DisasterRecovery = "enabled"
  Compliance      = "FedRAMP-High"
}

# -----------------------------------------------------------------------------
# Networking Configuration
# -----------------------------------------------------------------------------

vnet_address_space     = ["10.0.0.0/16"]
enable_ddos_protection = false  # Set to true for internet-facing prod ($3000/month)
enable_private_link    = true   # Private endpoints for security

# -----------------------------------------------------------------------------
# Azure Container Registry (ACR)
# -----------------------------------------------------------------------------

acr_sku                       = "Premium"  # Required for geo-replication
acr_public_network_access     = false      # Private endpoint only
acr_retention_days            = 30         # 1-month retention
acr_geo_replication_locations = ["westus2"]  # DR region

# -----------------------------------------------------------------------------
# Azure Kubernetes Service (AKS)
# -----------------------------------------------------------------------------

aks_kubernetes_version        = "1.28.3"
aks_automatic_channel_upgrade = "stable"
aks_sku_tier                  = "Standard"  # 99.95% SLA with Availability Zones

# Network configuration
aks_dns_service_ip     = "10.0.4.10"
aks_service_cidr       = "10.0.4.0/24"
aks_docker_bridge_cidr = "172.17.0.1/16"

# System Node Pool (Kubernetes system components)
# Distributed across Availability Zones for high availability
aks_system_node_pool_vm_size    = "Standard_D4s_v5"  # 4 vCPU, 16GB RAM
aks_system_node_pool_node_count = 3                  # 1 per zone
aks_system_node_pool_min_count  = 3                  # Fixed (no auto-scaling)
aks_system_node_pool_max_count  = 3

# User Node Pool (Application workloads)
# Auto-scales based on demand
aks_user_node_pool_vm_size    = "Standard_D8s_v5"  # 8 vCPU, 32GB RAM
aks_user_node_pool_node_count = 5                  # Initial capacity
aks_user_node_pool_min_count  = 5                  # Minimum for HA
aks_user_node_pool_max_count  = 15                 # Scale up during peak load

# Security features
aks_enable_private_cluster = true  # Private API server
enable_azure_defender      = true  # Container security scanning

# -----------------------------------------------------------------------------
# Azure Key Vault
# -----------------------------------------------------------------------------

keyvault_sku                   = "premium"  # HSM-backed for production
keyvault_public_network_access = false      # Private endpoint only

# -----------------------------------------------------------------------------
# Monitoring Configuration
# -----------------------------------------------------------------------------

log_retention_days              = 90   # 3-month retention for compliance
appinsights_sampling_percentage = 10   # Lower sampling for better visibility
enable_monitoring_alerts        = true  # Comprehensive alerts

# Alert notifications
alert_email_addresses = [
  "sre@example.com",
  "devops@example.com",
  "oncall@example.com"
]

# Webhook for PagerDuty/Teams/Slack
alert_webhook_urls = [
  # "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
  # "https://events.pagerduty.com/integration/YOUR_KEY/enqueue"
]

# -----------------------------------------------------------------------------
# Application Gateway
# -----------------------------------------------------------------------------

enable_application_gateway = true

# WAF v2 with auto-scaling
appgw_sku_name           = "WAF_v2"
appgw_sku_tier           = "WAF_v2"
appgw_capacity           = 2  # Not used when auto-scaling enabled
appgw_enable_autoscaling = true
appgw_min_capacity       = 2  # Minimum for HA
appgw_max_capacity       = 10 # Scale up during peak
appgw_enable_waf         = true
appgw_waf_mode           = "Prevention"  # Block threats (not just detect)

# -----------------------------------------------------------------------------
# Application Secrets
# -----------------------------------------------------------------------------

# IMPORTANT: Set via environment variable or Azure Key Vault reference
# export TF_VAR_openai_api_key="sk-your-key-here"
openai_api_key = ""  # Set via TF_VAR_openai_api_key environment variable

# SSL Certificate (required for Application Gateway)
# IMPORTANT: Set via environment variable
# export TF_VAR_ssl_certificate_data="base64-encoded-pfx-cert"
# export TF_VAR_ssl_certificate_password="your-cert-password"
ssl_certificate_data     = ""  # Set via TF_VAR_ssl_certificate_data
ssl_certificate_password = ""  # Set via TF_VAR_ssl_certificate_password

# -----------------------------------------------------------------------------
# Performance & Capacity Notes
# -----------------------------------------------------------------------------

# Expected Performance:
# - Concurrent Users: 50-500
# - Documents: Up to 100,000
# - Embedding Vectors: Up to 50 million
# - Query Response Time: 0.5-2 seconds
# - Ingestion Rate: 200 docs/min
# - Availability: 99.95% SLA (with Availability Zones)
# - RPO/RTO: 1 hour / 2 hours

# Expected Monthly Costs (without DDoS Protection):
# - AKS System (3x D4s_v5):       ~$630
# - AKS User (5-15x D8s_v5):      $1,400-$4,200
# - ACR Premium (2 regions):      $100
# - Application Gateway WAF_v2:   $400-$800
# - Key Vault Premium:            $15
# - VNet:                         $20
# - Log Analytics (100GB):        $250
# - Azure Defender:               $15
# - Public IPs (2):               $10
# Total:                          $2,840-$6,040/month
# Average:                        ~$2,000/month

# With DDoS Protection Standard (+$3,000/month):
# Total:                          $5,840-$9,040/month
# Average:                        ~$5,000/month

# High Availability Features:
# - Availability Zones (3 zones)
# - Geo-redundant ACR (disaster recovery)
# - Application Gateway with health probes
# - Azure Monitor with comprehensive alerts
# - Automated backups and snapshots

# Security Features:
# - Private cluster (API server not public)
# - Private endpoints (ACR, Key Vault)
# - WAF Prevention mode (OWASP 3.2)
# - Azure Defender for containers
# - Network policies and NSGs
# - HSM-backed Key Vault
# - 90-day audit logs
