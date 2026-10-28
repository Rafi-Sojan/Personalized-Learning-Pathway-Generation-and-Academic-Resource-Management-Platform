# Operational Readiness Record

**Document ID:** ILR-OPS-002  
**Version:** 1.0  
**Status:** Development readiness baseline  
**Last reviewed:** 2026-10-28

## 1. Purpose

This record defines the repository-owned controls required before a release is handed to an operator. It separates implementation evidence from activities that require staging infrastructure, licensed data, legal approval, or an independent assessor.

## 2. Implemented release controls

| Control | Evidence | Status |
|---|---|---|
| Schema migration gate | Compose backend runs `alembic upgrade head` before Uvicorn; worker waits for backend readiness | Implemented |
| Document retry policy | Resource processing attempts, retryable state, delayed retry, terminal failure, error detail, and processed timestamp | Implemented |
| Worker lease recovery | Worker reclaims stale `processing` records after `DOCUMENT_WORKER_TIMEOUT_SECONDS` | Implemented |
| Worker visibility | Admin-only `/api/v1/admin/processing` and process-local worker metrics | Implemented |
| Metrics protection | Optional bearer token for `/metrics`; path normalization limits label cardinality | Implemented |
| Release invariant check | `scripts/verify_release.py` and `release-gates.yml` | Implemented |
| Dependency and image checks | Python/npm audits, Trivy scans, and SPDX SBOM workflow | Implemented |
| Recovery verification | Scheduled PostgreSQL backup/restore workflow | Implemented |

## 3. Operator acceptance activities

The following cannot be completed by repository changes alone:

1. Provision staging PostgreSQL, Redis, private object storage, TLS, secrets, and OCR infrastructure.
2. Run a backup/restore drill and record measured recovery point and recovery time.
3. Configure Prometheus scraping for `/metrics` and alerts for readiness failures, 5xx responses, retryable/terminal worker failures, and stale processing jobs.
4. Configure object-storage encryption, lifecycle deletion, backup retention, and cross-region policy.
5. Complete independent penetration testing and privacy/legal approval.
6. Load a licensed or de-identified historical-exam corpus and approve learning-quality thresholds.

## 4. Release evidence package

Each approved release must retain the source revision, workflow run URLs, test reports, image digests, SBOMs, dependency-audit results, migration output, DAST report, backup/restore evidence, SLO review, privacy approval, and rollback decision. Evidence is attached to the release record rather than committed with credentials or generated backups.

## 5. Exit criteria

A release is operationally ready only when all repository gates pass and every operator acceptance activity is either evidenced as complete or explicitly accepted as a documented residual risk by the release owner.
