# Azure Front Door + WAF Bicep Template
# Deploy edge security with OWASP rules and custom policies

@description('Location for all resources')
param location string = resourceGroup().location

@description('Environment name (dev/staging/prod)')
param environmentName string = 'prod'

@description('Origin backend hostname (AKS ingress)')
param originHostname string

@description('Custom domain name (optional)')
param customDomain string = ''

@description('WAF mode (Prevention or Detection)')
@allowed([
  'Prevention'
  'Detection'
])
param wafMode string = 'Prevention'

var frontDoorName = 'fd-pubsec-${environmentName}'
var wafPolicyName = 'wafPubSec${environmentName}'
var originGroupName = 'aks-origin'
var originName = 'aks-ingress'
var routeName = 'default-route'

// ========== WAF Policy ==========
resource wafPolicy 'Microsoft.Network/FrontDoorWebApplicationFirewallPolicies@2022-05-01' = {
  name: wafPolicyName
  location: 'Global'
  sku: {
    name: 'Premium_AzureFrontDoor'
  }
  properties: {
    policySettings: {
      enabledState: 'Enabled'
      mode: wafMode
      requestBodyCheck: 'Enabled'
      maxRequestBodySizeInKb: 128
    }
    managedRules: {
      managedRuleSets: [
        {
          ruleSetType: 'Microsoft_DefaultRuleSet'
          ruleSetVersion: '2.1'
          ruleSetAction: 'Block'
          exclusions: []
        }
        {
          ruleSetType: 'Microsoft_BotManagerRuleSet'
          ruleSetVersion: '1.0'
          ruleSetAction: 'Block'
        }
      ]
    }
    customRules: {
      rules: [
        {
          name: 'RateLimitRule'
          priority: 100
          ruleType: 'RateLimitRule'
          rateLimitDurationInMinutes: 5
          rateLimitThreshold: 1000
          action: 'Block'
          matchConditions: [
            {
              matchVariable: 'RequestUri'
              operator: 'Contains'
              matchValue: [
                '/api/'
              ]
            }
          ]
        }
        {
          name: 'BlockLargePayloads'
          priority: 200
          ruleType: 'MatchRule'
          action: 'Block'
          matchConditions: [
            {
              matchVariable: 'RequestBodySize'
              operator: 'GreaterThan'
              matchValue: [
                '10485760' // 10MB
              ]
            }
          ]
        }
        {
          name: 'BlockPromptInjection'
          priority: 300
          ruleType: 'MatchRule'
          action: 'Block'
          matchConditions: [
            {
              matchVariable: 'RequestBody'
              operator: 'Contains'
              matchValue: [
                'ignore previous instructions'
                'system:'
                'forget everything'
                '\\\\n\\\\n==='
              ]
              transforms: [
                'Lowercase'
              ]
            }
          ]
        }
        {
          name: 'RequireValidHeaders'
          priority: 400
          ruleType: 'MatchRule'
          action: 'Block'
          matchConditions: [
            {
              matchVariable: 'RequestHeader'
              selector: 'X-Tenant-ID'
              operator: 'Equal'
              matchValue: []
              negateCondition: true
            }
            {
              matchVariable: 'RequestUri'
              operator: 'Contains'
              matchValue: [
                '/api/v1/'
              ]
            }
          ]
        }
      ]
    }
  }
}

// ========== Front Door Profile ==========
resource frontDoor 'Microsoft.Cdn/profiles@2023-05-01' = {
  name: frontDoorName
  location: 'Global'
  sku: {
    name: 'Premium_AzureFrontDoor'
  }
  properties: {
    originResponseTimeoutSeconds: 60
  }
}

// Endpoint
resource endpoint 'Microsoft.Cdn/profiles/afdEndpoints@2023-05-01' = {
  parent: frontDoor
  name: 'pubsec-info-assistant'
  location: 'Global'
  properties: {
    enabledState: 'Enabled'
  }
}

// Origin Group
resource originGroup 'Microsoft.Cdn/profiles/originGroups@2023-05-01' = {
  parent: frontDoor
  name: originGroupName
  properties: {
    loadBalancingSettings: {
      sampleSize: 4
      successfulSamplesRequired: 3
      additionalLatencyInMilliseconds: 50
    }
    healthProbeSettings: {
      probePath: '/health'
      probeRequestType: 'GET'
      probeProtocol: 'Https'
      probeIntervalInSeconds: 30
    }
    sessionAffinityState: 'Disabled'
  }
}

// Origin (AKS Ingress)
resource origin 'Microsoft.Cdn/profiles/originGroups/origins@2023-05-01' = {
  parent: originGroup
  name: originName
  properties: {
    hostName: originHostname
    httpPort: 80
    httpsPort: 443
    originHostHeader: originHostname
    priority: 1
    weight: 1000
    enabledState: 'Enabled'
    enforceCertificateNameCheck: true
    sharedPrivateLinkResource: {
      privateLink: {
        id: '/subscriptions/${subscription().subscriptionId}/resourceGroups/${resourceGroup().name}/providers/Microsoft.Network/privateLinkServices/pls-aks-ingress'
      }
      privateLinkLocation: location
      requestMessage: 'Front Door private link request'
    }
  }
}

// Route
resource route 'Microsoft.Cdn/profiles/afdEndpoints/routes@2023-05-01' = {
  parent: endpoint
  name: routeName
  properties: {
    originGroup: {
      id: originGroup.id
    }
    supportedProtocols: [
      'Https'
    ]
    patternsToMatch: [
      '/*'
    ]
    forwardingProtocol: 'HttpsOnly'
    linkToDefaultDomain: 'Enabled'
    httpsRedirect: 'Enabled'
    enabledState: 'Enabled'
  }
  dependsOn: [
    origin
  ]
}

// Security Policy (link WAF to endpoint)
resource securityPolicy 'Microsoft.Cdn/profiles/securityPolicies@2023-05-01' = {
  parent: frontDoor
  name: 'default-security-policy'
  properties: {
    parameters: {
      type: 'WebApplicationFirewall'
      wafPolicy: {
        id: wafPolicy.id
      }
      associations: [
        {
          domains: [
            {
              id: endpoint.id
            }
          ]
          patternsToMatch: [
            '/*'
          ]
        }
      ]
    }
  }
}

// ========== Diagnostic Settings ==========
resource diagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  scope: frontDoor
  name: 'fd-diagnostics'
  properties: {
    workspaceId: '/subscriptions/${subscription().subscriptionId}/resourceGroups/${resourceGroup().name}/providers/Microsoft.OperationalInsights/workspaces/log-pubsec-${environmentName}'
    logs: [
      {
        category: 'FrontDoorAccessLog'
        enabled: true
        retentionPolicy: {
          enabled: true
          days: 90
        }
      }
      {
        category: 'FrontDoorHealthProbeLog'
        enabled: true
        retentionPolicy: {
          enabled: true
          days: 30
        }
      }
      {
        category: 'FrontDoorWebApplicationFirewallLog'
        enabled: true
        retentionPolicy: {
          enabled: true
          days: 90
        }
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
        retentionPolicy: {
          enabled: true
          days: 30
        }
      }
    ]
  }
}

// ========== Outputs ==========
output frontDoorEndpoint string = endpoint.properties.hostName
output frontDoorId string = frontDoor.id
output wafPolicyId string = wafPolicy.id

@description('Use this hostname to configure your DNS CNAME')
output cnameTarget string = endpoint.properties.hostName
