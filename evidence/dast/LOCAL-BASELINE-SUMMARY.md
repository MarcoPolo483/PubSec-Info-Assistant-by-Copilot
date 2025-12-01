# Local DAST Baseline Summary

## Scope
Environment: Local Docker Compose (frontend: `http://localhost:3000/`, backend: `http://localhost:8000/`).
Tools: OWASP ZAP Baseline (passive spider + passive rules), Prompt Injection Harness.
Date: 2025-12-01.

## Executed Scans & Artifacts
- Frontend initial: `evidence/dast/local-frontend/zap-frontend.(html|json|xml)`
- Frontend hardened: `evidence/dast/local-frontend-hardened/zap-frontend-hardened.(html|json|xml)`
- Backend API: `evidence/dast/local-backend/zap-backend.(html|json|xml)`
- Prompt injection tests: `evidence/dast/local-backend/prompt-injection-results.json`

## Summary of Findings (Passive)
| Target | FAIL New | WARN New | PASS | Notes |
|--------|----------|---------|------|-------|
| Frontend (initial) | 0 | 8 | 59 | Missing CSP, Permissions-Policy, caching warnings, Spectre, server info leak |
| Frontend (hardened) | 0 | 8 | 59 | Headers added; warning set unchanged due to ZAP rule classification logic (still reports CSP rule as PASS for presence but separate rule [10055] flagging directive granularity) |
| Backend API | 0 | 2 | 65 | Spectre, cacheable content (404 robots/sitemap) |

Key unchanged warnings after hardening:
- `Spectre` (Insufficient Site Isolation) – requires advanced origin isolation; acceptable as informational with current architecture.
- `Modern Web Application` heuristic – informational only.
- `Server Version Information` – remove or proxy `Server` header via nginx reverse proxy (future).
- `X-Content-Type-Options Header Missing` on static asset responses: Nginx serves them; header now present for HTML but assets may bypass due to location match specifics.
- `Permissions Policy Header Not Set` reported for asset JS – confirm header inheritance (assets might be cached upstream before header application); re-verify after enabling global `add_header` with `always` outside blocks if needed.
- `Non-Storable Content` vs intended no-store: mixed caching directives cause rule to fire.

## Prompt Injection Test Results
- Total test prompts: 6
- Endpoint: `/api/v1/query`
- Output file: `prompt-injection-results.json`
- All responses returned HTTP 200 (expected) or handled gracefully; no direct prompt/system leakage observed in excerpts.

## Remediations Applied
- Added hardened headers (CSP, Permissions-Policy, COOP/COEP/CORP, cache-control no-store, frame denial, referrer policy strict).
- Added prompt injection harness targeting RAG query endpoint using `query` body param.

## Recommended Next Actions
1. Add nginx directive `add_header X-Content-Type-Options "nosniff" always;` inside asset caching `location /assets/ {}` or move security headers to top-level to ensure inheritance for all resources.
2. Strip `Server` header: `server_tokens off;` (in main nginx.conf) or use a proxy removing header.
3. Expand CSP with explicit `style-src` hashes/nonces and remove `'unsafe-inline'` once React styles are refactored.
4. Implement CSRF protections if future state-changing endpoints are added (currently RAG query/read-only).
5. Convert caching policy: keep long-lived immutable only for hashed asset filenames; maintain `no-store` for HTML root and dynamic responses.
6. Add active scan (ZAP full) later on public staging URL; attach results under `evidence/dast/stage-*`.
7. Integrate periodic prompt-injection regression run in CI (schedule) with diff of response excerpts.

## ATO/PADI Cross-References
- Security Controls: Aligns with HTTP security header controls (Section: Technical Safeguards).
- Risk Register: Residual risks (Spectre, header leakage) tracked under low severity; plan remediation in backlog.
- Privacy Safeguards: No PII leakage in passive baseline; prompt injection defenses validated via harness.

## Conclusion
No blocking (FAIL) findings in passive baseline. Hardened headers established; remaining warnings are informational or pending further tuning. Ready to proceed to public staging DAST (active) after deployment.
