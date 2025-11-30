# =============================================================================
# Application Gateway Module - L7 Load Balancer with WAF
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
variable "subnet_id" { type = string }
variable "sku_name" { type = string }
variable "sku_tier" { type = string }
variable "capacity" { type = number }
variable "enable_autoscaling" { type = bool }
variable "min_capacity" { type = number }
variable "max_capacity" { type = number }
variable "enable_waf" { type = bool }
variable "waf_mode" { type = string }
variable "waf_rule_set_type" { type = string }
variable "waf_rule_set_version" { type = string }
variable "ssl_certificate_data" { type = string }
variable "ssl_certificate_password" { type = string }
variable "backend_address_pool_fqdns" { type = list(string) }
variable "log_analytics_workspace_id" { type = string }
variable "tags" { type = map(string) }

# Public IP
resource "azurerm_public_ip" "appgw" {
  name                = "${var.project_name}-${var.environment}-appgw-pip"
  location            = var.location
  resource_group_name = var.resource_group_name
  allocation_method   = "Static"
  sku                 = "Standard"
  tags                = var.tags
}

# Application Gateway
resource "azurerm_application_gateway" "appgw" {
  name                = "${var.project_name}-${var.environment}-appgw"
  location            = var.location
  resource_group_name = var.resource_group_name

  sku {
    name     = var.sku_name
    tier     = var.sku_tier
    capacity = var.enable_autoscaling ? null : var.capacity
  }

  dynamic "autoscale_configuration" {
    for_each = var.enable_autoscaling ? [1] : []
    content {
      min_capacity = var.min_capacity
      max_capacity = var.max_capacity
    }
  }

  gateway_ip_configuration {
    name      = "gateway-ip-config"
    subnet_id = var.subnet_id
  }

  frontend_port {
    name = "https-port"
    port = 443
  }

  frontend_port {
    name = "http-port"
    port = 80
  }

  frontend_ip_configuration {
    name                 = "frontend-ip"
    public_ip_address_id = azurerm_public_ip.appgw.id
  }

  backend_address_pool {
    name  = "backend-pool"
    fqdns = var.backend_address_pool_fqdns
  }

  backend_http_settings {
    name                  = "https-settings"
    cookie_based_affinity = "Disabled"
    port                  = 443
    protocol              = "Https"
    request_timeout       = 60
    probe_name            = "health-probe"
  }

  http_listener {
    name                           = "https-listener"
    frontend_ip_configuration_name = "frontend-ip"
    frontend_port_name             = "https-port"
    protocol                       = "Https"
    ssl_certificate_name           = var.ssl_certificate_data != "" ? "ssl-cert" : null
  }

  request_routing_rule {
    name                       = "routing-rule"
    rule_type                  = "Basic"
    http_listener_name         = "https-listener"
    backend_address_pool_name  = "backend-pool"
    backend_http_settings_name = "https-settings"
    priority                   = 100
  }

  probe {
    name                = "health-probe"
    protocol            = "Https"
    path                = "/health"
    interval            = 30
    timeout             = 30
    unhealthy_threshold = 3
    host                = var.backend_address_pool_fqdns[0]
  }

  dynamic "ssl_certificate" {
    for_each = var.ssl_certificate_data != "" ? [1] : []
    content {
      name     = "ssl-cert"
      data     = var.ssl_certificate_data
      password = var.ssl_certificate_password
    }
  }

  dynamic "waf_configuration" {
    for_each = var.enable_waf ? [1] : []
    content {
      enabled          = true
      firewall_mode    = var.waf_mode
      rule_set_type    = var.waf_rule_set_type
      rule_set_version = var.waf_rule_set_version
    }
  }

  tags = var.tags
}

# Diagnostics
resource "azurerm_monitor_diagnostic_setting" "appgw" {
  name                       = "appgw-diagnostics"
  target_resource_id         = azurerm_application_gateway.appgw.id
  log_analytics_workspace_id = var.log_analytics_workspace_id

  enabled_log {
    category = "ApplicationGatewayAccessLog"
  }

  enabled_log {
    category = "ApplicationGatewayPerformanceLog"
  }

  enabled_log {
    category = "ApplicationGatewayFirewallLog"
  }

  metric {
    category = "AllMetrics"
  }
}

output "public_ip_address" { value = azurerm_public_ip.appgw.ip_address }
output "appgw_id" { value = azurerm_application_gateway.appgw.id }
