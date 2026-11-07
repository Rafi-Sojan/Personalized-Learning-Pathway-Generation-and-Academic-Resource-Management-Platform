# Project Context for Model Handoffs

**Document type:** Continuation brief  
**Version:** 1.3
**Last reviewed:** 2026-11-07  
**Use with:** [`AGENTS.md`](AGENTS.md) and [`plan.md`](plan.md)

## 1. Project in one page

Intelligent Learning Roadmap is an RVCE-focused learning platform. Learners select subjects, upload and process syllabus copies, review source-aware concept maps, generate dated study roadmaps, and inspect question frequency from past papers. The platform is a development baseline; academic validation and production acceptance are still open.

The product uses uploaded RVCE syllabus copies and question papers as its primary academic material. Learners may create a private subject workspace by selecting a validated RVCE branch, scheme, and semester, then attach its syllabus immediately or later. A personal workspace is not an academically verified RVCE catalog row; catalog publication still requires source provenance and authorized review. The learner UI does not manage a generic resource library. AI-generated links to learning websites are deferred by product decision. The user clarified that Part A is quiz material and Part B is the main questions. Quiz and Progress pages were removed from the learner interface; compatibility APIs may remain.

## 2. Architecture and repository map

| Path | Role |
|---|---|
| `frontend/` | React 19, Vite, TypeScript, routing, dashboard, syllabus, concept map, roadmap, and question-frequency UI. |
| `backend/app/` | FastAPI routes, authentication, authorization, SQLAlchemy models, business services, storage and worker integrations. |
| `backend/migrations/` | Alembic schema history. Migrations are the authoritative schema evolution mechanism. |
| `ml/` | Python PDF/text processing, concept mapping, dependency graph, scheduling, and evaluation. |
| `scoring-engine/` | C++17 ranking library and CLI. |
| `database/` | SQL references, RVCE source manifests/candidate data, seeds, and diagrams. |
| `scripts/` | Setup, import, validation, processing, backup, release, and operational utilities. |
| `docs/` | Controlled architecture, API, security, privacy, operations, evaluation, and acceptance records. |
| `.github/workflows/` | Backend, frontend, C++, release, security, accessibility, and operational CI workflows. |

The system is a modular monolith: the browser calls FastAPI; the API enforces authentication and ownership, persists through SQLAlchemy, and uses deterministic Python learning utilities. PostgreSQL and Redis are provisioned by Compose. Local storage is available for development; S3-compatible private storage is supported for deployment. Redis can be unavailable in development, with a process-local fallback.

## 3. Current product and data rules

- Preserve source document, page, syllabus version, unit, review state, and question metadata wherever available.
- Only reviewed/verified question records contribute to historical evidence and frequency rankings.
- Preserve printed assessment sections. Apply Part A/Part B classification only when source metadata or uploader input establishes it.
- Prerequisite proposals require review and cycle checks before they influence roadmap ordering.
- RVCE catalog candidates are not authoritative until reviewed. The formal register records 207 candidate rows, two quarantined title conflicts, and unresolved first-year branch mapping.
- Branch choices for personal subjects come from the controlled catalog manifest. Do not add arbitrary institutional branches or represent a learner-created subject as catalog-verified.
- The currently inventoried eight PDFs do not establish complete RVCE institutional coverage. The target admission cohort, branch set, scheme, and semester scope are undecided.
- AI link generation is deferred. Do not add provider credentials or place secrets in the browser.

## 4. Development workflow

Run commands from the repository root unless a command explicitly changes directory. The SQLite default is `sqlite:///./learning.db`, so its location depends on the current working directory. Keep Alembic and Uvicorn pointed at the same `DATABASE_URL` and working directory.

```powershell
# Backend environment and dependencies
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt -r ml/requirements.txt

# Apply schema before starting the API
alembic -c backend/alembic.ini upgrade head
$env:PYTHONPATH = "$PWD;$PWD\backend"
uvicorn app.main:app --reload --app-dir backend
```

In a second terminal:

```powershell
cd frontend
npm ci
npm run dev
```

The usual local addresses are frontend `http://localhost:5173`, API `http://localhost:8000`, API docs `http://localhost:8000/docs`, and readiness `http://localhost:8000/health/ready`. Use `.env.example` as the configuration template. Never copy real values into this brief.

For a local verification request, the documented Python command is `python -m pytest backend/tests ml/tests tests`; frontend scripts are `npm run build` and `npm run test:e2e`. CI workflows and [`docs/testing.md`](docs/testing.md) define broader checks. State only checks that were actually run.

## 5. Current project status

