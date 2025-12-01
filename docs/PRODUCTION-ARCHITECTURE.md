# Production Architecture (Azure Reference)

## Overview
The PubSec-Info-Assistant-by-Copilot production deployment targets a multi-tenant, security-hardened Azure environment designed for Protected B (or equivalent) data classification. Core objectives: isolation, resilience, observability, cost governance, and compliance alignment (ITSG-33 / NIST SP 800-53).

## Logical Components
- Frontend (React + Nginx) – Static assets served via Azure Front Door (WAF) + CDN.
- API (FastAPI) – Stateless app pods behind Azure Application Gateway (optional), exposed via Front Door.
- Vector Store (Qdrant) – Dedicated VM scale set or AKS StatefulSet with encrypted disks.
- Cache (Redis) – Azure Cache for Redis Premium (VNet injected, TLS enforced).
- Embeddings/LLM – Azure OpenAI / OpenAI (private networking via VNet integration + Private Endpoint if Azure OpenAI).
- Object Storage – Azure Blob Storage for document ingestion originals (private container, immutability policy + lifecycle rules).
- Observability Stack – Azure Monitor (Logs, Metrics), optional Prometheus/Grafana sidecar or managed service.
- CI/CD – GitHub Actions with OIDC to Azure for federated deploy (no static secrets).

## Tenancy Model
- Tenant identifier header: `X-Tenant-ID`.
- Logical isolation enforced at collection (Qdrant) naming: `{tenant_id}_documents`.
- Redis key namespace prefix: `tenant:{tenant_id}:...`.
- Rate limiting per tenant (extend in production using Redis counters vs in-memory window).
- Optional differential retention policies per tenant (config table / Key Vault secret set).

## Data Flow Summary
1. User uploads document → API receives file → stored temporarily (RAM) → processed (text extraction / embeddings) → vectors into Qdrant collection per tenant.
2. Query → API retrieves top-k embeddings from tenant collection → constructs prompt + context → calls LLM endpoint → returns response (with cost metadata).
3. Metrics and logs → shipped to Azure Monitor (Container Insights + custom metrics exporter) → retention + analytics.

## Network Segmentation
- Hub-Spoke VNet model.
  - Hub: Shared services (Azure Firewall, Bastion, Private DNS, Key Vault).
  - Spoke 1: Application (AKS, Redis, Qdrant).
  - Spoke 2: Data services (Blob Storage private endpoints, optional PostgreSQL / future persistence).
- NSGs applied at subnet level: allow only required east-west traffic.
- Private Endpoints: Blob Storage, Azure OpenAI.

## Security Controls (Highlights)
- TLS Everywhere: Front Door → App Gateway (optional) → AKS Ingress (cert managed via Cert Manager + Key Vault integration).
- WAF (Front Door) with custom rules: block anomalous LLM prompt injection patterns, payload size limits, known bad user-agents.
- Secrets: Azure Key Vault (Managed Identity access). No plaintext secrets in containers.
- Image Security: Trivy/Grype scans + signed images (Cosign) promoted only from trusted registry.
- Supply Chain: CodeQL, SAST, IaC scanning (Checkov/tfsec), dependency pinning, SBOM generation.

## Resilience & Scaling
- AKS with node pools:
  - General compute pool (API + frontend).
  - High-memory pool (Embedding / vector operations) – vertical autoscaling constraints defined.
- HPA on API deployment (metrics: CPU, request latency p95).
- Qdrant replication (if cluster mode) + daily snapshot to Blob for DR.
- Redis persistence (AOF enabled) + geo-replication (Premium).

## Observability & Telemetry
- OpenTelemetry tracing (FastAPI instrumentation) → Azure Monitor OTLP endpoint.
- Metrics: Prometheus scraping (pod annotations) → Azure Managed Prometheus or sidecar → exported SLO dashboards.
- Logs: Structured JSON logging with fields (timestamp, level, tenant_id, request_id, path, duration_ms, status_code).

## Identity & Access
- DevOps Access: GitHub OIDC role assignment in Azure (least privilege: deploy only).
- Runtime Access: Managed Identities for AKS workloads retrieving secrets.
- RBAC: Key Vault access policies limited to CI + specific app identity.

## Encryption
- At-rest: Managed disks (Qdrant VMSS / AKS PV) encrypted with CMK (Key Vault) optional.
- In-transit: TLS for all external calls; Private Link for service endpoints eliminates public exposure.

## Cost Governance
- Tagging: `Environment=Prod`, `App=PubSecInfoAssistant`, `TenantGroup=PublicSector`.
- Quota/Spend Monitoring: Daily Azure Cost Management alert; model usage cost tracker header integration with per-tenant quotas.

## Deployment Flow
1. Pull Request → CI (lint, test, SAST, IaC scan, build images, SBOM).
2. Merge to `main` → staging deploy (AKS staging namespace) + ZAP active scan.
3. Manual approval → production deploy (blue-green or canary) + post-deploy smoke tests.
4. Evidence artifacts archived to `evidence/` and linked in ATO docs.

## DR & Backup
- Qdrant snapshot daily + point-in-time restore docs.
- Blob lifecycle: versioning + immutability for defined retention (e.g., 30 days ingestion raw, then purge).
- Redis backup per provider schedule (Azure Cache auto backups).

## Future Enhancements
- Per-tenant encryption (DEK envelope via Key Vault) for sensitive vector payload fields.
- Attribute-level access control in retrieval phase.
- Differential rate limits and burst allowances stored in config service.

## Diagram (Textual)
[Client] -> [Front Door (WAF)] -> [App Gateway / Ingress] -> [AKS API Pods] -> [Redis] & [Qdrant] & [Blob Storage]
                                                            \-> [Azure OpenAI Private Endpoint]
                                                            \-> [Telemetry Exporters] -> [Azure Monitor]

## Compliance Cross-Reference Anchors
- Network isolation: ITSG-33 AC-4, SC-7.
- Secrets management: SC-12, IA-5.
- Logging & monitoring: AU-2, AU-6, CA-7.
- DR backups: CP-9, CP-10.
- Supply chain: SA-11, SI-2.

---
This document serves as the authoritative reference for production deployment decisions. Changes require architecture review + security sign-off.
