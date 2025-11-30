# Deployment Options & Recommendations 🚀

**Last Updated**: November 30, 2025  
**Product**: PubSec Information Assistant v1.0.0  
**Target**: CTOs, DevOps Teams, System Administrators

---

## 🎯 Simplest Deployment Recommendation

### **RECOMMENDED: Docker Compose (5 Minutes)**

**Best For**: Proof-of-concept, demos, small teams (<50 users), local development

**Why This is Simplest**:
- ✅ **One Command**: `docker-compose up -d` and you're done
- ✅ **Zero Infrastructure**: No Kubernetes, no cloud accounts, no Terraform
- ✅ **Everything Included**: Backend, frontend, databases, monitoring
- ✅ **Works Everywhere**: Windows, Mac, Linux - identical experience
- ✅ **Easy Rollback**: `docker-compose down` removes everything cleanly

```bash
# Complete deployment in 3 commands (5 minutes)
git clone https://github.com/MarcoPolo483/PubSec-Info-Assistant-by-Copilot.git
cd PubSec-Info-Assistant-by-Copilot
docker-compose up -d

# That's it! System is running at:
# - Web UI: http://localhost:3000
# - API: http://localhost:8000
# - Grafana: http://localhost:3001
```

---

## 📊 Deployment Options Comparison

| Option | Setup Time | Complexity | Cost/Month | Best For | Maintenance |
|--------|------------|------------|------------|----------|-------------|
| **Docker Compose** | ⏱️ 5 min | 🟢 Low | $0* | POC, demos, dev | Low |
| **Managed Cloud** | ⏱️ 30 min | 🟡 Medium | $650+ | Production, gov | Minimal |
| **Kubernetes** | ⏱️ 2-4 hours | 🔴 High | $1,500+ | Enterprise, scale | Medium |
| **On-Premises** | ⏱️ 4-6 hours | 🔴 High | $2,000+ | Max security, air-gap | High |

*Infrastructure only - excludes OpenAI API costs ($180-$17,000/month depending on usage)

---

## 🎯 T-Shirt Sizing Guide for Azure

Before choosing a deployment option, understand the **pre-configured t-shirt sizes** for Azure deployments. Each size is optimized for specific use cases with automated deployment scripts.

### Quick Size Selector

| Size | Use Case | Users | Monthly Cost | Setup | SLA |
|------|----------|-------|--------------|-------|-----|
| **XS** | Demo/POC | 1-10 | $150-300 | 20 min | 99.5% |
| **S** | Development | 10-50 | $400-600 | 30 min | 99.9% |
| **M** | Production | 50-500 | $1,500-2,500 | 45 min | 99.95% |
| **L** | Multi-Tenant | 500-5000+ | $10,000-15,000 | 60 min | 99.99% |

### Automated Deployment with T-Shirt Sizing

**Example: Deploy Size M (Production) to Azure**
```powershell
# Navigate to terraform directory
cd terraform

# Deploy with automated script (one command!)
.\scripts\deploy-tshirt.ps1 `
  -Size M `
  -Environment production `
  -Location eastus `
  -Owner "your.email@example.com" `
  -OpenAIKey "sk-your-key-here" `
  -EnableDDoS `
  -EnablePrivateCluster

# The script automatically:
# - Creates Terraform state backend
# - Generates optimized configuration for Size M
# - Initializes and plans deployment
# - Provisions all Azure resources (AKS, ACR, Key Vault, etc.)
# - Provides kubectl commands for next steps
```

**All Sizes Include**:
- ✅ Pre-configured VM sizes optimized for workload
- ✅ Auto-scaling policies tuned for size
- ✅ Cost-optimized storage and networking
- ✅ Security settings appropriate for environment
- ✅ Monitoring and alerting configurations
- ✅ Disaster recovery settings (M and L sizes)

**📖 Complete Guide**: See [`terraform/TSHIRT-SIZING-GUIDE.md`](terraform/TSHIRT-SIZING-GUIDE.md) for detailed specifications, resource allocations, and decision matrix.

---

## 🚀 Option 1: Docker Compose (SIMPLEST - RECOMMENDED)

### Overview

Deploy entire system as containers on a single machine. Perfect for:
- ✅ Quick demos and evaluations
- ✅ Development and testing
- ✅ Small teams (<50 users)
- ✅ Organizations without Kubernetes expertise

### Prerequisites

**Required**:
- Docker Desktop 24.0+ (Windows/Mac) or Docker Engine (Linux)
- 8GB RAM minimum (16GB recommended)
- 4 CPU cores minimum (8 cores recommended)
- 50GB disk space
- OpenAI API key

**Installation**:
```bash
# Windows (PowerShell as Administrator)
winget install Docker.DockerDesktop

