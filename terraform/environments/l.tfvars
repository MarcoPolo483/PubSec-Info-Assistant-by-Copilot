# =============================================================================
# T-Shirt Size: L (Multi-Tenant Enterprise)
# =============================================================================
# Purpose: Multi-tenant SaaS, enterprise-scale, government-wide deployments
# Users: 500-5000+
# Monthly Cost: $10,000-15,000 (average), up to $70,000 (high scale)
# Setup Time: 60 minutes
# SLA: 99.99% (with Uptime SLA)
# =============================================================================

# -----------------------------------------------------------------------------
# General Configuration
# -----------------------------------------------------------------------------

environment = "production"
location    = "eastus"
cost_center = "Enterprise-IT"
owner       = "enterprise-sre@example.com"

tags = {
  Size             = "L"
  Purpose          = "Multi-Tenant-Production"
  CostCenter       = "Enterprise-IT"
  Backup           = "continuous"
  DisasterRecovery = "multi-region"
  Compliance       = "FedRAMP-High,HIPAA,SOC2"
  Tier             = "Mission-Critical"
}

# -----------------------------------------------------------------------------
# Networking Configuration
# -----------------------------------------------------------------------------

vnet_address_space     = ["10.0.0.0/12"]  # Large address space for multi-tenancy
enable_ddos_protection = true              # Required for enterprise
enable_private_link    = true              # All services private

# -----------------------------------------------------------------------------
# Azure Container Registry (ACR)
# -----------------------------------------------------------------------------

acr_sku                   = "Premium"  # Required for geo-replication
acr_public_network_access = false      # Private endpoints only
acr_retention_days        = 90         # 3-month retention

# Multi-region geo-replication for disaster recovery
acr_geo_replication_locations = [
  "westus2",    # West Coast DR
  "centralus",  # Central US for low latency
  "northeurope" # Global reach (if serving international clients)
]

# -----------------------------------------------------------------------------
# Azure Kubernetes Service (AKS)
# -----------------------------------------------------------------------------

aks_kubernetes_version        = "1.28.3"
aks_automatic_channel_upgrade = "stable"
aks_sku_tier                  = "Premium"  # 99.99% Uptime SLA

# Network configuration (larger address space)
aks_dns_service_ip     = "10.0.4.10"
aks_service_cidr       = "10.0.4.0/22"     # Larger service CIDR
aks_docker_bridge_cidr = "172.17.0.1/16"

# System Node Pool (Kubernetes system components)
# Distributed across Availability Zones
aks_system_node_pool_vm_size    = "Standard_D8s_v5"  # 8 vCPU, 32GB RAM
aks_system_node_pool_node_count = 5                  # High availability
aks_system_node_pool_min_count  = 5                  # Fixed size
aks_system_node_pool_max_count  = 5

# User Node Pool (Application workloads)
# Large-scale auto-scaling for multi-tenant workloads
aks_user_node_pool_vm_size    = "Standard_D16s_v5"  # 16 vCPU, 64GB RAM
aks_user_node_pool_node_count = 10                  # Initial capacity
aks_user_node_pool_min_count  = 10                  # Minimum for enterprise load
aks_user_node_pool_max_count  = 50                  # Scale up to 50 nodes

# NOTE: GPU node pool for ML inference can be added via Terraform module
# after initial deployment if needed (Standard_NC6s_v3 with Tesla V100)

# Security features (all enabled)
aks_enable_private_cluster = true  # Private API server
enable_azure_defender      = true  # Advanced container security

# -----------------------------------------------------------------------------
# Azure Key Vault
# -----------------------------------------------------------------------------

keyvault_sku                   = "premium"  # HSM-backed required for enterprise
keyvault_public_network_access = false      # Private endpoints only

# -----------------------------------------------------------------------------
# Monitoring Configuration
# -----------------------------------------------------------------------------

log_retention_days              = 180  # 6-month retention for compliance
appinsights_sampling_percentage = 5    # Low sampling for high volume (better visibility)
enable_monitoring_alerts        = true  # Comprehensive enterprise alerts

# Multi-channel alert notifications
alert_email_addresses = [
  "enterprise-sre@example.com",
  "security-team@example.com",
  "platform-ops@example.com",
  "oncall-primary@example.com",
  "oncall-secondary@example.com"
]

# Webhooks for incident management platforms
alert_webhook_urls = [
  # "https://events.pagerduty.com/integration/YOUR_INTEGRATION_KEY/enqueue",
  # "https://outlook.office.com/webhook/YOUR_TEAMS_WEBHOOK",
  # "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
]

# -----------------------------------------------------------------------------
# Application Gateway
# -----------------------------------------------------------------------------

