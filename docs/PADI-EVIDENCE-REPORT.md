# PADI Evidence Report (Treasury Board PADI Template Alignment)

Document Date: 2025-12-01
Status: Draft — for Privacy Office / ATIP Review
Classification: UNCLASSIFIED / PUBLIC

Note: This report contains no PII. Replace ASSUMPTION/TODO items with facts and attach evidence per the checklist.

Cross-References
- `docs/SECURITY-SYSTEM-PROFILE.md` — Sections 9.4 (Privacy Analysis) and 9.5 (Data Sovereignty)
- `docs/SECURITY-ASSESSMENTS.md` — Privacy-related evidence and gaps
- `docs/ATO-READINESS-ROADMAP.md` — Action plan and decision gates
- `docs/RISK-REGISTER.md` — Privacy risks and residual risk

---

## Section A — Initiative Overview
- Initiative Name: PubSec-Info-Assistant-by-Copilot (EVA Domain Assistant 2.0)
- Description: An enterprise Retrieval-Augmented Generation (RAG) system providing natural language assistance using Azure OpenAI and a tenant-isolated knowledge base.
- Purpose/Goals: Improve information retrieval and guidance for public sector teams while maintaining Protected B compliance and privacy safeguards.
- Scope: Backend (FastAPI), Frontend (React), Vector DB (Qdrant), Cache (Redis), Azure OpenAI integration, Kubernetes on Azure.
- Stakeholders: Program Owner, Privacy Office (ATIP), Security (ISSO), DevSecOps, Operations.
- Legal Authority: ASSUMPTION — Authority under departmental program mandate and enabling statutes (TODO: cite specific statutes, policy instruments).

Deliverables:
- [ ] Program Charter / Business Case (reference)
- [ ] Legal Authority Statement (signed)

---

## Section B — Legal Authority & Collection
- Collection of Personal Information: See System Profile 9.4.1
  - Direct Collection: User-provided prompts and uploaded documents may contain PII (ASSUMPTION: limited to business context; not systematically collected).
  - Indirect Collection: Organizational documents ingested into RAG corpus may include PII. Source systems governed by their own authorities.
- Legal Authority Basis: ASSUMPTION — Departmental program mandates; Policy on Service and Digital; Directive on Privacy Practices (TODO: confirm with ATIP/legal).
- Notice to Individuals: TODO — Provide privacy notice at point of collection and in UI; link to departmental privacy policy.
- Consent Mechanisms: TODO — Inform consent for document ingestion and prompt processing; administrative consent for enterprise ingestion.

Deliverables:
- [ ] Legal Authority Confirmation (ATIP/legal memo)
- [ ] Privacy Notice Text and UI Placement
- [ ] Consent Design (user/admin flows)

---

## Section C — Personal Information Elements & Inventory
Categories of PI potentially processed (do not list actual examples):
- Identity (name, title, work email)
- Contact (work phone, work address)
- Employment (role, department, org unit)
- Content-derived PI (PII appearing in documents or prompts)
- System metadata (timestamps, tenant ID, correlation ID)

Data Inventory & Locations:
- Transient Processing: Prompts and responses in application memory
- Vector DB (Qdrant): Embeddings derived from documents (risk of re-identification if source contains PII)
- Cache (Redis): Short-lived cache keys/values, tenant-scoped
- Logs: Structured, redacted logs with correlation IDs; avoid storing raw PII
- LLM Provider: Azure OpenAI receives prompts and context (see Section F safeguards)

Deliverables:
- [ ] Data Inventory Spreadsheet (systems, fields, residency)
- [ ] Record of Authority & Retention Schedule Mapping

---

## Section D — Data Flows & Disclosures
Data Flow Summary (reference System Profile 9.4.2 and 9.4.5):
- Internal Use: Retrieval and answering based on tenant-scoped corpus
- External Disclosure: Azure OpenAI processing of prompts/context and returning completions
- Cross-Border Considerations: HIGH risk if non-Canadian processing is used (OpenAI USA); mitigation via Azure OpenAI Canada regions only

Attachments (to be provided):
- [ ] Data Flow Diagram(s) — collection, processing, storage, destruction
- [ ] Cross-Border Flow Matrix — systems, regions, data categories, mitigation
- [ ] Third-Party Disclosure Register — Azure services, sub-processors

---

## Section E — Privacy Risk Assessment (PADI Format)
Reference System Profile 9.4.6 for initial risks. Expand with likelihood/impact and residual risk.