# Mac
brew install --cask docker

# Linux (Ubuntu/Debian)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

### Step-by-Step Deployment

#### Step 1: Clone Repository (1 minute)
```bash
git clone https://github.com/MarcoPolo483/PubSec-Info-Assistant-by-Copilot.git
cd PubSec-Info-Assistant-by-Copilot
```

#### Step 2: Configure Environment (2 minutes)
```bash
# Copy template
cp .env.example .env

# Edit with your API keys (use notepad, nano, or vim)
# Windows:
notepad .env

# Mac/Linux:
nano .env
```

**Required settings** in `.env`:
```bash
# OpenAI Configuration (REQUIRED)
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4-turbo-preview

# Optional: Use Azure OpenAI instead
# AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
# AZURE_OPENAI_API_KEY=your-azure-key

# Redis Configuration (defaults work fine)
REDIS_URL=redis://redis:6379
REDIS_PASSWORD=change-me-in-production

# Qdrant Configuration (defaults work fine)
QDRANT_URL=http://qdrant:6333

# Application Settings
ENVIRONMENT=development
SECRET_KEY=change-me-to-random-32-character-string

# Optional: Enable cost tracking
ENABLE_COST_TRACKING=true
DEFAULT_TENANT_BALANCE=10000.0
```

#### Step 3: Start Services (2 minutes)
```bash
# Start all services in background
docker-compose up -d

# Watch logs (optional)
docker-compose logs -f backend

# Wait for services to be ready (~60 seconds)
# The backend will automatically wait for Qdrant and Redis
```

#### Step 4: Verify Deployment (30 seconds)
```bash
# Check all containers are running
docker-compose ps

# Expected output:
# NAME                 STATUS          PORTS
# backend              Up 1 minute     0.0.0.0:8000->8000/tcp
# frontend             Up 1 minute     0.0.0.0:3000->3000/tcp
# qdrant               Up 1 minute     0.0.0.0:6333->6333/tcp
# redis                Up 1 minute     0.0.0.0:6379->6379/tcp
# prometheus           Up 1 minute     0.0.0.0:9090->9090/tcp
# grafana              Up 1 minute     0.0.0.0:3001->3001/tcp

# Test health endpoint
curl http://localhost:8000/health

# Test ready endpoint (should return 200 when all services are ready)
curl http://localhost:8000/ready
```

#### Step 5: Access System
- **Web UI**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs (Interactive Swagger UI)
- **Grafana Dashboards**: http://localhost:3001 (login: admin/admin)
- **Prometheus Metrics**: http://localhost:9090

### Scaling Docker Compose

```bash
# Scale backend horizontally
docker-compose up -d --scale backend=3

# Scale frontend
docker-compose up -d --scale frontend=2

# View scaled services
docker-compose ps
```

### Troubleshooting

**Problem**: Containers fail to start
```bash
# Check logs
docker-compose logs backend
docker-compose logs qdrant
docker-compose logs redis

# Common issue: Port already in use
# Solution: Stop conflicting services or change ports in docker-compose.yml
```

**Problem**: "Connection refused" errors
```bash
# Wait longer for services to initialize
sleep 30
curl http://localhost:8000/ready

# Check if containers are healthy
docker-compose ps
```

**Problem**: High memory usage
```bash
# Restart services
docker-compose restart

# Check resource usage
docker stats

# Increase Docker Desktop memory limit:
# Docker Desktop → Settings → Resources → Memory (16GB recommended)
```

### Updating Docker Deployment

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart services
docker-compose down
docker-compose up -d --build

# Alternative: Rolling update (zero downtime)
docker-compose up -d --no-deps --build backend
docker-compose up -d --no-deps --build frontend
```

### Backing Up Data

```bash
# Backup Qdrant data
docker-compose exec qdrant tar czf - /qdrant/storage > qdrant-backup-$(date +%Y%m%d).tar.gz

