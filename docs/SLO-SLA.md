# SLO / SLA Definitions

## Purpose
Establish objective service performance & reliability targets with measurable indicators and error budgets to guide operations and release decisions.

## Services & Indicators
| Service | Indicator | Measurement Source | Target (SLO) | SLA (External) | Notes |
|---------|-----------|--------------------|--------------|----------------|-------|
| API (Query) | p95 Latency | Prometheus histogram (`request_latency_seconds`) | ≤ 1200 ms | 99.5% of requests ≤ 1500 ms | Includes vector retrieval + LLM call (cache warmed). |
| API (Ingestion) | p95 Ingestion Latency | Prometheus (`ingestion_duration_seconds`) | ≤ 5 s (<=2MB doc) | 99% ≤ 7 s | Larger PDFs excluded from SLO; separate batch metric. |
| Availability | Uptime % (rolling 30d) | Synthetic + Prometheus | 99.9% | 99.5% | Single-region initial; multi-region improves target. |
| Error Rate | 5xx % of total requests | Prometheus counter ratio | < 0.5% | < 1% | Excludes client 4xx errors. |
| Vector Consistency | Qdrant write success ratio | Qdrant metrics/logs | ≥ 99.99% | 99.9% | Monitors ingestion reliability. |
| Cache Hit Rate | Redis hit/miss ratio | Redis INFO metrics | ≥ 60% | N/A | Used for cost optimization; not formal SLA. |
| Cost per Query | Derived (LLM tokens / query) | Custom header aggregation | ≤ $0.01 avg | N/A | Used for scaling & budgeting. |

## Error Budgets
- Availability error budget (99.9% SLO): 0.1% downtime ≈ 43m 12s per 30 days.
- Latency budget breach triggers performance optimization sprint.
- If error rate SLO violated for 2 consecutive days: freeze feature deploys until mitigated.

## Alert Thresholds
| Indicator | Warning | Critical |
|-----------|---------|----------|
| p95 Query Latency | > 1400 ms (5m) | > 1700 ms (5m) |
| Error Rate | > 0.4% (15m) | > 0.8% (5m) |
| Availability (synthetic) | < 99.9% (daily) | < 99.5% (daily) |
| Qdrant Write Success | < 99.995% (30m) | < 99.98% (30m) |

## Observability Implementation
- Metrics exported via `/metrics` on API pods (histograms: latency, counters: requests_total, errors_total).
- Tracing spans: `ingestion.process`, `query.retrieve_vectors`, `query.llm_request` with attributes (tenant_id, vector_count).
- Synthetic probe (GitHub Action / Azure Monitor availability test) hitting `/health` and `/ready` every 60s.

## Reporting
- Daily SLO report pipeline aggregates last 30d metrics and emits JSON → `evidence/monitoring/slo-report.json`.
- Monthly executive summary (availability, latency p95, error rate, cost per 1K queries).

## SLA Exceptions
- Scheduled maintenance windows (announced ≥72h in advance) excluded from uptime calculation.
- Incidents caused by upstream providers (Azure OpenAI outage) flagged separately; counted if >30m continuous impact.

## Future Enhancements
- Break down latency by phase (vector lookup vs LLM completion) for targeted improvements.
- Adaptive caching strategy raising hit rate target to 75%.
- Multi-region failover reduces downtime target to 99.95% availability.

## Governance
SLOs reviewed quarterly; SLA updated annually or upon major architecture revision. Changes require approval from platform owner + security architect.
