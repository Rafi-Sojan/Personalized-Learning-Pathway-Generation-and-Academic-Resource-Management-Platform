# Architecture Specification

**Document ID:** ILR-ARC-001
**Version:** 1.0
**Status:** Development baseline
**Last reviewed:** 2026-10-27

## 1. Architectural style

The platform is a modular monolith with separately testable frontend, API, learning-logic, persistence, and native-scoring concerns. This structure supports a single-repository development workflow while preserving boundaries for future service extraction.

## 2. Logical components

1. **Frontend:** React/Vite presents courses, concept maps, roadmaps, resources, quizzes, and progress.
2. **API:** FastAPI owns HTTP contracts, authentication, ownership checks, validation, and application orchestration.
3. **Persistence:** SQLAlchemy models and repositories persist users, courses, concepts, prerequisites, resources, progress, and study plans.
4. **Learning logic:** The ML package provides deterministic preprocessing, concept mapping, graph, scheduling, and evaluation primitives.
5. **Scoring:** The C++ engine provides a fast ranking primitive and a command-line testable boundary.
6. **Infrastructure:** PostgreSQL is the Compose persistence service; Redis supports rate limits and future caching.

## 3. Trust boundaries

- The browser is an untrusted client and must not be trusted for identity, ownership, or scoring claims.
- The API is the authorization boundary for all private data.
- Uploaded documents are untrusted input and must remain outside public static paths.
- Redis is an availability optimization, not the source of truth.
- Derived ML and scoring results are recommendations and require validation before becoming authoritative records.

## 4. Runtime data flow

```text
Browser -> FastAPI -> authentication/authorization -> services -> SQLAlchemy -> database
                                      |                 |
                                      v                 v
                              rate limiter       ML/scoring integrations
                                      |
                                      v
                                    Redis
```

## 5. Deployment boundaries

SQLite is the zero-service development default. Docker Compose provisions PostgreSQL, Redis, backend, and frontend. The C++ scorer remains independently testable and is currently reached through a Python integration/fallback boundary. A native process or library boundary may be introduced when ranking workload and operational requirements justify it.

## 6. Architectural decisions

| Decision | Rationale | Consequence |
|---|---|---|
| Modular monolith | Keeps development and deployment simple | Requires discipline around module boundaries |
| Signed short-lived JWTs | Stateless API authentication | Revocation requires expiry or key rotation |
| SQLAlchemy plus Alembic | Portable persistence and controlled schema changes | Migrations must be run in deployment |
| Deterministic learning utilities | Explainability and repeatable tests | Less semantic coverage than a validated ML model |
| Redis fallback | Local development remains usable without Redis | Distributed rate-limit consistency requires Redis |