# Backup Redis data
docker-compose exec redis redis-cli SAVE
docker cp $(docker-compose ps -q redis):/data/dump.rdb redis-backup-$(date +%Y%m%d).rdb

# Backup environment configuration
cp .env .env.backup-$(date +%Y%m%d)
```

### Production Hardening for Docker Compose

If using Docker Compose in production (not recommended for >100 users):

```yaml
# docker-compose.override.yml
version: '3.8'

services:
  backend:
    restart: always
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
  
  redis:
    restart: always
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
  
  qdrant:
    restart: always
    volumes:
      - qdrant-data:/qdrant/storage

volumes:
  redis-data:
    driver: local
  qdrant-data:
    driver: local
```

---

## ☁️ Option 2: Managed Cloud (RECOMMENDED FOR PRODUCTION)

### Overview

Deploy to Azure, AWS, or GCP with fully managed services. Perfect for:
- ✅ Production government deployments
- ✅ High availability requirements (99.9%+ uptime)
- ✅ Compliance needs (FedRAMP, PIPEDA, GDPR)
- ✅ Minimal maintenance overhead

### 2A: Azure Deployment (Government Cloud)

**Best For**: US Federal/State government, Canadian government, HIPAA compliance

#### Prerequisites
```bash
# Install Azure CLI
# Windows (PowerShell)
winget install Microsoft.AzureCLI

# Mac
brew install azure-cli

# Login to Azure
az login

# Select subscription
az account set --subscription "Your-Subscription-Name"
```

#### Option 2A-1: Terraform (Infrastructure as Code)

**Simplest Azure deployment with full infrastructure automation**

**Using T-Shirt Sizing (Recommended)**:
```powershell
cd terraform

# Deploy Size M (Production) - Fully automated!
.\scripts\deploy-tshirt.ps1 `
  -Size M `
  -Environment production `
  -Location eastus `
  -Owner "your.email@example.com" `
  -OpenAIKey "sk-your-key-here" `
  -EnablePrivateCluster

# Or deploy Size S (Development)
.\scripts\deploy-tshirt.ps1 `
  -Size S `
  -Environment dev `
  -Location eastus `
  -Owner "dev-team@example.com" `
  -OpenAIKey "sk-your-key-here"

# Preview changes without applying (Dry Run)
.\scripts\deploy-tshirt.ps1 `
  -Size M `
  -Environment production `
  -DryRun

# The script handles everything:
# - Terraform state backend creation
# - Size-optimized configuration
# - Resource provisioning (AKS, ACR, Key Vault, etc.)
# - Security settings
# - Monitoring setup
```

**Manual Terraform (Advanced)**:
```bash
cd terraform

# Initialize Terraform
terraform init \
  -backend-config="resource_group_name=pubsec-terraform-state-rg" \
  -backend-config="storage_account_name=pubsecterraformstate" \
  -backend-config="container_name=tfstate" \
  -backend-config="key=production.tfstate"

# Deploy with custom tfvars
terraform plan -var-file="environments/production.tfvars"
terraform apply -var-file="environments/production.tfvars"

# Get AKS credentials
az aks get-credentials \
  --resource-group $(terraform output -raw resource_group_name) \
  --name $(terraform output -raw aks_cluster_name)

# Verify deployment
kubectl get nodes
```

**T-Shirt Sizing Benefits**:
- ✅ Pre-configured for your workload (XS, S, M, L)
- ✅ Automated validation and deployment
- ✅ Cost-optimized resource allocation
- ✅ Security settings appropriate for size
- ✅ Easy upgrades between sizes
kubectl get pods --all-namespaces
```

**What Terraform Creates**:
- Azure Kubernetes Service (AKS) cluster with auto-scaling
- Azure Container Registry (ACR) for Docker images
- Azure Key Vault for secrets management
- Virtual Network with subnets and NSGs
- Log Analytics + Application Insights
- Application Gateway with WAF (optional)
- Private endpoints for secure connectivity

**Cost**: ~$2,000-$5,000/month depending on scale

#### Option 2A-2: Azure Container Apps (Serverless)

**Simplest Azure option - no Kubernetes knowledge required**

