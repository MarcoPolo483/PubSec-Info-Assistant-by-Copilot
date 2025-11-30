# Disaster Recovery Plan

**Document Version**: 1.0  
**Last Updated**: November 30, 2024  
**Review Frequency**: Quarterly  
**Owner**: DevOps Team

## Executive Summary

This Disaster Recovery (DR) plan defines procedures for recovering the PubSec Info Assistant system in the event of catastrophic failure, data loss, or regional outage.

### Recovery Objectives

| Metric | Target | Maximum Acceptable |
|--------|--------|-------------------|
| **RTO** (Recovery Time Objective) | 2 hours | 4 hours |
| **RPO** (Recovery Point Objective) | 30 minutes | 1 hour |
| **Data Loss** | < 0.1% | < 1% |
| **Availability** | 99.9% | 99.5% |

### Disaster Scenarios Covered

1. **Regional Outage** - Primary cloud region unavailable
2. **Data Corruption** - Database corruption or ransomware
3. **Complete Infrastructure Loss** - Total cloud provider failure
4. **Security Breach** - Compromised credentials or data breach
5. **Human Error** - Accidental deletion of critical resources

---

## 1. Backup Strategy

### 1.1 Qdrant Vector Database Backups

**Frequency**: Every 6 hours  
**Retention**: 30 days  
**Storage**: S3/Azure Blob with cross-region replication

```bash
# Automated backup script (runs via CronJob)
#!/bin/bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="qdrant-backup-${TIMESTAMP}"

# Create Qdrant snapshot
kubectl exec qdrant-0 -n pubsec-info-assistant -- \
  curl -X POST http://localhost:6333/snapshots

# Copy snapshot to S3
kubectl exec qdrant-0 -n pubsec-info-assistant -- \
  aws s3 cp /qdrant/storage/snapshots/latest.snapshot \
  s3://pubsec-backups/qdrant/${BACKUP_NAME}.snapshot

# Verify backup integrity
aws s3api head-object --bucket pubsec-backups \
  --key qdrant/${BACKUP_NAME}.snapshot
```

**Backup Monitoring**:
```promql
# Alert if backup older than 7 hours
time() - qdrant_last_backup_timestamp > 25200
```

### 1.2 Redis Cache Backups

**Frequency**: Every 5 minutes (AOF), Daily (RDB)  
**Retention**: 7 days  
**Storage**: Persistent volumes with daily snapshots

```bash
# Trigger Redis save
kubectl exec redis-0 -n pubsec-info-assistant -- redis-cli BGSAVE

# Copy RDB to backup location
kubectl cp pubsec-info-assistant/redis-0:/data/dump.rdb \
  ./backups/redis-$(date +%Y%m%d).rdb

# Upload to S3
aws s3 cp ./backups/redis-$(date +%Y%m%d).rdb \
  s3://pubsec-backups/redis/
```

### 1.3 Configuration Backups

**Frequency**: On every change  
**Storage**: Git repository + encrypted S3 bucket

```bash
# Backup Kubernetes configs
kubectl get all,cm,secrets,pvc -n pubsec-info-assistant -o yaml \
  > k8s-backup-$(date +%Y%m%d).yaml

# Encrypt and upload
gpg --encrypt --recipient devops@pubsec.gov k8s-backup-*.yaml
aws s3 cp k8s-backup-*.yaml.gpg s3://pubsec-backups/configs/
```

### 1.4 Application State Backups

**Tenant Balances**: Real-time replication to secondary Redis  
**Rate Limit Counters**: Can be reconstructed (acceptable loss)  
**Cache Data**: Can be rebuilt from source (acceptable loss)

---

## 2. Recovery Procedures

### 2.1 Regional Failover (RTO: 30 minutes)

**Trigger**: Primary region unavailable for >15 minutes

**Steps**:

1. **Verify Secondary Region Readiness**
   ```bash
   # Check secondary cluster health
   kubectl --context=secondary-region get nodes
   kubectl --context=secondary-region get pods -n pubsec-info-assistant
   ```

2. **Update DNS Records**
   ```bash
   # Route 53 - Switch to secondary region
   aws route53 change-resource-record-sets \
     --hosted-zone-id Z1234567890ABC \
     --change-batch file://failover-to-secondary.json
   
   # Verify propagation
   dig pubsec-info-assistant.com
   ```

3. **Restore Latest Data**
   ```bash
   # Restore Qdrant from latest backup
   ./scripts/restore-qdrant.sh --source=s3://pubsec-backups/qdrant/latest \
     --target=secondary-region
   
   # Restore Redis from AOF
   ./scripts/restore-redis.sh --source=s3://pubsec-backups/redis/latest
   ```

4. **Verify Services**
   ```bash
   # Health checks
   curl https://pubsec-info-assistant.com/health
   curl https://pubsec-info-assistant.com/ready
   
   # Test query
   curl -X POST https://pubsec-info-assistant.com/api/v1/query?query=test
   ```

5. **Update Status Page**
   ```
   "We have successfully failed over to our secondary region. 
   Service is now restored. Data from the last 30 minutes is being synchronized."
   ```

