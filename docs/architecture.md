# Architecture Specification

**Document ID:** ILR-ARC-001
**Version:** 2.3
**Status:** Implementation-complete development baseline
**Last reviewed:** 2026-11-10

## 1. Architectural style

The platform is a modular monolith with separately testable frontend, API, learning-logic, persistence, and native-scoring concerns. This structure supports a single-repository development workflow while preserving boundaries for future service extraction.

## 2. Logical components

1. **Frontend:** React/Vite presents guided personal-subject setup, verified RVCE catalog enrollment, stored syllabus copies, reviewable course-planning profiles, source-aware concept maps, course/semester roadmaps, session completion, and past-paper frequency analysis. Quiz and standalone progress screens are outside the current learner UI.
2. **API:** FastAPI owns HTTP contracts, authentication, ownership checks, validation, and application orchestration.
3. **Persistence:** SQLAlchemy models and repositories persist users; learner courses with academic scope and personal/catalog origin; reviewed syllabus workload profiles; concepts with syllabus-version/unit/order/page provenance; prerequisites; private syllabus source documents; parsed historical exam questions; audit events; mastery evidence; and typed course/semester study-plan sessions.
4. **Learning logic:** The ML package provides deterministic preprocessing, concept mapping, hard unit/dependency ordering, course-type activity construction, balanced calendar scheduling, and evaluation primitives.
5. **Scoring:** The C++ engine provides a fast ranking primitive and a command-line testable boundary.
6. **Infrastructure:** PostgreSQL is the Compose persistence service; Redis supports rate limits and JSON response caching; local or S3-compatible storage holds private documents.

## 3. Trust boundaries

- The browser is an untrusted client and must not be trusted for identity, ownership, or scoring claims.
- The API is the authorization boundary for all private data.
- Uploaded documents are untrusted input and must remain outside public static paths.
- Past-paper PDFs are parsed in memory; only normalized question records and source/year metadata are retained by the import endpoint.
- Redis is an availability optimization, not the source of truth.
- Derived ML and scoring results are recommendations and require validation before becoming authoritative records.
- AI-provider credentials and generated website links are deferred and must not be placed in the browser bundle.

## 4. Runtime data flow

```text
Browser -> FastAPI -> authentication/authorization -> services -> SQLAlchemy -> database
                                      |                 |
                                      v                 v
                              rate limiter/cache  ML/scoring integrations
                                      |
                                      v
               Redis + private syllabus storage + question archive
```

### 4.1 Roadmap data flow

```text
private syllabus PDF
  -> page-tagged extraction
  -> course-scoped topics + course workload profile
  -> human review of topics/profile
  -> hard unit order + accepted prerequisites
  -> evidence/mastery priority within the eligible unit
  -> course-type activity demands
  -> course or balanced semester calendar
  -> typed persisted sessions + revision snapshot
  -> completion/mastery feedback for the next generation
```

The review boundary is deliberate. Extracted course type, hours, and CIE/SEE unit scope are suggestions until the owner verifies the profile. Semester scheduling accepts an explicit list of owned courses and requires a single program, scheme, and semester; it does not infer RVCE elective choices. Verified Part B questions influence priority and exam-practice evidence, while Part A questions are attached to retrieval-oriented activities. Source unit order and accepted prerequisites are constraints, not score features.

## 5. Deployment boundaries

SQLite is the zero-service development default. Docker Compose provisions PostgreSQL, Redis, backend, and frontend. The C++ scorer remains independently testable and is currently reached through a Python integration/fallback boundary. A native process or library boundary may be introduced when ranking workload and operational requirements justify it.

## 6. Architectural decisions

| Decision | Rationale | Consequence |
|---|---|---|
| Modular monolith | Keeps development and deployment simple | Requires discipline around module boundaries |
| Signed short-lived JWTs | Stateless API authentication | Per-user token versions provide logout/revocation; expiry and key rotation remain defense in depth |
| SQLAlchemy plus Alembic | Portable persistence and controlled schema changes | Migrations must be run in deployment |
| Deterministic learning utilities | Explainability and repeatable tests | Less semantic coverage than a validated ML model |
| Reviewed course-planning profile | RVCE syllabus tables contain useful but occasionally inconsistent workload and assessment facts | Persisted plans block on review when an extracted profile is available; warnings remain visible rather than being silently repaired |
| Explicit semester course selection | RVCE option groups require authoritative learner/catalog decisions | Scheduler balances only the courses supplied by the learner and rejects mixed academic scope |
| Hard source unit order | Printed unit order is an academic sequencing constraint | Frequency and mastery change priority only inside the currently eligible unit |
| Redis fallback | Local development remains usable without Redis | Distributed rate-limit consistency requires Redis |
| Storage abstraction | Local files remain simple while S3-compatible storage supports production durability | Production requires bucket encryption, lifecycle, and credential management |
| Durable audit events | Security/product changes survive process restarts and support retention | Operators must schedule retention cleanup and protect audit access |
| Separate personal and verified subject origins | Learners need immediate private workspaces without weakening academic catalog controls | Personal records use manifest-validated scope but do not publish or approve institutional course rows |
