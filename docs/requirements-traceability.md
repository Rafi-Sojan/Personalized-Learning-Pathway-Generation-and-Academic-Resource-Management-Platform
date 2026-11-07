# Requirements Traceability Matrix

**Document ID:** ILR-REQ-001
**Version:** 2.9
**Status:** Implementation-complete development baseline
**Last reviewed:** 2026-11-07

This document maps the attached project specification to the current implementation. Statuses are intentionally explicit so the repository does not imply production readiness where a development implementation remains.

## Verification rule

An item is marked **Implemented** only when the repository contains the behavior and a test, migration, source inspection, or other verification evidence supports it. **Partial** means the primary path exists but production completeness or acceptance evidence is missing. **Planned** means no complete implementation exists.

## Product requirements

| Requirement | Status | Implementation |
|---|---|---|
| Course and concept management | Implemented | Authenticated API and UI create private subjects under a validated branch/scheme/semester, distinguish personal and verified-catalog origins, expose syllabus state, and manage owned concepts |
| Learner branch and syllabus onboarding | Implemented | **My subjects** provides controlled branch/scheme/semester selection, subject identity, optional immediate PDF attachment, failure recovery, and direct syllabus-workflow navigation |
| Syllabus versions | Implemented | `POST/GET /api/v1/courses/{course_id}/syllabus-versions` |
| Text-based syllabus analysis | Implemented | `POST /api/v1/syllabus/analyze` with bounded input |
| Stored syllabus PDF copies | Implemented | Course-owned `/syllabus/sources/upload`, private storage, checksum, and source listing |
| Syllabus-derived concepts | Implemented; content validation open | Course-scoped unit parsing creates review-gated root/child concepts with page evidence, excludes non-teaching tails, and uses unit/parent-aware identities so repeated labels do not collapse; candidate quality still requires RVCE reviewer evaluation |
| PDF text extraction | Implemented | Bounded PyPDF/OCR processing records per-page markers in private processed text |
| OCR for scanned PDFs | Implemented | Optional Tesseract/PyMuPDF provider is integrated for image-only PDFs, bounded by configured page/text limits, and packaged in `backend/Dockerfile.ocr` |
| Manual resource catalog and mapping UI | Out of scope | Removed from learner navigation; legacy backend mapping contracts remain for compatibility |
| AI-generated website links for concepts | Deferred | Provider/API key, link grounding, validation, and persistence are intentionally postponed |
| Concept prerequisites | Implemented | Prerequisite table, API mutation, and cycle detection |
| Concept graph visualization | Implemented | React Flow map uses stable unit columns, parent-child edges, accepted prerequisite edges, source-page labels, and pending/verified styling; rejected current topics are omitted |
| Syllabus-driven deadline-aware roadmap generation | Implemented | Persisted plans require a processed syllabus copy and map; full concept estimates are split across daily-capacity segments rather than truncated |
| Feasibility checks | Implemented | Scheduler rejects impossible full-effort capacity and cyclic graphs; previews label a partial final concept when capacity expires |
| Roadmap explanations | Implemented | `rvce-evidence-priority-v2` records dependency-safe explanations for reviewed historical evidence, mastery gap, downstream unlock value, difficulty, and algorithm version |
| Quiz attempts | Backend retained; learner UI removed | Concept quiz endpoint and attempt submission remain available for compatibility |
| Progress adaptation and study activity | Backend retained; learner UI removed | Quiz/progress APIs and persisted records remain, but have no learner navigation or screens |
| Live learner dashboard | Implemented | Current date/greeting, subject and mapped-topic counts, roadmap focus, empty states, and navigation actions use live API data |
| Account data export and deletion | Implemented | Export covers source provenance, historical questions, complete plan history, mappings and audits; foreign-key-safe deletion removes owned rows/files and anonymizes surviving review references |
| Roadmap revision history | Implemented | Generated plans create revision snapshots and supersede prior active plans |
| Past-paper PDF parsing | Implemented | Bounded page-aware extraction excludes scheme/solution ranges, recognizes RVCE numbering and printed CIE/SEE/part structure, preserves source coordinates, validates explicit course codes, and supports optional OCR |
| Subject/topic question frequency | Implemented; academic validation open | Only verified main rows mapped to verified current-syllabus concepts create topic counts; mapped/unmapped main and quiz totals, year counts, repeats, evidence references, and archive filters are reported separately |
| Historical exam ranking | Implemented | Historical question records, text/PDF import, corpus-aware phrase/acronym/OCR/context matching with conservative abstention, durable candidate evidence, manual correction, review-gated frequency, C++ scorer contract, and benchmark harness |
| Reproducible learning evaluation | Implemented | JSON harness computes matcher decisions from raw prompts and reports precision, recall/F1, accuracy, coverage, abstention/status accuracy, MRR, roadmap completion, and ranking metrics |

## Platform requirements

