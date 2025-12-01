# Data Retention & Purge Policy

## Scope
Define retention periods for ingested documents, vectors, audit logs, and transient data to meet regulatory and cost requirements.

## Retention Periods

| Data Type | Default Retention | Justification | Purge Method |
|-----------|-------------------|---------------|--------------|
| Ingested Document Originals (Blob) | 30 days | Regulatory minimum | Lifecycle policy (soft-delete 7d) |
| Vector Embeddings (Qdrant) | Until tenant deletes | Core service data | Manual `/api/v1/documents/{id}` or batch script |
| Query Logs (structured) | 90 days | Operational analysis | Azure Log Analytics retention |
| Audit Logs | 1 year | Compliance (AU-11) | Blob immutable + archive tier |
| Redis Cache | 24 hours TTL | Transient cache | Automatic expiration |
| Metrics (Prometheus) | 30 days | Cost optimization | Prometheus retention flag |
| Snapshots (Qdrant backups) | 30 days | DR recovery window | Blob lifecycle policy |

## Tenant-Specific Policies
- Configurable per-tenant retention via config table (future enhancement)
- Example: High-security tenant extends audit to 7 years

## Purge Jobs

### 1. Document Purge (Batch)
```python
# Cron job: daily at 02:00 UTC
# Pseudocode:
for tenant in active_tenants:
    cutoff = now() - 30 days
    docs = get_documents_before(tenant, cutoff)
    for doc in docs:
        delete_blob(doc.blob_uri)
        delete_vectors(doc.document_id)
        audit("document.purged", tenant, {"document_id": doc.id, "reason": "retention_expired"})
```

### 2. Log Archive
- Azure Monitor: Auto-archive to cold tier after 90 days
- Blob audit logs: Move to Archive tier after 1 year (via lifecycle rule)

### 3. Cache Eviction
- Redis: Automatic via TTL
- Optional: Manual `FLUSHDB` for tenant offboarding

## Deletion API
- Endpoint: `DELETE /api/v1/documents/{document_id}`
- Effect: Remove vectors from Qdrant, emit audit event, optionally delete blob
- Validation: Tenant ID must match; 404 if not found

## Compliance
- Aligns with PIPEDA/GDPR "right to erasure" (allow tenant-triggered delete)
- AU-11 (audit record retention)
- SI-12 (information handling and retention)

## Monitoring
- Alert if purge job fails (check cron logs)
- Monthly report: purged document count, storage savings

## User Communication
- Notify tenants 7 days before auto-purge (if applicable)
- Provide self-service purge in future UI

## Governance
- Retention policies reviewed annually
- Adjust based on regulatory changes or tenant contracts