**Expected Downtime**: 15-30 minutes  
**Expected Data Loss**: Up to 30 minutes of tenant balance updates

### 2.2 Database Corruption Recovery (RTO: 2 hours)

**Trigger**: Qdrant data corruption detected, CRC errors, or ransomware

**Steps**:

1. **Isolate Affected Systems**
   ```bash
   # Scale down to prevent further corruption
   kubectl scale statefulset/qdrant --replicas=0 -n pubsec-info-assistant
   
   # Take snapshot of corrupted state for forensics
   kubectl exec qdrant-0 -n pubsec-info-assistant -- \
     tar czf /tmp/corrupted-state.tar.gz /qdrant/storage
   ```

2. **Identify Last Good Backup**
   ```bash
   # List available backups
   aws s3 ls s3://pubsec-backups/qdrant/ --recursive
   
   # Verify backup integrity
   aws s3 cp s3://pubsec-backups/qdrant/20241130_140000.snapshot /tmp/
   qdrant-cli verify-snapshot /tmp/20241130_140000.snapshot
   ```

3. **Restore from Backup**
   ```bash
   # Delete corrupted volumes
   kubectl delete pvc qdrant-storage-qdrant-0 -n pubsec-info-assistant
   kubectl delete pvc qdrant-storage-qdrant-1 -n pubsec-info-assistant
   kubectl delete pvc qdrant-storage-qdrant-2 -n pubsec-info-assistant
   
   # Create new PVCs
   kubectl apply -f k8s/base/statefulsets.yaml
   
   # Restore each replica
   for i in {0..2}; do
     kubectl cp /tmp/20241130_140000.snapshot \
       pubsec-info-assistant/qdrant-$i:/qdrant/storage/snapshots/restore.snapshot
     
     kubectl exec qdrant-$i -n pubsec-info-assistant -- \
       curl -X POST http://localhost:6333/snapshots/restore \
       -d '{"snapshot": "restore.snapshot"}'
   done
   
   # Scale up
   kubectl scale statefulset/qdrant --replicas=3 -n pubsec-info-assistant
   ```

4. **Verify Data Integrity**
   ```bash
   # Check collection stats
   kubectl exec qdrant-0 -n pubsec-info-assistant -- \
     curl http://localhost:6333/collections
   
   # Sample queries
   python scripts/verify-data-integrity.py --sample-size=1000
   ```

5. **Replay Missed Transactions** (if logs available)
   ```bash
   # Re-ingest documents uploaded after backup
   python scripts/replay-ingestion-logs.py \
     --from-timestamp="2024-11-30T14:00:00Z" \
     --to-timestamp="2024-11-30T16:00:00Z"
   ```

**Expected Downtime**: 1-2 hours  
**Expected Data Loss**: Documents ingested after last backup (up to 6 hours)

### 2.3 Complete Infrastructure Loss (RTO: 4 hours)

**Trigger**: Cloud provider failure, account compromise, or catastrophic deletion

**Steps**:

1. **Provision New Infrastructure**
   ```bash
   # Terraform - Deploy to new cloud provider or account
   cd terraform/azure  # or aws/gcp
   terraform init
   terraform plan -out=disaster-recovery.tfplan
   terraform apply disaster-recovery.tfplan
   ```

2. **Deploy Kubernetes Cluster**
   ```bash
   # AKS example
   az aks create --resource-group pubsec-dr \
     --name pubsec-cluster-dr \
     --node-count 5 \
     --enable-addons monitoring \
     --generate-ssh-keys
   
   # Get credentials
   az aks get-credentials --resource-group pubsec-dr \
     --name pubsec-cluster-dr
   ```

3. **Deploy Application**
   ```bash
   # Create namespace
   kubectl create namespace pubsec-info-assistant
   
   # Apply Kubernetes manifests
   kubectl apply -k k8s/overlays/production
   
   # Create secrets
   kubectl create secret generic pubsec-secrets \
     --from-literal=openai-api-key=$OPENAI_API_KEY \
     --from-literal=secret-key=$SECRET_KEY \
     -n pubsec-info-assistant
   ```

4. **Restore All Data**
   ```bash
   # Parallel restoration
   ./scripts/restore-qdrant.sh --source=s3://pubsec-backups/qdrant/latest &
   ./scripts/restore-redis.sh --source=s3://pubsec-backups/redis/latest &
   wait
   ```

5. **Update DNS**
   ```bash
   # Point to new infrastructure
   aws route53 change-resource-record-sets \
     --hosted-zone-id Z1234567890ABC \
     --change-batch file://new-infrastructure.json
   ```

6. **Smoke Tests**
   ```bash
   # Run full test suite
   pytest backend/tests/ --base-url=https://pubsec-info-assistant.com
   playwright test --base-url=https://pubsec-info-assistant.com
   ```

**Expected Downtime**: 2-4 hours  
**Expected Data Loss**: Minimal (up to 30 minutes)

---

## 3. Recovery Testing

### 3.1 Monthly DR Drills

