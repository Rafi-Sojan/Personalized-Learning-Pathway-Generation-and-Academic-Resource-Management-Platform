# Requirements Traceability Matrix

**Document ID:** ILR-REQ-001
**Version:** 2.1
**Status:** Implementation-complete development baseline
**Last reviewed:** 2026-10-28

This document maps the attached project specification to the current implementation. Statuses are intentionally explicit so the repository does not imply production readiness where a development implementation remains.

## Verification rule

An item is marked **Implemented** only when the repository contains the behavior and a test, migration, source inspection, or other verification evidence supports it. **Partial** means the primary path exists but production completeness or acceptance evidence is missing. **Planned** means no complete implementation exists.

## Product requirements

| Requirement | Status | Implementation |
|---|---|---|
| Course and concept management | Implemented | SQLAlchemy course/concept models and authenticated course/concept routes |
| Syllabus versions | Implemented | `POST/GET /api/v1/courses/{course_id}/syllabus-versions` |
| Text-based syllabus analysis | Implemented | `POST /api/v1/syllabus/analyze` with bounded input |
| Digital PDF uploads | Implemented | Validated private uploads under `storage/uploads` |
| PDF text extraction | Implemented | PyPDF processing endpoint and processed text output |
| OCR for scanned PDFs | Implemented | Optional Tesseract/PyMuPDF provider is integrated for image-only PDFs, bounded by configured page/text limits, and packaged in `backend/Dockerfile.ocr` |
| Resource-to-topic mapping | Implemented | Resource-to-concept mapping records support proposed, accepted, and rejected review states |
| Concept prerequisites | Implemented | Prerequisite table, API mutation, and cycle detection |
| Concept graph visualization | Implemented | React Flow concept map |
| Deadline-aware roadmap generation | Implemented | Persisted study plans with target date and daily capacity |
| Feasibility checks | Implemented | Scheduler rejects impossible capacity and cyclic graphs |
| Roadmap explanations | Implemented | Items include transparent prioritization explanations |
| Quiz attempts | Implemented | Concept quiz endpoint and attempt submission |
| Progress adaptation | Implemented | Quiz/progress updates modify topic mastery state |
| Account data export and deletion | Implemented | Authenticated export and email-confirmed deletion endpoints plus frontend account screen |
| Roadmap revision history | Implemented | Generated plans create revision snapshots and supersede prior active plans |
| Historical exam ranking | Implemented | Historical question records, numbered-text import, concept matching, frequency/difficulty ranking, C++ scorer contract, and benchmark harness |
| Reproducible learning evaluation | Implemented | JSON benchmark harness reports mapping precision, roadmap completion, and ranking hit rate |

## Platform requirements

| Requirement | Status | Implementation |
|---|---|---|
| Maintained password hashing | Implemented | Argon2 through `pwdlib` |
| Signed short-lived access tokens | Implemented | HS256 JWTs with configurable expiry |
| Token revocation/logout | Implemented | Per-user token version, authenticated logout endpoint, and frontend session control |
| Object ownership checks | Implemented | Course, concept, resource, progress, quiz, and roadmap queries are user-scoped |
| PostgreSQL persistence | Implemented | SQLAlchemy URL configurable; Compose provisions PostgreSQL |
| SQLite no-service development | Implemented | Default local database URL |
| Redis caching/rate limiting | Implemented | Redis-backed rate limiting plus JSON response caching for courses and concepts, with invalidation on writes and process-local fallback |
| Private file storage | Implemented | UUID filenames, non-public storage paths, checksum metadata |
| Docker Compose | Implemented | Frontend, backend, worker, PostgreSQL, Redis, configurable storage, health checks, and corrected development mounts |
| Non-root backend container | Implemented | Backend image runs as `appuser` |
| Alembic migrations | Implemented | Configured environment plus lifecycle, resource mapping, exam, storage metadata, and audit-event migrations |
| CI tests and quality checks | Implemented | Python tests, Ruff, mypy, frontend build/audit, C++ tests |
| Container vulnerability scanning | Implemented | CI audits Python/npm dependencies, builds both images, scans high/critical findings, and publishes SPDX SBOM artifacts |
| Role-based administration | Implemented | Server-side student, instructor, and admin roles; protected admin user-management endpoints; environment-backed initial admin provisioning |
| Object storage | Implemented | Local private storage and optional S3-compatible backend with upload, materialization, processed-output, and deletion support |
| Audit retention | Implemented | Durable audit-event records, account deletion cleanup, configurable retention, and purge utility |
| Runtime smoke verification | Implemented | Compose health/readiness workflow runs the full service stack in CI |
| DAST baseline | Implemented | Scheduled/manual OWASP ZAP workflow and local PowerShell runner produce retained reports |
| Monitoring and alerting contract | Implemented | Health/readiness endpoints, Prometheus-compatible metrics, SLO document, and alert conditions |
| Accessibility/performance gates | Implemented | Playwright accessibility checks, Lighthouse workflow, and frontend JavaScript bundle budget |
| Backup and restore verification | Implemented | PostgreSQL backup/restore scripts and scheduled CI drill restoring into a fresh database |
| Durable document-worker retry and failure handling | Implemented | Processing attempts, delayed retryable state, terminal failed state, bounded error detail, and admin queue summary |
| Migration gate before container startup | Implemented | Compose backend applies Alembic migrations before serving and worker waits for backend readiness |
| Protected operational metrics | Implemented | Optional bearer-token protection and normalized path labels on `/metrics` |
| Release invariant verification | Implemented | `scripts/verify_release.py` validates controlled artifacts, configuration entries, migration gate, and pinned actions |

## Known development limitations

- The seeded demo account is for local development only.
- Production rejects the development secret and Compose requires `SECRET_KEY` and `POSTGRES_PASSWORD` from `.env`.
- S3-compatible storage, Tesseract OCR, external penetration testing, and production alerting still require operator infrastructure and credentials; implementation hooks and CI procedures are present.
- Historical exam ranking depends on the quality and concept coverage of imported question papers; the repository provides deterministic ingestion and ranking, not a licensed corpus.
- Docker runtime validation is reproducible in `.github/workflows/compose-smoke.yml`; local Docker execution depends on the developer machine.
- External penetration testing, production SLO approval, and privacy/legal approval remain operator or release-owner acceptance activities.
- `npm audit` validates repository dependencies, not the globally installed npm CLI or Node runtime.
- Release-gate execution still requires the GitHub runner, container runtime, and operator-owned staging evidence; the local repository check does not replace those acceptance activities.
