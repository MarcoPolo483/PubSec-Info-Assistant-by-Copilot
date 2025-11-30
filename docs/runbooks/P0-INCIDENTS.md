# P0 Incident Runbooks - System Down

**Priority Level**: P0 - Critical  
**Response Time**: Immediate (24/7)  
**Escalation**: Page on-call engineer immediately

## P0-1: Complete System Outage

### Symptoms
- All endpoints returning 5xx errors
- Health checks failing across all services
- No user traffic reaching the application

### Investigation Steps

1. **Check Infrastructure Status**
   ```bash
   # Check Kubernetes cluster health
   kubectl get nodes
   kubectl get pods -n pubsec-info-assistant
   
   # Check pod status
   kubectl get pods -n pubsec-info-assistant -o wide
   ```

2. **Check Service Dependencies**
   ```bash
   # Test Qdrant connectivity
   kubectl exec -it qdrant-0 -n pubsec-info-assistant -- curl localhost:6333
   
   # Test Redis connectivity
   kubectl exec -it redis-0 -n pubsec-info-assistant -- redis-cli ping
   ```

3. **Check Recent Deployments**
   ```bash
   # Review recent changes
   kubectl rollout history deployment/backend -n pubsec-info-assistant
   kubectl describe deployment/backend -n pubsec-info-assistant
   ```

### Resolution Steps

**Option 1: Rollback Recent Deployment**
```bash
# Rollback to previous version
kubectl rollout undo deployment/backend -n pubsec-info-assistant
kubectl rollout status deployment/backend -n pubsec-info-assistant

# Verify health
curl https://pubsec-info-assistant.com/health
```

**Option 2: Restart All Services**
```bash
# Restart backend pods
kubectl rollout restart deployment/backend -n pubsec-info-assistant

# Restart frontend pods
kubectl rollout restart deployment/frontend -n pubsec-info-assistant

# Monitor restart
watch kubectl get pods -n pubsec-info-assistant
```

**Option 3: Scale Up Emergency Capacity**
```bash
# Increase replicas
kubectl scale deployment/backend --replicas=10 -n pubsec-info-assistant

# Check HPA status
kubectl get hpa -n pubsec-info-assistant
```

### Communication Template

**Slack Channel**: #pubsec-incidents

```
🚨 **P0 INCIDENT** - System Outage

**Status**: INVESTIGATING
**Impact**: All users unable to access the system
**Started**: [TIMESTAMP]
**ETA**: Investigating, updates every 15 minutes

**Actions Taken**:
- [ ] Infrastructure health check
- [ ] Dependency verification
- [ ] Rollback initiated

Next update: [TIME + 15 min]
```

### Post-Incident Actions

1. **Immediate** (within 1 hour):
   - Document root cause in incident ticket
   - Update status page
   - Send customer notification

2. **Follow-up** (within 24 hours):
   - Schedule post-mortem meeting
   - Create Jira tickets for preventive measures
   - Update monitoring thresholds

3. **Long-term** (within 1 week):
   - Conduct blameless post-mortem
   - Update runbooks based on learnings
   - Implement preventive controls

---

## P0-2: Database Unavailable (Qdrant Down)

### Symptoms
- Backend logs show "Qdrant connection error"
- Query endpoint returning 500 errors
- Ingestion endpoint failing

### Investigation Steps

1. **Check Qdrant Pods**
   ```bash
   kubectl get pods -l component=qdrant -n pubsec-info-assistant
   kubectl logs qdrant-0 -n pubsec-info-assistant --tail=100
   ```

2. **Check Storage**
   ```bash
   kubectl get pvc -n pubsec-info-assistant
   kubectl describe pvc qdrant-storage-qdrant-0
   ```

3. **Test Connectivity**
   ```bash
   kubectl exec -it backend-[POD-ID] -n pubsec-info-assistant -- curl http://qdrant:6333
   ```

### Resolution Steps

**Option 1: Restart Qdrant Pods**
```bash
# Delete unhealthy pod (StatefulSet will recreate)
kubectl delete pod qdrant-0 -n pubsec-info-assistant

# Wait for pod to be ready
kubectl wait --for=condition=ready pod/qdrant-0 -n pubsec-info-assistant --timeout=300s
```

**Option 2: Restore from Backup**
```bash
# Stop Qdrant pods
kubectl scale statefulset/qdrant --replicas=0 -n pubsec-info-assistant

# Restore from latest backup
kubectl exec -it qdrant-0 -n pubsec-info-assistant -- /restore-backup.sh

# Start Qdrant pods
kubectl scale statefulset/qdrant --replicas=3 -n pubsec-info-assistant
```

