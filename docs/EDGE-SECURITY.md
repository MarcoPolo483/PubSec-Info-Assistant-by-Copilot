# Edge Security (Azure Front Door / WAF)

## Overview
Azure Front Door provides global load balancing, CDN, and WAF to protect and accelerate the application.

## Architecture
```
[Client] → [Front Door (WAF)] → [Application Gateway (optional)] → [AKS Ingress] → [API Pods]
```

## Front Door Configuration
- **Routing**: `pubsec-assistant.example.com` → Backend pool (AKS ingress LB)
- **Caching**: Static assets (frontend) cached at edge; API bypassed
- **SSL/TLS**: Managed certificate via Front Door (auto-renewal)
- **Origin Protection**: AKS ingress only accepts traffic from Front Door (IP whitelist or shared secret header)

## WAF Policy (OWASP Core Ruleset + Custom)
### Managed Rules
- **OWASP 3.2**: Default ruleset (SQL injection, XSS, RCE)
- **Bot Protection**: Block known bad bots; allow Googlebot, verified crawlers

### Custom Rules
1. **Rate Limiting**: 1000 req/5min per IP → 429 response
2. **Geo-blocking** (optional): Allowlist Canada + specific countries if required
3. **Header Validation**: Require `X-Tenant-ID` on API paths; 400 if missing
4. **Prompt Injection Patterns** (experimental):
   - Block payloads containing: `"ignore previous instructions"`, `"system prompt"`, `"reveal secrets"`
   - Use regex with caution; tune false positives
5. **Payload Size Limit**: 10MB max (prevent DoS via large file uploads)

### Exclusions
- `/api/v1/query` body content excluded from XSS rules (LLM input is varied)
- Use precise exclusions to avoid disabling protection

## Logging & Monitoring
- Enable WAF logs → Azure Monitor Log Analytics
- Alert on:
  - High block rate (>10% of traffic)
  - Anomalous patterns (sudden spike from single IP)
- Dashboards: Grafana WAF metrics panel

## Headers Hardening (Front Door Response Rules)
- Strip `Server` header from origin responses
- Add `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- Enforce `Content-Security-Policy` (already set by nginx; validate consistency)

## DDoS Protection
- Azure DDoS Protection Standard enabled on VNet
- Automatic mitigation for volumetric attacks

## Origin Security
- **IP Restriction**: AKS NSG allows only Front Door service tag
- **Shared Secret Header**: Front Door adds `X-Azure-FDID: <secret>` → AKS ingress validates

## Cost Considerations
- Front Door Premium tier required for advanced WAF + Private Link
- Estimate: ~$500/month baseline + bandwidth

## Testing
- Use ZAP active scan against Front Door URL (not direct AKS endpoint)
- Validate WAF blocks malicious payloads without impacting legitimate traffic

## Compliance
- SC-7 (boundary protection), SC-5 (DoS protection), SI-4 (monitoring)
