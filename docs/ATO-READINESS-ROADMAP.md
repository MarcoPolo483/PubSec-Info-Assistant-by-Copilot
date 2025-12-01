# ATO Readiness Roadmap (ITSG-33 / NIST 800-53)

Document Date: 2025-12-01
Status: Draft — for CIO/ISSO review
Classification: UNCLASSIFIED / PUBLIC

Purpose
- Define staged readiness levels and decision gates to reach an Authority to Operate (ATO) for PubSec-Info-Assistant-by-Copilot (Protected B).
- Map required artifacts, controls, and evidence to each level, aligned to ITSG-33 and NIST SP 800-53; integrate PADI privacy requirements.
- Cross-reference: `SECURITY-SYSTEM-PROFILE.md` (Sections 4.6, 5.3, 9.4–9.5), `SECURITY-ASSESSMENTS.md`, `RISK-REGISTER.md`, `SECURITY-CONTROLS-AND-DEVSECOPS.md`.

---

Readiness Levels & Decision Gates

Level 0 — Prototype (No live users, no PII)
- Scope: Internal development/testing only; synthetic data. No Protected B/PII. Isolated environment.
- Minimum controls/evidence:
  - SAST (CodeQL/Semgrep/Bandit) runs clean of HIGH/CRITICAL
  - Basic DAST baseline (ZAP) against dev URL
  - Dockerfiles avoid secrets; images scan with Trivy (no HIGH/CRITICAL)
  - Initial `RISK-REGISTER.md` drafted; `SECURITY-SYSTEM-PROFILE.md` baseline
- Decision gate to L1: No PII present; code scanning evidence archived under `evidence/`

Level 1 — Pre-Prod Pilot (Limited users, Protected B test data only)
- Scope: Pilot in non-public environment, limited accounts; controlled data sets.
- Required controls/evidence:
  - TRA (draft) incl. AI threat taxonomy and multi-tenant scenarios
  - PIA/PADI (draft) incl. cross-border analysis (Sec. 9.4.5) and data sovereignty (Sec. 9.5)
  - SAST/SCA/SBOM integrated; DAST baseline; IaC scanning (Checkov/tfsec)
  - Key Vault/Managed Identity configured, MFA for admins (ASSUMPTION A1/A2/A3 validated)
  - RBAC (7 roles) implemented for core flows; logging and SIEM plan
- Decision gate to L2: P0 risks mitigated or time-bound; evidence archived; pen test scheduled

Level 2 — Conditional ATO (Limited production with conditions)
- Scope: Production with scope/conditions; monitoring and incident response active
- Required controls/evidence:
  - TRA (final) and Risk Register with owners; residual risk acceptance records
  - PIA/PADI (final) with DPA for Azure OpenAI; consent/notice documented
  - Penetration test completed; HIGH/MEDIUM remediated or accepted with plan
  - DAST full (authenticated) incl. RAG prompt-injection suite; SAST/SCA/SBOM continuous
  - Key Vault rotation policy operating; Entra ID MFA enforced; access reviews
  - Container hardening (non-root), Trivy clean; Network Policies + WAF + rate limiting
  - SIEM (Sentinel) integration with alert rules; DR runbook validated
  - Data residency enforced (Azure Canada); private endpoints for sensitive services
- Decision gate to L3: All controls operational; monitoring produces alerts; evidence complete

Level 3 — Full ATO (Production)
- Scope: Broad production with continuous monitoring, audits, and governance
- Required controls/evidence:
  - Continuous Monitoring Strategy (CMS) and dashboards
  - Supply chain integrity (cosign image signing, SLSA provenance)
  - Annual pen test and quarterly access reviews
  - DR drills with lessons learned; patch SLAs met; CMP finalized
  - Audit-ready evidence package; CIO Authorization Letter issued

---

Current Readiness Snapshot (Repository State)
- Strengths (in repo):
  - System Profile enhanced (AI threats, RBAC matrix, PADI privacy, data sovereignty)
  - Security Assessments mapping includes AI/RAG-specific TRA/PIA/SAST/DAST requirements
  - Risk Register expanded with AI taxonomy, cross-border, multi-tenancy, RBAC risks
  - DevSecOps controls doc created with evidence folder structure and 30/60/90 roadmap