**Option 3: Failover to Secondary Region** (if multi-region)
```bash
# Update DNS to point to secondary region
# Route 53: Update weighted routing policy
aws route53 change-resource-record-sets --hosted-zone-id ZXXXXX --change-batch file://failover.json
```

### Monitoring Queries

```promql
# Qdrant availability
up{job="qdrant"} == 0

# Connection errors
rate(qdrant_connection_errors_total[5m]) > 0
```

---

## P0-3: Redis Cache Failure

### Symptoms
- Backend logs show "Redis connection failed"
- All queries bypass cache (high latency)
- Rate limiting not enforced

### Investigation Steps

1. **Check Redis Cluster**
   ```bash
   kubectl get pods -l component=redis -n pubsec-info-assistant
   kubectl logs redis-0 -n pubsec-info-assistant --tail=100
   ```

2. **Test Redis Commands**
   ```bash
   kubectl exec -it redis-0 -n pubsec-info-assistant -- redis-cli
   > PING
   > INFO replication
   > CLUSTER INFO
   ```

### Resolution Steps

**Option 1: Restart Redis Pods**
```bash
# Rolling restart
kubectl rollout restart statefulset/redis -n pubsec-info-assistant
```

**Option 2: Failover to Replica**
```bash
# Promote replica to master
kubectl exec -it redis-1 -n pubsec-info-assistant -- redis-cli REPLICAOF NO ONE
```

**Option 3: Emergency Mode (No Cache)**
```bash
# Update backend config to skip cache
kubectl set env deployment/backend REDIS_ENABLED=false -n pubsec-info-assistant
```

### Impact Mitigation

While Redis is down:
- Queries will be slower (no cache)
- Rate limiting may not work (use API Gateway rate limiting)
- Cost tracking may be delayed (buffer in application memory)

---

## P0-4: OpenAI API Outage

### Symptoms
- Backend logs show "OpenAI API error"
- Query endpoint returning 503 errors
- All LLM generations failing

### Investigation Steps

1. **Check OpenAI Status**
   - Visit: https://status.openai.com
   - Check API key validity
   - Review rate limits

2. **Check Backend Logs**
   ```bash
   kubectl logs deployment/backend -n pubsec-info-assistant | grep -i "openai"
   ```

### Resolution Steps

**Option 1: Wait for OpenAI Recovery**
```
- Enable maintenance mode
- Display user-friendly message
- Monitor OpenAI status page
```

**Option 2: Fallback to Anthropic (if configured)**
```bash
# Switch LLM provider
kubectl set env deployment/backend LLM_PROVIDER=anthropic -n pubsec-info-assistant
```

**Option 3: Use Cached Responses Only**
```bash
# Enable cache-only mode
kubectl set env deployment/backend CACHE_ONLY_MODE=true -n pubsec-info-assistant
```

### Communication Template

```
⚠️ **SERVICE DEGRADATION** - LLM Provider Outage

**Impact**: New queries may be slower or unavailable
**Workaround**: Use cached queries when possible
**ETA**: Waiting for OpenAI service restoration

Cached queries are still available and fast.
We're monitoring the situation and will update every 30 minutes.
```

---

## Emergency Contacts

| Role | Name | Phone | Slack |
|------|------|-------|-------|
| On-Call Engineer | Rotating | +1-XXX-XXX-XXXX | @oncall |
| Engineering Manager | [Name] | +1-XXX-XXX-XXXX | @eng-manager |
| CTO | [Name] | +1-XXX-XXX-XXXX | @cto |
| DevOps Lead | [Name] | +1-XXX-XXX-XXXX | @devops-lead |

## Escalation Path

1. **0-15 min**: On-call engineer investigates
2. **15-30 min**: Escalate to Engineering Manager
3. **30-60 min**: Escalate to CTO
4. **60+ min**: Executive briefing, customer communication

## Status Page Updates

Update: https://status.pubsec-info-assistant.com

```bash
# Post incident update
curl -X POST https://api.statuspage.io/v1/pages/[PAGE_ID]/incidents \
  -H "Authorization: OAuth [TOKEN]" \
  -d '{
    "incident": {
      "name": "System Outage",
      "status": "investigating",
      "impact_override": "critical",
      "body": "We are investigating reports of service unavailability."
    }
  }'
```