```bash
# Create resource group
az group create --name pubsec-rg --location eastus

# Create Container Apps environment
az containerapp env create \
  --name pubsec-env \
  --resource-group pubsec-rg \
  --location eastus

# Deploy backend
az containerapp create \
  --name pubsec-backend \
  --resource-group pubsec-rg \
  --environment pubsec-env \
  --image ghcr.io/marcopolo483/pubsec-backend:latest \
  --target-port 8000 \
  --ingress external \
  --env-vars "OPENAI_API_KEY=secretref:openai-key" \
  --min-replicas 1 \
  --max-replicas 10

# Deploy frontend
az containerapp create \
  --name pubsec-frontend \
  --resource-group pubsec-rg \
  --environment pubsec-env \
  --image ghcr.io/marcopolo483/pubsec-frontend:latest \
  --target-port 3000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 5

# Get URLs
az containerapp show --name pubsec-backend --resource-group pubsec-rg --query properties.configuration.ingress.fqdn
az containerapp show --name pubsec-frontend --resource-group pubsec-rg --query properties.configuration.ingress.fqdn
```

**Cost**: ~$200-$800/month depending on usage

### 2B: AWS Deployment (GovCloud)

**Best For**: US government agencies requiring NIST 800-171, ITAR compliance

```bash
# Install AWS CLI
# Windows
winget install Amazon.AWSCLI

# Mac
brew install awscli

# Configure AWS credentials
aws configure

# Option 1: Deploy to ECS Fargate (Serverless)
aws cloudformation create-stack \
  --stack-name pubsec-ecs \
  --template-body file://infrastructure/aws/ecs-fargate.yaml \
  --parameters ParameterKey=OpenAIKey,ParameterValue=sk-your-key

# Option 2: Deploy to EKS (Kubernetes)
eksctl create cluster \
  --name pubsec-cluster \
  --region us-gov-west-1 \
  --nodegroup-name standard-workers \
  --node-type t3.xlarge \
  --nodes 3 \
  --nodes-min 2 \
  --nodes-max 10

# Deploy application
kubectl apply -k infrastructure/kubernetes/overlays/aws-govcloud/
```

**Cost**: ~$1,500-$4,000/month depending on scale

### 2C: Google Cloud (Canada Region)

**Best For**: Canadian organizations requiring PIPEDA compliance, data residency

```bash
# Install gcloud CLI
# Windows
winget install Google.CloudSDK

# Mac
brew install google-cloud-sdk

# Login and set project
gcloud auth login
gcloud config set project your-project-id

# Create GKE cluster in Canada
gcloud container clusters create pubsec-cluster \
  --zone northamerica-northeast1-a \
  --num-nodes 3 \
  --machine-type n1-standard-4 \
  --enable-autoscaling \
  --min-nodes 2 \
  --max-nodes 10

# Deploy application
kubectl apply -k infrastructure/kubernetes/overlays/gcp-canada/

# Or use Cloud Run (serverless)
gcloud run deploy pubsec-backend \
  --image gcr.io/your-project/pubsec-backend:latest \
  --region northamerica-northeast1 \
  --allow-unauthenticated \
  --set-env-vars OPENAI_API_KEY=sk-your-key
```

**Cost**: ~$1,200-$3,500/month depending on scale

---

## ⚙️ Option 3: Kubernetes (Enterprise Scale)

### Overview

Deploy to any Kubernetes cluster (on-premises or cloud). Perfect for:
- ✅ Enterprise deployments (>1000 users)
- ✅ Multi-region high availability
- ✅ Auto-scaling requirements
- ✅ Organizations with Kubernetes expertise

### Prerequisites

```bash
# Install kubectl
# Windows
winget install Kubernetes.kubectl

# Mac
brew install kubectl

# Verify Kubernetes cluster access
kubectl cluster-info
kubectl get nodes
```

### Deployment Steps

#### Step 1: Apply Base Manifests
```bash
cd infrastructure/kubernetes

# Create namespace
kubectl create namespace pubsec-assistant

# Apply secrets (edit with your values first)
kubectl create secret generic pubsec-secrets \
  --from-literal=openai-api-key=sk-your-key \
  --from-literal=redis-password=your-redis-password \
  --namespace pubsec-assistant

# Apply base configuration
kubectl apply -k base/ --namespace pubsec-assistant
```

