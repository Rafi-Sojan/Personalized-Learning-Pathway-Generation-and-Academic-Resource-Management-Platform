# Requirements Traceability Matrix

**Document ID:** ILR-REQ-001
**Version:** 1.0
**Status:** Development baseline
**Last reviewed:** 2026-10-27

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
| Historical exam ranking | Partial | C++ scorer now has a backend-consumable stdin contract; real question-paper ingestion and historical benchmark data are pending |
| Reproducible learning evaluation | Implemented | JSON benchmark harness reports mapping precision, roadmap completion, and ranking hit rate |

## Platform requirements

| Requirement | Status | Implementation |
|---|---|---|
| Maintained password hashing | Implemented | Argon2 through `pwdlib` |
| Signed short-lived access tokens | Implemented | HS256 JWTs with configurable expiry |
| Object ownership checks | Implemented | Course, concept, resource, progress, quiz, and roadmap queries are user-scoped |
| PostgreSQL persistence | Implemented | SQLAlchemy URL configurable; Compose provisions PostgreSQL |
| SQLite no-service development | Implemented | Default local database URL |
| Redis caching/rate limiting | Partial | Redis-backed rate limiting with process-local fallback; broad result caching remains limited |
| Private file storage | Implemented | UUID filenames, non-public storage paths, checksum metadata |
| Docker Compose | Implemented | Frontend, backend, PostgreSQL, and Redis services |
| Non-root backend container | Implemented | Backend image runs as `appuser` |
| Alembic migrations | Implemented | Configured environment and initial migration |
| CI tests and quality checks | Implemented | Python tests, Ruff, mypy, frontend build/audit, C++ tests |
| Container vulnerability scanning | Implemented | CI audits Python/npm dependencies, builds both images, scans high/critical findings, and publishes SPDX SBOM artifacts |

## Known development limitations

- The seeded demo account is for local development only.
- Production rejects the development secret and Compose requires `SECRET_KEY` and `POSTGRES_PASSWORD` from `.env`.
- Object storage and long-term revision audit retention are not production-complete; queued document processing, OCR, and resource-mapping review are implemented.
- Frontend routes are lazy-loaded; the largest remaining chunk is the concept/progress visualization dependency group.
- Docker runtime validation was not performed on the development machine because Docker was unavailable.
- `npm audit` validates repository dependencies, not the globally installed npm CLI or Node runtime.
