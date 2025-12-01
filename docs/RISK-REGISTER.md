# RISK REGISTER & THREAT MODEL
Date: 2025-12-01
Author: Senior Government Cloud Security Architect (generated)

Scope and context
- System: PubSec-Info-Assistant-by-Copilot (repo id 1106866181)
- Default data classification: Protected B (assumed)
- Sources examined: backend/, frontend/, Dockerfile.backend, Dockerfile.frontend, docker-compose.yml, k8s/, .zap/, README.md, PROJECT-SUMMARY.md, DEMO-GUIDE.md
- Purpose: provide a prioritized, actionable risk register aligned to ITSG-33 / NIST SP 800-53 to support mitigation planning and CIO risk acceptance.

Instructions for owners
- Replace **ASSUMPTION** and **TODO** entries with factual data and evidence.
- For each risk, collect evidence as listed and add mitigation tickets to the tracker.

Risk register table columns: ID, Threat, Asset / Component, Vulnerability, Likelihood (Low/Med/High), Impact (Low/Med/High), Inherent Risk (L/M/H), Mitigation(s), Residual Risk, Owner, Priority (P0-P3), Evidence required.

---

R1: Prompt injection leading to disclosure of Protected B or PII
- Asset/Component: Backend prompt-processing, Azure OpenAI calls (backend/, Dockerfile.backend)
- Vulnerability: Unvalidated user-provided content included in prompts; lack of redaction/minimization; absence of input/output moderation.
- Likelihood: High
- Impact: High (exfiltration of Protected B)
- Inherent Risk: High
- Mitigations:
  - Implement strict input validation and PII redaction prior to model calls (code-level filters).
  - Use prompt engineering to add explicit 'do not reveal' constraints and system messages.
  - Apply model-side moderation APIs and post-response filters; block or human-review sensitive outputs.
  - Log correlation IDs and maintain prompt-output audit trail in secure store with restricted access (Key Vault + encrypted storage).
  - Rate-limit and anomaly-detect high-volume or pattern-based exfiltration attempts.
- Residual Risk: Medium (depends on human-in-loop coverage and moderation efficacy)
- Owner: Dev / Security
- Priority: P0
- Evidence required: code showing redaction, moderation logs, DAST/pentest findings related to prompt injection, monitoring rules.

R2: Model hallucination producing inaccurate or misleading public-sector guidance
- Asset/Component: Azure OpenAI output presented to users (frontend/, backend/)
- Vulnerability: No source attribution, lack of grounding to trusted knowledge base, no human review for critical responses.
- Likelihood: Medium
- Impact: Medium to High (depends on use-case and reliance)
- Inherent Risk: Medium
- Mitigations:
  - Ground responses with references from validated knowledge sources and include citations.
  - Add confidence scoring and indicate when content is AI-generated; require human review for policy/legal guidance.
  - Implement guardrails that flag high-risk topics and route to subject-matter experts.
- Residual Risk: Low-Medium
- Owner: Product / Privacy
- Priority: P1
- Evidence required: code showing citations, logs of human review flows, UI disclaimers, PIA entries.

R3: Unauthorized access due to weak IAM or leaked secrets
- Asset/Component: Entra ID/service principals/CI secrets, Key Vault (ASSUMPTION: Key Vault intended)
- Vulnerability: Service principal credentials in CI/CD, missing managed identities, weak RBAC, secrets in repo or docker-compose.yml
- Likelihood: Medium
- Impact: High
- Inherent Risk: High
- Mitigations:
  - Use managed identities for Azure resources and Key Vault for secrets; remove secrets from repo.
  - Enforce least-privilege RBAC, Conditional Access, MFA for admin roles, PIM for privileged ops.
  - Rotate keys and enable monitoring for anomalous sign-ins.
  - Run secret scanning (truffleHog) and block merges with secrets.
- Residual Risk: Medium
- Owner: DevOps / Identity
- Priority: P0
- Evidence required: Key Vault configs, CI/CD secret handling docs, identity matrix, audit logs.

R4: Vulnerable third-party dependencies leading to supply-chain compromise
- Asset/Component: NPM/PyPI packages, base Docker images, GitHub Actions (repo files)
- Vulnerability: Outdated/unpinned dependencies, usage of untrusted base images, unpinned actions
- Likelihood: Medium
- Impact: High
- Inherent Risk: High
- Mitigations:
  - Generate SBOM and integrate SCA scans (Trivy/Snyk); enable Dependabot.
  - Pin base images and use minimal, scanned base images; sign images (cosign).
  - Harden CI with least-priv privilege and pinned actions.
- Residual Risk: Medium
- Owner: DevSecOps
- Priority: P0
- Evidence required: SBOM, SCA reports, pinned action list, image signing evidence.

R5: Container and orchestration misconfigurations (privileged containers, exposed ports)
- Asset/Component: Dockerfile.backend, Dockerfile.frontend, docker-compose.yml, k8s/
- Vulnerability: Containers running as root, missing resource limits, exposed admin ports, config maps holding secrets
- Likelihood: Medium
- Impact: Medium
- Inherent Risk: Medium
- Mitigations:
  - Enforce non-root users, add securityContext in k8s manifests, remove sensitive data from configmaps, enforce network segmentation.
  - Run automated container scans (Trivy) and kube-bench.