#### Step 2: Apply Environment Overlay
```bash
# Development
kubectl apply -k overlays/development/ --namespace pubsec-assistant

# Staging
kubectl apply -k overlays/staging/ --namespace pubsec-assistant

# Production (with all features)
kubectl apply -k overlays/production/ --namespace pubsec-assistant
```

#### Step 3: Verify Deployment
```bash
# Check all pods are running
kubectl get pods --namespace pubsec-assistant

# Expected output:
# NAME                         READY   STATUS    RESTARTS   AGE
# backend-7d9f8b5c4d-abc12     1/1     Running   0          2m
# backend-7d9f8b5c4d-def34     1/1     Running   0          2m
# backend-7d9f8b5c4d-ghi56     1/1     Running   0          2m
# frontend-6c8d5b9f7a-jkl78    1/1     Running   0          2m
# frontend-6c8d5b9f7a-mno90    1/1     Running   0          2m
# qdrant-0                     1/1     Running   0          2m
# qdrant-1                     1/1     Running   0          2m
# qdrant-2                     1/1     Running   0          2m
# redis-master-0               1/1     Running   0          2m
# redis-replica-0              1/1     Running   0          2m
# redis-replica-1              1/1     Running   0          2m

# Check services
kubectl get services --namespace pubsec-assistant

# Get load balancer IP
kubectl get service backend --namespace pubsec-assistant \
  -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
```

#### Step 4: Configure Ingress (Optional)
```bash
# Install NGINX Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml

# Apply ingress configuration
kubectl apply -f infrastructure/kubernetes/ingress.yaml --namespace pubsec-assistant

# Access via domain (after DNS configuration)
# https://pubsec.yourdomain.com
```

### Kubernetes Features Included

✅ **High Availability**:
- Backend: 3-10 pod replicas with HorizontalPodAutoscaler
- Frontend: 2-5 pod replicas
- Qdrant: 3-node StatefulSet with persistent volumes
- Redis: Master-replica setup with sentinel

✅ **Auto-Scaling**:
- CPU-based auto-scaling (target 70% utilization)
- Cluster auto-scaling (adds nodes automatically)

✅ **Resilience**:
- PodDisruptionBudgets prevent all pods terminating simultaneously
- Liveness and readiness probes for automatic recovery
- Rolling updates with zero downtime

✅ **Security**:
- NetworkPolicies for pod-to-pod communication
- RBAC for service accounts
- Pod Security Standards enforced
- Secrets encrypted at rest

---

## 🏢 Option 4: On-Premises (Maximum Security)

### Overview

Deploy to your own data center with full control. Perfect for:
- ✅ Air-gapped networks (no internet)
- ✅ Maximum data sovereignty
- ✅ Classified information handling
- ✅ Strict compliance requirements

### Deployment Options

#### 4A: On-Premises Kubernetes (Recommended)

Use same Kubernetes manifests as Option 3, but on your own cluster:

**Supported Platforms**:
- VMware Tanzu
- Red Hat OpenShift
- Rancher
- K3s (lightweight Kubernetes)
- Canonical MicroK8s

```bash
# Example: Deploy to OpenShift
oc new-project pubsec-assistant
oc apply -k infrastructure/kubernetes/overlays/openshift/
```

#### 4B: VM-Based Deployment

Deploy Docker Compose on internal VMs:

```bash
# On each VM:
# 1. Install Docker
curl -fsSL https://get.docker.com | sh

# 2. Clone repository (via internal Git server)
git clone https://git.internal.gov/pubsec-assistant.git

# 3. Configure for internal network
cp .env.example .env
nano .env  # Edit for internal endpoints

# 4. Deploy
docker-compose -f docker-compose.prod.yml up -d

# 5. Configure load balancer to distribute across VMs
```

#### 4C: Air-Gapped Deployment

For systems with no internet access:

