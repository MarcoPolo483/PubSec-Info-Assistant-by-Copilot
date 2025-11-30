# =============================================================================
# PubSec Info Assistant - Terraform Outputs
# =============================================================================

output "outputs_summary" {
  description = "Summary of all infrastructure outputs"
  value = {
    resource_group = {
      name     = azurerm_resource_group.main.name
      location = azurerm_resource_group.main.location
      id       = azurerm_resource_group.main.id
    }
    
    aks = {
      cluster_name     = module.aks.aks_cluster_name
      cluster_id       = module.aks.aks_cluster_id
      cluster_fqdn     = module.aks.aks_cluster_fqdn
      node_resource_group = module.aks.node_resource_group
      kubelet_identity_object_id = module.aks.kubelet_identity_object_id
      get_credentials_command = "az aks get-credentials --resource-group ${azurerm_resource_group.main.name} --name ${module.aks.aks_cluster_name}"
    }
    
    acr = {
      name         = module.acr.acr_name
      login_server = module.acr.acr_login_server
      id           = module.acr.acr_id
    }
    
    keyvault = {
      name = module.keyvault.keyvault_name
      uri  = module.keyvault.keyvault_uri
      id   = module.keyvault.keyvault_id
    }
    
    networking = {
      vnet_name = module.networking.vnet_name
      vnet_id   = module.networking.vnet_id
      aks_subnet_id = module.networking.aks_subnet_id
      appgw_subnet_id = module.networking.appgw_subnet_id
    }
    
    monitoring = {
      log_analytics_workspace_id   = module.monitoring.log_analytics_workspace_id
      log_analytics_workspace_name = module.monitoring.log_analytics_workspace_name
      application_insights_name    = module.monitoring.application_insights_name
    }
  }
}

# Sensitive outputs (use terraform output -json to retrieve)
output "sensitive_outputs" {
  description = "Sensitive configuration values"
  sensitive   = true
  value = {
    application_insights_connection_string   = module.monitoring.application_insights_connection_string
    application_insights_instrumentation_key = module.monitoring.application_insights_instrumentation_key
    redis_password = random_password.redis_password.result
    qdrant_api_key = random_password.qdrant_api_key.result
    app_secret_key = random_password.app_secret_key.result
  }
}
