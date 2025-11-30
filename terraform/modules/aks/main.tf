# =============================================================================
# AKS Module - Azure Kubernetes Service
# =============================================================================

terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.80"
    }
  }
}

# =============================================================================
# Variables
# =============================================================================

variable "resource_group_name" {
  description = "Resource group name"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
}

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vnet_id" {
  description = "Virtual network ID"
  type        = string
}

variable "subnet_id" {
  description = "Subnet ID for AKS"
  type        = string
}

variable "kubernetes_version" {
  description = "Kubernetes version"
  type        = string
}

variable "automatic_channel_upgrade" {
  description = "Automatic channel upgrade"
  type        = string
  default     = "stable"
}

variable "sku_tier" {
  description = "AKS SKU tier"
  type        = string
  default     = "Standard"
}

variable "dns_service_ip" {
  description = "DNS service IP"
  type        = string
}

variable "docker_bridge_cidr" {
  description = "Docker bridge CIDR"
  type        = string
}

variable "service_cidr" {
  description = "Service CIDR"
  type        = string
}

variable "system_node_pool_vm_size" {
  description = "System node pool VM size"
  type        = string
}

variable "system_node_pool_node_count" {
  description = "System node pool node count"
  type        = number
}

variable "system_node_pool_min_count" {
  description = "System node pool minimum count"
  type        = number
}

variable "system_node_pool_max_count" {
  description = "System node pool maximum count"
  type        = number
}

variable "user_node_pool_vm_size" {
  description = "User node pool VM size"
  type        = string
}

variable "user_node_pool_node_count" {
  description = "User node pool node count"
  type        = number
}

variable "user_node_pool_min_count" {
  description = "User node pool minimum count"
  type        = number
}

variable "user_node_pool_max_count" {
  description = "User node pool maximum count"
  type        = number
}

variable "enable_azure_policy" {
  description = "Enable Azure Policy"
  type        = bool
  default     = true
}

variable "enable_azure_defender" {
  description = "Enable Azure Defender"
  type        = bool
  default     = true
}

variable "enable_pod_security_policy" {
  description = "Enable pod security policy"
  type        = bool
  default     = true
}

variable "enable_secret_rotation" {
  description = "Enable secret rotation"
  type        = bool
  default     = true
}

variable "enable_workload_identity" {
  description = "Enable workload identity"
  type        = bool
  default     = true
}

variable "log_analytics_workspace_id" {
  description = "Log Analytics workspace ID"
  type        = string
}

variable "acr_id" {
  description = "Azure Container Registry ID"
  type        = string
}

variable "enable_private_cluster" {
  description = "Enable private cluster"
  type        = bool
  default     = true
}

variable "private_dns_zone_id" {
  description = "Private DNS zone ID"
  type        = string
  default     = null
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}

# =============================================================================
# AKS Cluster
# =============================================================================

