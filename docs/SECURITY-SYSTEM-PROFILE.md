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

| Role | Description | Permissions |
|------|-------------|-------------|
| **Admin** | System administrator | Full access, tenant management, user management |
| **Operator** | Operations team | Service monitoring, incident response, no data access |
| **Analyst** | Document analyst | Query, ingest documents, view results |
| **Viewer** | Read-only user | Query only, no ingestion |
| **Auditor** | Compliance/audit | Read-only access to logs and metrics |

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
