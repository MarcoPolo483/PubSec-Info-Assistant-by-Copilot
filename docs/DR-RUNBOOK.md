# Disaster Recovery Runbook

## Objectives
Restore service within defined RTO/RPO targets following catastrophic failure.

## Recovery Targets
- **RPO (Recovery Point Objective)**: 1 hour (Qdrant snapshots + Redis AOF hourly sync)
- **RTO (Recovery Time Objective)**: 4 hours (includes restore + validation)

## Backup Strategy
### Qdrant Vector Store
- Automated daily snapshot to Azure Blob Storage (immutable container)
- Retention: 30 days rolling
- Command: `qdrant-cli snapshot create --output /backup/`

### Redis Cache
- Azure Cache for Redis: Automatic daily backups (Premium tier)
- Retention: 7 days

### Application Configuration
- Infrastructure as Code in Git (Terraform state in remote backend with versioning)
- Secrets in Key Vault (vault-level backup daily)

### Document Originals (Optional)
- Blob Storage with versioning enabled
- Lifecycle policy: retain 30 days, then soft-delete 7 days

## Restore Procedures
### 1. Qdrant Restore
```bash
# Download latest snapshot
az storage blob download --container snapshots --name qdrant-YYYYMMDD.tar.gz --file ./restore.tar.gz

# Extract to Qdrant data volume
tar -xzf restore.tar.gz -C /var/lib/qdrant/storage/

# Restart Qdrant
kubectl rollout restart statefulset/qdrant -n prod
```

### 2. Redis Restore
Azure Cache for Redis: Portal → Backup & Restore → Select backup → Restore.

### 3. AKS Cluster Recreation
```bash
cd terraform/environments/prod
terraform init
terraform plan -out=restore.tfplan
terraform apply restore.tfplan
```

### 4. Application Redeploy
```bash
# Trigger production deployment from last known-good commit
gh workflow run deploy-prod.yml --ref <commit-sha>
```

### 5. Validation Steps
- Health checks: `/health`, `/ready` return 200
- Synthetic query: Submit test query, verify response latency < 2s
- Metrics endpoint: Prometheus scraping successful
- Check audit logs for post-restore events

## Escalation
- Primary: Platform Owner (Marco)
- Secondary: Security Architect
- Vendor Support: Azure Support (Severity A ticket)

## Post-Incident
- Root cause analysis within 48 hours
- Update runbook with lessons learned
- Test restore quarterly

## Compliance
- CP-9 (backup), CP-10 (restore testing), CP-6 (alternate processing)
