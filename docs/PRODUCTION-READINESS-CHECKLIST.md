# Production Readiness Checklist

| Category | Control | Status | Evidence / Path |
|----------|---------|--------|-----------------|
| Architecture | Reference diagram & data flows | NEW | `docs/PRODUCTION-ARCHITECTURE.md` |
| Tenancy | Collection & cache namespacing | BASE | Code (`backend/app/ingestion/*`) |
| Security Headers | CSP, COOP/COEP, Permissions-Policy | PARTIAL | `frontend/nginx.conf`, backend middleware |
| Auth / Rate Limit | API key + in-memory limit | DEV | `backend/app/main.py` (rate_limit) |
| Secrets Mgmt | Key Vault design | NEW | `docs/SECRETS-MANAGEMENT.md` (pending) |
| SAST | CodeQL + SAST archive | COMPLETE | `.github/workflows/codeql-analysis.yml`, `evidence/sast/` |
| SCA / SBOM | Dependencies & SBOM | COMPLETE | `evidence/sbom/` |
| IaC Scanning | Checkov / tfsec | COMPLETE | `.github/workflows/evidence-archive.yml` |
| Container Security | Trivy scans | COMPLETE | `.github/workflows/container-security.yml`, `evidence/container/` |
| DAST Passive | Local baseline + hardened | COMPLETE | `evidence/dast/LOCAL-BASELINE-SUMMARY.md` |
| Prompt Injection | Harness + results | COMPLETE | `.github/security/prompt_injection_tests.py`, `evidence/dast/local-backend/` |
| Observability | Metrics + tracing design | PARTIAL | Prometheus config, OpenTelemetry packages |
| Logging | Structured request logging | PARTIAL | `backend/app/main.py` middleware |
| Performance | Load test plan | NEW | `docs/PERFORMANCE-TESTING.md` (pending) |
| DR / Backup | Snapshot & restore strategy | NEW | `docs/DR-RUNBOOK.md` (pending) |
| Incident Response | Severity matrix & steps | NEW | `docs/INCIDENT-RESPONSE.md` (pending) |
| Compliance Mapping | Control→Evidence grid | NEW | `docs/COMPLIANCE-MAPPING.md` (pending) |
| SLO/SLA | Defined targets & error budgets | NEW | `docs/SLO-SLA.md` (pending) |
| Deployment Gating | Staging active scan gate | PLANNED | GitHub Actions enhancement |
| Edge Security | WAF/CDN config stub | NEW | `docs/EDGE-SECURITY.md` (pending) |

## Gate Criteria
1. No HIGH severity unmitigated findings (SAST/DAST/IaC/Container).
2. All baseline security headers present (backend + frontend).
3. Secrets only retrieved at runtime via Managed Identity (no static secrets in repo).
4. SLOs defined and initial telemetry operational.
5. DR & Incident runbooks committed.
6. Compliance mapping complete linking every required control to evidence.
7. Active ZAP staging scan report archived with no HIGH alerts.
8. Signed container images promoted (Cosign plan if not yet implemented).

## Action Tracking
Refer to `SECURITY-BACKLOG.md` for prioritized tasks; this checklist is the readiness snapshot.

## Next Immediate Tasks
- [ ] Document Key Vault & secret rotation.
- [ ] Implement Redis-backed rate limiting (replace in-memory window).
- [ ] Add audit logging event schema (ingestion, query, deletion).
- [ ] Finalize SLO/SLA doc.
- [ ] Add load testing scenarios (k6/Locust) skeleton.
