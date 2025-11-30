# Azure Infrastructure Deployment - Terraform

Production-ready Infrastructure-as-Code for deploying PubSec Info Assistant to Azure using AKS, ACR, and supporting services.

## 📋 Table of Contents

- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Modules](#modules)
- [Environments](#environments)
- [CI/CD Integration](#cicd-integration)
- [Security](#security)
- [Troubleshooting](#troubleshooting)
- [Cost Estimation](#cost-estimation)

## 🏗️ Architecture

This Terraform configuration provisions a complete Azure infrastructure:

```
┌─────────────────────────────────────────────────────────┐
│                   Application Gateway                    │
│              (L7 Load Balancer + WAF)                    │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│              Azure Kubernetes Service (AKS)              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐│
│  │ Backend  │  │ Frontend │  │  Qdrant  │  │  Redis  ││
│  │  Pods    │  │   Pods   │  │   Pods   │  │  Pods   ││
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘│
└─────────────────────────────────────────────────────────┘
         │                    │                    │
┌────────▼────────┐  ┌────────▼────────┐  ┌──────▼──────┐
│ Azure Container │  │  Azure Key      │  │   Azure     │
│   Registry      │  │    Vault        │  │  Monitor    │
│    (ACR)        │  │  (Secrets)      │  │ (Logging)   │
└─────────────────┘  └─────────────────┘  └─────────────┘
```

### Deployed Resources

- **AKS Cluster**: Kubernetes 1.28+ with system and user node pools
- **Azure Container Registry (ACR)**: Premium SKU with geo-replication
- **Virtual Network**: Multi-subnet architecture with NSGs
- **Key Vault**: Premium SKU for secrets management
- **Log Analytics + Application Insights**: Full observability stack
- **Application Gateway**: WAF v2 with auto-scaling
- **Private Endpoints**: Secure connectivity for ACR and Key Vault

## ✅ Prerequisites

### Required Tools

```bash
# Azure CLI (2.50+)
az --version

# Terraform (1.5+)
terraform version

# kubectl (1.28+)
kubectl version --client

# jq (for JSON parsing)
jq --version
```

### Azure Setup

1. **Azure Subscription**: Active subscription with Owner or Contributor role
2. **Service Principal** (for CI/CD):
   ```bash
   az ad sp create-for-rbac --name "pubsec-terraform-sp" \
     --role Contributor \
     --scopes /subscriptions/<SUBSCRIPTION_ID>
   ```

3. **Terraform State Storage**:
   ```bash
   # Create resource group
   az group create --name pubsec-terraform-state-rg --location eastus
   
   # Create storage account
   az storage account create \
     --name pubsecterraformstate \
     --resource-group pubsec-terraform-state-rg \
     --location eastus \
     --sku Standard_LRS \
     --encryption-services blob
   
   # Create blob container
   az storage container create \
     --name tfstate \
     --account-name pubsecterraformstate
   ```

4. **Azure Permissions**:
   - `Microsoft.ContainerService/*` (AKS)
   - `Microsoft.ContainerRegistry/*` (ACR)
   - `Microsoft.Network/*` (VNet, NSG)
   - `Microsoft.KeyVault/*` (Key Vault)
   - `Microsoft.OperationalInsights/*` (Log Analytics)

## 🚀 Quick Start

### 1. Clone and Initialize

```bash
cd terraform
terraform init \
  -backend-config="resource_group_name=pubsec-terraform-state-rg" \
  -backend-config="storage_account_name=pubsecterraformstate" \
  -backend-config="container_name=tfstate" \
  -backend-config="key=dev.tfstate"
```

### 2. Configure Environment

Create `terraform.tfvars` (or use pre-configured environment files):

```hcl
environment  = "dev"
location     = "eastus"
owner        = "devops@example.com"
cost_center  = "IT-Development"

openai_api_key = "sk-your-key-here"  # Or use Azure Key Vault

# Override defaults as needed
aks_system_node_pool_min_count = 2
aks_user_node_pool_min_count = 2
```

### 3. Plan and Apply

```bash
# Review changes
terraform plan -var-file="environments/dev.tfvars"

# Apply infrastructure
terraform apply -var-file="environments/dev.tfvars"
```

### 4. Configure kubectl

```bash
# Get AKS credentials
az aks get-credentials \
  --resource-group $(terraform output -raw resource_group_name) \
  --name $(terraform output -raw aks_cluster_name)

# Verify connection
kubectl get nodes
```

## ⚙️ Configuration

### Environment Variables

Required secrets (store in Azure Key Vault or GitHub Secrets):

```bash
# OpenAI API Key
export TF_VAR_openai_api_key="sk-..."

# Azure Credentials (for CI/CD)
export AZURE_CLIENT_ID="..."
export AZURE_CLIENT_SECRET="..."
export AZURE_TENANT_ID="..."
export AZURE_SUBSCRIPTION_ID="..."
```

### Customization

Edit `variables.tf` or use `-var` flags:

```bash
terraform plan \
  -var="aks_system_node_pool_vm_size=Standard_D8s_v5" \
  -var="enable_application_gateway=false" \
  -var="acr_sku=Standard"
```

## 📦 Modules

### Networking (`modules/networking`)
- Virtual Network with 4 subnets (AKS, AppGW, Private Endpoints, Database)
- Network Security Groups with default rules
- Private DNS Zones for ACR, Key Vault, AKS

### AKS (`modules/aks`)
- System node pool (3-10 nodes, D4s_v5)
- User node pool (3-20 nodes, D8s_v5)
- Azure CNI networking
- Azure Monitor integration
- RBAC + Azure AD integration
- Workload Identity enabled

### ACR (`modules/acr`)
- Premium SKU with geo-replication
- Private endpoint integration
- Content trust and quarantine policies
- Retention policies (7-30 days)

### Key Vault (`modules/keyvault`)
- Premium SKU with HSM backing
- RBAC authorization
- Soft delete + purge protection
- Private endpoint integration
- Automatic secret rotation

### Monitoring (`modules/monitoring`)
- Log Analytics workspace (30-90 day retention)
- Application Insights
- Metric alerts (CPU, memory)
- Action groups for notifications

### Application Gateway (`modules/application-gateway`)
- WAF v2 with OWASP 3.2 rules
- Auto-scaling (2-10 instances)
- SSL/TLS termination
- Health probes

## 🌍 Environments

### Development (`environments/dev.tfvars`)
- Minimal costs (~$300/month)
- 1 system node, 1 user node
- No geo-replication
- Standard Key Vault
- No Application Gateway

### Staging (`environments/staging.tfvars`)
- Moderate costs (~$800/month)
- 2 system nodes, 2 user nodes
- Private cluster enabled
- Premium Key Vault
- Application Gateway with WAF (Detection mode)

### Production (`environments/production.tfvars`)
- High availability (~$2000/month)
- 3 system nodes, 5 user nodes
- Multi-region geo-replication
- DDoS protection
- Application Gateway with WAF (Prevention mode)
- 90-day log retention

## 🔄 CI/CD Integration

### GitHub Actions Workflow

The `.github/workflows/cd.yml` includes:

1. **Terraform Plan**: Validate and plan changes
2. **Terraform Apply**: Apply infrastructure (on approval)
3. **Build & Push**: Build Docker images to ACR
4. **Deploy**: Update AKS deployments with new images

### Required GitHub Secrets

```yaml
AZURE_CLIENT_ID: <service-principal-client-id>
AZURE_TENANT_ID: <azure-tenant-id>
AZURE_SUBSCRIPTION_ID: <azure-subscription-id>
TERRAFORM_STATE_RG: pubsec-terraform-state-rg
TERRAFORM_STATE_SA: pubsecterraformstate
OPENAI_API_KEY: sk-...
```

### Manual Deployment

```bash
# Trigger deployment
gh workflow run cd.yml \
  -f environment=production \
  -f skip_tests=false
```

## 🔒 Security

### Network Security
- Private cluster option (production)
- Network policies enabled
- NSG rules for subnet isolation
- Private endpoints for ACR/Key Vault

### Identity & Access
- Managed Identities for AKS
- RBAC for all resources
- Workload Identity for pod-level access
- Key Vault integration for secrets

### Compliance
- FedRAMP-High tagging
- Audit logging enabled
- Azure Defender for containers
- Azure Policy enforcement

### Secrets Management
```bash
# Add secret to Key Vault
az keyvault secret set \
  --vault-name $(terraform output -raw keyvault_name) \
  --name "new-secret" \
  --value "secret-value"
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Terraform Init Fails
```bash
# Clear local state
rm -rf .terraform .terraform.lock.hcl

# Re-initialize
terraform init -reconfigure
```

#### 2. AKS Cluster Not Accessible
```bash
# Refresh credentials
az aks get-credentials --resource-group <RG> --name <AKS> --overwrite-existing

# Check API server connectivity
kubectl cluster-info
```

#### 3. ACR Authentication Issues
```bash
# Attach ACR to AKS
az aks update --resource-group <RG> --name <AKS> --attach-acr <ACR_NAME>

# Verify
az aks check-acr --resource-group <RG> --name <AKS> --acr <ACR_NAME>.azurecr.io
```

#### 4. Terraform State Lock
```bash
# Force unlock (use with caution)
terraform force-unlock <LOCK_ID>
```

#### 5. Quota Exceeded
```bash
# Check quotas
az vm list-usage --location eastus -o table

# Request increase
az support tickets create --issue-type "quota"
```

### Debug Mode

```bash
# Enable Terraform debug logging
export TF_LOG=DEBUG
export TF_LOG_PATH=terraform-debug.log

terraform plan
```

### Resource Validation

```bash
# Validate all resources exist
terraform state list

# Check specific resource
terraform state show azurerm_kubernetes_cluster.aks
```

## 💰 Cost Estimation

### Development Environment
| Resource | SKU/Size | Quantity | Monthly Cost |
|----------|----------|----------|--------------|
| AKS (system) | D2s_v5 | 1 node | $70 |
| AKS (user) | D4s_v5 | 1 node | $140 |
| ACR | Premium | 1 | $50 |
| Key Vault | Standard | 1 | $5 |
| Log Analytics | 10GB/month | 1 | $25 |
| VNet | Standard | 1 | $10 |
| **Total** | | | **~$300/month** |

### Production Environment
| Resource | SKU/Size | Quantity | Monthly Cost |
|----------|----------|----------|--------------|
| AKS (system) | D4s_v5 | 3 nodes | $630 |
| AKS (user) | D8s_v5 | 5 nodes | $1,400 |
| ACR | Premium (geo-rep) | 3 regions | $150 |
| Application Gateway | WAF_v2 | auto-scale | $400 |
| Key Vault | Premium | 1 | $10 |
| Log Analytics | 100GB/month | 1 | $250 |
| DDoS Protection | Standard | 1 | $3,000 |
| **Total** | | | **~$5,840/month** |

> **Note**: Costs vary by region and usage. Use [Azure Pricing Calculator](https://azure.microsoft.com/pricing/calculator/) for accurate estimates.

## 📚 Additional Resources

- [Azure AKS Documentation](https://docs.microsoft.com/azure/aks/)
- [Terraform Azure Provider](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)
- [AKS Best Practices](https://docs.microsoft.com/azure/aks/best-practices)
- [Azure Well-Architected Framework](https://docs.microsoft.com/azure/architecture/framework/)

## 🤝 Support

For issues or questions:
1. Check [Troubleshooting](#troubleshooting) section
2. Review [GitHub Issues](../../issues)
3. Contact SRE team: sre@example.com

---

**Version**: 1.0.0  
**Last Updated**: 2025-11-30  
**Maintained By**: DevOps/SRE Team
