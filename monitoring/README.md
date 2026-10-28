# Monitoring configuration

This directory contains the repository-owned Prometheus scrape and alert baseline. It is a configuration artifact, not a complete production monitoring deployment.

## Use

Mount `prometheus.yml` and `alert-rules.yml` into Prometheus, keep the API and Prometheus on a private network, and configure bearer authentication through the deployment secret manager when `METRICS_AUTH_TOKEN` is enabled. Do not commit a token or embed a production secret in this directory.

The API metrics cover request/status counters and in-process worker outcomes. Durable queue state is available to authorized operators at `/api/v1/admin/processing`; a production deployment should add a scheduled authenticated probe or exporter for retryable, failed, and stale resources.

## Alert ownership

The release owner must assign notification destinations and escalation times for API availability, elevated 5xx responses, terminal document failures, and lease expirations. Alert rules do not define an on-call rotation or an incident SLA by themselves.