- Gaps to reach L2 (Conditional ATO):
  - Formal TRA and PIA/PADI documents (draft→final)
  - Authenticated DAST full scan; AI/RAG prompt-injection test suite
  - Penetration test report (with remediation evidence)
  - Entra ID/MFA, Managed Identity, Key Vault: deployment config docs + rotation evidence
  - SIEM (Sentinel) integration and alert rules; log retention policy
  - Container image signing (cosign) and SBOM in CI/CD; Dependabot enabled
  - Data residency verification (Azure OpenAI Canada) and private endpoints

---

Action Plan & Owners (P0 within 30 days)
1. TRA v1.0 (incl. AI taxonomy, cross-border, multi-tenant) — Owner: Security Lead — Deliverable: `evidence/ra/TRA-v1.0.pdf`
2. PIA/PADI v1.0 (A–F sections) — Owner: Privacy Officer — Deliverable: `evidence/privacy/PIA-v1.0.pdf`
3. Authenticated DAST config + RAG prompt-injection suite — Owner: Security Tester — Deliverable: `evidence/dast/zap-full/`
4. Key Vault + Managed Identity docs + rotation evidence — Owner: Security Engineer — Deliverable: `evidence/iam/keyvault-rotation/`
5. Dependabot + SBOM generation in CI — Owner: DevSecOps Lead — Deliverables: `.github/dependabot.yml`, `evidence/sbom/`
6. Harden backend image (non-root) + Trivy clean — Owner: Platform Lead — Deliverable: `evidence/container/trivy/`
7. SIEM integration (Sentinel) + alert rules — Owner: SecOps Lead — Deliverable: `evidence/monitoring/sentinel/`

60-Day (P1) Targets
- Pen test executed; remediation completed for HIGH/MEDIUM — `evidence/pentest/`
- kube-bench/kubeaudit integrated; CIS results archived — `evidence/iac/`
- DR drill performed; report archived — `evidence/dr/`

90-Day (Sustained) Targets
- Cosign signing + SLSA attestations in CD — `evidence/container/attestations/`
- Quarterly access reviews; CMP finalized — `evidence/iam/access-reviews/`, `docs/CMP.md`

---

Evidence Index (living)
- Governance
  - `docs/SECURITY-SYSTEM-PROFILE.md` — baseline, AI threats, RBAC, privacy
  - `docs/SECURITY-ASSESSMENTS.md` — artifact mapping and roadmap
  - `docs/RISK-REGISTER.md` — prioritized risks and owners
  - `docs/SECURITY-CONTROLS-AND-DEVSECOPS.md` — controls, pipelines, evidence folders
- Assessments & Testing
  - `evidence/sast/` — CodeQL, Semgrep, Bandit
  - `evidence/sca/` — Safety, npm audit, Trivy SCA
  - `evidence/dast/` — ZAP baseline/full, RAG test results
  - `evidence/pentest/` — pen test reports, remediation
- Platform & IAM
  - `evidence/container/` — Trivy, cosign signatures
  - `evidence/iac/` — Checkov/tfsec, kube-bench/audit
  - `evidence/iam/` — Entra ID configs, access reviews, MFA
- Privacy
  - `evidence/privacy/` — PIA/PADI, DPA, data residency configs

---

Decision Gate Checklist
- L0→L1:
  - [ ] No PII present; synthetic data only
  - [ ] SAST/SCA clean (no HIGH/CRITICAL); DAST baseline archived
- L1→L2:
  - [ ] TRA (final) and Risk Register (owners, timelines)
  - [ ] PIA/PADI (final), DPA in place; consent/notice documented
  - [ ] Pen test report; HIGH/MEDIUM remediated or accepted with plan
  - [ ] DAST full (authn), AI/RAG prompt-injection tests archived
  - [ ] Key Vault rotation, Entra ID MFA, RBAC verified; SIEM live
  - [ ] Data residency enforced (Canada), private endpoints validated
- L2→L3:
  - [ ] Continuous Monitoring Strategy running, dashboards in place
  - [ ] cosign + SLSA in CD; quarterly access reviews
  - [ ] DR drill reports; patch SLAs met; CMP finalized
  - [ ] Complete evidence package ready for audit; CIO Authorization letter

---

Risk Acceptance & Escalation
- Cross-border data flows (Sec. 9.4.5) require CIO risk acceptance if Azure OpenAI Canada cannot be enforced for all processing.
- Document residual risks per `RISK-REGISTER.md`; record approvals and expiry dates.

Notes
- Avoid storing PII in prompts/logs; apply redaction (Presidio) and minimization.
- Keep evidence directories updated by CI/CD to ensure audit-readiness at all times.
