# Test and Verification Specification

**Document ID:** ILR-TST-001
**Version:** 1.0
**Status:** Development baseline
**Last reviewed:** 2026-10-27

## 1. Verification objectives

Testing shall verify functional behavior, authorization boundaries, data validation, deterministic learning logic, native scoring behavior, build reproducibility, and deployment configuration. Passing tests do not constitute a security certification or production readiness approval.

## Current checks

The baseline verification record includes:

- 13 Python tests across backend, ML, and cross-module flows, including the reproducible evaluation benchmark.
- Ruff static checks with no reported violations.
- Mypy checks with no reported issues across 43 backend source files.
- Frontend `npm ci` followed by a successful TypeScript/Vite production build.
- `npm audit --audit-level=high` with zero reported project dependency vulnerabilities at the time of verification.
- Alembic initial migration applied successfully to the local SQLite database.
- Compose YAML parsed successfully; Docker runtime execution was unavailable because Docker was not installed.
- C++17 scoring CLI compilation and native test execution.

For the current hardening pass, Python bytecode compilation and the frontend production build passed. The local shell did not have the backend dependencies installed, so the Python test, Ruff, mypy, and pip-audit commands must be rerun in the project virtual environment or CI. Docker was unavailable locally, and the npm advisory endpoint was unreachable from the restricted shell.

## Security-focused tests

The API tests verify that:

- Private routes reject unauthenticated requests.
- Invalid login credentials are rejected.
- Valid login produces a bearer token.
- Authenticated progress updates succeed.
- Roadmap generation succeeds for feasible inputs.
- Invalid upload type is rejected.
- PDF content with a misleading `.pdf` filename is rejected.
- Account export and roadmap revision history return authenticated user-scoped data.

The dependency-free load smoke test can be run against a local API with `python scripts/load_test.py --requests 50 --workers 5`. A baseline OWASP ZAP scan is available through `scripts/run_dast.ps1` when Docker is available.

## Test gaps

- PostgreSQL and Redis integration tests are not run in the local test suite.
- OCR and malformed-PDF tests are not yet present.
- Browser-level frontend tests are not yet present.
- No load, fuzz, DAST, or penetration testing has been performed.
- Browser-level tests require the Playwright package and browser binaries; the current shell has not installed the browser binary, while CI provisions it explicitly.

The Playwright smoke suite is located in `frontend/e2e/`, is invoked with `npm run test:e2e`, and is now part of the frontend CI workflow. CI installs the Chromium browser before execution.
- CMake was not available on the development machine; the C++ implementation was verified with direct `g++` compilation.
