# Security Backlog (ATO/PADI)

Date: 2025-12-01
Status: Draft — for Security/Privacy/DevSecOps triage
Classification: UNCLASSIFIED / PUBLIC

Purpose
- Prioritized, actionable backlog to reach Conditional ATO (L2) and Full ATO (L3).
- Each item includes clear acceptance evidence to archive under `evidence/`.
- Labels suggested for GitHub issues: `security`, `privacy`, `PADI`, `ATO`, `DevSecOps`, `LLM`, `k8s`, `container`, `IAM`, `SCA`, `SAST`, `DAST`, `SBOM`.

Legend
- Effort: S (≤1 day), M (2–5 days), L (≥1 week)
- Priority: P0 (30 days), P1 (60 days), P2 (90 days), P3 (backlog)

---

## P0 — 30-Day Critical (Gate to L2)

1) TRA v1.0 incl. AI taxonomy & cross-border
- Effort: M — Owner: Security Lead — Labels: security, ATO, risk, LLM
- Acceptance/Evidence: `evidence/ra/TRA-v1.0.pdf`; diagrams, risk ratings, residual risk table
- Dependencies: `docs/SECURITY-SYSTEM-PROFILE.md` Sections 4.6, 9.4.5

2) PIA/PADI v1.0 (A–F), DPA draft
- Effort: M — Owner: Privacy Officer — Labels: privacy, PADI, ATO
- Acceptance/Evidence: `evidence/privacy/PIA-v1.0.pdf`, DPA draft; data flow & cross-border matrices
- Dependencies: `docs/PADI-EVIDENCE-REPORT.md`

3) DAST (authenticated) + RAG prompt-injection test suite
- Effort: M — Owner: Security Tester — Labels: DAST, LLM, security
- Acceptance/Evidence: `evidence/dast/zap-full/` reports, prompt-injection results, auth config
- Dependencies: working env URL, test creds, `SECURITY-ASSESSMENTS.md`

4) Key Vault + Managed Identity + rotation evidence
- Effort: S/M — Owner: Security Engineer — Labels: IAM, secrets, DevSecOps
- Acceptance/Evidence: `evidence/iam/keyvault-rotation/` (config, rotation logs), managed identity assignments
- Dependencies: Azure subscription config

5) Dependabot + SBOM generation in CI
- Effort: S — Owner: DevSecOps Lead — Labels: SCA, SBOM, DevSecOps
- Acceptance/Evidence: `.github/dependabot.yml`, `evidence/sbom/` (backend/frontend/container)
- Dependencies: GitHub Actions secrets/tokens

6) Harden backend image (non-root) + k8s securityContext
- Effort: S — Owner: Platform Lead — Labels: container, k8s, security
- Acceptance/Evidence: PR with Dockerfile changes, k8s manifests, `evidence/container/trivy/` clean scan
- Dependencies: `Dockerfile.backend`, `k8s/base/*`

7) SIEM (Sentinel) integration + alert rules
- Effort: M — Owner: SecOps Lead — Labels: monitoring, SIEM, ATO
- Acceptance/Evidence: `evidence/monitoring/sentinel/` (connectors, rules, sample alerts)
- Dependencies: log forwarding from app/infra

8) Data residency enforcement (Azure OpenAI Canada) + private endpoints
- Effort: S/M — Owner: Cloud Architect & Privacy — Labels: privacy, residency, cloud
- Acceptance/Evidence: `evidence/privacy/residency/` (region settings, endpoint allowlist), private endpoint configs
- Dependencies: Azure tenant policy

---

## P1 — 60-Day Important

9) Penetration test (incl. AI red teaming) + remediation
- Effort: L — Owner: Security Lead — Labels: pentest, ATO, LLM
- Acceptance/Evidence: `evidence/pentest/` reports, retest confirmation

10) kube-bench/kubeaudit CI integration
- Effort: M — Owner: Platform Lead — Labels: k8s, IaC, security
- Acceptance/Evidence: `evidence/iac/` CIS results and remediation PRs

11) RBAC enforcement tests for 7 roles
- Effort: M — Owner: Dev Lead — Labels: IAM, tests, security
- Acceptance/Evidence: PR with automated tests; mapping to `SECURITY-SYSTEM-PROFILE` Section 5.3

12) Automated cross-tenant isolation tests
- Effort: M — Owner: QA — Labels: multi-tenant, tests, security
- Acceptance/Evidence: CI job and `evidence/dast/` results for X-Tenant-ID manipulation scenarios

13) DR drill and report
- Effort: M — Owner: Operations Lead — Labels: DR, operations
- Acceptance/Evidence: `evidence/dr/` drill report and lessons learned

---

## P2 — 90-Day Sustained

14) cosign image signing + SLSA attestations
- Effort: M — Owner: DevSecOps Lead — Labels: supply-chain, container
- Acceptance/Evidence: `evidence/container/attestations/` signatures and policy

15) API Gateway rate limiting + WAF tuning
- Effort: S/M — Owner: Platform Lead — Labels: gateway, security
- Acceptance/Evidence: policy configs and DAST evidence of rate limit behavior

16) mTLS for internal services
- Effort: M — Owner: Platform Lead — Labels: network, security
- Acceptance/Evidence: manifests/configs, connectivity tests

17) Privacy notice & consent UX
- Effort: S — Owner: Product & Privacy — Labels: privacy, UX
- Acceptance/Evidence: screenshots, text approved by Privacy; links in app

---

## P3 — Backlog / Enhancements

18) Nuclei template scanning for API
- Effort: S — Owner: Security Tester — Labels: DAST, automation
- Acceptance/Evidence: CI job and reports in `evidence/dast/nuclei/`

19) Hallucination evaluation harness & guardrails
- Effort: M — Owner: Data/AI — Labels: LLM, quality
- Acceptance/Evidence: test suite, thresholds, failure alerts

20) Differential privacy exploration for embeddings
- Effort: L — Owner: Data/AI — Labels: privacy, research
- Acceptance/Evidence: design doc and PoC results

21) Blue/green deploy with policy checks (OPA/Gatekeeper)
- Effort: M — Owner: DevOps — Labels: CD, policy
- Acceptance/Evidence: pipelines and policy results archived in `evidence/iac/`

---

## Suggested GitHub Labels
- `security`, `privacy`, `ATO`, `PADI`, `DevSecOps`, `LLM`, `k8s`, `container`, `IAM`, `SCA`, `SAST`, `DAST`, `SBOM`, `pentest`, `monitoring`, `DR`

## References
- `docs/SECURITY-SYSTEM-PROFILE.md` Sections 4.6, 5.3, 9.4–9.5
- `docs/SECURITY-ASSESSMENTS.md`
- `docs/RISK-REGISTER.md`
- `docs/SECURITY-CONTROLS-AND-DEVSECOPS.md`
- `docs/ATO-READINESS-ROADMAP.md`
