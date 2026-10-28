# Service-Level Objectives and Observability

**Document ID:** ILR-SLO-001  
**Version:** 1.0  
**Status:** Development baseline  
**Last reviewed:** 2026-10-28

## 1. Initial objectives

| Service indicator | Target | Measurement |
|---|---:|---|
| API availability | 99.5% monthly in production | `/health/ready` success ratio |
| Readiness latency | 95% under 500 ms | Synthetic probe and reverse-proxy metrics |
| Authenticated API errors | Below 1% excluding 4xx validation/auth responses | Prometheus status counters and logs |
| Queued document completion | 99% completed or explicitly failed within 10 minutes | Resource processing status and worker logs |
| Backup recovery point | Maximum 24 hours | Scheduled PostgreSQL backup evidence |
| Restore recovery objective | Maximum 4 hours | Quarterly restore drill |

## 2. Observability contract

The API exposes `/health` for liveness, `/health/ready` for database/Redis readiness, and `/metrics` for Prometheus-compatible request and status counters. Metrics should be kept on a private network and scraped by the deployment monitor. Request logs include request IDs but exclude credentials, tokens, and document contents.

## 3. Alert conditions

Operators should alert on readiness failures, sustained 5xx responses, queued documents older than the processing objective, backup failures, restore-drill failures, high/critical image findings, DAST regressions, and repeated rate-limit or authentication anomalies.

## 4. Review and escalation

SLOs are a starting operational contract, not a guarantee. The release owner must review targets after staging measurements, assign on-call ownership, document maintenance windows, and record incidents against the affected revision.
