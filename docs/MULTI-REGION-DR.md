# Multi-Region DR Architecture

## Executive Summary

This document defines the multi-region disaster recovery strategy for the PubSec-Info-Assistant, achieving **RPO <1 hour** and **RTO <4 hours** with automated failover capabilities.

## Architecture Overview

```
Primary Region (Canada Central)          Secondary Region (Canada East)
┌─────────────────────────────┐         ┌─────────────────────────────┐
│  AKS Production Cluster     │         │  AKS DR Cluster (cold/warm) │
│  ├─ Backend Pods (active)   │ ◄─────► │  ├─ Backend Pods (standby)  │
│  ├─ Frontend Pods (active)  │  Sync  │  ├─ Frontend Pods (standby) │
│  └─ Services                │         │  └─ Services                │
├─────────────────────────────┤         ├─────────────────────────────┤
│  Qdrant (active)            │ ◄─────► │  Qdrant (replica)           │
│  └─ Daily snapshots → Blob  │  Async  │  └─ Restored from Blob      │
├─────────────────────────────┤         ├─────────────────────────────┤
│  Redis (active)             │ ◄─────► │  Redis (replica - optional) │
│  └─ AOF → Blob backup       │  Async  │  └─ Restored from AOF       │
├─────────────────────────────┤         ├─────────────────────────────┤
│  Azure Blob (GRS)           │ ═══════►│  Azure Blob (replicated)    │
│  └─ Audit logs, documents   │   Geo   │  └─ Read-only access        │
├─────────────────────────────┤         ├─────────────────────────────┤
│  Key Vault (replicated)     │ ═══════►│  Key Vault (replica)        │
│  └─ Secrets, certs          │   Auto  │  └─ Same secrets            │
└─────────────────────────────┘         └─────────────────────────────┘
               │                                       │
               └───────────────────┬───────────────────┘
                                   │
                           Azure Front Door
                              (Global)
                    ┌───────────────────────┐
                    │  Traffic Manager      │
                    │  - Health probes      │
                    │  - Auto failover      │
                    │  - Priority routing   │
                    └───────────────────────┘
```

## Deployment Models

### 1. Cold Standby (Initial - Cost-Optimized)
- **Primary**: Full production workload
- **Secondary**: Infrastructure provisioned, minimal/no pods running
- **RTO**: 4 hours (manual restore + validation)
- **Cost**: 10-20% of primary region
- **Use case**: Budget-constrained, acceptable downtime

### 2. Warm Standby (Recommended - Balanced)
- **Primary**: Full production workload
- **Secondary**: Reduced capacity (25-50% pods), continuous data sync
- **RTO**: 1 hour (scale up + DNS switch)
- **Cost**: 40-60% of primary region
- **Use case**: Balanced cost/availability

### 3. Active-Active (Future - High Availability)
- **Primary**: 100% capacity
- **Secondary**: 100% capacity, active serving traffic
- **RTO**: < 5 minutes (automatic failover)
- **Cost**: 190% of primary region (2x infra + orchestration)
- **Use case**: Zero-tolerance downtime (Phase 2+)

## Data Replication Strategy

### Qdrant Vector Database
**Method**: Snapshot-based replication
```yaml
Primary (Canada Central):
  - Nightly snapshot at 02:00 UTC
  - Upload to Blob Storage (GRS)
  - Retention: 30 days

Secondary (Canada East):
  - Poll Blob every 1 hour for new snapshots
  - Auto-restore latest snapshot to standby Qdrant
  - Validation: Vector count comparison

RPO: 1 hour (last successful snapshot)
RTO: 2 hours (restore + validation)
```

**Automation**:
```python
# scripts/dr_qdrant_sync.py
async def sync_qdrant_to_secondary():
    # 1. Download latest snapshot from primary Blob
    # 2. Upload to secondary Qdrant
    # 3. Validate collection count
    # 4. Log replication status
```

### Redis Cache
**Method**: AOF backup replication
```yaml
Primary:
  - AOF enabled with fsync every second
  - Hourly backup to Blob Storage (GRS)
  - Retention: 7 days

Secondary:
  - Restore from latest AOF on failover
  - Optional: Redis Enterprise Geo-Replication (future)

RPO: 1 hour (last AOF backup)
RTO: 30 minutes (restore + cache warmup)
```