resource "azurerm_kubernetes_cluster" "aks" {
  name                = "${var.project_name}-${var.environment}-aks"
  location            = var.location
  resource_group_name = var.resource_group_name
  dns_prefix          = "${var.project_name}-${var.environment}"
  kubernetes_version  = var.kubernetes_version
  sku_tier            = var.sku_tier

  automatic_channel_upgrade = var.automatic_channel_upgrade

  # System node pool
  default_node_pool {
    name                = "system"
    node_count          = var.system_node_pool_node_count
    vm_size             = var.system_node_pool_vm_size
    vnet_subnet_id      = var.subnet_id
    enable_auto_scaling = true
    min_count           = var.system_node_pool_min_count
    max_count           = var.system_node_pool_max_count
    max_pods            = 110
    os_disk_size_gb     = 128
    os_disk_type        = "Managed"
    type                = "VirtualMachineScaleSets"

    node_labels = {
      "role" = "system"
    }

    upgrade_settings {
      max_surge = "33%"
    }
  }

  # Identity
  identity {
    type = "SystemAssigned"
  }

  # Network profile
  network_profile {
    network_plugin     = "azure"
    network_policy     = "azure"
    dns_service_ip     = var.dns_service_ip
    docker_bridge_cidr = var.docker_bridge_cidr
    service_cidr       = var.service_cidr
    load_balancer_sku  = "standard"
  }

  # Azure Monitor integration
  oms_agent {
    log_analytics_workspace_id = var.log_analytics_workspace_id
  }

  # Azure Defender
  dynamic "microsoft_defender" {
    for_each = var.enable_azure_defender ? [1] : []
    content {
      log_analytics_workspace_id = var.log_analytics_workspace_id
    }
  }

  # Azure Policy
  azure_policy_enabled = var.enable_azure_policy

  # Workload Identity
  workload_identity_enabled = var.enable_workload_identity
  oidc_issuer_enabled       = var.enable_workload_identity

  # Secret rotation
  dynamic "key_vault_secrets_provider" {
    for_each = var.enable_secret_rotation ? [1] : []
    content {
      secret_rotation_enabled  = true
      secret_rotation_interval = "2m"
    }
  }

  # Private cluster
  private_cluster_enabled = var.enable_private_cluster
  private_dns_zone_id     = var.private_dns_zone_id

  # Maintenance window
  maintenance_window {
    allowed {
      day   = "Sunday"
      hours = [2, 3, 4]
    }
  }

  # Auto-scaler profile
  auto_scaler_profile {
    balance_similar_node_groups      = true
    expander                         = "random"
    max_graceful_termination_sec     = 600
    max_node_provisioning_time       = "15m"
    max_unready_nodes                = 3
    max_unready_percentage           = 45
    new_pod_scale_up_delay           = "0s"
    scale_down_delay_after_add       = "10m"
    scale_down_delay_after_delete    = "10s"
    scale_down_delay_after_failure   = "3m"
    scan_interval                    = "10s"
    scale_down_unneeded              = "10m"
    scale_down_unready               = "20m"
    scale_down_utilization_threshold = "0.5"
  }

  tags = var.tags

  lifecycle {
    ignore_changes = [
      default_node_pool[0].node_count
    ]
  }
}

# =============================================================================
# User Node Pool (Application Workloads)
# =============================================================================

resource "azurerm_kubernetes_cluster_node_pool" "user" {
  name                  = "user"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.aks.id
  vm_size               = var.user_node_pool_vm_size
  node_count            = var.user_node_pool_node_count
  vnet_subnet_id        = var.subnet_id

  enable_auto_scaling = true
  min_count           = var.user_node_pool_min_count
  max_count           = var.user_node_pool_max_count
  max_pods            = 110
  os_disk_size_gb     = 256
  os_disk_type        = "Managed"
  os_type             = "Linux"

  node_labels = {
    "role"     = "user"
    "workload" = "application"
  }

  node_taints = []

  upgrade_settings {
    max_surge = "33%"
  }

  tags = var.tags

  lifecycle {
    ignore_changes = [
      node_count
    ]
  }
}

# =============================================================================
# ACR Integration
# =============================================================================

resource "azurerm_role_assignment" "aks_acr_pull" {
  principal_id                     = azurerm_kubernetes_cluster.aks.kubelet_identity[0].object_id
  role_definition_name             = "AcrPull"
  scope                            = var.acr_id
  skip_service_principal_aad_check = true
}

# =============================================================================
# Outputs
# =============================================================================

output "aks_cluster_name" {
  description = "AKS cluster name"
  value       = azurerm_kubernetes_cluster.aks.name
}

output "aks_cluster_id" {
  description = "AKS cluster ID"
  value       = azurerm_kubernetes_cluster.aks.id
}

output "aks_cluster_fqdn" {
  description = "AKS cluster FQDN"
  value       = azurerm_kubernetes_cluster.aks.fqdn
}

output "kubelet_identity_object_id" {
  description = "Kubelet identity object ID"
  value       = azurerm_kubernetes_cluster.aks.kubelet_identity[0].object_id
}

output "node_resource_group" {
  description = "Node resource group name"
  value       = azurerm_kubernetes_cluster.aks.node_resource_group
}

output "kube_config" {
  description = "Kubernetes configuration"
  value       = azurerm_kubernetes_cluster.aks.kube_config_raw
  sensitive   = true
}