**Schedule**: First Sunday of each month, 2:00 AM UTC

**Test Scenarios** (rotating):
- Month 1: Regional failover test
- Month 2: Database restore from backup
- Month 3: Complete infrastructure rebuild
- Month 4: Security breach simulation

**Success Criteria**:
- RTO < 4 hours
- RPO < 1 hour
- All tests passing post-recovery
- Documentation accurate

### 3.2 Automated Recovery Tests

```bash
# Weekly backup verification
./scripts/test-backup-restore.sh --backup-date=latest --dry-run

# Daily backup integrity checks
aws s3 sync s3://pubsec-backups/qdrant/ /tmp/backup-test/ --dryrun
```

---

## 4. Data Retention Policy

| Data Type | Retention | Backup Frequency | Storage Location |
|-----------|-----------|------------------|------------------|
| Vector embeddings | 3 years | 6 hours | S3 Standard |
| Document metadata | 3 years | 6 hours | S3 Standard |
| Query logs | 90 days | Daily | S3 Glacier |
| Tenant balances | 7 years | Real-time | Multi-region Redis |
| Audit logs | 7 years | Real-time | S3 Glacier + CloudWatch |
| System metrics | 90 days | 1 minute | Prometheus + S3 |
| Backups | 30 days | Per policy | S3 Standard-IA |

---

## 5. Communication Plan

### 5.1 Internal Communication

**Slack Channels**:
- `#pubsec-incidents` - Active incident coordination
- `#pubsec-alerts` - Automated monitoring alerts
- `#pubsec-dr` - DR testing and planning

**Email Distribution Lists**:
- `engineering@pubsec.gov` - All engineers
- `oncall@pubsec.gov` - On-call rotation
- `executives@pubsec.gov` - Leadership team

### 5.2 External Communication

**Status Page**: https://status.pubsec-info-assistant.com

**Customer Email Template** (Major Outage):
```
Subject: Service Restoration Update - PubSec Info Assistant

Dear Valued Customer,

We experienced a service disruption affecting the PubSec Info Assistant 
platform between [START_TIME] and [END_TIME] UTC.

IMPACT:
- [Describe impact]

ROOT CAUSE:
- [Brief explanation]

RESOLUTION:
- [What was done]

DATA IMPACT:
- [Any data loss or inconsistency]

We sincerely apologize for any inconvenience. If you have questions, 
please contact support@pubsec.gov.

Regards,
PubSec Info Assistant Team
```

---

## 6. Post-Recovery Validation

### 6.1 Health Checks

```bash
# System health
curl https://pubsec-info-assistant.com/health | jq

# Component connectivity
./scripts/test-connectivity.sh

# Data integrity
python scripts/validate-data-integrity.py --full-scan
```

### 6.2 Performance Validation

```bash
# Load test to ensure capacity
k6 run --vus 500 --duration 10m k6-tests/load-test.js

# Latency verification
curl -w "@curl-format.txt" -o /dev/null -s \
  https://pubsec-info-assistant.com/api/v1/query?query=test
```

### 6.3 Data Consistency Checks

```bash
# Compare record counts
./scripts/compare-backup-counts.sh \
  --backup-date=20241130_140000 \
  --current-state=live

# Verify tenant balances
python scripts/verify-tenant-balances.py --reconcile
```

---

## 7. Continuous Improvement

### 7.1 Post-Incident Reviews

After each DR event or test:
1. Schedule post-mortem within 48 hours
2. Document lessons learned
3. Update runbooks
4. Create Jira tickets for improvements
5. Share learnings with team

### 7.2 Metrics to Track

- **MTTR** (Mean Time To Recover): Target < 2 hours
- **MTBF** (Mean Time Between Failures): Target > 720 hours (30 days)
- **Backup Success Rate**: Target > 99.9%
- **DR Test Success Rate**: Target > 95%

---

## Appendix A: Emergency Contacts

| Role | Primary | Secondary | Phone | Email |
|------|---------|-----------|-------|-------|
| On-Call Engineer | Rotating | Rotating | +1-XXX-XXX-XXXX | oncall@pubsec.gov |
| DevOps Lead | [Name] | [Name] | +1-XXX-XXX-XXXX | devops@pubsec.gov |
| Security Team | [Name] | [Name] | +1-XXX-XXX-XXXX | security@pubsec.gov |
| Cloud Provider Support | N/A | N/A | +1-800-XXX-XXXX | support@provider.com |

## Appendix B: Backup Inventory

Current backup sizes (as of November 2024):
- Qdrant snapshots: ~50 GB per backup
- Redis RDB: ~5 GB per backup
- Configuration: ~10 MB per backup
- Total daily backup storage: ~450 GB
- 30-day retention cost: ~$15,000/month

## Appendix C: Related Documents

- [P0 Incident Runbooks](./P0-INCIDENTS.md)
- [Security Incident Response Plan](./SECURITY-INCIDENT.md)
- [Business Continuity Plan](./BUSINESS-CONTINUITY.md)
- [Backup Verification Procedures](./BACKUP-VERIFICATION.md)
