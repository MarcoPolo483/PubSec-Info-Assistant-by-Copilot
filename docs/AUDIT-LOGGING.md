# Audit Logging Strategy

## Objectives
Provide per-tenant, immutable audit trails for security-relevant events to meet compliance and forensic needs.

## Event Model
- `ingestion.started` / `ingestion.completed` / `ingestion.failed`
- `document.deleted`
- `query.requested` / `query.completed` (include token counts and cost metadata)
- `tenant.stats.viewed`

## Common Fields
- `timestamp` (UTC)
- `tenant_id`
- `request_id`
- `actor` (if authenticated user context available)
- `ip` (from headers)
- `event_type`
- `details` (bounded JSON)

## Storage & Retention
- Primary: Log to stdout as structured JSON; ship via Azure Monitor agent.
- Optional: Dedicated audit log sink (Blob with append-only container, immutability policy 1 year).
- Retention: 1 year for audit logs; 7 years for incident snapshots.

## Implementation Notes
- Use FastAPI middleware & service functions to emit events at critical points.
- Keep PII minimal; avoid content bodies.
- Correlate with OpenTelemetry trace IDs when available.

## Access Controls
- Read access via security team role only; redact sensitive fields in dashboards.

## Compliance Anchors
- AU-2, AU-6 (logging policy and audit review).
