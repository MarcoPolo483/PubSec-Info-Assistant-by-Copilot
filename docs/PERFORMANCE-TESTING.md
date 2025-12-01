# Performance Testing Plan

## Objectives
Validate system behavior under load to ensure SLO compliance and identify bottlenecks.

## Tooling
- **k6** (preferred): Scripting-friendly, Prometheus export
- **Locust** (alternative): Python-based, distributed load generation

## Test Scenarios

### 1. Query Load Test
- **Target**: `/api/v1/query` (POST)
- **Profile**: Ramp 0→500 VUs over 5 min, sustain 10 min, ramp down 2 min
- **Success Criteria**: p95 latency ≤ 1200 ms, error rate < 0.5%
- **Payload**: Random queries from test corpus (50 samples)

### 2. Ingestion Load Test
- **Target**: `/api/v1/ingest` (POST)
- **Profile**: 50 concurrent uploads, 500 documents total
- **Success Criteria**: p95 ingestion ≤ 5s for ≤2MB PDFs, success rate ≥ 99%
- **Files**: Use synthetic test PDFs (100KB–2MB)

### 3. Mixed Workload
- **Ratio**: 80% queries, 15% ingestion, 5% stats/delete
- **Duration**: 30 min sustained
- **Success Criteria**: All endpoints meet individual SLOs concurrently

### 4. Spike Test
- **Profile**: Baseline 100 VUs → spike to 1000 VUs for 2 min → return to baseline
- **Success Criteria**: No crashes, error rate spike < 2%, recovery < 1 min

### 5. Soak Test (Stability)
- **Profile**: 200 VUs sustained for 4 hours
- **Success Criteria**: Memory stable, no degradation in p95 latency, no error rate creep

## k6 Script Example
```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '5m', target: 500 },
    { duration: '10m', target: 500 },
    { duration: '2m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<1200'],
    http_req_failed: ['rate<0.005'],
  },
};

export default function () {
  let payload = JSON.stringify({ query: 'What is the capital of France?', top_k: 5 });
  let params = { headers: { 'Content-Type': 'application/json', 'X-Tenant-ID': 'test-tenant' } };
  let res = http.post('https://stage.pubsec-assistant.example.com/api/v1/query', payload, params);
  check(res, { 'status is 200': (r) => r.status === 200 });
  sleep(1);
}
```

## Execution
```bash
# Local run (against local stack)
k6 run --vus 50 --duration 5m scripts/perf/query-load.js

# Cloud run (against staging)
k6 cloud run scripts/perf/query-load.js
```

## Metrics Collection
- Export k6 metrics to Prometheus
- Dashboard: Grafana panel with p50/p95/p99, error rate, throughput

## Bottleneck Analysis
- Use OpenTelemetry traces to pinpoint slow spans (vector retrieval vs LLM call)
- Profile Redis cache hit rate; target ≥60%
- Check Qdrant query latency; optimize index if >200ms

## Capacity Planning
- Document max sustainable load: e.g., 500 qps @ p95 < 1.2s
- Scale plan: HPA triggers at 70% CPU or queue depth >100

## Reporting
- Store results in `evidence/performance/{date}-{scenario}.json`
- Include in quarterly performance review

## Compliance
- Supports CA-7 (continuous monitoring) and capacity planning for SC-5 (DoS protection)