- Residual Risk: Low
- Owner: Cloud Architect / DevOps
- Priority: P0
- Evidence required: hardened Dockerfiles, k8s manifests, CIS scan results.

R6: Inadequate logging and monitoring allowing undetected exfiltration or misuse
- Asset/Component: Application logs, telemetry (monitoring/)
- Vulnerability: Incomplete logs, PII left in logs, no SIEM alerts for anomalies
- Likelihood: Medium
- Impact: High (data breach unnoticed)
- Inherent Risk: High
- Mitigations:
  - Implement structured logging with redaction, correlation IDs, forward to SIEM (Azure Sentinel), create alerts for anomalous model output patterns and data exfiltration indicators.
  - Define retention and access controls for logs.
- Residual Risk: Medium
- Owner: Ops/SRE / Security
- Priority: P0
- Evidence required: logging config, sample redacted logs, SIEM rules and alerting playbooks.

R7: Data persistence of Protected B in vector DB or storage without proper controls
- Asset/Component: Vector DB, Blob storage, conversation store (ASSUMPTION: persistent store used)
- Vulnerability: Storing user data or embeddings with sensitive content without encryption-at-rest, access controls
- Likelihood: Medium
- Impact: High
- Inherent Risk: High
- Mitigations:
  - Avoid storing raw prompts/PII; store redacted or pseudonymized data only.
  - Encrypt data at rest (CMEK recommended) and enforce VNET/private endpoints.
  - Apply strict ACLs and monitor access.
- Residual Risk: Medium
- Owner: Data Owner / DevOps
- Priority: P0
- Evidence required: storage configs, encryption keys, access control lists, data inventory showing what is persisted.

R8: Abuse of AI model via adversarial inputs (prompt poisoning, data poisoning via knowledge sources)
- Asset/Component: Knowledge base ingestion pipelines, content indexing (if present)
- Vulnerability: Ingesting untrusted documents or web-scraped content that contains malicious prompts or biased data
- Likelihood: Medium
- Impact: Medium
- Inherent Risk: Medium
- Mitigations:
  - Vet content ingestion pipelines, validate sources, apply sanitization and metadata tagging.
  - Maintain provenance records and whitelist sources.
  - Periodic retraining validation if model fine-tuning used.
- Residual Risk: Low-Medium
- Owner: Data Engineering / Product
- Priority: P1
- Evidence required: ingestion pipeline configs, source whitelist, provenance logs.

R9: Regulatory and privacy non-compliance (missing PIA/PADI artifacts)
- Asset/Component: Organizational process and documentation
- Vulnerability: Lack of completed PIA/PADI, retention policies, or consent mechanisms
- Likelihood: High
- Impact: High (legal/operational consequences)
- Inherent Risk: High
- Mitigations:
  - Complete PIA/PADI, implement retention/disposal policy, user consent notices, privacy-by-design reviews.
  - Map controls to PADI guardrails and publish Privacy Reviewer Summary.
- Residual Risk: Medium
- Owner: Privacy & Product
- Priority: P0
- Evidence required: PIA/PADI document, data inventory, consent mechanism screenshots, retention policy.

R10: Denial of Service (DoS) or resource exhaustion attacks on model endpoints or API
- Asset/Component: Backend API, Azure OpenAI endpoint (rate-limited?)
- Vulnerability: No rate-limiting, insufficient autoscaling protections, abusive traffic
- Likelihood: Medium
- Impact: Medium
- Inherent Risk: Medium
- Mitigations:
  - Implement API rate-limiting, quotas at APIM or gateway, WAF protections, autoscaling policies, and monitoring/alerts on abnormal usage.
- Residual Risk: Low-Medium
- Owner: Ops / Cloud
- Priority: P1
- Evidence required: APIM/WAF configs, rate-limit policies, autoscaling configs.

---

Risk scoring notes
- Likelihood: High / Medium / Low (based on exploitability and exposure)
- Impact: High / Medium / Low (based on data sensitivity and operational impact)
- Inherent Risk derived from combination of Likelihood and Impact
- Residual Risk assumes mitigations listed are implemented; owners must update after implementation and testing.

AI-specific threat modeling considerations
- Prompt injection & data exfiltration are high-priority unique risks.
- Model integrity and hallucinations require operational mitigations (grounding, human-in-loop)
- Traceability: store prompts and outputs securely with correlation IDs for forensic analysis, but balance with privacy redaction requirements.

Next steps (actionable)
1. Owners to confirm or replace ASSUMPTION entries and assign named owners.
2. Create mitigation tickets for all P0 items and track in project tracker.
3. Run DAST/SAST/SCA and add evidence to docs/ folder per SECURITY-ASSESSMENTS.md roadmap.
4. Initiate PIA/PADI and TRA activities and collect artifacts.
5. Schedule pen test after remediations of P0 findings.

Appendix: How to use this file
- Add rows or entries following the table template above. Keep a living risk register by updating Likelihood/Impact after mitigation and noting evidence links (docs/ or issue URLs).
