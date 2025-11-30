# =============================================================================
# PubSec Info Assistant - Terraform Variables
# =============================================================================

# -----------------------------------------------------------------------------
# General Configuration
# -----------------------------------------------------------------------------

variable "environment" {
  description = "Environment name (dev, staging, production)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "Environment must be dev, staging, or production."
  }
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "eastus"
}

variable "cost_center" {
  description = "Cost center for resource tagging"
  type        = string
  default     = "IT-Security"
}

variable "owner" {
  description = "Owner email for resource tagging"
  type        = string
}

variable "tags" {
  description = "Additional tags for resources"
  type        = map(string)
  default     = {}
}

# -----------------------------------------------------------------------------
# Networking Configuration
# -----------------------------------------------------------------------------

variable "vnet_address_space" {
  description = "Address space for virtual network"
  type        = list(string)
  default     = ["10.0.0.0/16"]
}

variable "enable_ddos_protection" {
  description = "Enable DDoS protection standard"
  type        = bool
  default     = false
}

variable "enable_private_link" {
  description = "Enable private link for services"
  type        = bool
  default     = true
}

# -----------------------------------------------------------------------------
# Azure Container Registry (ACR)
# -----------------------------------------------------------------------------

variable "acr_sku" {
  description = "SKU for Azure Container Registry"
  type        = string
  default     = "Premium"
  validation {
    condition     = contains(["Basic", "Standard", "Premium"], var.acr_sku)
    error_message = "ACR SKU must be Basic, Standard, or Premium."
  }
}

variable "acr_public_network_access" {
  description = "Enable public network access for ACR"
  type        = bool
  default     = false
}

variable "acr_retention_days" {
  description = "Retention days for untagged manifests"
  type        = number
  default     = 7
}

variable "acr_geo_replication_locations" {
  description = "Locations for ACR geo-replication"
  type        = list(string)
  default     = []
}

# -----------------------------------------------------------------------------
# Azure Kubernetes Service (AKS)
# -----------------------------------------------------------------------------

variable "aks_kubernetes_version" {
  description = "Kubernetes version for AKS cluster"
  type        = string
  default     = "1.28.3"
}

variable "aks_automatic_channel_upgrade" {
  description = "AKS automatic channel upgrade"
  type        = string
  default     = "stable"
  validation {
    condition     = contains(["none", "patch", "stable", "rapid"], var.aks_automatic_channel_upgrade)
    error_message = "Must be none, patch, stable, or rapid."
  }
}

variable "aks_sku_tier" {
  description = "AKS SKU tier (Free, Standard, Premium)"
  type        = string
  default     = "Standard"
  validation {
    condition     = contains(["Free", "Standard", "Premium"], var.aks_sku_tier)
    error_message = "Must be Free, Standard, or Premium."
  }
}

variable "aks_dns_service_ip" {
  description = "DNS service IP for AKS"
  type        = string
  default     = "10.0.4.10"
}

variable "aks_service_cidr" {
  description = "Service CIDR for AKS"
  type        = string
  default     = "10.0.4.0/24"
}

variable "aks_docker_bridge_cidr" {
  description = "Docker bridge CIDR for AKS"
  type        = string
  default     = "172.17.0.1/16"
}

# System Node Pool
variable "aks_system_node_pool_vm_size" {
  description = "VM size for system node pool"
  type        = string
  default     = "Standard_D4s_v5"
}

variable "aks_system_node_pool_node_count" {
  description = "Initial node count for system pool"
  type        = number
  default     = 3
}

variable "aks_system_node_pool_min_count" {
  description = "Minimum node count for system pool"
  type        = number
  default     = 3
}

variable "aks_system_node_pool_max_count" {
  description = "Maximum node count for system pool"
  type        = number
  default     = 10
}

# User Node Pool
variable "aks_user_node_pool_vm_size" {
  description = "VM size for user node pool"
  type        = string
  default     = "Standard_D8s_v5"
}

variable "aks_user_node_pool_node_count" {
  description = "Initial node count for user pool"
  type        = number
  default     = 3
}

variable "aks_user_node_pool_min_count" {
  description = "Minimum node count for user pool"
  type        = number
  default     = 3
}

variable "aks_user_node_pool_max_count" {
  description = "Maximum node count for user pool"
  type        = number
  default     = 20
}

variable "aks_enable_private_cluster" {
  description = "Enable private AKS cluster"
  type        = bool
  default     = true
}

variable "enable_azure_defender" {
  description = "Enable Azure Defender for AKS"
  type        = bool
  default     = true
}

# -----------------------------------------------------------------------------
# Azure Key Vault
# -----------------------------------------------------------------------------

variable "keyvault_sku" {
  description = "SKU for Azure Key Vault"
  type        = string
  default     = "premium"
  validation {
    condition     = contains(["standard", "premium"], var.keyvault_sku)
    error_message = "Must be standard or premium."
  }
}

variable "keyvault_public_network_access" {
  description = "Enable public network access for Key Vault"
  type        = bool
  default     = false
}

# -----------------------------------------------------------------------------
# Application Secrets
# -----------------------------------------------------------------------------

variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  sensitive   = true
}

# -----------------------------------------------------------------------------
# Monitoring Configuration
# -----------------------------------------------------------------------------

variable "log_retention_days" {
  description = "Log retention days in Log Analytics"
  type        = number
  default     = 90
}

variable "appinsights_sampling_percentage" {
  description = "Application Insights sampling percentage"
  type        = number
  default     = 10
  validation {
    condition     = var.appinsights_sampling_percentage >= 0 && var.appinsights_sampling_percentage <= 100
    error_message = "Must be between 0 and 100."
  }
}

variable "enable_monitoring_alerts" {
  description = "Enable monitoring alerts"
  type        = bool
  default     = true
}

variable "alert_email_addresses" {
  description = "Email addresses for alerts"
  type        = list(string)
  default     = []
}

variable "alert_webhook_urls" {
  description = "Webhook URLs for alerts"
  type        = list(string)
  default     = []
}

# -----------------------------------------------------------------------------
# Application Gateway
# -----------------------------------------------------------------------------

variable "enable_application_gateway" {
  description = "Enable Application Gateway"
  type        = bool
  default     = true
}

variable "appgw_sku_name" {
  description = "Application Gateway SKU name"
  type        = string
  default     = "WAF_v2"
}

variable "appgw_sku_tier" {
  description = "Application Gateway SKU tier"
  type        = string
  default     = "WAF_v2"
}

variable "appgw_capacity" {
  description = "Application Gateway capacity (if not autoscaling)"
  type        = number
  default     = 2
}

variable "appgw_enable_autoscaling" {
  description = "Enable Application Gateway autoscaling"
  type        = bool
  default     = true
}

variable "appgw_min_capacity" {
  description = "Minimum capacity for autoscaling"
  type        = number
  default     = 2
}

variable "appgw_max_capacity" {
  description = "Maximum capacity for autoscaling"
  type        = number
  default     = 10
}

variable "appgw_enable_waf" {
  description = "Enable WAF on Application Gateway"
  type        = bool
  default     = true
}

variable "appgw_waf_mode" {
  description = "WAF mode (Detection or Prevention)"
  type        = string
  default     = "Prevention"
  validation {
    condition     = contains(["Detection", "Prevention"], var.appgw_waf_mode)
    error_message = "Must be Detection or Prevention."
  }
}

variable "ssl_certificate_data" {
  description = "Base64-encoded SSL certificate data"
  type        = string
  default     = ""
  sensitive   = true
}

variable "ssl_certificate_password" {
  description = "SSL certificate password"
  type        = string
  default     = ""
  sensitive   = true
}
