# Intelligent Learning Roadmap

**Project document:** ILR-DOC-001
**Release status:** Development baseline verified locally; release acceptance open
**Documentation version:** 3.0
**Last reviewed:** 2026-11-07

Intelligent Learning Roadmap is an RVCE-focused platform that turns stored syllabus copies into source-aware concept maps and study roadmaps, and identifies topic frequency in historical question papers. It combines a web dashboard, a typed API, explainable learning utilities, and a native scoring engine.

## 1. Project status

This repository provides an implementation-complete development baseline for an RVCE-focused learning platform with signed authentication, Argon2 password hashing, role-gated administration, ownership-aware SQLAlchemy persistence, secure asynchronous document processing, optional OCR, object-storage abstraction, syllabus-derived maps and roadmaps, past-paper parsing and topic frequency, Redis-backed caching/throttling, privacy workflows, and a native scoring boundary. Learners can create private subject workspaces under a validated RVCE branch, scheme, and semester and attach a syllabus during setup. These personal records remain explicitly distinct from source-backed, academically verified RVCE catalog entries. Learner academic workflows center on syllabus PDFs and question papers; manual learning-resource catalog management is not in scope. AI-generated concept links are deferred. The RVCE program/scheme catalog is source-provenance validated. Eight supplied PDFs have been inventoried; extracted course candidates remain pending academic verification, conflict resolution, and first-year branch mapping. SQLite is used for a no-service local run; Docker Compose provisions PostgreSQL, Redis, a worker, private storage, and the frontend/backend services.

## 2. Capabilities

- RVCE subject selection and review-gated syllabus concept maps with unit/page provenance and parent-child topic hierarchy.
- Guided personal-subject onboarding with controlled RVCE branch/scheme/semester selection, optional immediate syllabus attachment, and visible personal-versus-verified provenance.
- Syllabus topic extraction through a FastAPI endpoint.
- Dated roadmap generation that splits full concept estimates across bounded daily study segments.
- Stored syllabus PDFs processed into course concepts and roadmap inputs.
- Page-aware past-paper parsing that excludes answer schemes and reports verified topic frequency by subject and year, including repeated prompts.
- Versioned syllabus extraction with source document/page provenance, confidence, review state, and separate outcome/lab/assessment-policy facts.
- Reviewable historical-paper questions with explicit assessment metadata, source-page references, marks where printed, manual concept correction, and verified-only frequency evidence.
- Explicit syllabus prerequisite suggestions that require approval and cycle validation before they affect roadmap ordering.
- Course-specific roadmap previews with prerequisite order, mastery gap, verified historical recurrence/recency/marks, and question evidence references.
- Section-aware paper parsing preserves printed parts and structural CIE/SEE headers; Part A quiz classification is applied only when the source/uploader establishes it, while verified, current-syllabus-mapped main questions drive historical frequency.
- Quiz and progress backend contracts remain available; quizzes and progress are not exposed in the current learner UI.
- Explainable hybrid concept matching with corpus rarity, phrases, derived acronyms, OCR-tolerant similarity, hierarchy context, conservative abstention, and review-visible alternatives.
- Versioned dependency-safe roadmap prioritization using reviewed question evidence, mastery gap, downstream unlock value, and difficulty.
- C++ scoring library and command-line demonstration for concept prioritization.
- Historical exam question import, concept association, and frequency/difficulty ranking.
- S3-compatible private storage option with durable audit-event retention and purge tooling.
- Complete account export and foreign-key-safe deletion for syllabus, question-paper, roadmap, progress, review, audit, and private-file records.
- Student, instructor, and administrator roles with protected user-management operations.
- RVCE program and scheme catalog metadata, PDF checksum/page provenance, batch import, administrator academic review, and verified semester enrollment.

## 3. Repository structure

