# Production Deployment Guide
**PubSec-Info-Assistant – World-Class Enterprise & Government-Grade RAG Platform**

---

## Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Architecture Summary](#architecture-summary)
4. [Pre-Deployment Checklist](#pre-deployment-checklist)
5. [Azure Infrastructure Setup](#azure-infrastructure-setup)
6. [Application Deployment](#application-deployment)
7. [Post-Deployment Validation](#post-deployment-validation)
8. [Monitoring & Observability](#monitoring--observability)
9. [Security Hardening](#security-hardening)
10. [Go-Live Checklist](#go-live-checklist)
11. [Operational Handoff](#operational-handoff)
12. [Support & Escalation](#support--escalation)

---

## Overview

This guide provides step-by-step instructions for deploying the **PubSec-Info-Assistant** RAG platform to production in Azure, meeting **ITSG-33**, **NIST SP 800-53**, and **Protected B** requirements.

**Target Audience**: Cloud Architects, DevOps Engineers, Security Leads  
**Deployment Model**: Azure Kubernetes Service (AKS) with Front Door + WAF  
**Compliance**: ITSG-33 / NIST 800-53 (38 controls), TB PADI evidence package  
**Expected Deployment Time**: 4–6 hours (excluding Azure resource provisioning)

---

## Prerequisites

### Required Azure Resources
- Azure Subscription with Owner or Contributor + RBAC Admin access
- Azure Key Vault with Managed Identity RBAC configured
- Azure Storage Account (Premium Blob, immutable tier for audit logs)
- Azure Monitor workspace with Application Insights
- Azure Container Registry (ACR) with Premium tier (geo-replication optional)
- Azure Virtual Network (VNet) with hub-spoke topology
- Azure Front Door Premium with WAF Policy
- Azure OpenAI endpoint (GPT-4 + text-embedding-ada-002)

### CI/CD Prerequisites
- GitHub repository with OIDC federation to Azure (see `docs/SECRETS-MANAGEMENT.md`)
- GitHub Actions secrets configured:
  - `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`
  - `STAGING_RG`, `STAGING_AKS_CLUSTER`
  - `PRODUCTION_RG`, `PRODUCTION_AKS_CLUSTER`

### Local Tooling
- Azure CLI ≥2.50
- kubectl ≥1.28
- Helm ≥3.12
- Docker ≥24.0
- k6 or Locust (for performance testing)

### Documentation Review
Ensure familiarity with:
- `docs/PRODUCTION-ARCHITECTURE.md` – Reference architecture
- `docs/PRODUCTION-READINESS-CHECKLIST.md` – Gate criteria
- `docs/SLO-SLA.md` – Performance targets
- `docs/SECRETS-MANAGEMENT.md` – Key Vault integration
- `docs/DR-RUNBOOK.md` – Backup/restore procedures
- `docs/INCIDENT-RESPONSE.md` – Security incident handling

---

## Architecture Summary

```
[Users/Agencies]
      ↓
[Azure Front Door + WAF (OWASP 3.2 + custom rules)]
      ↓
[Private Endpoint → AKS Ingress Controller]
      ↓
[AKS Production Namespace]
   ├─ Backend (FastAPI pods, non-root)
   ├─ Frontend (Nginx pods, security headers)
   ├─ Qdrant (vector DB, daily snapshots)
   └─ Redis (cache, AOF persistence)
      ↓
[Azure OpenAI (Private Endpoint)]
[Azure Key Vault (secrets via CSI driver)]
[Azure Blob Storage (documents + audit logs)]
[Azure Monitor (metrics/logs/traces)]
```

**Network Isolation**: Spoke VNet with NSGs; no public IPs on workloads; Private Endpoints for all PaaS services.

---

## Pre-Deployment Checklist

Use `docs/PRODUCTION-READINESS-CHECKLIST.md` as gate criteria. Verify:

- [ ] **Security Scans**: No HIGH/CRITICAL in latest CodeQL, Trivy, ZAP reports
- [ ] **Container Hardening**: Backend runs as non-root user, minimal base image
- [ ] **Secrets**: All secrets in Key Vault; no plaintext in config/env files
- [ ] **Audit Logging**: Structured JSON logs with tenant_id, event_type, timestamp
- [ ] **SLO/SLA Defined**: Query p95 ≤1200ms, uptime 99.9%, error rate <0.5%
- [ ] **Runbooks**: DR, Incident Response, Performance Testing, Data Retention committed
- [ ] **Compliance Mapping**: 32+ controls ✅ complete with evidence paths
- [ ] **DAST Baseline**: ZAP reports archived in `evidence/dast/`
- [ ] **Staging Gate**: `.github/workflows/deploy-staging-gate.yml` active

---

## Azure Infrastructure Setup

### 1. Create Resource Groups
```powershell
az group create --name rg-pubsec-prod-eastus --location eastus
az group create --name rg-pubsec-network --location eastus
az group create --name rg-pubsec-security --location eastus
```

### 2. Deploy VNet with Hub-Spoke
```powershell
# Hub VNet (shared services)
az network vnet create \
  --resource-group rg-pubsec-network \
  --name vnet-hub \
  --address-prefix 10.0.0.0/16 \
  --subnet-name AzureBastionSubnet \
  --subnet-prefix 10.0.0.0/27

# Spoke VNet (production workloads)
az network vnet create \
  --resource-group rg-pubsec-network \
  --name vnet-spoke-prod \
  --address-prefix 10.1.0.0/16 \
  --subnet-name snet-aks \
  --subnet-prefix 10.1.0.0/22

# Peering
az network vnet peering create \
  --resource-group rg-pubsec-network \
  --name hub-to-spoke \
  --vnet-name vnet-hub \
  --remote-vnet vnet-spoke-prod \
  --allow-vnet-access

az network vnet peering create \
  --resource-group rg-pubsec-network \
  --name spoke-to-hub \
  --vnet-name vnet-spoke-prod \
  --remote-vnet vnet-hub \
  --allow-vnet-access
```

### 3. Create AKS Cluster
```powershell
az aks create \
  --resource-group rg-pubsec-prod-eastus \
  --name aks-pubsec-prod \
  --node-count 3 \
  --node-vm-size Standard_D4s_v5 \
  --network-plugin azure \
  --vnet-subnet-id /subscriptions/{sub-id}/resourceGroups/rg-pubsec-network/providers/Microsoft.Network/virtualNetworks/vnet-spoke-prod/subnets/snet-aks \
  --enable-managed-identity \
  --enable-oidc-issuer \
  --enable-workload-identity \
  --enable-addons monitoring,azure-keyvault-secrets-provider \
  --workspace-resource-id /subscriptions/{sub-id}/resourceGroups/rg-pubsec-prod-eastus/providers/Microsoft.OperationalInsights/workspaces/log-pubsec-prod \
  --enable-private-cluster \
  --zones 1 2 3

az aks get-credentials --resource-group rg-pubsec-prod-eastus --name aks-pubsec-prod
```

### 4. Create Key Vault
```powershell
az keyvault create \
  --resource-group rg-pubsec-security \
  --name kv-pubsec-prod-xyz \
  --location eastus \
  --enable-rbac-authorization \
  --enable-purge-protection \
  --retention-days 90

# Grant Managed Identity access
az role assignment create \
  --role "Key Vault Secrets User" \
  --assignee {aks-managed-identity-object-id} \
  --scope /subscriptions/{sub-id}/resourceGroups/rg-pubsec-security/providers/Microsoft.KeyVault/vaults/kv-pubsec-prod-xyz

# Populate secrets
az keyvault secret set --vault-name kv-pubsec-prod-xyz --name azure-openai-api-key --value "{openai-key}"
az keyvault secret set --vault-name kv-pubsec-prod-xyz --name redis-password --value "{redis-password}"
```

### 5. Deploy Qdrant & Redis
```yaml
# qdrant-deployment.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: qdrant
  namespace: production
spec:
  serviceName: qdrant
  replicas: 2
  selector:
    matchLabels:
      app: qdrant
  template:
    metadata:
      labels:
        app: qdrant
    spec:
      containers:
      - name: qdrant
        image: qdrant/qdrant:v1.7.4
        ports:
        - containerPort: 6333
        volumeMounts:
        - name: qdrant-storage
          mountPath: /qdrant/storage
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
          limits:
            memory: "8Gi"
            cpu: "4"
  volumeClaimTemplates:
  - metadata:
      name: qdrant-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: managed-premium
      resources:
        requests:
          storage: 100Gi
---
apiVersion: v1
kind: Service
metadata:
  name: qdrant
  namespace: production
spec:
  clusterIP: None
  selector:
    app: qdrant
  ports:
  - port: 6333
```

```yaml
# redis-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: production
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7.2-alpine
        command: ["redis-server", "--appendonly", "yes", "--requirepass", "$(REDIS_PASSWORD)"]
        env:
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: password
        ports:
        - containerPort: 6379
        volumeMounts:
        - name: redis-data
          mountPath: /data
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
      volumes:
      - name: redis-data
        persistentVolumeClaim:
          claimName: redis-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: production
spec:
  selector:
    app: redis
  ports:
  - port: 6379
```

### 6. Create Front Door + WAF
```powershell
# Create WAF policy
az network front-door waf-policy create \
  --resource-group rg-pubsec-prod-eastus \
  --name wafPubSec \
  --mode Prevention \
  --sku Premium_AzureFrontDoor

# Add OWASP managed rule set
az network front-door waf-policy managed-rules add \
  --resource-group rg-pubsec-prod-eastus \
  --policy-name wafPubSec \
  --type Microsoft_DefaultRuleSet \
  --version 2.1

# Add custom rate limit rule
az network front-door waf-policy rule create \
  --resource-group rg-pubsec-prod-eastus \
  --policy-name wafPubSec \
  --name RateLimitRule \
  --rule-type RateLimitRule \
  --action Block \
  --rate-limit-threshold 1000 \
  --rate-limit-duration-in-minutes 5

# Create Front Door profile
az afd profile create \
  --resource-group rg-pubsec-prod-eastus \
  --profile-name fd-pubsec-prod \
  --sku Premium_AzureFrontDoor

# Create endpoint
az afd endpoint create \
  --resource-group rg-pubsec-prod-eastus \
  --profile-name fd-pubsec-prod \
  --endpoint-name pubsec-info-assistant

# Create origin group (point to AKS ingress Private Endpoint)
az afd origin-group create \
  --resource-group rg-pubsec-prod-eastus \
  --profile-name fd-pubsec-prod \
  --origin-group-name aks-origin \
  --probe-path /api/health \
  --probe-protocol Https

az afd origin create \
  --resource-group rg-pubsec-prod-eastus \
  --profile-name fd-pubsec-prod \
  --origin-group-name aks-origin \
  --origin-name aks-ingress \
  --host-name ingress.internal.example.com \
  --origin-host-header ingress.internal.example.com \
  --priority 1 \
  --weight 1000 \
  --enabled-state Enabled \
  --http-port 80 \
  --https-port 443
```

---

## Application Deployment

### 1. Create Kubernetes Namespace
```powershell
kubectl create namespace production
kubectl label namespace production istio-injection=enabled  # If using service mesh
```

### 2. Deploy Secrets via CSI Driver
```yaml
# secretproviderclass.yaml
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: azure-keyvault-secrets
  namespace: production
spec:
  provider: azure
  parameters:
    usePodIdentity: "false"
    useVMManagedIdentity: "true"
    userAssignedIdentityID: {aks-managed-identity-client-id}
    keyvaultName: kv-pubsec-prod-xyz
    tenantId: {azure-tenant-id}
    objects: |
      array:
        - |
          objectName: azure-openai-api-key
          objectType: secret
        - |
          objectName: redis-password
          objectType: secret
```

### 3. Deploy Backend
```yaml
# backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      serviceAccountName: backend-sa
      containers:
      - name: backend
        image: ghcr.io/{org}/pubsec-info-assistant-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: AZURE_OPENAI_ENDPOINT
          value: "https://{openai-resource}.openai.azure.com/"
        - name: AZURE_OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: keyvault-secrets
              key: azure-openai-api-key
        - name: QDRANT_HOST
          value: "qdrant.production.svc.cluster.local"
        - name: REDIS_HOST
          value: "redis.production.svc.cluster.local"
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: keyvault-secrets
              key: redis-password
        volumeMounts:
        - name: secrets-store
          mountPath: "/mnt/secrets"
          readOnly: true
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
        livenessProbe:
          httpGet:
            path: /api/health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: secrets-store
        csi:
          driver: secrets-store.csi.k8s.io
          readOnly: true
          volumeAttributes:
            secretProviderClass: azure-keyvault-secrets
---
apiVersion: v1
kind: Service
metadata:
  name: backend
  namespace: production
spec:
  selector:
    app: backend
  ports:
  - port: 8000
```

### 4. Deploy Frontend
```yaml
# frontend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: frontend
        image: ghcr.io/{org}/pubsec-info-assistant-frontend:latest
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1"
---
apiVersion: v1
kind: Service
metadata:
  name: frontend
  namespace: production
spec:
  selector:
    app: frontend
  ports:
  - port: 80
```

### 5. Deploy Ingress Controller
```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: pubsec-ingress
  namespace: production
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/backend-protocol: "HTTP"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - pubsec-info-assistant.example.com
    secretName: tls-cert
  rules:
  - host: pubsec-info-assistant.example.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: backend
            port:
              number: 8000
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 80
```

### 6. Apply Manifests
```powershell
kubectl apply -f qdrant-deployment.yaml
kubectl apply -f redis-deployment.yaml
kubectl apply -f secretproviderclass.yaml
kubectl apply -f backend-deployment.yaml
kubectl apply -f frontend-deployment.yaml
kubectl apply -f ingress.yaml

# Wait for rollouts
kubectl rollout status deployment/backend -n production --timeout=10m
kubectl rollout status deployment/frontend -n production --timeout=10m
```

---

## Post-Deployment Validation

### 1. Health Checks
```powershell
# Backend health
kubectl exec -it deployment/backend -n production -- curl http://localhost:8000/api/health

# Frontend (from within cluster)
kubectl run curl-test --image=curlimages/curl --rm -it --restart=Never -- curl http://frontend.production.svc.cluster.local
```

### 2. End-to-End Smoke Test
```powershell
# Test ingestion
curl -X POST https://pubsec-info-assistant.example.com/api/v1/ingest \
  -H "X-Tenant-ID: tenant-prod-001" \
  -H "Content-Type: application/json" \
  -d '{"document_id": "smoke-test-001", "content": "This is a production smoke test.", "metadata": {}}'

# Test query
curl -X POST https://pubsec-info-assistant.example.com/api/v1/query \
  -H "X-Tenant-ID: tenant-prod-001" \
  -H "Content-Type: application/json" \
  -d '{"query": "smoke test"}'
```

### 3. Performance Baseline
Run k6 load test (see `docs/PERFORMANCE-TESTING.md`):
```powershell
k6 run --vus 50 --duration 5m .github/performance/k6-query-load.js
```

Expected results:
- p95 query latency ≤1200ms
- Error rate <0.5%
- Throughput ≥100 req/s

### 4. Security Validation
- [ ] ZAP active scan: No HIGH/CRITICAL (run via `.github/workflows/deploy-staging-gate.yml`)
- [ ] TLS certificate valid (CN matches, not expired)
- [ ] WAF blocking malicious payloads (test SQL injection, XSS)
- [ ] Secrets not in logs: `kubectl logs -n production deployment/backend | grep -i "api[_-]key"`

---

## Monitoring & Observability

### 1. Configure Prometheus Scraping
```yaml
# servicemonitor.yaml (if using Prometheus Operator)
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: backend-metrics
  namespace: production
spec:
  selector:
    matchLabels:
      app: backend
  endpoints:
  - port: metrics
    interval: 30s
```

### 2. Create Grafana Dashboards
Import dashboards from `monitoring/grafana/`:
- Query Latency (p50/p95/p99)
- Error Rate by Endpoint
- Qdrant Collection Size
- Redis Hit Rate

### 3. Set Up Alerts
```yaml
# prometheus-alerts.yaml
groups:
- name: pubsec-slo
  rules:
  - alert: HighQueryLatency
    expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job="backend"}[5m])) > 1.2
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "p95 query latency exceeds SLO (>1200ms)"
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.005
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "Error rate >0.5%"
```

### 4. Enable Azure Monitor Integration
```powershell
az monitor diagnostic-settings create \
  --name pubsec-diagnostics \
  --resource /subscriptions/{sub-id}/resourceGroups/rg-pubsec-prod-eastus/providers/Microsoft.ContainerService/managedClusters/aks-pubsec-prod \
  --logs '[{"category":"kube-apiserver","enabled":true},{"category":"kube-audit","enabled":true}]' \
  --metrics '[{"category":"AllMetrics","enabled":true}]' \
  --workspace /subscriptions/{sub-id}/resourceGroups/rg-pubsec-prod-eastus/providers/Microsoft.OperationalInsights/workspaces/log-pubsec-prod
```

---

## Security Hardening

### 1. Enable Pod Security Standards
```yaml
# podsecuritypolicy.yaml (PSS enforced at namespace level)
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

### 2. Network Policies
```yaml
# networkpolicy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-netpol
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: ingress-controller
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: qdrant
    ports:
    - protocol: TCP
      port: 6333
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
  - to:  # Azure OpenAI Private Endpoint
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 443
```

### 3. RBAC Least Privilege
```yaml
# backend-rbac.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: backend-sa
  namespace: production
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: backend-role
  namespace: production
rules:
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: backend-rolebinding
  namespace: production
subjects:
- kind: ServiceAccount
  name: backend-sa
roleRef:
  kind: Role
  name: backend-role
  apiGroup: rbac.authorization.k8s.io
```

### 4. Enable Audit Logging to Blob Storage
Configure backend to stream audit logs to Azure Blob (append-only, immutable):
```python
# backend/app/audit_sink.py (pseudo)
from azure.storage.blob import BlobServiceClient

blob_client = BlobServiceClient.from_connection_string(os.getenv("AUDIT_STORAGE_CONN"))
container = blob_client.get_container_client("audit-logs")

def emit_audit_event(event):
    blob_name = f"{event['tenant_id']}/{datetime.utcnow().strftime('%Y/%m/%d')}/audit.jsonl"
    blob = container.get_blob_client(blob_name)
    blob.append_block(json.dumps(event) + "\n")
```

---

## Go-Live Checklist

Before announcing production availability:

- [ ] **Functional Testing**: All API endpoints (ingest, query, delete, stats) validated
- [ ] **Performance**: Baseline load test meets SLOs (p95 query ≤1200ms, error rate <0.5%)
- [ ] **Security**: ZAP active scan passed, WAF rules active, no secrets in logs
- [ ] **Compliance**: Evidence archive complete (`evidence/` directory committed)
- [ ] **Monitoring**: Grafana dashboards live, alerts firing to correct channels
- [ ] **DR**: Backup jobs scheduled (Qdrant daily snapshots, Redis AOF, Blob lifecycle)
- [ ] **Documentation**: All runbooks accessible to ops team (DR, IR, Perf Testing, Retention)
- [ ] **Audit Logging**: Structured logs streaming to immutable Blob storage
- [ ] **Secrets Rotation**: Key Vault rotation policy enabled (quarterly)
- [ ] **Incident Response**: On-call rotation configured, escalation contacts verified
- [ ] **Capacity Planning**: Baseline metrics recorded, scaling thresholds documented
- [ ] **User Acceptance Testing**: Sample tenants onboarded, feedback collected
- [ ] **Change Advisory Board**: Production deployment approved by stakeholders

---

## Operational Handoff

Transfer ownership to operations team:

1. **Documentation Package**:
   - `docs/PRODUCTION-ARCHITECTURE.md` – Reference architecture
   - `docs/DR-RUNBOOK.md` – Disaster recovery procedures
   - `docs/INCIDENT-RESPONSE.md` – Security incident handling
   - `docs/PERFORMANCE-TESTING.md` – Load testing scenarios
   - `docs/DATA-RETENTION.md` – Purge policies
   - `docs/API-VERSIONING.md` – Deprecation strategy
   - `docs/EDGE-SECURITY.md` – WAF configuration
   - `docs/TENANCY-ISOLATION.md` – Isolation review

2. **Access & Credentials**:
   - Azure RBAC roles granted (Contributor for ops, Reader for support)
   - Grafana read-only access for L1 support
   - PagerDuty/Slack alerting channels configured

3. **Training Sessions**:
   - DR drill walkthrough (restore from Qdrant snapshot)
   - Incident response tabletop exercise (credential compromise scenario)
   - Performance tuning workshop (Redis cache optimization)

4. **Weekly Sync**:
   - Review SLO burn rate, adjust error budgets
   - Update compliance mapping with new evidence
   - Prioritize backlog items (JWT enhancement, per-tenant encryption)

---

## Support & Escalation

### L1 Support (24x7 NOC)
- **Scope**: Service degradation, health check failures, alert triage
- **SLA**: Acknowledge within 15 minutes
- **Contact**: support@example.com, PagerDuty escalation policy

### L2 Engineering (Business Hours)
- **Scope**: Performance tuning, log analysis, configuration changes
- **SLA**: Respond within 2 hours (SEV-2)
- **Contact**: engineering@example.com

### L3 Security (On-Call)
- **Scope**: Security incidents, compliance inquiries, audit support
- **SLA**: Respond within 1 hour (SEV-1 security)
- **Contact**: security@example.com, PagerDuty SEV-1 policy

### Vendor Escalation
- **Azure Support**: Premier support contract, TAM assigned
- **OpenAI Support**: Enterprise tier SLA (email support@openai.com)

---

## Conclusion

The **PubSec-Info-Assistant** is now production-ready with:
- ✅ **38 ITSG-33 / NIST 800-53 controls** implemented with evidence
- ✅ **Hardened containers** (non-root, minimal attack surface)
- ✅ **Comprehensive monitoring** (Prometheus, Grafana, Azure Monitor)
- ✅ **Automated security gates** (CodeQL, SAST, DAST, container scans)
- ✅ **Operational runbooks** (DR, IR, performance, retention, versioning)
- ✅ **Protected B classification** aligned with TB PADI requirements

**Next Steps**:
1. Execute go-live checklist
2. Monitor SLO burn rate for first 48 hours
3. Conduct post-deployment review after 1 week
4. Plan Phase 2 enhancements (JWT/OAuth, per-tenant encryption, active-active DR)

For questions or issues, consult runbooks or escalate per support matrix above.

---

**Document Version**: 1.0  
**Last Updated**: 2025-01-01  
**Maintained By**: Cloud Architecture Team  
**Classification**: Unclassified (deployment guide contains no secrets)