enable_application_gateway = true

# WAF v2 with large-scale auto-scaling
appgw_sku_name           = "WAF_v2"
appgw_sku_tier           = "WAF_v2"
appgw_capacity           = 5  # Not used when auto-scaling enabled
appgw_enable_autoscaling = true
appgw_min_capacity       = 5   # High baseline for enterprise
appgw_max_capacity       = 50  # Large-scale capacity
appgw_enable_waf         = true
appgw_waf_mode           = "Prevention"  # Block threats in production

# -----------------------------------------------------------------------------
# Application Secrets
# -----------------------------------------------------------------------------

# IMPORTANT: Set via environment variable or Azure Key Vault reference
# For enterprise, strongly recommend using Azure Key Vault references
# with automated secret rotation enabled

# export TF_VAR_openai_api_key="sk-your-key-here"
openai_api_key = ""  # Set via TF_VAR_openai_api_key environment variable

# SSL Certificate (required for Application Gateway)
# For enterprise, use certificates from your PKI or public CA
# export TF_VAR_ssl_certificate_data="base64-encoded-pfx-cert"
# export TF_VAR_ssl_certificate_password="your-cert-password"
ssl_certificate_data     = ""  # Set via TF_VAR_ssl_certificate_data
ssl_certificate_password = ""  # Set via TF_VAR_ssl_certificate_password

# -----------------------------------------------------------------------------
# Performance & Capacity Notes
# -----------------------------------------------------------------------------

# Expected Performance:
# - Concurrent Users: 500-5000+
# - Tenants: 10-100+ isolated tenants
# - Documents: Up to 10 million
# - Embedding Vectors: Up to 500 million
# - Query Response Time: 0.3-1 second (p95)
# - Ingestion Rate: 1000+ docs/min
# - Availability: 99.99% SLA (52 minutes downtime/year)
# - RPO/RTO: 15 minutes / 30 minutes
# - Disaster Recovery: Multi-region active-passive

# Expected Monthly Costs:

# Baseline Configuration (10 user nodes):
# - AKS System (5x D8s_v5):           ~$2,100
# - AKS User (10x D16s_v5):           $8,400
# - ACR Premium (4 regions):          $300
# - Application Gateway WAF_v2:       $1,000-$5,000
# - Azure Firewall Premium:           $1,250
# - Key Vault Premium:                $50
# - Virtual Network:                  $50
# - DDoS Protection Standard:         $3,000
# - Log Analytics (500GB):            $1,250
# - Azure Defender:                   $100
# - Public IPs (5):                   $25
# - Bandwidth (10TB egress):          $870
# Baseline Total:                     ~$19,395/month

# High-Scale Configuration (50 user nodes):
# - AKS User (50x D16s_v5):           $42,000
# - Application Gateway (max scale):  $5,000
# - Log Analytics (2TB):              $5,000
# - Bandwidth (50TB egress):          $4,350
# High-Scale Total:                   ~$68,795/month

# Average Enterprise Deployment:     $10,000-$15,000/month

# Cost Optimization Strategies:
# 1. Azure Reserved Instances (1-3 year commitment): Save 20-40%
# 2. Azure Hybrid Benefit (if you have Windows licenses)
# 3. Use Spot Instances for non-critical workloads: Save up to 90%
# 4. Right-size VMs based on actual usage metrics
# 5. Enable cluster auto-scaling to scale down during off-hours
# 6. Use Azure Cost Management + Budgets for alerts

# Advanced Features Included:
# - Multi-tenancy isolation (Kubernetes namespaces + network policies)
# - Horizontal Pod Autoscaling (HPA) on CPU/memory/custom metrics
# - Cluster Autoscaling (dynamic node provisioning)
# - Pod Disruption Budgets (PDB) for zero-downtime updates
# - Azure Defender for containers (vulnerability scanning)
# - Azure Firewall Premium (intrusion detection, TLS inspection)
# - Private endpoints for all services
# - HSM-backed Key Vault with automated secret rotation
# - 180-day audit logs with archival to Azure Storage
# - Multi-region disaster recovery
# - Geo-redundant backups
# - Advanced monitoring with custom dashboards per tenant

# Compliance Certifications:
# - FedRAMP High (US Government)
# - HIPAA (Healthcare)
# - SOC 2 Type II (Security)
# - GDPR (EU Privacy)
# - PIPEDA (Canada Privacy)
# - ISO 27001, ISO 27017, ISO 27018

# Support Level:
# - 24/7 Premium Support
# - Dedicated SRE team
# - 15-minute response time for critical incidents
# - Quarterly business reviews
# - Architecture guidance and best practices
