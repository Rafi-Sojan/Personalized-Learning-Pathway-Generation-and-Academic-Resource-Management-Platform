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
| OCR for scanned PDFs | Planned | Extension point; Tesseract/OpenCV are not installed or wired |
| Resource-to-topic mapping | Partial | Deterministic ML utilities exist; persistent mapping review workflow is pending |
| Concept prerequisites | Implemented | Prerequisite table, API mutation, and cycle detection |
| Concept graph visualization | Implemented | React Flow concept map |
| Deadline-aware roadmap generation | Implemented | Persisted study plans with target date and daily capacity |
| Feasibility checks | Implemented | Scheduler rejects impossible capacity and cyclic graphs |
| Roadmap explanations | Implemented | Items include transparent prioritization explanations |
| Quiz attempts | Implemented | Concept quiz endpoint and attempt submission |
| Progress adaptation | Implemented | Quiz/progress updates modify topic mastery state |
| Roadmap revision history | Planned | Study plans are persisted; revision audit records are not yet modeled |
| Historical exam ranking | Partial | C++ scorer and ranking endpoint are present; real question-paper ingestion is pending |

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
| Container vulnerability scanning | Planned | CI does not yet publish or scan built images |

## Known development limitations

- The seeded demo account is for local development only.
- The default secret is rejected in production mode, but Compose still contains a development secret fallback.
- OCR, asynchronous document workers, object storage, revision audit records, and complete resource-mapping review are not production-complete.
- The frontend bundle currently emits a chunk-size warning because React Flow and Recharts are loaded in the main bundle.
- Docker runtime validation was not performed on the development machine because Docker was unavailable.
- `npm audit` validates repository dependencies, not the globally installed npm CLI or Node runtime.