```bash
# Step 1: On internet-connected machine, pull all images
docker pull ghcr.io/marcopolo483/pubsec-backend:latest
docker pull ghcr.io/marcopolo483/pubsec-frontend:latest
docker pull qdrant/qdrant:v1.7.4
docker pull redis:7.2-alpine
docker pull prom/prometheus:v2.45.0
docker pull grafana/grafana:10.0.0

# Step 2: Save images to TAR files
docker save ghcr.io/marcopolo483/pubsec-backend:latest -o backend.tar
docker save ghcr.io/marcopolo483/pubsec-frontend:latest -o frontend.tar
docker save qdrant/qdrant:v1.7.4 -o qdrant.tar
docker save redis:7.2-alpine -o redis.tar
docker save prom/prometheus:v2.45.0 -o prometheus.tar
docker save grafana/grafana:10.0.0 -o grafana.tar

# Step 3: Transfer TAR files to air-gapped machine (USB, secure transfer)

# Step 4: On air-gapped machine, load images
docker load -i backend.tar
docker load -i frontend.tar
docker load -i qdrant.tar
docker load -i redis.tar
docker load -i prometheus.tar
docker load -i grafana.tar

# Step 5: Deploy with docker-compose (uses local images)
docker-compose up -d
```

**AI Model Considerations for Air-Gapped**:
- ❌ Cannot use OpenAI API (requires internet)
- ✅ Use local models instead (e.g., Llama 2, Mistral)
- ✅ Deploy models on local GPUs

Update `.env` for local AI:
```bash
# Use local LLM instead of OpenAI
LLM_PROVIDER=local
LOCAL_MODEL_PATH=/models/llama-2-70b-chat
LOCAL_EMBEDDING_MODEL=/models/all-MiniLM-L6-v2

# Disable internet-dependent features
ENABLE_EXTERNAL_RERANKING=false
ENABLE_CONTENT_FILTERING=false  # Or use local model
```

---

## 🎯 Decision Matrix: Which Option Should You Choose?

### Quick Selector

```
┌─────────────────────────────────────────────┐
│ Do you need a demo/POC right now?          │
└─────────────────────────────────────────────┘
              │
              ▼ YES
    ┌──────────────────┐
    │ Docker Compose   │ ← START HERE (5 minutes)
    └──────────────────┘
              │
              ▼ NO
┌─────────────────────────────────────────────┐
│ Are you deploying to production?            │
└─────────────────────────────────────────────┘
              │
       ┌──────┴──────┐
       │ YES         │ NO → Docker Compose
       ▼             │
┌─────────────────────────────┐
│ What's your priority?       │
└─────────────────────────────┘
       │
   ┌───┴───┬───────┬─────┐
   │       │       │     │
   ▼       ▼       ▼     ▼
 Speed  Security Cost  Scale
   │       │       │     │
   │       │       │     │
Azure/  On-Prem  Azure  K8s
 AWS               CA
```

### Detailed Comparison

| Criteria | Docker Compose | Managed Cloud | Kubernetes | On-Premises |
|----------|----------------|---------------|------------|-------------|
| **Setup Time** | ⏱️ 5 min | ⏱️ 30 min | ⏱️ 2-4 hours | ⏱️ 4-6 hours |
| **Skill Level** | Beginner | Intermediate | Advanced | Advanced |
| **Max Users** | 50 | 10,000+ | 100,000+ | Unlimited |
| **Uptime** | 95% | 99.9% | 99.95% | 99.99% |
| **Auto-Scaling** | ❌ Manual | ✅ Automatic | ✅ Automatic | ⚠️ Manual |
| **Multi-Region** | ❌ No | ✅ Yes | ✅ Yes | ⚠️ Complex |
| **Cost/Month** | $0-200* | $650-5,000 | $1,500-10,000 | $2,000-15,000 |
| **Maintenance** | Low | Minimal | Medium | High |
| **Data Residency** | ✅ Local | ✅ Configurable | ✅ Configurable | ✅ Complete |
| **Air-Gapped** | ✅ Yes | ❌ No | ⚠️ Partial | ✅ Yes |
| **Compliance** | Basic | FedRAMP/PIPEDA | FedRAMP/PIPEDA | All |

*Excludes OpenAI API costs

---

## 📝 Deployment Checklist

### Pre-Deployment (All Options)

- [ ] Obtain OpenAI API key (or configure local LLM for air-gapped)
- [ ] Review and approve privacy policy
- [ ] Complete security questionnaire
- [ ] Review cost estimates and approve budget
- [ ] Identify deployment owner (DevOps/SRE team)
- [ ] Schedule deployment window (if production)
- [ ] Prepare rollback plan
- [ ] Configure monitoring and alerting endpoints
- [ ] Test backup and restore procedures
- [ ] Obtain required approvals (CTO, CISO, CFO)

