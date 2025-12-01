# Security Controls & DevSecOps Implementation

Document Date: 2025-12-01
Status: Draft – for Security Lead review
Classification: UNCLASSIFIED / PUBLIC

Purpose
- Define technical and operational safeguards for PubSec-Info-Assistant-by-Copilot aligned to ITSG-33 / NIST SP 800-53 (Protected B).
- Describe CI/CD security workflows and evidence artifacts required for ATO.
- Cross-reference `SECURITY-SYSTEM-PROFILE.md` Sections 4.6 (AI threats), 5.3 (RBAC), and 9.4–9.5 (privacy & sovereignty).

Scope
- Backend (FastAPI), Frontend (React), Vector DB (Qdrant), Cache (Redis), Azure OpenAI integration, Kubernetes, Docker, GitHub Actions.

---

Controls Overview (by domain)

Access Control (AC)
- Entra ID (Azure AD) for user auth; MFA enforced for admin roles (ASSUMPTION A3 – validate).
- API auth: OAuth2/JWT (RS256), optional `X-API-Key`, tenant header `X-Tenant-ID` validated per request.
- RBAC: 7 roles per `SECURITY-SYSTEM-PROFILE` Section 5.3; least privilege enforced in code and Kubernetes RBAC.
- Evidence: IAM config docs, role-to-permission matrix, access reviews, MFA enforcement screenshots.

Identification & Authentication (IA)
- Managed Identities for service-to-service; Azure Key Vault for secrets (ASSUMPTION A1/A2 – validate).
- Key rotation policies documented; audit logs retained 1 year.
- Evidence: Key Vault configuration, rotation logs, managed identity assignments.

System & Communications Protection (SC)
- TLS 1.2+/1.3 end-to-end; mTLS for internal services (TODO: document in k8s manifests).
- Network Policies isolate namespaces/services; WAF at ingress; rate limiting at gateway/APIM.
- Evidence: ingress/WAF configs, network-policy manifests, TLS cert management docs.

Audit & Accountability (AU)
- Structured, redacted logs with correlation IDs; forwarded to SIEM (Azure Sentinel) (TODO: integration doc).
- Audit trails for admin actions and LLM calls; immutable storage.
- Evidence: log architecture, retention policy, sample audit logs, SIEM alert rules.

Configuration Management (CM)
- Git-based change control; PR approvals; environment-specific configs.
- Baseline configurations for containers/k8s; patch SLAs; Dependabot enabled (TODO: `.github/dependabot.yml`).
- Evidence: CMP, baseline docs, patch compliance reports, PR history.

Contingency Planning (CP)
- BCP/DRP documented; RTO/RPO targets; monthly DR drills.
- Backups for Qdrant and configs; restore runbooks.
- Evidence: `docs/runbooks/DISASTER-RECOVERY.md`, drill reports, backup schedules.

Risk Assessment (RA)
- TRA with AI taxonomy (OWASP LLM Top 10, MITRE ATLAS); risk register maintained.
- Evidence: TRA document, risk register updates, residual risk acceptance records.

Supply Chain (SA/SR)
- SCA and SBOM generation; container image scanning and signing (cosign – TODO).
- Actions pinned to versions/SHAs; provenance via SLSA attestations (TODO).
- Evidence: SBOMs, SCA reports, Trivy results, cosign signatures, Scorecard.

Privacy (Appendix/NIST Privacy Framework)
- PII detection/redaction (MS Presidio – TODO integration); minimization by design.
- DPA with Azure OpenAI; data residency Canada-only (Section 9.5).
- Evidence: PIA/PADI, DPA, residency configs, consent notices.

---

CI/CD Security Workflows (GitHub Actions)

SAST Pipeline
- Tools: CodeQL (Python/JS), Semgrep OWASP rules, Bandit.
- Triggers: on pull_request, push to `main`.
- Artifacts: SARIF reports stored under `evidence/sast/`.
- Gates: Fail on HIGH/CRITICAL; exceptions require Security Lead approval.

SCA & SBOM Pipeline
- Tools: Trivy (fs and image), Safety (pip), npm audit; CycloneDX for SBOM.
- Artifacts: `evidence/sca/`, `evidence/sbom/`.
- Gates: Fail on unpatched HIGH CVEs; Dependabot auto PRs created.

DAST Pipeline
- Tools: OWASP ZAP baseline (existing), full active scan (TODO), Nuclei (optional).
- Auth: Configure authenticated tests; include multi-tenant scenarios (`X-Tenant-ID`).
- Artifacts: `evidence/dast/` including prompt-injection test results.

Container Security Pipeline
- Build minimal, non-root images; scan with Trivy.
- Sign images with cosign (TODO); store attestations.
- Artifacts: `evidence/container/`.

IaC Security Pipeline
- Tools: Checkov/tfsec for Terraform; kube-bench/kubeaudit for k8s.
- Artifacts: `evidence/iac/`.

Secrets Management Checks
- TruffleHog, git-secrets pre-commit; block merges with exposed secrets.
- Key Vault rotation job evidence archived quarterly.

---

Implementation Tasks (30/60/90 Day Roadmap)

30-Day (P0)
- Create TRA with AI threat taxonomy and cross-border analysis.
- Generate SBOMs (backend/frontend) and integrate storage.
- Document Key Vault + Managed Identity setup; enable Dependabot.
- Harden `Dockerfile.backend` to non-root; add k8s securityContext.

60-Day (P1)
- Configure full OWASP ZAP active scan with auth.
- Integrate kube-bench/kubeaudit; document SIEM integration.
- Execute penetration test incl. AI red teaming.

90-Day (Sustained)
- Implement cosign signing; SLSA attestations.
- Quarterly access reviews; DR drill and report.
- Finalize CMP and configuration baselines.

---

Evidence Folder Structure (to create)
- `evidence/sast/` – CodeQL, Semgrep, Bandit reports
- `evidence/sca/` – Safety, npm audit, Trivy SCA reports
- `evidence/sbom/` – CycloneDX/SPDX files
- `evidence/dast/` – ZAP baseline/full, RAG prompt-injection results
- `evidence/container/` – Trivy image scans, cosign signatures
- `evidence/iac/` – Checkov/tfsec, kube-bench/kubeaudit outputs
- `evidence/iam/` – Entra ID configs, access reviews, MFA evidence
- `evidence/privacy/` – PIA/PADI, DPA, residency configs

---

References
- `docs/SECURITY-SYSTEM-PROFILE.md` Sections 4.6, 5.3, 9.4–9.5
- `docs/SECURITY-ASSESSMENTS.md`
- OWASP Top 10 for LLM Applications; MITRE ATLAS; NIST AI RMF
- NIST SP 800-53; ITSG-33; Treasury Board PADI
