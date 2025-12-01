# Security System Profile

**System Name**: PubSec Information Assistant  
**Version**: 0.1.0  
**Classification**: Protected B (Default)  
**Control Framework**: ITSG-33 / NIST 800-53  
**Prepared Date**: December 2024  
**Document Status**: Initial Draft for ATO/PADI Submission

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Description & Architecture](#2-system-description--architecture)
3. [Data Classification](#3-data-classification)
4. [AI Data Paths & Trust Boundaries](#4-ai-data-paths--trust-boundaries)
5. [Identity Flows](#5-identity-flows)
6. [External Dependencies](#6-external-dependencies)
7. [Security Controls Mapping](#7-security-controls-mapping)
8. [Gap Analysis](#8-gap-analysis)
9. [Privacy Impact Considerations](#9-privacy-impact-considerations)
10. [Appendices](#10-appendices)

---

## 1. Executive Summary

### 1.1 System Purpose

The PubSec Information Assistant is an enterprise-grade Retrieval-Augmented Generation (RAG) system designed for public sector agencies to answer policy, process, and compliance questions with evidence-backed citations and provenance tracking. The system enables secure, auditable AI-assisted document retrieval and question answering.

### 1.2 Security Classification

**Default Classification**: Protected B

This classification assumes the system may process information that could cause serious injury to individuals, organizations, or government if disclosed inappropriately. The system is designed to support Protected B classification requirements including:

- Tenant data isolation
- Encryption at rest and in transit
- Access control and audit logging
- Multi-tenancy with data segregation

### 1.3 Authorization Scope

This document provides the foundational security profile for:

- Authorization to Operate (ATO) assessment
- Privacy and Data Impact (PADI) submission
- ITSG-33 / NIST 800-53 control mapping

---

## 2. System Description & Architecture

### 2.1 System Overview

The PubSec Information Assistant is a multi-tier, microservices-based application consisting of:

| Component | Technology | Purpose |
|-----------|------------|---------|
| Frontend | React 18, TypeScript, Vite | User interface for queries and document management |
| Backend API | FastAPI (Python 3.11+) | REST API, RAG orchestration, tenant management |
| Vector Database | Qdrant | Document embeddings storage and similarity search |
| Cache Layer | Redis 7.x | Session management, query caching, rate limiting |
| LLM Integration | OpenAI API | Answer generation via GPT-4 |
| Embedding Service | OpenAI text-embedding-ada-002 | Document vectorization |
| Monitoring | Prometheus, Grafana | Observability and metrics |

### 2.2 High-Level Architecture Diagram

```
┌───────────────────────────────────────────────────────────────────────────┐
│                           TRUST BOUNDARY: USER ACCESS                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────┐                              ┌─────────────────────┐     │
│  │   Browser   │ ◄──── HTTPS (TLS 1.3) ────► │    Frontend (SPA)   │     │
│  │  (User)     │                              │    React/TypeScript │     │
│  └─────────────┘                              │    Port: 3000       │     │
│                                               └──────────┬──────────┘     │
│                                                          │                │
├──────────────────────────────────────────────────────────┼────────────────┤
│                  TRUST BOUNDARY: APPLICATION TIER         │                │
├──────────────────────────────────────────────────────────┼────────────────┤
│                                                          │                │
│                                               ┌──────────▼──────────┐     │
│                                               │   Backend API       │     │
│                                               │   FastAPI           │     │
│                                               │   Port: 8000        │     │
│                                               │   - RAG Service     │     │
│                                               │   - Ingestion       │     │
│                                               │   - Retrieval       │     │
│                                               └───┬────┬────┬───────┘     │
│                                                   │    │    │             │
│              ┌────────────────────────────────────┘    │    └────────┐    │
│              │                                         │             │    │
│   ┌──────────▼────────┐  ┌─────────────────────────────▼───┐  ┌─────▼────┐
│   │   Qdrant          │  │          Redis Cache            │  │Prometheus│
│   │   Vector Store    │  │   - Query Cache                 │  │Grafana   │
│   │   Port: 6333/6334 │  │   - Session Store               │  │Metrics   │
│   │   - Embeddings    │  │   - Rate Limiting               │  │          │
│   │   - Similarity    │  │   - Tenant Balance              │  │          │
│   │     Search        │  │   Port: 6379                    │  │          │
│   └───────────────────┘  └─────────────────────────────────┘  └──────────┘
│                                                                           │
├───────────────────────────────────────────────────────────────────────────┤
│                  TRUST BOUNDARY: EXTERNAL AI SERVICES                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│   ┌─────────────────────────────────────────────────────────────────┐     │
│   │                     Azure OpenAI / OpenAI API                   │     │
│   │   - text-embedding-ada-002 (Embeddings)                         │     │
│   │   - gpt-4-turbo-preview (LLM Generation)                        │     │
│   │   Endpoint: api.openai.com / [Azure OpenAI Endpoint]            │     │
│   └─────────────────────────────────────────────────────────────────┘     │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Component Details

#### 2.3.1 Frontend (React SPA)

- **Location**: `/frontend/`
- **Runtime**: Browser-based single-page application
- **Framework**: React 18.3.1, TypeScript 5.6.3, Vite 5.4.10
- **Dependencies**: axios (HTTP client), lucide-react (icons)
- **Build Output**: Static assets served via Nginx
- **Security Features**:
  - Content Security Policy headers (**ASSUMPTION**: configured in nginx.conf)
  - CORS restrictions
  - No direct database access

#### 2.3.2 Backend API (FastAPI)

- **Location**: `/backend/app/`
- **Runtime**: Python 3.11+, Uvicorn ASGI server
- **Framework**: FastAPI 0.115.0, Pydantic 2.9.0
- **Key Modules**:
  - `main.py`: Application entry point, route handlers
  - `config.py`: Environment-based configuration (pydantic-settings)
  - `rag_service.py`: RAG pipeline orchestration
  - `ingestion/`: Document processing pipeline
  - `retrieval/`: Vector search and retrieval
  - `llm/adapters.py`: LLM provider adapters (OpenAI, Anthropic stub)
  - `cache/redis_cache.py`: Caching and rate limiting

#### 2.3.3 Vector Database (Qdrant)

- **Version**: 1.7.4 (Docker), 1.12.0 (Kubernetes)
- **Purpose**: Store document embeddings for semantic search
- **Data Isolation**: Per-tenant collections (`tenant_{tenant_id}`)
- **Ports**: 6333 (HTTP), 6334 (gRPC)
- **Storage**: Persistent volume claims (50Gi per node)

#### 2.3.4 Cache Layer (Redis)

- **Version**: 7.x Alpine
- **Purpose**: Query caching, session management, rate limiting, tenant balance tracking
- **Data Isolation**: Key prefixes (`tenant:{tenant_id}:*`)
- **Persistence**: AOF (every 5 minutes), RDB (daily)
- **Memory Policy**: LRU eviction (512MB limit in development)

### 2.4 Deployment Architecture

#### 2.4.1 Container Deployment (Docker Compose)

The system deploys as six containerized services:

```yaml
Services:
  - pubsec-qdrant (Vector DB)
  - pubsec-redis (Cache)
  - pubsec-backend (API)
  - pubsec-frontend (UI)
  - pubsec-prometheus (Metrics)
  - pubsec-grafana (Dashboards)
```

#### 2.4.2 Kubernetes Deployment (Production)

- **Backend**: Deployment with 3 replicas, HPA enabled
- **Qdrant**: StatefulSet with 3 replicas, 50Gi PVC each
- **Redis**: StatefulSet with 3 replicas, 10Gi PVC each
- **Security Context**: 
  - Non-root user (UID 1000)
  - Read-only root filesystem
  - Dropped capabilities
  - Pod anti-affinity for distribution

---

## 3. Data Classification

### 3.1 Classification Framework

The system is designed to handle **Protected B** information by default, aligning with Government of Canada security classification levels.

| Classification Level | Description | System Support |
|---------------------|-------------|----------------|
| **Unclassified** | Public information | ✅ Supported |
| **Protected A** | Low sensitivity | ✅ Supported |
| **Protected B** | Moderate sensitivity (default) | ✅ Supported |
| **Protected C** | High sensitivity | ⚠️ **TODO**: Additional controls required |
| **Classified** | Secret/Top Secret | ❌ Not Supported |

### 3.2 Data Types and Classification

| Data Type | Classification | Location | Retention |
|-----------|---------------|----------|-----------|
| User queries | Protected B | Redis (cache), Logs | 90 days (logs), TTL 1hr (cache) |
| Document content | Protected B | Qdrant (vectors) | 3 years |
| Document metadata | Protected B | Qdrant (payload) | 3 years |
| Tenant identifiers | Protected A | All services | Lifetime |
| API keys/secrets | Protected B | Kubernetes Secrets, .env | N/A |
| Audit logs | Protected A | Application logs | 7 years |
| Session tokens | Protected A | Redis | TTL 30 min |
| Cost/Balance data | Protected A | Redis | 7 years (regulatory) |

### 3.3 Data Handling Requirements

#### 3.3.1 Encryption at Rest

| Component | Encryption Method | Status |
|-----------|------------------|--------|
| Qdrant storage | AES-256 (volume encryption) | **ASSUMPTION**: Cloud provider volume encryption |
| Redis persistence | AES-256 (volume encryption) | **ASSUMPTION**: Cloud provider volume encryption |
| Backups (S3) | Server-side encryption (SSE-S3) | Documented in SOC2 controls |
| Kubernetes secrets | Base64 (default) | **TODO**: Enable Sealed Secrets or External Secrets Operator |

#### 3.3.2 Encryption in Transit

| Communication Path | Protocol | Status |
|-------------------|----------|--------|
| Browser ↔ Frontend | TLS 1.3 | Configured via Ingress |
| Frontend ↔ Backend | HTTPS | Via Kubernetes Service |
| Backend ↔ Qdrant | HTTP | **TODO**: Enable TLS for internal traffic |
| Backend ↔ Redis | TCP | **TODO**: Enable TLS, configure AUTH password |
| Backend ↔ OpenAI | HTTPS/TLS 1.3 | Built-in to SDK |

### 3.4 Data Residency

**ASSUMPTION**: For Government of Canada Protected B compliance, data residency requirements include:

- Primary data center: Canadian region (e.g., Canada Central, Canada East for Azure)
- Backup storage: Canadian region only
- **TODO**: Confirm Azure OpenAI Canada deployment availability or implement Azure OpenAI Service with Canadian residency

---

## 4. AI Data Paths & Trust Boundaries

### 4.1 AI Data Flow Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         AI DATA FLOW DIAGRAM                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  INGESTION PATH (Document → Vector Embeddings)                          │
│  ═══════════════════════════════════════════════════════════════════    │
│                                                                         │
│  [User Upload] ──► [File Parser] ──► [Chunker] ──► [Embedding API]     │
│        │              │                   │              │              │
│        ▼              ▼                   ▼              ▼              │
│   Validation    HTML/PDF/DOCX/TXT   512 tokens     OpenAI ada-002      │
│   (size, type)  extraction         20% overlap    1536-dim vectors     │
│                                                         │              │
│                                                         ▼              │
│                                              [Qdrant Collection]       │
│                                              tenant_{tenant_id}        │
│                                                                         │
│  QUERY PATH (Question → Answer with Citations)                          │
│  ═══════════════════════════════════════════════════════════════════    │
│                                                                         │
│  [User Query] ──► [Cache Check] ──► [Query Embedding] ──► [Retrieval]  │
│        │              │                   │                   │         │
│        ▼              ▼                   ▼                   ▼         │
│   Validation    Redis Lookup       OpenAI ada-002      Qdrant Search   │
│   (length)      (hash key)         (same model)        (cosine sim)    │
│                                                              │         │
│                                                              ▼         │
│                                                    [Top-K Results]     │
│                                                    (default: 5)        │
│                                                              │         │
│                                                              ▼         │
│  [Answer Generation] ◄───────────────────── [Context Assembly]         │
│        │                                                               │
│        ▼                                                               │
│   OpenAI GPT-4 API                                                     │
│   - System prompt (RAG instructions)                                   │
│   - User prompt (query + context)                                      │
│   - Temperature: 0.0                                                   │
│   - Max tokens: 2000                                                   │
│        │                                                               │
│        ▼                                                               │
│  [Citation Extraction] ──► [Cost Calculation] ──► [Response]           │
│   Regex pattern:            Token-based                                │
│   [Doc N] format            Input/Output costs                         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Trust Boundaries

#### Trust Boundary 1: User Browser ↔ Application

- **Boundary Type**: External network boundary
- **Controls**:
  - TLS 1.3 encryption
  - CORS policy (whitelisted origins)
  - Input validation
  - Rate limiting (300 requests/60s per API key)
- **Data Crossing**: User queries, document uploads, API responses

#### Trust Boundary 2: Application ↔ Internal Services

- **Boundary Type**: Internal network (Docker network / Kubernetes namespace)
- **Controls**:
  - Kubernetes NetworkPolicy
  - Service mesh (optional)
  - **TODO**: Enable mTLS for service-to-service communication
- **Data Crossing**: Vector embeddings, cached responses, tenant data

#### Trust Boundary 3: Application ↔ External AI Services

- **Boundary Type**: External cloud API boundary
- **Controls**:
  - API key authentication (OPENAI_API_KEY)
  - HTTPS/TLS 1.3
  - Retry with exponential backoff
- **Data Crossing**:
  - **Outbound**: Document chunks (for embedding), Query + context (for generation)
  - **Inbound**: Embedding vectors, Generated answers
- **Privacy Considerations**:
  - ⚠️ **CRITICAL**: Document content is sent to external AI provider
  - **ASSUMPTION**: OpenAI API data usage policy reviewed
  - **TODO**: Evaluate Azure OpenAI in Government Cloud for data residency

### 4.3 AI Input/Output Data Analysis

#### 4.3.1 Embedding Generation (text-embedding-ada-002)

| Attribute | Details |
|-----------|---------|
| **Input** | Document chunk text (512 tokens, 20% overlap) |
| **Output** | 1536-dimensional float vector |
| **Data Sensitivity** | Protected B document content |
| **Retention at Provider** | OpenAI API: 30 days (default), opt-out available; Azure OpenAI: No retention (data not used for training). Reference: [OpenAI Data Usage Policy](https://openai.com/policies/api-data-usage-policies), [Azure OpenAI Data Privacy](https://learn.microsoft.com/en-us/legal/cognitive-services/openai/data-privacy) |
| **Alternative** | sentence-transformers (fallback, local) |

#### 4.3.2 Answer Generation (gpt-4-turbo-preview)

| Attribute | Details |
|-----------|---------|
| **Input - System Prompt** | RAG instructions (static, non-sensitive) |
| **Input - User Prompt** | Query text + retrieved document chunks (Protected B) |
| **Output** | Generated answer with citation references |
| **Temperature** | 0.0 (deterministic) |
| **Max Tokens** | 2000 |
| **Data Sensitivity** | Query context contains Protected B content |

### 4.4 AI Metadata Flows

| Metadata Type | Source | Destination | Purpose |
|--------------|--------|-------------|---------|
| Token usage | OpenAI API response | Redis, Logs | Cost tracking |
| Processing time | Backend measurement | Prometheus | Performance monitoring |
| Model version | OpenAI API response | Logs | Audit trail |
| Citation references | LLM output | API response | Provenance tracking |
| Confidence scores | Qdrant similarity | API response | Quality assessment |

### 4.5 AI Security Controls

| Control | Implementation | Status |
|---------|---------------|--------|
| Prompt injection prevention | System prompt separation, input validation | ✅ Implemented |
| Content filtering | Azure OpenAI content filters | **TODO**: Enable if using Azure OpenAI |
| Hallucination detection | Citation validation against source docs | ✅ Implemented |
| PII redaction | **TODO**: Integrate Microsoft Presidio | **TODO** |
| Output validation | Regex-based citation extraction | ✅ Implemented |

### 4.6 AI-Specific Threat Landscape

#### 4.6.1 Prompt Injection & Adversarial Inputs

| Threat Vector | Description | Mitigation | Status |
|--------------|-------------|------------|--------|
| **Direct Prompt Injection** | User query attempts to override system instructions (e.g., "Ignore previous instructions and...") | System/user prompt separation; input sanitization; detection patterns | ✅ Partial |
| **Indirect Prompt Injection** | Malicious content embedded in ingested documents (e.g., hidden instructions in PDFs) | Document sanitization; content scanning; source validation | **TODO** |
| **Jailbreaking** | Attempts to bypass content filters or safety rails | Azure OpenAI safety settings; output filtering | **TODO** (if using Azure OpenAI) |
| **Context Manipulation** | Crafted queries to extract unrelated document content | Relevance scoring; context window limits; retrieval threshold | ✅ Implemented |

#### 4.6.2 Model & Data Integrity Risks

| Threat Vector | Description | Mitigation | Status |
|--------------|-------------|------------|--------|
| **Training Data Contamination** | N/A (using external API, no training) | API-based model (not trainable by client) | ✅ N/A |
| **Model Substitution** | Attacker replaces model endpoint | HTTPS/TLS pinning; endpoint validation | ✅ Implemented |
| **Output Manipulation** | Malicious modification of LLM responses | Citation validation; response hashing; audit logs | ⚠️ Partial |
| **Data Poisoning (Vector DB)** | Malicious embeddings injected into Qdrant | Tenant isolation; ingestion ACLs; content validation | ✅ Partial |

#### 4.6.3 Privacy & Confidentiality Risks

| Threat Vector | Description | Mitigation | Status |
|--------------|-------------|------------|--------|
| **PII Leakage to AI Provider** | Protected B data sent to OpenAI API | **TODO**: PII redaction pre-processing; consider Azure OpenAI Canada | **HIGH PRIORITY** |
| **Model Memorization** | LLM retains sensitive data from API calls | OpenAI API: 30-day retention (opt-out available); Azure OpenAI: No retention | **ASSUMPTION** |
| **Cross-Tenant Inference** | Model "learns" from one tenant's data and reveals it to another | API-based (no shared fine-tuning); tenant isolation | ✅ Implemented |
| **Query History Exposure** | Cached queries reveal sensitive patterns | Redis key encryption; TTL enforcement; access controls | ⚠️ Partial |

#### 4.6.4 Availability & Denial of Service

| Threat Vector | Description | Mitigation | Status |
|--------------|-------------|------------|--------|
| **Token Exhaustion** | Attacker consumes tenant quota | Per-tenant rate limiting; cost caps; balance checks | ✅ Implemented |
| **Embedding Flooding** | Large document uploads exhaust resources | File size limits (50MB); chunk limits; ingestion throttling | ✅ Implemented |
| **Cache Poisoning** | Attacker fills Redis cache with garbage | Cache eviction policies; per-tenant cache quotas | ⚠️ Partial |
| **API Rate Limiting Bypass** | Distributed attack from multiple IPs | IP-based rate limiting; CAPTCHA; anomaly detection | **TODO** |

#### 4.6.5 Supply Chain & Dependency Risks

| Threat Vector | Description | Mitigation | Status |
|--------------|-------------|------------|--------|
| **Malicious PyPI/npm Package** | Compromised dependency injects backdoor | Dependency pinning; lock files; Dependabot scanning | ✅ Implemented |
| **Container Image Tampering** | Malicious code in base images | Official images only; image signing; vulnerability scanning | ✅ Implemented |
| **Model Provider Compromise** | OpenAI/Azure API compromised | Multi-provider fallback; response validation; audit logs | **TODO** |

### 4.7 AI Safety & Ethical Controls

| Control | Implementation | Status |
|---------|---------------|--------|
| **Bias Detection** | **TODO**: Monitor for demographic bias in retrieval results | **TODO** |
| **Explainability** | Citation-based provenance (source document references) | ✅ Implemented |
| **Human-in-the-Loop** | **TODO**: Flag low-confidence answers for review | **TODO** |
| **Usage Monitoring** | Query logging; cost tracking; pattern analysis | ✅ Implemented |
| **Redress Mechanism** | **TODO**: Feedback loop for incorrect answers | **TODO** |

---

## 5. Identity Flows

### 5.1 Current Authentication Architecture

**ASSUMPTION**: The repository shows a basic authentication pattern. Production deployment should integrate with Entra ID (Azure AD).

#### 5.1.1 API Key Authentication (Current Implementation)

```
┌────────────────────────────────────────────────────────────────────┐
│                    CURRENT API KEY FLOW                            │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  [Client] ──► HTTP Request ──► [Backend API]                       │
│              Headers:                │                             │
│              - X-API-Key: <key>      │                             │
│              - X-Tenant-ID: <id>     │                             │
│                                      ▼                             │
│                             ┌────────────────┐                     │
│                             │ _require_api_key │                   │
│                             │ (main.py L82-88) │                   │
│                             └────────────────┘                     │
│                                      │                             │
│                                      ▼                             │
│                             ┌────────────────┐                     │
│                             │  rate_limit    │                     │
│                             │  (in-memory)   │                     │
│                             └────────────────┘                     │
│                                                                    │
│  Note: Current implementation accepts missing API key as "public"  │
│  **TODO**: Implement proper authentication for production          │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

#### 5.1.2 Multi-Tenancy Implementation

- **Tenant Identification**: `X-Tenant-ID` header
- **Default Tenant**: "default" if header not provided
- **Data Isolation**:
  - Qdrant: Collection per tenant (`tenant_{tenant_id}`)
  - Redis: Key prefix (`tenant:{tenant_id}:*`)

### 5.2 Target Identity Architecture (Entra ID Integration)

**TODO**: Implement the following identity architecture for production:

```
┌────────────────────────────────────────────────────────────────────────┐
│               TARGET ENTRA ID INTEGRATION (TODO)                       │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌──────────┐         ┌───────────────────┐         ┌──────────────┐  │
│  │  User    │ ──────► │   Entra ID        │ ──────► │  Backend API │  │
│  │  Browser │  OAuth2 │   (Azure AD)      │  JWT    │  FastAPI     │  │
│  └──────────┘  PKCE   └───────────────────┘  Token  └──────────────┘  │
│                              │                             │          │
│                              │                             │          │
│                              ▼                             │          │
│                    ┌─────────────────┐                     │          │
│                    │  App Registration │                   │          │
│                    │  - Client ID      │                   │          │
│                    │  - API Scopes     │                   │          │
│                    │  - Redirect URIs  │                   │          │
│                    └─────────────────┘                     │          │
│                                                            │          │
│                                                            ▼          │
│                                                  ┌─────────────────┐  │
│                                                  │  JWT Validation │  │
│                                                  │  - Issuer       │  │
│                                                  │  - Audience     │  │
│                                                  │  - Signature    │  │
│                                                  │  - Claims       │  │
│                                                  └─────────────────┘  │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### 5.3 Role Design (Target State)

**TODO**: Implement RBAC with the following roles:

| Role | Description | Permissions | Entra ID Group | Azure RBAC Role |
|------|-------------|-------------|----------------|-----------------|
| **System Admin** | Platform administrator | Full access: tenant mgmt, user mgmt, config changes, delete operations | `sg-pubsec-sysadmin` | Owner (scoped to resource group) |
| **Tenant Admin** | Per-tenant administrator | Tenant-scoped: user mgmt, document ingestion, query, view analytics | `sg-pubsec-tenant-{tenant_id}-admin` | Contributor (scoped to tenant namespace) |
| **Data Steward** | Document governance | Ingest, update, delete documents; manage collections; no user mgmt | `sg-pubsec-data-steward` | Custom: Data Steward |
| **Operator** | DevOps/SRE team | Monitor services, restart pods, view logs; no data access, no config changes | `sg-pubsec-operator` | Reader + Monitoring Contributor |
| **Analyst** | End user (query + ingest) | Query, ingest documents, view own query history | `sg-pubsec-analyst` | Custom: Analyst |
| **Viewer** | Read-only end user | Query only, view results; no ingestion, no history access | `sg-pubsec-viewer` | Custom: Viewer |
| **Auditor** | Compliance/security audit | Read-only: audit logs, metrics, config; no data access, no operations | `sg-pubsec-auditor` | Log Analytics Reader + Security Reader |

#### 5.3.1 Permission Matrix

| Operation | System Admin | Tenant Admin | Data Steward | Operator | Analyst | Viewer | Auditor |
|-----------|:------------:|:------------:|:------------:|:--------:|:-------:|:------:|:-------:|
| **System Operations** | | | | | | | |
| Create/Delete Tenant | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Modify System Config | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Restart Services | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| **User Management** | | | | | | | |
| Manage Users (Global) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Manage Users (Tenant) | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Assign Roles | ✅ | ✅ (tenant-scoped) | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Document Operations** | | | | | | | |
| Ingest Documents | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ |
| Delete Documents | ✅ | ✅ | ✅ | ❌ | ⚠️ (own only) | ❌ | ❌ |
| Update Metadata | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Query Operations** | | | | | | | |
| Submit Queries | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ |
| View Query History (All) | ✅ | ✅ (tenant-scoped) | ❌ | ❌ | ❌ | ❌ | ✅ |
| View Query History (Own) | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | ✅ |
| **Monitoring & Audit** | | | | | | | |
| View Metrics | ✅ | ✅ (tenant-scoped) | ❌ | ✅ | ❌ | ❌ | ✅ |
| View Logs | ✅ | ⚠️ (tenant-scoped) | ❌ | ✅ | ❌ | ❌ | ✅ |
| Access Audit Trail | ✅ | ⚠️ (tenant-scoped) | ❌ | ❌ | ❌ | ❌ | ✅ |
| Export Compliance Reports | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

**Legend**: ✅ Full Access | ⚠️ Limited/Scoped Access | ❌ No Access

#### 5.3.2 Azure RBAC Custom Role Definitions

**TODO**: Create the following custom RBAC roles in Azure:

```json
{
  "Name": "PubSec Data Steward",
  "Description": "Manage documents and collections without user/system administration",
  "Actions": [
    "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/read",
    "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/write",
    "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/delete",
    "Microsoft.ContainerRegistry/registries/pull/read"
  ],
  "NotActions": [],
  "AssignableScopes": ["/subscriptions/{subscription-id}/resourceGroups/{rg-name}"]
}

{
  "Name": "PubSec Analyst",
  "Description": "Query and ingest documents (no admin operations)",
  "Actions": [
    "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/read",
    "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/write"
  ],
  "NotActions": [],
  "AssignableScopes": ["/subscriptions/{subscription-id}/resourceGroups/{rg-name}"]
}

{
  "Name": "PubSec Viewer",
  "Description": "Read-only query access",
  "Actions": [
    "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/read"
  ],
  "NotActions": [],
  "AssignableScopes": ["/subscriptions/{subscription-id}/resourceGroups/{rg-name}"]
}
```

### 5.4 Service Principals and Managed Identities

**TODO**: Configure the following service principals for production:

| Service Principal | Purpose | Required Permissions |
|-------------------|---------|---------------------|
| `sp-pubsec-backend` | Backend API authentication | Azure OpenAI access, Key Vault access |
| `sp-pubsec-qdrant` | Qdrant storage access | Storage account access (if using Azure storage) |
| `mi-aks-cluster` | AKS managed identity | Key Vault, Container Registry |

### 5.5 Token and Session Management

| Token Type | Implementation | Lifetime | Storage |
|------------|----------------|----------|---------|
| Access Token (JWT) | **TODO**: Entra ID | 30 min (configurable) | Browser memory |
| Refresh Token | **TODO**: Entra ID | 8 hours | HTTP-only cookie |
| API Key | Current (basic) | No expiry | Client config |
| Session ID | **TODO** | 30 min | Redis |

### 5.6 Identity Flow Gaps

| Gap ID | Description | Priority | Status |
|--------|-------------|----------|--------|
| **ID-GAP-01** | No OAuth2/OIDC implementation | High | **TODO** |
| **ID-GAP-02** | API keys have no expiry | Medium | **TODO** |
| **ID-GAP-03** | No MFA enforcement | High | **TODO** |
| **ID-GAP-04** | Missing service principal setup | High | **TODO** |
| **ID-GAP-05** | No session invalidation mechanism | Medium | **TODO** |

---

## 6. External Dependencies

### 6.1 Cloud Services & APIs

| Service | Provider | Purpose | Data Transmitted | Classification |
|---------|----------|---------|-----------------|----------------|
| OpenAI API | OpenAI | LLM generation, embeddings | Document chunks, queries | Protected B |
| Azure OpenAI | Microsoft | Alternative LLM provider | Document chunks, queries | Protected B |
| Container Registry | GitHub (GHCR) | Container images | Build artifacts | Unclassified |
| DNS | Cloud provider | Domain resolution | Hostnames | Unclassified |

### 6.2 Python Dependencies (Backend)

#### Core Framework

| Package | Version | Purpose | Security Notes |
|---------|---------|---------|----------------|
| fastapi | 0.115.0 | Web framework | Actively maintained |
| uvicorn | 0.31.0 | ASGI server | Production-ready |
| pydantic | 2.9.0 | Data validation | Type-safe |
| pydantic-settings | 2.5.2 | Configuration | Environment-based |

#### Document Processing

| Package | Version | Purpose | Security Notes |
|---------|---------|---------|----------------|
| pypdf | 4.3.1 | PDF parsing | Review for CVEs |
| beautifulsoup4 | 4.12.3 | HTML parsing | Trusted package |
| python-docx | 1.1.2 | DOCX parsing | Review for CVEs |
| lxml | 5.3.0 | XML processing | Known attack surface |
| pytesseract | 0.3.13 | OCR | Requires Tesseract binary |
| Pillow | 10.4.0 | Image processing | Review for CVEs |

#### AI & Vector DB

| Package | Version | Purpose | Security Notes |
|---------|---------|---------|----------------|
| openai | 1.51.0 | OpenAI SDK | Official SDK |
| sentence-transformers | 3.2.1 | Local embeddings | Large dependency tree |
| qdrant-client | 1.12.0 | Vector DB client | Official SDK |

#### Caching & Security

| Package | Version | Purpose | Security Notes |
|---------|---------|---------|----------------|
| redis | 5.2.0 | Redis client | Async support |
| python-jose | 3.3.0 | JWT handling | Cryptography backend |
| passlib | 1.7.4 | Password hashing | bcrypt backend |

#### Observability

| Package | Version | Purpose | Security Notes |
|---------|---------|---------|----------------|
| prometheus-client | 0.21.0 | Metrics | Standard library |
| opentelemetry-api | 1.28.1 | Tracing | CNCF project |

### 6.3 JavaScript Dependencies (Frontend)

| Package | Version | Purpose | Security Notes |
|---------|---------|---------|----------------|
| react | 18.3.1 | UI framework | Meta-maintained |
| react-dom | 18.3.1 | DOM rendering | Meta-maintained |
| axios | 1.7.7 | HTTP client | Review for CVEs |
| lucide-react | 0.460.0 | Icons | Community package |
| typescript | 5.6.3 | Type system | Microsoft-maintained |
| vite | 5.4.10 | Build tool | Actively maintained |

### 6.4 Container Images

| Image | Version | Source | Purpose |
|-------|---------|--------|---------|
| qdrant/qdrant | v1.7.4 / v1.12.0 | Docker Hub | Vector database |
| redis | 7-alpine / 7.2-alpine | Docker Hub | Cache |
| prom/prometheus | v2.48.0 | Docker Hub | Metrics |
| grafana/grafana | 10.2.2 | Docker Hub | Dashboards |
| nginx | (frontend base) | Docker Hub | Static file serving |
| python | 3.11 (backend base) | Docker Hub | Runtime |

### 6.5 External Endpoints

| Endpoint | Protocol | Purpose | Firewall Rule |
|----------|----------|---------|---------------|
| api.openai.com | HTTPS/443 | OpenAI API | Outbound |
| [Azure OpenAI endpoint] | HTTPS/443 | Azure OpenAI | Outbound |
| ghcr.io | HTTPS/443 | Container registry | Outbound |
| pypi.org | HTTPS/443 | Python packages | Build-time only |
| npmjs.com | HTTPS/443 | Node packages | Build-time only |

### 6.6 Dependency Security Considerations

| Concern | Mitigation | Status |
|---------|-----------|--------|
| Known CVEs | Dependabot alerts, regular updates | ✅ Enabled |
| Supply chain attacks | Package pinning, lock files | ✅ Implemented |
| Outdated packages | Automated dependency updates | ✅ Configured |
| Malicious packages | Registry verification | **ASSUMPTION** |

---

## 7. Security Controls Mapping

### 7.1 ITSG-33 / NIST 800-53 Control Families

This section maps system capabilities to relevant security control families.

#### 7.1.1 Access Control (AC)

| Control | Description | Implementation | Status |
|---------|-------------|----------------|--------|
| AC-1 | Access Control Policy | SECURITY.md, SOC2 documentation | ✅ Documented |
| AC-2 | Account Management | **TODO**: Entra ID integration | **TODO** |
| AC-3 | Access Enforcement | API key + tenant header validation | ⚠️ Partial |
| AC-4 | Information Flow | Tenant data isolation | ✅ Implemented |
| AC-6 | Least Privilege | K8s RBAC, non-root containers | ✅ Implemented |
| AC-7 | Unsuccessful Login Attempts | Rate limiting (429 after threshold) | ⚠️ Partial |
| AC-14 | Permitted Actions | Public read, authenticated write | ⚠️ Partial |
| AC-17 | Remote Access | HTTPS only, no SSH to containers | ✅ Implemented |

#### 7.1.2 Audit and Accountability (AU)

| Control | Description | Implementation | Status |
|---------|-------------|----------------|--------|
| AU-1 | Audit Policy | SOC2 documentation | ✅ Documented |
| AU-2 | Audit Events | Application logging | ✅ Implemented |
| AU-3 | Content of Audit Records | Structured JSON logs | ✅ Implemented |
| AU-4 | Audit Storage | Log retention 7 years | **ASSUMPTION** |
| AU-6 | Audit Review | Grafana dashboards | ✅ Implemented |
| AU-9 | Protection of Audit Info | Immutable logs | **ASSUMPTION** |
| AU-11 | Audit Record Retention | 7 years (documented) | **ASSUMPTION** |

#### 7.1.3 Configuration Management (CM)

| Control | Description | Implementation | Status |
|---------|-------------|----------------|--------|
| CM-1 | Configuration Policy | Infrastructure as Code | ✅ Implemented |
| CM-2 | Baseline Configuration | Docker Compose, K8s manifests | ✅ Implemented |
| CM-3 | Configuration Change Control | Git, PR reviews | ✅ Implemented |
| CM-6 | Configuration Settings | Environment variables | ✅ Implemented |
| CM-7 | Least Functionality | Minimal container images | ⚠️ Partial |
| CM-8 | Component Inventory | requirements.txt, package.json | ✅ Implemented |

#### 7.1.4 Identification and Authentication (IA)

| Control | Description | Implementation | Status |
|---------|-------------|----------------|--------|
| IA-1 | I&A Policy | SECURITY.md | ✅ Documented |
| IA-2 | User Identification | API key + tenant ID | ⚠️ Partial |
| IA-5 | Authenticator Management | **TODO**: Token rotation | **TODO** |
| IA-8 | Non-Organizational Users | Multi-tenancy | ✅ Implemented |

#### 7.1.5 Incident Response (IR)

| Control | Description | Implementation | Status |
|---------|-------------|----------------|--------|
| IR-1 | Incident Response Policy | P0-INCIDENTS.md | ✅ Documented |
| IR-4 | Incident Handling | Runbooks | ✅ Documented |
| IR-5 | Incident Monitoring | Prometheus alerts | ✅ Implemented |
| IR-6 | Incident Reporting | Slack, PagerDuty templates | ✅ Documented |

#### 7.1.6 System and Communications Protection (SC)

| Control | Description | Implementation | Status |
|---------|-------------|----------------|--------|
| SC-1 | SC Policy | SECURITY.md | ✅ Documented |
| SC-7 | Boundary Protection | K8s NetworkPolicy | ✅ Implemented |
| SC-8 | Transmission Confidentiality | TLS 1.3 | ✅ Implemented |
| SC-12 | Cryptographic Key Mgmt | K8s Secrets | ⚠️ Partial |
| SC-13 | Cryptographic Protection | AES-256, TLS | **ASSUMPTION** |
| SC-28 | Protection of Info at Rest | Volume encryption | **ASSUMPTION** |

#### 7.1.7 System and Information Integrity (SI)

| Control | Description | Implementation | Status |
|---------|-------------|----------------|--------|
| SI-1 | SI Policy | SECURITY.md | ✅ Documented |
| SI-2 | Flaw Remediation | Dependabot, CI scanning | ✅ Implemented |
| SI-3 | Malicious Code Protection | Container scanning | ✅ Implemented |
| SI-4 | Information System Monitoring | Prometheus, Grafana | ✅ Implemented |
| SI-10 | Information Input Validation | Pydantic models | ✅ Implemented |

---

## 8. Gap Analysis

### 8.1 Critical Gaps (High Priority)

| Gap ID | Category | Description | Remediation | Priority |
|--------|----------|-------------|-------------|----------|
| **GAP-01** | Identity | No OAuth2/OIDC authentication | Implement Entra ID integration | **HIGH** |
| **GAP-02** | Identity | No MFA enforcement | Enable Entra ID conditional access | **HIGH** |
| **GAP-03** | Data Protection | PII not redacted before AI processing | Integrate Microsoft Presidio | **HIGH** |
| **GAP-04** | Data Residency | OpenAI API may store data outside Canada | Evaluate Azure OpenAI Canada | **HIGH** |
| **GAP-05** | Encryption | Internal service traffic not encrypted | Enable mTLS / service mesh | **HIGH** |

### 8.2 Moderate Gaps (Medium Priority)

| Gap ID | Category | Description | Remediation | Priority |
|--------|----------|-------------|-------------|----------|
| **GAP-06** | Secrets | K8s secrets not encrypted at rest | Implement Sealed Secrets | **MEDIUM** |
| **GAP-07** | API Security | API keys have no expiry | Implement key rotation policy | **MEDIUM** |
| **GAP-08** | Audit | Audit log integrity not verified | Implement log signing | **MEDIUM** |
| **GAP-09** | Session | No session invalidation mechanism | Implement token revocation | **MEDIUM** |
| **GAP-10** | Content Filtering | AI content filters not configured | Enable Azure OpenAI content safety | **MEDIUM** |

### 8.3 Minor Gaps (Low Priority)

| Gap ID | Category | Description | Remediation | Priority |
|--------|----------|-------------|-------------|----------|
| **GAP-11** | Documentation | No formal data flow diagrams | Create C4 diagrams | **LOW** |
| **GAP-12** | Testing | No chaos engineering tests | Implement Chaos Monkey | **LOW** |
| **GAP-13** | Performance | No response time SLO monitoring | Add latency alerts | **LOW** |

### 8.4 Assumptions Requiring Validation

| ID | Assumption | Validation Required |
|----|------------|---------------------|
| **ASSUMP-01** | Cloud provider volume encryption enabled | Verify Azure/AWS disk encryption settings |
| **ASSUMP-02** | OpenAI API data retention policy acceptable for Protected B | Review: OpenAI API retains data for 30 days by default (opt-out available). Azure OpenAI does not retain or use API data for training. Confirm contractual terms meet GC requirements. |
| **ASSUMP-03** | Log retention meets 7-year requirement | Verify log aggregation configuration |
| **ASSUMP-04** | nginx.conf includes security headers | Audit nginx configuration |
| **ASSUMP-05** | Container images scanned for vulnerabilities | Verify CI pipeline scanning |

---

## 9. Privacy Impact Considerations

### 9.1 Personal Information Collected

| PI Category | Collection Point | Purpose | Retention |
|-------------|-----------------|---------|-----------|
| User queries | API requests | RAG processing | 90 days (logs), 1hr (cache) |
| Document content | Ingestion API | Vector search | 3 years |
| Tenant identifiers | HTTP headers | Multi-tenancy | Lifetime |
| Usage metrics | All requests | Cost tracking, analytics | 7 years |

### 9.2 Privacy Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| PII in documents processed by external AI | High | High | **TODO**: Implement PII redaction |
| Query logs contain sensitive information | Medium | Medium | Implement log redaction |
| Cross-tenant data exposure | Low | High | Tenant isolation (implemented) |
| Data breach at AI provider | Low | High | Evaluate Azure OpenAI Government |

### 9.3 Privacy Controls

| Control | Implementation | Status |
|---------|---------------|--------|
| Data minimization | Only required fields collected | ✅ Implemented |
| Purpose limitation | Data used only for RAG | ✅ Implemented |
| Storage limitation | Retention policies defined | ⚠️ Partial |
| Consent management | **TODO**: Implement consent tracking | **TODO** |
| Right to erasure | Tenant offboarding scripts | ✅ Documented |
| Data portability | **TODO**: Export functionality | **TODO** |

### 9.4 PADI-Aligned Privacy Analysis

#### 9.4.1 Collection of Personal Information

| Collection Point | Type of PI | Direct/Indirect | Purpose | Consent Required? |
|-----------------|------------|-----------------|---------|-------------------|
| Document Upload | Content may contain names, contact info, policy references | Direct (user uploads) | RAG indexing and retrieval | Yes (via terms of service) |
| Query Submission | User questions may contain PII | Direct (user input) | Answer generation | Yes (via terms of service) |
| Usage Logs | Timestamps, tenant IDs, query patterns | Indirect (system-generated) | Audit, performance monitoring | No (legitimate operational purpose) |
| Session Data | Tenant ID, session ID | Indirect (system-generated) | Multi-tenancy, rate limiting | No (technical necessity) |

**ASSUMPTION**: No names, email addresses, or other direct identifiers are collected beyond what users voluntarily include in documents or queries.

#### 9.4.2 Use and Disclosure

| Data Type | Internal Use | External Disclosure | Legal Basis |
|-----------|-------------|---------------------|-------------|
| Document Content | Vector indexing, retrieval | OpenAI/Azure OpenAI (API processing) | Contractual (service provision) |
| Queries | Answer generation, caching | OpenAI/Azure OpenAI (API processing) | Contractual (service provision) |
| Usage Metrics | Cost tracking, analytics | None (internal only) | Legitimate operational purpose |
| Audit Logs | Security monitoring, compliance | Auditors (upon request) | Legal obligation |

**CRITICAL**: Document chunks and queries containing Protected B information are transmitted to external AI providers (OpenAI or Azure OpenAI). This constitutes **cross-border data transfer** if using OpenAI's US-based API.

#### 9.4.3 Retention and Disposal

| Data Type | Retention Period | Disposal Method | Status |
|-----------|-----------------|-----------------|--------|
| Vector Embeddings | 3 years (configurable) | Qdrant collection deletion + volume wipe | **ASSUMPTION** |
| Cached Queries | 1 hour (TTL) | Redis automatic expiry | ✅ Implemented |
| Application Logs | 90 days (rotating) | Automated log rotation | ✅ Implemented |
| Audit Logs | 7 years | Secure archive, then shred | **ASSUMPTION** |
| Tenant Data (on offboarding) | Immediate deletion | Collection drop + backup purge | ✅ Documented |

**TODO**: Implement automated data lifecycle management and secure disposal verification.

#### 9.4.4 Safeguards

| Safeguard Type | Implementation | PADI Evidence |
|---------------|----------------|---------------|
| **Administrative** | | |
| Privacy Policy | **TODO**: Publish privacy policy | **TODO** |
| Staff Training | **TODO**: Privacy awareness training | **TODO** |
| Data Steward Designation | **TODO**: Assign data steward role | **TODO** |
| **Technical** | | |
| Encryption at Rest | AES-256 (cloud provider volume encryption) | **ASSUMPTION**: Verify in infrastructure |
| Encryption in Transit | TLS 1.3 (all external connections) | ✅ Implemented (verify with SSL Labs scan) |
| Access Controls | Tenant isolation, RBAC | ✅ Implemented (partial—needs Entra ID) |
| Audit Logging | Structured JSON logs, request tracing | ✅ Implemented |
| PII Redaction | **TODO**: Presidio integration | **HIGH PRIORITY** |
| **Physical** | | |
| Data Center Security | Cloud provider (Azure/AWS SOC 2 certified) | ✅ Contractual (verify attestations) |
| Geographic Restrictions | **TODO**: Enforce Canadian data residency | **HIGH PRIORITY** |

#### 9.4.5 Cross-Border Data Flow Analysis

| Data Flow | Source | Destination | Classification | PADI Implication |
|-----------|--------|-------------|----------------|------------------|
| Document Chunks → OpenAI API | Canada (assumed) | USA (api.openai.com) | Protected B | **HIGH RISK**: Requires TBS approval for cross-border transfer of Protected B |
| Queries → OpenAI API | Canada (assumed) | USA (api.openai.com) | Protected B | **HIGH RISK**: Same as above |
| Document Chunks → Azure OpenAI Canada | Canada | Canada (Azure Canada Central/East) | Protected B | **COMPLIANT** (if configured) |
| Logs → Azure Log Analytics | Canada | Canada (if configured) | Protected A | ✅ Configurable |

**RECOMMENDATION**: For Protected B compliance, deploy Azure OpenAI in Canadian regions and enforce data residency policies.

#### 9.4.6 Privacy Risks (PADI Format)

| Risk ID | Risk Description | Likelihood | Impact | Inherent Risk | Mitigation | Residual Risk |
|---------|-----------------|------------|--------|---------------|-----------|---------------|
| **PR-01** | PII in documents sent to US-based AI provider | High | High | **HIGH** | Use Azure OpenAI Canada; implement PII redaction | **MEDIUM** |
| **PR-02** | Query history exposes sensitive patterns | Medium | Medium | **MEDIUM** | Implement log redaction; limit retention | **LOW** |
| **PR-03** | Data breach at AI provider | Low | High | **MEDIUM** | Contractual controls; encryption in transit | **MEDIUM** |
| **PR-04** | Unauthorized cross-tenant access | Low | High | **MEDIUM** | Tenant isolation (implemented); RBAC | **LOW** |
| **PR-05** | Insufficient consent for AI processing | Medium | Medium | **MEDIUM** | Update terms of service; explicit consent flow | **LOW** |

### 9.5 Data Sovereignty & Residency

**TODO**: Implement the following controls for Protected B data sovereignty:

| Requirement | Current State | Target State | Priority |
|-------------|--------------|--------------|----------|
| **Primary Storage** | Configurable (Qdrant, Redis locations) | Azure Canada Central/East | **HIGH** |
| **Backup Storage** | Configurable | Azure Canada Central/East (geo-redundant within Canada) | **HIGH** |
| **AI Processing** | OpenAI USA or Azure OpenAI (configurable) | Azure OpenAI Canada Central/East | **HIGH** |
| **Logging & Monitoring** | Prometheus/Grafana (local or cloud) | Azure Log Analytics (Canada) | **MEDIUM** |
| **Container Registry** | GitHub Container Registry (global) | Azure Container Registry (Canada) | **MEDIUM** |

**ASSUMPTION**: Azure OpenAI is available in Canadian regions with appropriate data residency commitments. Verify: [Azure OpenAI Service Regions](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/models#model-summary-table-and-region-availability)

### 9.4 Data Sharing

| Recipient | Data Shared | Purpose | Legal Basis |
|-----------|-------------|---------|-------------|
| OpenAI/Azure | Document chunks, queries | AI processing | Contractual |
| Cloud provider | Encrypted storage | Infrastructure | Contractual |
| Monitoring tools | Anonymized metrics | Operations | Legitimate interest |

---

## 10. Appendices

### 10.1 Glossary

| Term | Definition |
|------|------------|
| ATO | Authorization to Operate |
| Entra ID | Microsoft Entra ID (formerly Azure AD) |
| ITSG-33 | IT Security Guidance for Government of Canada |
| NIST 800-53 | Security and Privacy Controls for Information Systems |
| PADI | Privacy and Data Impact Assessment |
| PII | Personally Identifiable Information |
| Protected B | Canadian government security classification |
| RAG | Retrieval-Augmented Generation |

### 10.2 Referenced Documents

| Document | Location | Purpose |
|----------|----------|---------|
| README.md | Repository root | System overview |
| SECURITY.md | Repository root | Security policy |
| SOC2-COMPLIANCE.md | docs/compliance/ | SOC2 control evidence |
| WCAG-STATEMENT.md | docs/compliance/ | Accessibility compliance |
| P0-INCIDENTS.md | docs/runbooks/ | Incident response |
| DISASTER-RECOVERY.md | docs/runbooks/ | DR procedures |

### 10.3 Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1.0 | December 2024 | Security Assessment | Initial draft |

---

**Document Classification**: Protected A  
**Next Review Date**: March 2025  
**Document Owner**: Security Team

---

*This document was prepared based on repository analysis and may contain assumptions that require validation with the development and security teams.*
