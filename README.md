# Intelligent Learning Roadmap

**Project document:** ILR-DOC-001
**Release status:** Development baseline
**Documentation version:** 1.0
**Last reviewed:** 2026-10-27

Intelligent Learning Roadmap is a modular learning-support platform that converts course material, learner progress, and concept dependencies into an actionable study plan. It combines a web dashboard, a typed API, explainable learning utilities, and a native scoring engine.

## 1. Project status

This repository provides a functional development slice with signed authentication, Argon2 password hashing, ownership-aware SQLAlchemy persistence, upload validation, deadline-aware roadmap generation, and optional Redis-backed throttling. SQLite is used for a no-service local run; Docker Compose provisions PostgreSQL and Redis.

## 2. Capabilities

- Course and concept tracking with prerequisite-aware statuses.
- Syllabus topic extraction through a FastAPI endpoint.
- Dated roadmap generation for incomplete concepts.
- Curated resources and concept-level quiz contracts.
- Progress updates and dashboard summaries.
- Deterministic Python utilities for text cleaning, semantic matching, dependency ordering, scheduling, and evaluation.
- C++ scoring library and command-line demonstration for concept prioritization.

## 3. Repository structure

| Directory | Responsibility |
| --- | --- |
| `frontend/` | React, Vite, and TypeScript user interface |
| `backend/` | FastAPI application, schemas, services, and API routes |
| `ml/` | Explainable preprocessing, mapping, graph, scheduling, and metrics |
| `scoring-engine/` | C++ scoring library, CLI, and native tests |
| `database/` | Initial relational schema, seed data, and ER documentation |
| `tests/` | Cross-module integration tests |
| `docs/` | Architecture, API, security, database, and evaluation notes |

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
```

Start the API from the repository root:

```bash
uvicorn app.main:app --reload --app-dir backend
```

In a second terminal, start the frontend:

```bash
cd frontend
npm ci
npm run dev
```

The dashboard is available at `http://localhost:5173`. Interactive API documentation is available at `http://localhost:8000/docs`.

For the full local stack, including PostgreSQL, Redis, private upload storage, the API worker, and the containerized frontend/backend, copy `.env.example` to `.env`, replace the development placeholders, and run:

```bash
copy .env.example .env  # Windows
# cp .env.example .env  # macOS/Linux
docker compose up --build
```

The seeded development account is `demo@example.com` with password `demo-password`. Replace the Compose `SECRET_KEY` before any shared deployment.

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
python -m pip_audit -r backend/requirements.txt -r ml/requirements.txt
```

The same operations are available through the root `Makefile` where the required tools are installed.

## 7. API overview

The API is mounted under `/api/v1`:

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/auth/login` | Issue a development access token |
| `GET` | `/auth/export` | Export authenticated account data |
| `POST` | `/auth/delete` | Delete authenticated account after email confirmation |
| `GET` | `/courses` | List or create courses |
| `GET` | `/concepts` | List concepts and prerequisites |
| `POST` | `/syllabus/analyze` | Extract topics from syllabus text |
| `GET` | `/roadmap` | Generate a dated study plan |
| `GET` | `/roadmap/history` | List roadmap revisions |
| `GET` | `/resources` | List learning resources |
| `GET`, `POST` | `/resources/{id}/mappings` | Review resource-to-concept mappings |
| `GET`, `POST` | `/progress` | Read or record learner progress |
| `GET` | `/quizzes/{concept_id}` | Retrieve a concept quiz |
| `GET` | `/rankings` | Retrieve the development leaderboard |

## 8. Configuration

Copy `.env.example` to `.env` when local overrides are required. The most relevant settings are `FRONTEND_ORIGIN`, `API_PREFIX`, `DATABASE_URL`, `REDIS_URL`, and `SECRET_KEY`. The current development repository does not require a database or Redis connection.

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

The existing `database/diagrams/er-diagram.md` and `scoring-engine/README.md` provide component-specific supporting records.

## 10. Contribution and change control

New API behavior should include a route test, new learning logic should include a focused ML test, and changes to the native scorer should include a C++ test. Keep generated files, credentials, uploads, and local build output out of version control according to `.gitignore`.

Changes affecting security, privacy, persistence, API compatibility, deployment, or learning outcomes must update the applicable controlled document and include verification evidence.

## 11. License

See [LICENSE](LICENSE).
