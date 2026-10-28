# Deployment and Release Specification

**Document ID:** ILR-REL-001
**Version:** 2.1
**Status:** Implementation-complete development baseline
**Last reviewed:** 2026-10-28

## 1. Supported deployment modes

| Mode | Intended use | Dependencies |
|---|---|---|
| Local no-service | Development and unit testing | Python, Node.js, SQLite |
| Docker Compose | Integrated development or controlled staging | Docker, PostgreSQL, Redis |
| Production | Requires operational approval | Managed database, secrets, TLS, observability, backup/recovery, object storage, and external security acceptance |

## 2. Release inputs

A release candidate shall identify the source revision, Python and Node versions, dependency lockfiles, container base image digests or versions, database migration state, and configuration template. Runtime secrets must be supplied outside the repository.

The standard backend image intentionally excludes the optional OCR stack. OCR releases must use `backend/Dockerfile.ocr`, scan both images, verify the installed Tesseract/PyMuPDF versions separately, and apply the same migration startup gate before serving.

## 3. Release gates

The following checks are required before a release is approved:

1. Backend tests, lint, type checks, and dependency audit pass.
2. Frontend lockfile installation and production build pass.
3. C++ tests pass using the supported compiler/toolchain.
4. Database migrations apply cleanly to an empty database and are reversible or have a documented forward-only recovery plan; the Compose smoke workflow verifies service startup.
5. API authentication, ownership, upload validation, and rate limiting are tested.
6. Container images are scanned and an SBOM is produced by the security workflow.
7. Secrets, demo accounts, default credentials, and development fallbacks are removed or overridden.
8. A rollback revision, database recovery plan, DAST report, and audit-retention policy are recorded.
9. `python scripts/verify_release.py` passes, including controlled-document, configuration, migration-gate, and GitHub Action pin checks.

## 6. Automated acceptance workflows

- `backend-tests.yml` runs backend/ML quality checks and PostgreSQL/Redis integration checks.
- `frontend-checks.yml` runs the locked frontend build, browser smoke tests, and dependency audit.
- `frontend-a11y-performance.yml` runs Playwright accessibility checks, the bundle budget, and Lighthouse accessibility/performance thresholds.
- `security-scan.yml` audits dependencies, scans images, and publishes SBOMs.
- `compose-smoke.yml` starts the integrated stack and verifies liveness/readiness.
- `dast.yml` runs the scheduled/manual OWASP ZAP baseline scan and retains the report artifact.
- `backup-restore.yml` performs a scheduled/manual PostgreSQL logical backup and restores it into a fresh database.
- `release-gates.yml` verifies repository release invariants and builds the locked frontend for tagged/manual release candidates.

## 4. Deployment procedure

1. Build immutable images from the approved revision.
2. Scan images and dependencies.
3. Provision secrets and private network connectivity.
4. Apply database migrations using a controlled deployment identity. Compose performs this as a startup gate for the integrated stack; production orchestration should use an equivalent one-shot migration job.
5. Deploy backend, worker components if enabled, Redis, and frontend.
6. Run health checks, image verification, and a smoke test against the deployed API.
7. Confirm logs, metrics, rate limiting, and backup jobs.
8. Record the release revision and verification evidence.

## 5. Rollback

Application rollback must use the previous approved image. Database rollback must follow the migration-specific recovery plan; destructive schema reversions must not be attempted without a verified backup. If a security issue is involved, revoke affected secrets and tokens as part of the rollback response.