| Directory | Responsibility |
| --- | --- |
| `frontend/` | React, Vite, and TypeScript user interface |
| `backend/` | FastAPI application, schemas, services, and API routes |
| `ml/` | Explainable preprocessing, mapping, graph, scheduling, and metrics |
| `scoring-engine/` | C++ scoring library, CLI, and native tests |
| `database/` | Initial relational schema, empty seed placeholder, and ER documentation |
| `tests/` | Cross-module integration tests |
| `docs/` | Architecture, API, security, database, and evaluation notes |
| `monitoring/` | Prometheus scrape configuration and alert rules |

## 4. Prerequisites

- Python 3.11 or newer
- Node.js 24.22.1 or newer and npm 11.21.1 or newer
- A C++17 compiler for the scoring engine
- CMake 3.20 or newer for the native build

## 5. Local development

Create and activate a virtual environment, then install the Python dependencies:

```bash
python -m venv .venv
# Windows PowerShell
.venv\\Scripts\\Activate.ps1
# macOS/Linux
source .venv/bin/activate
python -m pip install -r backend/requirements.txt -r ml/requirements.txt
# Optional OCR and S3-compatible storage dependencies:
python -m pip install -r backend/requirements-ocr.txt -r backend/requirements-storage.txt
```

Start the API from the repository root:

```bash
alembic -c backend/alembic.ini upgrade head
# PowerShell: $env:PYTHONPATH = "$PWD;$PWD\backend"
# macOS/Linux: export PYTHONPATH=".:./backend"
uvicorn app.main:app --reload --app-dir backend
```

In a second terminal, start the frontend:

```bash
cd frontend
npm ci
npm run dev
```

The dashboard is available at `http://localhost:5173`. Interactive API documentation is available at `http://localhost:8000/docs`.

After signing in, open **My subjects** to create a private subject workspace. Select the RVCE branch, semester, and supported scheme, enter the subject code and title, and optionally attach the syllabus PDF in the same form. Open **RVCE syllabus** only when enrolling academically verified catalog rows; a personal workspace does not create or approve an institutional catalog record.

For the full local stack, including PostgreSQL, Redis, private upload storage, the API worker, and the containerized frontend/backend, copy `.env.example` to `.env`, replace the development placeholders, and run:

```bash
copy .env.example .env  # Windows
# cp .env.example .env  # macOS/Linux
docker compose up --build
```

Register a learner account from the login screen or configure `INITIAL_ADMIN_EMAIL` and `INITIAL_ADMIN_PASSWORD` for local administration. Local startup no longer creates generic sample courses or concepts. Replace the Compose `SECRET_KEY` before any shared deployment.

## 6. Testing and builds

Run the Python test suite:

```bash
python -m pytest backend/tests ml/tests tests
```

Build the frontend:

```bash
cd frontend
npm run build
```

Build and test the C++ engine:

```bash
cmake -S scoring-engine -B scoring-engine/build
cmake --build scoring-engine/build --config Release
ctest --test-dir scoring-engine/build --output-on-failure
```

Backend quality checks:

```bash
python -m ruff check backend ml tests
python -m mypy backend/app --ignore-missing-imports
python -m pip install pip-audit
pip-audit -r backend/requirements.txt -r backend/requirements-ocr.txt -r backend/requirements-storage.txt -r ml/requirements.txt
```

Release and evaluation checks:

```bash
python scripts/evaluate_learning.py ml/evaluation/benchmark.example.json --minimum mapping_f1=0.80 --minimum matcher_precision=0.90 --minimum matcher_f1=0.90 --minimum matcher_abstention_accuracy=0.90 --minimum ranking_ndcg=0.80 --minimum historical_ranking_ndcg=0.80
python scripts/verify_release.py
python scripts/load_test.py --url http://localhost:8000/health/ready --requests 100 --workers 10
```