- `docs/remaining-targets.md` is the authoritative completion register. It says core implementation is present and requires Release gates verification; academic, source authorization, privacy/legal, security, accessibility, staging, and release-owner evidence remain open.
- `docs/implementation-record.md` describes RVCE catalog ingestion, candidate review, enrollment, and the evidence recorded for the prior implementation.
- `README.md` documents local startup, repository structure, capabilities, and formal docs.
- The working tree has broad uncommitted changes across backend, frontend, ML, data, and documentation, including untracked ingestion-related files. Inspect `git status` before making changes. Preserve this work; do not reset or clean it.
- No project commit should be assumed. Confirm commit state from Git before referring to a change as committed.
- The 2026-11-06 repository correction pass removed seed-data assumptions from tests, completed account export/deletion coverage, split full roadmap estimates across days, added failed-paper object cleanup, aligned Python/native scoring, replaced the demo leaderboard with a private learner summary, synchronized `database/init.sql`, normalized frontend API errors, and added frontend security headers.
- Local evidence for that pass is 32 passed and one skipped Python test, passing Ruff/mypy/release verification, a passing frontend production build, a 16-table model/schema match, and a strict-warning native scorer test. Five browser scenarios reported `ok`, but the unsupported local Node 24.11.1 runner required termination after reporting; clean completion remains a pinned CI requirement.
- The 2026-11-07 ingestion correction made question parsing page-aware, excludes solution/scheme ranges, recognizes RVCE numbering and structural CIE/SEE headings, rejects explicit paper/course-code mismatches, maps only to verified current-syllabus concepts, exposes manual remapping, and reports mapped/unmapped frequency totals. Syllabus parsing now builds unit-scoped heading/child hierarchies, excludes non-teaching tails, and leaves every extracted row pending review. The concept map displays unit, page, hierarchy, and review state.
- The 2026-11-07 onboarding slice added learner-created branch/scheme/semester subject workspaces, optional syllabus attachment during creation, syllabus deep links, verified-catalog availability previews, course-origin provenance, and migration `0012_course_academic_scope`. The configured PDF ceiling is 200 pages so both inventoried first-year syllabus books fit within the bounded processor.
- Read-only checks on the two supplied files produced 64 clean `21CS45` questions (19 quiz, 45 main; 32 CIE/test, 32 SEE) and 106 separate `AI253IA` concepts (19 roots, 87 children) without scheme/rubric contamination. These are different subjects and the API now prevents combining them. After the onboarding slice, the full local suite recorded 39 passed/1 skipped, with passing Ruff, mypy, release verification, frontend build/bundle checks, schema consistency, and migration lifecycle checks. Seven Playwright scenarios reported `ok`, but the below-policy Node/npm runner required termination after reporting; the targeted subject scenario exited cleanly, and the isolated live walkthrough succeeded. Pinned CI remains required. These are implementation checks, not academic acceptance.
- The root local database was not changed by the 2026-11-07 correction. It may still contain a legacy multi-course map created under an unrelated course code; do not delete it automatically. Regenerate from a correctly coded enrolled subject and review the new syllabus/question rows before treating UI counts as current.

### Recent local runtime note

On 2026-11-03, the local root `learning.db` was found at revision `0010` while the development app had already created an empty `syllabus_records` table. Migration `0011` was made tolerant of that existing table/index state and applied to the root database. The API was restarted; `/health/ready` returned HTTP 200 with `ready-with-redis-fallback`, and the frontend root returned HTTP 200. The browser session was redirected to sign-in after the restart. A 299-topic dashboard load was observed after the schema migration, and the roadmap preview was updated to honor available daily capacity. Recheck the current migration revision, service processes, sign-in state, and roadmap preview before relying on this historical runtime snapshot.

A pre-migration copy was created as `learning.db.before-0011.bak`; `.gitignore` excludes `*.bak`. Keep database backups local and protected.

On 2026-11-06 no API or frontend service was running during the initial repository inspection. The correction pass used isolated temporary test storage/database state and did not mutate the root `learning.db`. Recheck live services and migration identity before relying on the earlier 2026-11-03 runtime observation.

On 2026-11-07, after fresh and legacy migration lifecycle checks passed, the root `learning.db` was copied to `learning.db.before-0012.bak` and upgraded from `0011_ingestion_provenance_review` to `0012_course_academic_scope`. The post-migration check reported head `0012`, retained the existing single course, and backfilled it with `origin=personal`. Both local servers used for the isolated live walkthrough were stopped afterward.

## 6. Source documents to consult

| Question | Source of truth |
|---|---|
| What remains and what evidence closes it? | `docs/remaining-targets.md`; summary in `plan.md`. |
| How is RVCE material imported and reviewed? | `docs/rvce-catalog.md`, `docs/implementation-record.md`, and `docs/syllabus-and-paper-ingestion.md`. |
| What API behavior is supported? | `docs/api-specification.md` and `backend/app/api/v1/`. |
| What is the schema and migration procedure? | `docs/database-design.md`, `backend/migrations/`, and `docs/operations.md`. |
| What security/privacy conditions apply? | `docs/security.md`, `docs/security-audit.md`, `docs/privacy-impact-assessment.md`, and `docs/data-protection.md`. |
| How should code comments and checks be handled? | `docs/code-commenting-standard.md`, `docs/testing.md`, and CI workflows. |
| Is release approval complete? | `docs/release-acceptance.md` and `docs/operational-readiness.md`. |

## 7. Handoff format

When handing work to another model or maintainer, provide the requested outcome, current status, files changed, important decisions, checks actually run and their results, remaining risks or uncertainty, and the next concrete action. Include file paths and relevant document IDs. Do not rely on this chat being available.