**Degraded Mode**: Secondary can operate without cache (queries hit database directly)

### Azure Blob Storage
**Method**: Geo-Redundant Storage (GRS)
```yaml
Replication:
  - Automatic Azure-managed replication
  - Documents and audit logs replicated asynchronously
  - Read-only access in secondary during normal operation

RPO: < 15 minutes (Azure SLA)
RTO: 0 minutes (instant read access on failover)
```

**Failover Trigger**:
```bash
# Initiate account failover (manual approval required)
az storage account failover --name stpubsecprodxyz --resource-group rg-pubsec-prod-eastus --yes
```

### Azure Key Vault
**Method**: Azure-managed replication
```yaml
Replication:
  - Automatic multi-region replication (Azure-managed)
  - Secrets available in both regions immediately
  - No manual sync required

RPO: 0 (synchronous)
RTO: 0 (instant access)
```

### Azure OpenAI
**Method**: Multi-region endpoint configuration
```yaml
Primary: Canada Central endpoint
Secondary: Canada East endpoint (separate resource)

Failover:
  - Update backend config to secondary endpoint
  - Redeploy pods with new env var
  - No data migration needed

RTO: 15 minutes (config change + pod restart)
```

## Failover Procedures

### Automatic Failover (Front Door)
```yaml
Health Probe Configuration:
  - Endpoint: https://primary-aks/health
  - Interval: 30 seconds
  - Failure threshold: 3 consecutive failures (90s)
  - Action: Route traffic to secondary origin

Trigger Conditions:
  - Primary health check fails
  - Primary returns 5xx for > 90 seconds
  - Network partition detected

Automated Actions:
  1. Front Door marks primary unhealthy
  2. Traffic routed to secondary endpoint
  3. Alert sent to ops team (PagerDuty/Teams)
  4. No manual intervention required
```

### Manual Failover (Disaster Scenario)
```bash
#!/bin/bash
# scripts/failover-to-secondary.sh

set -e

echo "Initiating manual DR failover to Canada East..."

# 1. Scale secondary AKS to production capacity
az aks scale \
  --resource-group rg-pubsec-dr-canadaeast \
  --name aks-pubsec-dr \
  --node-count 6

# 2. Restore latest Qdrant snapshot
python scripts/dr_manager.py restore \
  --type qdrant \
  --timestamp latest \
  --region canadaeast

# 3. Restore Redis AOF
python scripts/dr_manager.py restore \
  --type redis \
  --timestamp latest \
  --region canadaeast

# 4. Update Front Door priority routing
az afd route update \
  --resource-group rg-pubsec-prod-eastus \
  --profile-name fd-pubsec-prod \
  --endpoint-name pubsec-info-assistant \
  --route-name default-route \
  --origin-group aks-origin-canadaeast

# 5. Validate secondary health
curl -f https://secondary-aks.canadaeast.cloudapp.azure.com/health || exit 1

# 6. Monitor logs
kubectl logs -f deployment/backend -n production --tail=100

echo "Failover complete. Monitor dashboards for validation."
```

**Expected Timeline**:
- **T+0**: Disaster declared, script initiated
- **T+15min**: Secondary AKS scaled, pods ready
- **T+45min**: Qdrant snapshot restored, validated
- **T+60min**: Redis restored, cache warming
- **T+90min**: Front Door updated, traffic flowing
- **T+120min**: Full validation complete, ops team notified

### Failback Procedure
```bash
#!/bin/bash
# scripts/failback-to-primary.sh

# 1. Verify primary region is healthy
# 2. Sync any data changes from secondary → primary
# 3. Gradual traffic shift (10% → 50% → 100%)
# 4. Monitor for 24 hours before decommissioning DR workload
```

## Testing & Validation

### Quarterly DR Drill
```yaml
Objective: Validate RTO/RPO targets and team readiness

Steps:
  1. Announce drill (non-business hours)
  2. Simulate primary region failure
  3. Execute manual failover script
  4. Validate all services operational
  5. Run smoke tests (ingest, query, auth)
  6. Measure actual RTO (target: < 4 hours)
  7. Failback to primary
  8. Document lessons learned

Success Criteria:
  - Secondary operational within RTO
  - No data loss beyond RPO
  - All team members follow runbook
  - Post-drill improvements identified

Next Drill: Scheduled for 2025-Q1
```