The 2026-11-07 learning-engine v2 verification recorded 55 passing Python tests and one skipped service-container integration test, a successful frontend production build with 20 JavaScript assets inside the bundle budget, passing Ruff and mypy checks, 65 controlled artifacts and 320 Python docstrings accepted by the release verifier, and a synchronized SQL reference snapshot covering 16 tables and 45 indexes. Migration `0013` passed fresh upgrade, downgrade/re-upgrade, and a copy-of-`0012` preservation check retaining all six historical-question rows. The eight computed synthetic matcher cases scored 1.0 for precision, recall/F1, accuracy, abstention/status accuracy, and MRR at 0.625 accepted-match coverage; this is regression evidence, not RVCE academic validation. The service integration workflow now supplies the backend import path, and the digest-pinned frontend nginx replacement reports zero fixed HIGH/CRITICAL findings under the same local Trivy policy that found 67 in the former image. GitHub reruns remain required before those checks are recorded as passing. Earlier, all seven Playwright scenarios reported `ok`; under the below-policy local Node 24.11.1/npm 11.6.2 toolchain, the full runner required termination after reporting. The declared Node 24.22.1/npm 11.21.1 CI run remains required for clean candidate evidence.

RVCE course extraction reads the source PDFs in place, verifies their SHA-256 fingerprints, and writes pending-review candidates plus conflicts under `database/`. Set `RVCE_SYLLABUS_DIR` to the supplied syllabus directory and run `make extract-rvce` to regenerate and validate the files. After the backend is running and an administrator is logged in, submit candidates with `python scripts/import_rvce_candidates.py --token <admin-token>`. Imported candidates stay hidden from learners until an administrator approves them. First-year candidates are labeled `BE-UNMAPPED` and remain unavailable for branch enrollment until reviewed.

The same operations are available through the root `Makefile` where the required tools are installed.

## 7. API overview