### Docker Compose Specific

- [ ] Install Docker Desktop or Docker Engine
- [ ] Allocate 16GB RAM, 8 CPU cores, 50GB disk
- [ ] Configure firewall rules (ports 3000, 8000, 6333, 6379, 9090, 3001)
- [ ] Copy and edit `.env` file with API keys
- [ ] Run `docker-compose up -d`
- [ ] Verify health endpoint: `curl http://localhost:8000/health`
- [ ] Test sample query in web UI

### Managed Cloud Specific

- [ ] Create cloud account (Azure/AWS/GCP)
- [ ] Configure billing alerts
- [ ] Set up IAM roles and service accounts
- [ ] Configure VPC/VNet with private subnets
- [ ] Enable encryption at rest and in transit
- [ ] Configure backup policies
- [ ] Set up disaster recovery region
- [ ] Run Terraform/CloudFormation deployment
- [ ] Configure DNS records
- [ ] Test from multiple regions

### Kubernetes Specific

- [ ] Verify cluster access (`kubectl cluster-info`)
- [ ] Create namespace: `kubectl create namespace pubsec-assistant`
- [ ] Configure secrets and ConfigMaps
- [ ] Apply base manifests: `kubectl apply -k base/`
- [ ] Apply environment overlay: `kubectl apply -k overlays/production/`
- [ ] Configure Ingress controller
- [ ] Set up cert-manager for TLS certificates
- [ ] Configure HorizontalPodAutoscaler thresholds
- [ ] Test pod auto-scaling
- [ ] Verify PodDisruptionBudgets

### On-Premises Specific

- [ ] Provision VMs or bare metal servers
- [ ] Install operating system (RHEL, Ubuntu, etc.)
- [ ] Configure network segmentation
- [ ] Install Docker or Kubernetes
- [ ] Configure internal DNS
- [ ] Set up internal load balancer
- [ ] Configure air-gapped image registry (if applicable)
- [ ] Transfer Docker images (if air-gapped)
- [ ] Configure local LLM (if no internet)
- [ ] Test from internal network

### Post-Deployment (All Options)

- [ ] Verify all services are running
- [ ] Test health endpoint: `/health`
- [ ] Test ready endpoint: `/ready`
- [ ] Ingest sample document
- [ ] Run sample queries and verify citations
- [ ] Check Grafana dashboards
- [ ] Configure monitoring alerts
- [ ] Test disaster recovery procedure
- [ ] Train end users
- [ ] Schedule first security audit
- [ ] Document deployment architecture
- [ ] Create runbooks for common issues

---

## 🆘 Getting Help

### Self-Service Resources
- **Documentation**: [Full docs](../docs/)
- **Demo Guide**: [DEMO-GUIDE.md](../DEMO-GUIDE.md)
- **Troubleshooting**: [terraform/README.md](../terraform/README.md)
- **GitHub Issues**: https://github.com/MarcoPolo483/PubSec-Info-Assistant-by-Copilot/issues

### Community Support
- **Discussions**: https://github.com/MarcoPolo483/PubSec-Info-Assistant-by-Copilot/discussions
- **Response Time**: <24 hours

### Enterprise Support (Paid Customers)
- **Email**: enterprise-support@pubsec.gov
- **Slack**: Enterprise customers channel
- **Response Time**: <1 hour (P0), <4 hours (P1)

---

## 🎓 Next Steps

1. **Start with Docker Compose** (5 minutes) - Get hands-on experience
2. **Run the Demo** (15 minutes) - See all features in action using [DEMO-GUIDE.md](../DEMO-GUIDE.md)
3. **Review Compliance** - Read [INTERNATIONAL-DEPLOYMENT-GUIDE.md](./INTERNATIONAL-DEPLOYMENT-GUIDE.md)
4. **Plan Production** - Choose managed cloud or Kubernetes based on your needs
5. **Schedule Training** - Onboard your team with documentation and video tutorials

**Ready to deploy?** Start with Docker Compose now:
```bash
git clone https://github.com/MarcoPolo483/PubSec-Info-Assistant-by-Copilot.git
cd PubSec-Info-Assistant-by-Copilot
docker-compose up -d
```

**Questions?** Open an issue or email enterprise-support@pubsec.gov