Example Risks (to be validated):
1) Cross-Border Processing of PI
- Risk: PI in prompts/context processed by non-Canadian endpoints
- Likelihood: Medium-High; Impact: High; Inherent Risk: High
- Mitigations: Enforce Azure OpenAI (Canada Central/East), private endpoints, endpoint audits
- Residual Risk: Low-Medium; Decision: CIO risk acceptance if exceptions
- Evidence: Azure region configs, endpoints allowlist

2) Model Memorization / PII Leakage
- Risk: LLM outputs could reveal memorized PI or training artifacts
- Likelihood: Medium; Impact: High
- Mitigations: PII redaction (MS Presidio) before prompts, minimization, provider contractual limitations (no training on data), post-response filters
- Residual Risk: Medium; Evidence: redaction logs, provider DPA, moderation settings

3) Multi-Tenant Data Leakage
- Risk: Cross-tenant access via header manipulation, cache poisoning
- Likelihood: Medium; Impact: High
- Mitigations: Strict tenant scoping, Redis auth & key namespacing, DAST tests, code review
- Residual Risk: Medium; Evidence: tests, code paths, configs

4) Excessive Retention
- Risk: Retaining embeddings/logs longer than necessary
- Likelihood: Medium; Impact: Medium
- Mitigations: Retention schedules (embeddings: 7 years; logs: 1 year) with automation and verification
- Residual Risk: Low-Medium; Evidence: policies, automation jobs

5) Inadequate Transparency/Consent
- Risk: Individuals not informed about AI processing or data use
- Likelihood: Medium; Impact: Medium
- Mitigations: UI notices, consent toggles, documentation
- Residual Risk: Low; Evidence: screenshots, policy links

Deliverables:
- [ ] Risk Register (privacy subset) with owners and timelines
- [ ] Residual Risk Acceptance (CIO/Privacy sign-off)

---

## Section F — Safeguards (Administrative, Technical, Physical)
Administrative
- Policies: Privacy Policy, Acceptable Use, AI Use Policy
- Training: Privacy & secure handling for users and admins
- Contracts: DPA with Azure OpenAI; supplier privacy terms

Technical
- Access Control: Entra ID, MFA for admins, 7-role RBAC per System Profile 5.3
- Data Minimization: PII redaction (MS Presidio) before LLM calls; avoid raw PI in logs
- Encryption: TLS 1.2+/1.3 in transit; encryption at rest (CMEK recommended)
- Network: Private endpoints, VNET, WAF, rate limiting, Kubernetes NetworkPolicies
- Monitoring: SIEM (Sentinel), anomaly detection for exfiltration/prompt abuse, structured logs
- Resilience: Backups, DR runbooks, autoscaling

Physical
- Provider data center controls (Azure) — SOC 2 / ISO 27001 references

Deliverables:
- [ ] DPA with Azure OpenAI
- [ ] Configurations: Azure regions (Canada), private endpoints, Key Vault
- [ ] Logs & Monitoring: SIEM alerts, redaction samples
- [ ] RBAC Evidence: Role definitions, access reviews

---

## Section G — Recommendations, Decisions & Sign-Offs
Recommendations
- Use Azure OpenAI in Canadian regions only for Protected B
- Implement and verify PII redaction before inference; enforce log redaction
- Complete consent/notice UX and publish privacy documentation
- Enforce private endpoints and geofencing; maintain endpoint allowlist
- Archive PIA/PADI, TRA, and DPA artifacts in `evidence/privacy/`

Decisions (to be completed)
- [ ] Cross-border processing risk acceptance (if any exceptions)
- [ ] Residual privacy risks acceptance
- [ ] Final approval by Privacy Office and CIO

Sign-Offs
- Privacy Officer (Name, Title, Date)
- ISSO / Security Lead (Name, Title, Date)
- CIO / AO (Name, Title, Date)

---

## Evidence Checklist (Attach or Link)
- [ ] Data Inventory (systems, fields, residency)
- [ ] Data Flow Diagrams & Cross-Border Matrix
- [ ] DPA with Azure OpenAI
- [ ] Region & Endpoint Configurations (Canada Central/East)
- [ ] PII Redaction Design & Logs (Presidio)
- [ ] RBAC Implementation & Access Reviews
- [ ] SIEM Alerts & Monitoring Procedures
- [ ] Retention Policy & Automation Evidence

Notes
- Ensure no PII is placed in this document or in source control.
- Link evidence files under `evidence/privacy/` and related directories as created in the DevSecOps document.
