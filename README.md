# Intelligent Learning Roadmap

Intelligent Learning Roadmap is a modular learning-support platform that converts course material, learner progress, and concept dependencies into an actionable study plan. It combines a web dashboard, a typed API, explainable learning utilities, and a native scoring engine.

## Project status

This repository provides a functional development skeleton and a tested vertical slice. The default API repository is in memory so that the application can be started without provisioning a database or cache. PostgreSQL, Redis, production authentication, and file-backed syllabus processing are extension points documented in `docs/`.

## Capabilities

- Course and concept tracking with prerequisite-aware statuses.
- Syllabus topic extraction through a FastAPI endpoint.
- Dated roadmap generation for incomplete concepts.
- Curated resources and concept-level quiz contracts.
- Progress updates and dashboard summaries.
- Deterministic Python utilities for text cleaning, semantic matching, dependency ordering, scheduling, and evaluation.
- C++ scoring library and command-line demonstration for concept prioritization.

## Repository structure

| Directory | Responsibility |
| --- | --- |
| `frontend/` | React, Vite, and TypeScript user interface |
| `backend/` | FastAPI application, schemas, services, and API routes |
| `ml/` | Explainable preprocessing, mapping, graph, scheduling, and metrics |
| `scoring-engine/` | C++ scoring library, CLI, and native tests |
| `database/` | Initial relational schema, seed data, and ER documentation |
| `tests/` | Cross-module integration tests |
| `docs/` | Architecture, API, security, database, and evaluation notes |

## Prerequisites

- Python 3.11 or newer
- Node.js 20 or newer
- A C++17 compiler for the scoring engine
- CMake 3.20 or newer for the native build

## Local development

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
npm install
npm run dev
```

The dashboard is available at `http://localhost:5173`. Interactive API documentation is available at `http://localhost:8000/docs`.

## Testing and builds

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

The same operations are available through the root `Makefile` where the required tools are installed.

## API overview

The API is mounted under `/api/v1`:

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/auth/login` | Issue a development access token |
| `GET` | `/courses` | List or create courses |
| `GET` | `/concepts` | List concepts and prerequisites |
| `POST` | `/syllabus/analyze` | Extract topics from syllabus text |
| `GET` | `/roadmap` | Generate a dated study plan |
| `GET` | `/resources` | List learning resources |
| `GET`, `POST` | `/progress` | Read or record learner progress |
| `GET` | `/quizzes/{concept_id}` | Retrieve a concept quiz |
| `GET` | `/rankings` | Retrieve the development leaderboard |

## Configuration

Copy `.env.example` to `.env` when local overrides are required. The most relevant settings are `FRONTEND_ORIGIN`, `API_PREFIX`, `DATABASE_URL`, `REDIS_URL`, and `SECRET_KEY`. The current development repository does not require a database or Redis connection.

## Documentation and contribution

Design notes and extension guidance are available in `docs/`. New API behavior should include a route test, new learning logic should include a focused ML test, and changes to the native scorer should include a C++ test. Keep generated files, credentials, uploads, and local build output out of version control according to `.gitignore`.

## License

See [LICENSE](LICENSE).