The API is mounted under `/api/v1`:

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/auth/login` | Issue a development access token |
| `GET` | `/auth/export` | Export authenticated account data |
| `POST` | `/auth/delete` | Delete authenticated account after email confirmation |
| `POST` | `/auth/logout` | Revoke the authenticated user's existing tokens |
| `GET` | `/courses` | List owned subject workspaces with academic scope, origin, and syllabus status |
| `POST` | `/courses` | Create a personal subject workspace under a validated branch, scheme, and semester |
| `GET` | `/concepts?course_id={id}&syllabus_only=true` | List syllabus-derived concepts with unit/page provenance |
| `POST` | `/syllabus/analyze` | Extract topics from syllabus text |
| `GET` | `/syllabus/sources?course_id={id}` | List stored course syllabus PDF copies |
| `POST` | `/syllabus/sources/upload?course_id={id}` | Store a course syllabus PDF copy |
| `POST` | `/syllabus/sources/{id}/process` | Extract text from a stored syllabus copy |
| `POST` | `/syllabus/sources/{id}/generate-map` | Create concepts from extracted syllabus topics with source provenance |
| `GET` | `/roadmap` | Preview a capacity-bounded, multi-day study plan |
| `POST` | `/roadmap/generate` | Persist a full-effort plan from a processed syllabus-derived concept map |
| `GET` | `/roadmap/history` | List roadmap revisions |
| `GET`, `POST` | `/progress` | Read or record learner progress |
| `GET` | `/quizzes/{concept_id}` | Retrieve a concept quiz |
| `GET` | `/rankings` | Retrieve the authenticated learner's private mastery summary |
| `GET` | `/exams/questions` | Search question records by subject, year, or prompt text |
| `POST` | `/exams/import` | Import numbered or paragraph-separated question paper text |
| `POST` | `/exams/import-pdf` | Parse a question-paper PDF and associate questions with syllabus topics |
| `GET` | `/exams/frequency` | Read Part B topic frequency; Part A quiz counts are reported separately |
| `GET` | `/exams/rankings` | Rank concepts by historical question evidence |
| `GET`, `POST` | `/admin/users` | Admin-only user and role management |
| `GET` | `/metrics` | Internal Prometheus-compatible request/status metrics |
| `GET` | `/catalog/rvce` | Validated RVCE program, scheme, and source metadata |
| `GET`, `POST` | `/catalog/rvce/courses` | Read verified or add source-backed RVCE course records |
| `POST` | `/catalog/rvce/courses/import` | Admin bulk import of candidates into pending review |
| `GET` | `/catalog/rvce/courses/review` | Instructor/admin review queue |
| `PATCH` | `/catalog/rvce/courses/{id}/verification` | Admin approval, rejection, or return to review |
| `POST` | `/catalog/rvce/enroll` | Add verified branch-specific semester courses to a learner account |

## 8. Configuration

Copy `.env.example` to `.env` when local overrides are required. The most relevant settings are `FRONTEND_ORIGIN`, `API_PREFIX`, `DATABASE_URL`, `REDIS_URL`, and `SECRET_KEY`. `MAX_PDF_PAGES` defaults to 200 so the inventoried 126- and 152-page first-year syllabus books remain processable while document work stays bounded by page, upload-size, and extracted-text limits. The current development repository does not require a database or Redis connection. Production-style storage is enabled with `STORAGE_BACKEND=s3`, `STORAGE_BUCKET`, and the related object-storage settings.

## 9. Controlled documentation

The following documents form the formal project record. Statuses and gaps are controlled through [document-control.md](docs/document-control.md):

| Document | Purpose |
|---|---|
| [document-control.md](docs/document-control.md) | Governance, document hierarchy, status definitions, and change control |
| [requirements-traceability.md](docs/requirements-traceability.md) | Requirement coverage, implementation status, and gaps |
| [architecture.md](docs/architecture.md) | Logical components, trust boundaries, data flow, and decisions |
| [frontend-design.md](docs/frontend-design.md) | Client structure, user journeys, and UI requirements |
| [ml-and-scoring.md](docs/ml-and-scoring.md) | Preprocessing, mapping, scheduling, evaluation, and C++ scoring |
| [api-specification.md](docs/api-specification.md) | Endpoint inventory, authentication, ownership, and compatibility |
| [database-design.md](docs/database-design.md) | Persistence model, integrity, files, and recovery requirements |
| [data-protection.md](docs/data-protection.md) | Data inventory, ownership, retention, privacy, and deletion gaps |
| [security.md](docs/security.md) | Mandatory security baseline |
| [security-audit.md](docs/security-audit.md) | Audit findings, residual risks, and release checklist |
| [deployment-and-release.md](docs/deployment-and-release.md) | Release gates, deployment, scanning, and rollback |
| [operations.md](docs/operations.md) | Setup, configuration, health checks, and incident response |
| [testing.md](docs/testing.md) | Verification strategy, evidence, and test gaps |
| [evaluation.md](docs/evaluation.md) | Learning-quality metrics and acceptance criteria |
| [privacy-impact-assessment.md](docs/privacy-impact-assessment.md) | Personal-data flows, privacy risks, rights, and approvals |
| [service-level-objectives.md](docs/service-level-objectives.md) | Reliability objectives, observability, and alerting |
| [operational-readiness.md](docs/operational-readiness.md) | Release handoff controls, operator acceptance, and evidence requirements |
| [accessibility-and-performance.md](docs/accessibility-and-performance.md) | Frontend automated and manual acceptance criteria |
| [security-acceptance.md](docs/security-acceptance.md) | Independent security testing and approval requirements |
| [release-acceptance.md](docs/release-acceptance.md) | Evidence-based production release approval template |
| [rvce-catalog.md](docs/rvce-catalog.md) | RVCE syllabus authority, catalog manifest, and import contract |
| [implementation-record.md](docs/implementation-record.md) | Formal RVCE ingestion, approval, enrollment, operating, and acceptance record |
| [remaining-targets.md](docs/remaining-targets.md) | Consolidated completion register with owners, dependencies, and required acceptance evidence |
| [code-commenting-standard.md](docs/code-commenting-standard.md) | Function-level documentation requirements and review standard |

The existing `database/diagrams/er-diagram.md` and `scoring-engine/README.md` provide component-specific supporting records.

## 10. Contribution and change control

New API behavior should include a route test, new learning logic should include a focused ML test, and changes to the native scorer should include a C++ test. Keep generated files, credentials, uploads, and local build output out of version control according to `.gitignore`.

Changes affecting security, privacy, persistence, API compatibility, deployment, or learning outcomes must update the applicable controlled document and include verification evidence.

## 11. License

See [LICENSE](LICENSE).
