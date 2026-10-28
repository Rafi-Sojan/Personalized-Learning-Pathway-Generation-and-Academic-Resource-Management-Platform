# Test and Verification Specification

**Document ID:** ILR-TST-001
**Version:** 2.1
**Status:** Implementation-complete development baseline
**Last reviewed:** 2026-10-28

## 1. Verification objectives

Testing shall verify functional behavior, authorization boundaries, data validation, deterministic learning logic, native scoring behavior, build reproducibility, and deployment configuration. Passing tests do not constitute a security certification or production readiness approval.

## Current checks

The baseline verification record includes:

- 17 Python tests across backend, ML, and cross-module flows, including token revocation, metrics, processing administration, numbered-question parsing, role enforcement, historical exam import, and the reproducible evaluation benchmark.
- CI executes Ruff static checks and Mypy checks across the backend source tree.
- Frontend `npm ci` followed by a successful TypeScript/Vite production build.
- `npm audit --offline --audit-level=high` reported zero project dependency vulnerabilities during this verification pass.
- Alembic initial migration applied successfully to the local SQLite database.
- Compose YAML is checked in and the CI Compose smoke workflow starts PostgreSQL, Redis, backend, worker, and frontend, then verifies health/readiness.
- C++17 scoring CLI compilation and native test execution.

For the current hardening pass, Python bytecode compilation and the frontend production build passed. The local shell does not currently have the backend dependencies installed, so the Python test, Ruff, mypy, and pip-audit commands must be run in the project virtual environment or CI. Docker was unavailable locally; CI contains the runtime smoke and DAST jobs. The frontend offline npm audit passed with zero vulnerabilities.

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

- PostgreSQL and Redis integration tests require service containers and are run by CI.
- OCR execution requires the optional OCR image and an installed Tesseract binary.
- External penetration testing remains an operational acceptance activity; the repository includes DAST automation and bounded malformed-input checks.
- Browser-level tests require the Playwright package and browser binaries; the checked-in Playwright smoke and accessibility tests run in CI with Chromium provisioning.
- Lighthouse accessibility and performance thresholds are enforced by `.github/workflows/frontend-a11y-performance.yml`; the local shell has not executed the CI-only Lighthouse audit.

The Playwright smoke suite is located in `frontend/e2e/`, is invoked with `npm run test:e2e`, and is part of the frontend CI workflow. CI installs the Chromium browser before execution.
- CMake is exercised by the C++ workflow; direct `g++` compilation remains a local fallback.
- The DAST workflow is scheduled weekly and manually dispatchable. Reports are retained as workflow artifacts.