| Requirement | Status | Implementation |
|---|---|---|
| Maintained password hashing | Implemented | Argon2 through `pwdlib` |
| Signed short-lived access tokens | Implemented | HS256 JWTs with configurable expiry |
| Token revocation/logout | Implemented | Per-user token version, authenticated logout endpoint, and frontend session control |
| Object ownership checks | Implemented | Course, concept, resource, progress, quiz, and roadmap queries are user-scoped |
| PostgreSQL persistence | Implemented | SQLAlchemy URL configurable; Compose provisions PostgreSQL |
| SQLite no-service development | Implemented | Default local database URL with connection-level foreign-key enforcement and isolated temporary test databases |
| Redis caching/rate limiting | Implemented | Redis-backed rate limiting plus JSON response caching for courses and concepts, with invalidation on writes and process-local fallback |
| Private file storage | Implemented | UUID filenames, non-public storage paths, checksum metadata, account cleanup, and compensating deletion for failed/duplicate paper imports |
| Docker Compose | Implemented | Frontend, backend, worker, PostgreSQL, Redis, configurable storage, health checks, and corrected development mounts |
| Non-root backend container | Implemented | Backend image runs as `appuser` |
| Alembic migrations | Implemented | Configured environment plus lifecycle, resource mapping, exam, storage metadata, audit-event, ingestion provenance, course academic-scope, and matcher-evidence migrations |
| CI tests and quality checks | Implemented | Release workflow includes Python API tests, Ruff, mypy, source and invariant validation, learning benchmark gates, frontend build/audit/E2E, native C++ tests, and Compose runtime/restore checks |
| Container vulnerability scanning | Implemented | CI audits Python/npm dependencies, builds both images, scans high/critical findings, and publishes SPDX SBOM artifacts |
| Role-based administration | Implemented | Server-side student, instructor, and admin roles; protected admin user-management endpoints; environment-backed initial admin provisioning |
| Object storage | Implemented | Local private storage and optional S3-compatible backend with upload, materialization, processed-output, and deletion support |
| Audit retention | Implemented | Durable audit-event records, complete account export/deletion cleanup, configurable retention, and purge utility |
| Runtime smoke verification | Implemented | Compose health/readiness workflow runs the full service stack in CI |
| DAST baseline | Implemented | Scheduled/manual OWASP ZAP workflow and local PowerShell runner produce retained reports |
| Monitoring and alerting contract | Implemented | Health/readiness endpoints, Prometheus-compatible metrics, SLO document, and alert conditions |
| Accessibility/performance gates | Implemented | Playwright accessibility checks, Lighthouse workflow, and frontend JavaScript bundle budget |
| Backup and restore verification | Implemented | PostgreSQL backup/restore scripts and scheduled CI drill restoring into a fresh database |
| Durable document-worker retry and failure handling | Implemented | Processing attempts, delayed retryable state, terminal failed state, bounded error detail, and admin queue summary |
| Migration gate before container startup | Implemented | Compose backend applies Alembic migrations before serving and worker waits for backend readiness |
| Protected operational metrics | Implemented | Optional bearer-token protection and normalized path labels on `/metrics` |
| Release invariant verification | Implemented | `scripts/verify_release.py` validates controlled artifacts, configuration entries, migration gate, and pinned actions |
| Prometheus scrape and alert configuration | Implemented | Version-controlled scrape baseline and alert rules under `monitoring/` |
| Expanded learning-quality evaluation | Implemented | Release gates enforce computed matcher precision/F1/abstention behavior plus mapping F1 and ranking NDCG; the source-controlled cases are regression fixtures, not academic acceptance |
| Frontend manual acceptance record | Partial | Automated accessibility/performance gates and formal manual-review checklist are present; operator review remains required |
| External security acceptance | Partial | DAST and repository controls are implemented; independent penetration testing remains required |
| Production privacy/legal approval | Partial | PIA and formal approval requirements are documented; data-owner/legal approval remains required |
| Licensed evaluation corpus | Partial | Deterministic benchmark and threshold gate exist; licensed/de-identified production-quality corpus remains required |
| Staging load/performance evidence | Partial | Dependency-free load tool and formal evidence procedure exist; deployed staging measurements remain required |
| RVCE program and scheme catalog | Implemented | Source-provenance manifest, normalized program aliases, validator, and `/catalog/rvce` endpoint |
| RVCE subject/course syllabus rows | Partial | Source-verified extraction and batch import, provenance retention, admin review UI, branch mapping at approval, and API flow tests are implemented; 207 candidates are awaiting academic review and two conflicting rows are quarantined |
| Formal implementation and source-comment records | Implemented | Controlled implementation record, repository-wide code-comment standard, and release-gate enforcement of Python function docstrings across backend, ML, scripts, and tests |
| Consolidated project completion register | Implemented | `docs/remaining-targets.md` identifies each open target, accountable role, external dependency, and objective closure evidence |

## Known development limitations

- Fresh local startup creates no demo account or generic course fixtures.
- Production rejects the development secret and Compose requires `SECRET_KEY` and `POSTGRES_PASSWORD` from `.env`.
- S3-compatible storage, Tesseract OCR, external penetration testing, and production alerting still require operator infrastructure and credentials; implementation hooks and CI procedures are present.
- Historical exam ranking depends on the quality and concept coverage of imported question papers; the repository provides deterministic ingestion and ranking, not a licensed corpus.
- Hybrid matcher scores are deterministic relevance values, not calibrated probabilities. The eight source-controlled cases prevent engineering regressions but cannot establish RVCE academic accuracy; EVAL-01 remains open.
- Existing local databases created before the stricter course-scoping and review rules can retain legacy concepts or question mappings. Regenerate the map from the correctly coded syllabus and review records before treating local counts as current; no automatic destructive cleanup is performed.
- Learner-created branch-scoped subjects are private workspaces, not institutional catalog approval. Official rows remain partial until RVCE academic review evidence closes the catalog targets.
- Docker runtime validation is reproducible in `.github/workflows/compose-smoke.yml`; local Docker execution depends on the developer machine.
- External penetration testing, production SLO approval, and privacy/legal approval remain operator or release-owner acceptance activities.
- `npm audit` validates repository dependencies, not the globally installed npm CLI or Node runtime.
- Release-gate execution still requires the GitHub runner, container runtime, and operator-owned staging evidence; the local repository check does not replace those acceptance activities.
- The Release gates workflow is defined and locally checked; production acceptance still requires a successful candidate run and the external sign-offs listed in `docs/remaining-targets.md`.
- Monitoring rule files define alert behavior but do not provision a notification destination or on-call rotation; those remain deployment-owned configuration.
