# Repository Agent Guidance

**Document type:** Cross-model engineering instructions  
**Version:** 1.0  
**Last reviewed:** 2026-11-05  
**Applies to:** All automated and human contributors working in this repository

## 1. Purpose and authority

This file gives repository-specific instructions to coding agents. Read it together with [`context.md`](context.md) for the project facts and [`plan.md`](plan.md) for outstanding work. The detailed acceptance status is maintained in [`docs/remaining-targets.md`](docs/remaining-targets.md).

Follow instructions in this order: system and safety requirements, the current user's explicit request, this repository guidance, then applicable project specifications. A project document does not grant permission to take an action that the user has not authorized.

## 2. Start-of-task procedure

1. Read this file, `context.md`, and the relevant sections of `plan.md`.
2. Inspect `git status` and the files related to the request before editing. The working tree may contain ongoing work from earlier sessions.
3. Read the controlling domain document before changing security, privacy, API, database, RVCE catalog, learning-quality, accessibility, or release behavior. The document index is in [`README.md`](README.md) and [`docs/document-control.md`](docs/document-control.md).
4. Identify exact files and boundaries for the task. If multiple agents are used, assign non-overlapping file ownership and integrate their changes deliberately.
5. Update the applicable formal document when behavior, a decision, a target status, or acceptance evidence changes.
6. In the handoff, list changed files, decisions, checks actually run and their results, unverified behavior, and the next actionable step.

Do not reset, clean, overwrite, or mass-format unrelated files. Do not commit unless the user requests a commit. If a task requires changing existing user work, inspect that work first and preserve unrelated changes.

## 3. Product scope and decisions

- This is an RVCE-focused learning platform. The main learner workflow is subject selection, private syllabus-copy ingestion, source-aware concept mapping, study-roadmap generation, and question-paper frequency analysis.
- The uploaded syllabus copies and question papers are the academic source material. Manual management of a generic learning-resource catalog is outside the current learner workflow.
- AI-generated website links for concepts are deferred. Do not select an AI provider, add an API key, or make a network call to an AI provider unless the user makes that decision.
- Part A is classified as quiz material and Part B as main questions when the uploader or source metadata establishes that split. Preserve printed question sections and source pages. Do not infer assessment classification when the source does not support it.
- Quizzes and Progress were removed from the learner UI by product decision. Compatibility APIs may remain; do not reintroduce those screens or navigation items without an explicit request.
- The RVCE catalog is evidence-backed, and rows still require academic review. Never invent branch mappings, course identity, scheme, semester, credits, or source provenance to make a catalog appear complete.
- A development implementation baseline is not academic acceptance or production approval. Keep open evidence and external decisions visible.

## 4. Engineering conventions

### Architecture

- `frontend/` contains the React, Vite, and TypeScript client.
- `backend/` contains the FastAPI application, SQLAlchemy persistence, API schemas, services, and Alembic migrations.
- `ml/` contains deterministic preprocessing, mapping, graph, scheduling, and evaluation utilities.
- `scoring-engine/` contains the C++17 ranking component.
- `database/`, `docs/`, `scripts/`, and `.github/workflows/` contain schema references, controlled project documents, operator utilities, and CI/release gates.
- Follow the neighboring module's established patterns. Keep authorization and ownership checks on the server, validate untrusted document input, and preserve source provenance through derived data.

### Documentation and comments

- Follow [`docs/code-commenting-standard.md`](docs/code-commenting-standard.md). Python functions use docstrings; exported and non-trivial TypeScript functions use JSDoc; public C++ APIs use Doxygen-compatible comments.
- Comments explain purpose, constraints, side effects, ownership, provenance, security behavior, and non-obvious decisions. Update comments when behavior changes.
- Keep API documentation, database migrations, requirements traceability, and acceptance records aligned with code changes.

### Data and security

- Treat syllabus PDFs, exam papers, OCR output, and user-entered text as untrusted input.
- Keep uploads private. Do not place documents, credentials, tokens, API keys, personal data, licensed exam material, or database backups in source control.
- Preserve course ownership checks and role-based permissions. Never trust client-supplied identity, review status, or scoring claims.
- Use `.env.example` for configuration names and placeholders only. Do not copy real secrets into documentation or logs.
- Apply database schema changes through Alembic migrations. Run commands from the repository root with the intended `DATABASE_URL`; SQLite's relative path depends on the working directory. The development API may create missing tables, but `create_all` does not upgrade existing tables.

### Dependencies and verification

- Use `npm ci` for the frontend so the lockfile remains authoritative. Change dependencies only when the task requires it and record the reason.
- The documented local commands are in [`README.md`](README.md), [`docs/operations.md`](docs/operations.md), and [`docs/testing.md`](docs/testing.md). Frontend scripts are declared in `frontend/package.json`.
- Use focused validation that matches the change and the user's requested scope. Never state that a test, audit, build, migration, or acceptance check passed unless it was actually run and its result was observed.
- External RVCE, legal/privacy, independent security, accessibility, staging, or release-owner approval cannot be replaced by local tests or model review.

## 5. Multi-model collaboration

- Give each parallel agent an explicit objective, allowed paths, expected output, and verification boundary.
- Avoid concurrent edits to the same file. If two tasks must touch a shared contract, have one owner integrate the change after both proposals are reviewed.
- Treat another model's output as a proposal until its code, assumptions, and evidence are checked against this repository.
- Before applying a patch from another model, reread the current file and diff; do not apply a stale patch over newer user work.
- Keep decisions and durable findings in `context.md`, `plan.md`, or the relevant controlled document rather than relying on chat history.
- A complete handoff states: objective and status; files changed; important decisions; commands/checks and observed results; remaining uncertainty; and the next action.

