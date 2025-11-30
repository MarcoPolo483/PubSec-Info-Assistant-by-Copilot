# =============================================================================
# Monitoring Module - Log Analytics & Application Insights
# =============================================================================

terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.80"
    }
  }
}

variable "resource_group_name" { type = string }
variable "location" { type = string }
variable "project_name" { type = string }
variable "environment" { type = string }
variable "log_retention_days" { type = number }
variable "application_type" { type = string }
variable "sampling_percentage" { type = number }
variable "enable_alerts" { type = bool }
variable "alert_email_addresses" { type = list(string) }
variable "alert_webhook_urls" { type = list(string) }
variable "aks_cluster_id" { type = string }
variable "tags" { type = map(string) }

resource "azurerm_log_analytics_workspace" "law" {
  name                = "${var.project_name}-${var.environment}-law"
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = "PerGB2018"
  retention_in_days   = var.log_retention_days
  tags                = var.tags
}

resource "azurerm_application_insights" "ai" {
  name                = "${var.project_name}-${var.environment}-ai"
  location            = var.location
  resource_group_name = var.resource_group_name
  workspace_id        = azurerm_log_analytics_workspace.law.id
  application_type    = var.application_type
  sampling_percentage = var.sampling_percentage
  tags                = var.tags
}

resource "azurerm_monitor_action_group" "main" {
  count               = var.enable_alerts ? 1 : 0
  name                = "${var.project_name}-${var.environment}-action-group"
  resource_group_name = var.resource_group_name
  short_name          = "pubsec-ag"

  dynamic "email_receiver" {
    for_each = var.alert_email_addresses
    content {
      name          = "email-${email_receiver.key}"
      email_address = email_receiver.value
    }
  }

  dynamic "webhook_receiver" {
    for_each = var.alert_webhook_urls
    content {
      name        = "webhook-${webhook_receiver.key}"
      service_uri = webhook_receiver.value
    }
  }

  tags = var.tags
}

resource "azurerm_monitor_metric_alert" "aks_cpu" {
  count               = var.enable_alerts ? 1 : 0
  name                = "${var.project_name}-${var.environment}-aks-cpu-alert"
  resource_group_name = var.resource_group_name
  scopes              = [var.aks_cluster_id]
  description         = "Alert when AKS CPU usage exceeds 80%"
  severity            = 2
  frequency           = "PT1M"
  window_size         = "PT5M"

  criteria {
    metric_namespace = "Microsoft.ContainerService/managedClusters"
    metric_name      = "node_cpu_usage_percentage"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = 80
  }

  action {
    action_group_id = azurerm_monitor_action_group.main[0].id
  }

  tags = var.tags
}

resource "azurerm_monitor_metric_alert" "aks_memory" {
  count               = var.enable_alerts ? 1 : 0
  name                = "${var.project_name}-${var.environment}-aks-memory-alert"
  resource_group_name = var.resource_group_name
  scopes              = [var.aks_cluster_id]
  description         = "Alert when AKS memory usage exceeds 85%"
  severity            = 2
  frequency           = "PT1M"
  window_size         = "PT5M"

  criteria {
    metric_namespace = "Microsoft.ContainerService/managedClusters"
    metric_name      = "node_memory_working_set_percentage"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = 85
  }

  action {
    action_group_id = azurerm_monitor_action_group.main[0].id
  }

  tags = var.tags
}

output "log_analytics_workspace_id" { value = azurerm_log_analytics_workspace.law.id }
output "log_analytics_workspace_name" { value = azurerm_log_analytics_workspace.law.name }
output "application_insights_name" { value = azurerm_application_insights.ai.name }
output "application_insights_connection_string" { value = azurerm_application_insights.ai.connection_string; sensitive = true }
output "application_insights_instrumentation_key" { value = azurerm_application_insights.ai.instrumentation_key; sensitive = true }
