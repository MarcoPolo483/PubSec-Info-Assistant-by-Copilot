# Secrets Management Plan (Azure Key Vault)

## Goals
Eliminate static secrets in code/CI; use federated identity and runtime retrieval.

## Approach
- Use GitHub OIDC to issue short-lived Azure tokens for deploy jobs; no PATs.
- App workloads authenticate via Managed Identity to Key Vault.
- Secrets never stored in `.env` in production; development-only `.env` allowed locally.

## Key Vault Layout
- Vault: `kv-pubsec-info-assistant-prod` (RBAC enabled)
- Secrets (examples):
  - `OpenAI__ApiKey`
  - `OpenAI__Endpoint`
  - `Redis__ConnectionString`
  - `Qdrant__ApiKey` (if applicable)
  - `App__CorsOrigins`
  - `App__DefaultTenant`

## Access
- `mi-app-pubsec` (User-Assigned Managed Identity) granted `get` on secrets.
- GitHub deploy identity granted `set`, `get` for CI config publishing.

## Retrieval Pattern (Backend)
- At startup, resolve env values with fallback to Key Vault via SDK or sidecar.
- Cache secrets in memory; do not persist on disk.

## Rotation Policy
- Quarterly rotation for API keys.
- Emergency rotation procedure documented in Incident Runbook.

## Auditing
- Enable Key Vault logging to Azure Monitor; alert on secret access anomalies.

## CI/CD Integration
- `azure/login` uses OIDC; `azure/cli` fetches secrets when needed.
- No long-lived service principals.

## Developer Workflow
- Local dev: `.env` with dummy values.
- Prod: environment set via Kubernetes secrets populated from Key Vault CSI driver.

## Compliance Anchors
- IA-5, SC-12: Credential management and key storage.
