# Incident Response Runbook

## Scope
Structured response to security incidents, outages, and data breaches.

## Severity Matrix
| Severity | Description | Response Time | Examples |
|----------|-------------|---------------|----------|
| SEV-1 (Critical) | Complete service down or data breach | 15 min | Total outage, credential leak, PII exposure |
| SEV-2 (High) | Partial degradation or security event | 1 hour | API errors >5%, suspicious access patterns |
| SEV-3 (Medium) | Minor impact, workaround available | 4 hours | Single tenant slow, non-critical bug |
| SEV-4 (Low) | Informational, no user impact | 24 hours | Warning alerts, cosmetic issues |

## Response Phases

### 1. Detection & Triage (0-15 min)
- Alert triggers via Azure Monitor or Prometheus
- On-call engineer validates severity
- Create incident ticket (Jira/ServiceNow)
- Notify stakeholders via incident channel (#incidents-prod)

### 2. Containment (15-60 min)
- **Security Event**: Rotate compromised credentials immediately
- **Outage**: Activate failover or scale horizontally
- **Data Breach**: Isolate affected tenant; suspend API access
- Preserve logs and evidence (copy to immutable storage)

### 3. Investigation (Concurrent)
- Review audit logs for timeline
- Check recent deployments (rollback if suspect)
- Query metrics for anomalies
- Collect container logs and traces

### 4. Remediation
- Apply fix or workaround
- Deploy to staging → validate → promote to prod
- Re-enable affected services
- Monitor for 30 minutes post-fix

### 5. Communication
- **Internal**: Update incident channel every 30 min
- **External** (if customer-impacting): Status page update within 2 hours
- **Regulatory** (if breach): Notify within 72 hours (GDPR/PIPEDA)

### 6. Post-Incident Review (PIR)
- Schedule within 48 hours of resolution
- Document root cause, timeline, mitigation
- Identify action items (add to SECURITY-BACKLOG.md)
- Update runbooks and monitoring

## Security Incident Specifics
### Credential Compromise
1. Rotate all secrets in Key Vault
2. Revoke API keys for affected tenants
3. Audit all actions by compromised identity (last 30 days)
4. Notify affected parties

### Prompt Injection Exploit
1. Review query logs for malicious patterns
2. Blacklist prompts if identifiable
3. Update WAF rules
4. Re-run prompt-injection harness with new patterns

### Data Exfiltration
1. Freeze tenant access
2. Forensic analysis of vector retrieval logs
3. Notify tenant + regulatory authorities
4. Enhance access controls

## Tools
- Azure Monitor: Alerts and log queries
- Prometheus/Grafana: Metrics dashboards
- GitHub: Rollback commits
- Key Vault: Secret rotation

## Escalation Contacts
- SEV-1: Immediate escalation to Platform Owner + Security Architect
- SEV-2: On-call engineer coordinates; escalate if unresolved in 2 hours
- SEV-3/4: Standard queue

## Compliance
- IR-4 (incident handling), IR-5 (incident monitoring), IR-6 (reporting), AU-6 (audit review)
