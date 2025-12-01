# API Versioning Strategy

## Goals
Enable backward-compatible evolution and graceful deprecation.

## Versioning Scheme
- **Semantic Versioning** in URL: `/api/v{major}/*`
- Current: `v1`
- Future: `v2` introduces breaking changes; `v1` maintained in parallel for deprecation window

## Version Lifecycle
1. **Active**: Full support, receives new features
2. **Deprecated**: Maintenance only, sunset date announced
3. **Sunset**: Removed from production

## Deprecation Policy
- Minimum 6 months notice before sunset
- Announce via:
  - API response header: `Sunset: Sat, 01 Jun 2026 00:00:00 GMT`
  - Documentation banner
  - Direct tenant notification (email)

## Breaking vs Non-Breaking Changes
| Change Type | Requires New Version? | Example |
|-------------|-----------------------|---------|
| Add optional field | No | New query parameter with default |
| Add new endpoint | No | `/api/v1/admin/purge` |
| Change response schema | **Yes** | Remove field, change type |
| Rename endpoint | **Yes** | `/ingest` → `/upload` |
| Change auth mechanism | **Yes** | API key → OAuth2 |

## Backward Compatibility Rules
- Never remove fields from response without major version bump
- Add fields with defaults to avoid breaking clients
- Use feature flags for gradual rollout within same version

## Version Header
- Optional client request: `Accept-Version: v1` (if not in URL)
- Response: `API-Version: v1`

## Migration Path (v1 → v2 example)
1. Launch v2 in parallel (dual endpoints active)
2. Provide migration guide with code samples
3. Deprecate v1 (6-month window)
4. Monitor usage metrics; reach out to high-traffic tenants
5. Sunset v1 after window

## Documentation
- Maintain separate OpenAPI specs per version
- Version selector in docs UI

## Testing
- Integration tests for each active version
- Canary deploy v2 to subset of tenants before GA

## Compliance
- SA-15 (supply chain continuity)
- CM-3 (configuration change control)