### Continuous Validation
```yaml
Daily:
  - Qdrant snapshot size comparison (primary vs backup)
  - Redis AOF backup verification
  - Blob replication lag monitoring

Weekly:
  - Secondary AKS pod health check
  - Key Vault secret sync validation
  - Front Door routing simulation

Monthly:
  - Restore test (secondary from backup)
  - Performance baseline comparison
  - Cost optimization review
```

## Monitoring & Alerts

### Critical Alerts
```yaml
- name: Primary Region Unhealthy
  condition: health_check_failures > 3
  severity: SEV-1
  action: Page on-call, initiate failover runbook

- name: Replication Lag High
  condition: qdrant_snapshot_age > 90 minutes
  severity: SEV-2
  action: Alert ops team, check sync job

- name: Secondary AKS Down
  condition: secondary_cluster_health != healthy
  severity: SEV-2
  action: Alert ops team, lose DR capability

- name: Blob Replication Failed
  condition: blob_replication_status != success
  severity: SEV-2
  action: Alert ops team, check Azure status
```

### Dashboards
- **DR Status Dashboard**: Replication lag, secondary health, last successful drill
- **Failover Metrics**: Historical RTO/RPO, failover events, drill results
- **Cost Tracking**: Primary vs DR spend, optimization opportunities

## Cost Analysis

### Warm Standby (Recommended)
```
Primary Region (Canada Central):
  - AKS (6 nodes, D4s_v5): $1,200/month
  - Qdrant storage (500GB Premium SSD): $120/month
  - Redis (Premium 6GB): $280/month
  - Azure OpenAI (usage-based): ~$2,000/month
  - Blob Storage (1TB, GRS): $45/month
  - Networking (egress): $150/month
  Total: $3,795/month

Secondary Region (Canada East - 50% capacity):
  - AKS (3 nodes, D4s_v5): $600/month
  - Qdrant storage (250GB Premium SSD): $60/month
  - Redis (Standard 6GB): $80/month
  - Azure OpenAI (standby): $500/month
  - Networking: $50/month
  Total: $1,290/month

DR Overhead: 34% (~$1,290 / $3,795)
Total Monthly: $5,085
```

**Cost Optimization**:
- Use Azure Reserved Instances (40% savings on compute)
- Enable AKS node autoscaling (scale to zero during drills)
- Archive old snapshots to Cool storage ($0.01/GB vs $0.18/GB)

## Compliance Alignment

| Control | Requirement | Implementation |
|---------|-------------|----------------|
| **CP-6** | Alternate Processing Site | Secondary AKS cluster in Canada East |
| **CP-7** | Alternate Processing Site (Operations) | Warm standby with 1-hour RTO |
| **CP-9** | System Backup | Qdrant snapshots, Redis AOF, Blob GRS |
| **CP-10** | System Recovery | Automated restore scripts + quarterly drills |

## Governance

### Responsibilities
- **Cloud Architect**: DR strategy, capacity planning
- **DevOps Lead**: Automation scripts, failover procedures
- **Operations**: Drill execution, monitoring, incident response
- **Security**: Encryption at rest/transit in both regions

### Review Cadence
- **Monthly**: Replication metrics, cost review
- **Quarterly**: DR drill execution, RTO/RPO validation
- **Annually**: Strategy reassessment, upgrade to active-active evaluation

### Change Control
All DR architecture changes require:
1. Architecture review board approval
2. Tabletop walkthrough with ops team
3. Drill validation before production deployment

## Roadmap

### Phase 1 (Current): Warm Standby
- ✅ GRS Blob storage
- ✅ Key Vault replication
- ✅ Qdrant snapshot-based sync
- ⚠️ Manual failover scripts (automation in progress)

### Phase 2 (Q1 2026): Enhanced Automation
- 🔄 Automated failover orchestration (Azure Automation + Logic Apps)
- 🔄 Redis Enterprise Geo-Replication
- 🔄 Continuous replication (< 15 min RPO)

### Phase 3 (Q3 2026): Active-Active
- 📝 100% secondary capacity
- 📝 Global load balancing
- 📝 Cross-region session affinity
- 📝 Conflict resolution for writes

---

**Document Version**: 1.0  
**Last Updated**: 2025-12-01  
**Next Review**: 2025-Q1 DR Drill  
**Classification**: UNCLASSIFIED
