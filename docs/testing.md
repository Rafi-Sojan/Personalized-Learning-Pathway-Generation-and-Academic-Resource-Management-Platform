# Test and Verification Specification

**Document ID:** ILR-TST-001
**Version:** 2.4
**Status:** Implementation-complete development baseline
**Last reviewed:** 2026-11-07

## 1. Verification objectives

Testing shall verify functional behavior, authorization boundaries, data validation, deterministic learning logic, native scoring behavior, build reproducibility, and deployment configuration. Passing tests do not constitute a security certification or production readiness approval.

## 2. Current checks

The 2026-11-07 local verification includes:

- `python -m pytest backend/tests ml/tests tests -q`: 37 passed and one PostgreSQL/Redis integration test skipped because `INTEGRATION_TESTS` was not enabled.
- Focused regressions cover seed-free account/course setup, complete account export and foreign-key-safe deletion, external review anonymization, private-file deletion, multi-day roadmap segmentation, partial-preview disclosure, duplicate-paper object cleanup, Python/native scoring parity, solution-page exclusion, RVCE question-number variants, printed CIE/SEE detection, strict paper/course identity, hierarchical syllabus parsing, and manual question remapping.
- Ruff passed across backend, ML, tests, and the root test configuration. Mypy passed across 52 backend source files.
- `scripts/verify_release.py` passed with 60 controlled artifacts, 264 Python docstrings, 72 frontend function comments, two C++ API comments, and immutable workflow pins checked.
- The TypeScript/Vite production build passed and 19 JavaScript assets stayed within the bundle budget.
- The prior 2026-11-06 run had all five Playwright scenarios report `ok`, including accessibility, syllabus intake, and the legacy resource redirect. The unsupported local Node 24.11.1 process did not exit after reporting and was terminated; the pinned Node 24.22.1 CI run remains the clean-exit authority. Browser tests were not rerun on 2026-11-07.
- The prior 2026-11-06 run executed `database/init.sql` in memory and matched all tables and columns across the 16-table SQLAlchemy model; schema consistency was not rerun on 2026-11-07.
- The prior 2026-11-06 native scorer test compiled and ran with `g++ -std=c++17 -Wall -Wextra -Werror`; native tests were not rerun on 2026-11-07.

Two supplied RVCE-format PDFs were also used for deterministic, read-only parser checks. The 20-page combined CIE/scheme/SEE packet explicitly declares `21CS45` and produced 64 question rows: 19 Part A quiz items, 45 main questions, 32 CIE/test rows, and 32 SEE rows, with zero scheme/solution prompts. Selecting course `AI253IA` from the separate supplied 96-page 2022 AI/ML third-year scheme produced 106 teaching concepts: 19 roots and 87 children, with zero outcome, lab, rubric, or marks-distribution concepts. The course-identity guard prevents these two different subjects from being combined. These checks establish behavior on the observed layouts only; they are not a human-annotated precision/recall benchmark, source-authorization decision, or academic acceptance.

Dependency audits, Compose runtime checks, PostgreSQL/Redis integration, DAST, Lighthouse, backup/restore, and the complete Release gates workflow were not executed in this local pass. Their CI and external evidence requirements remain open.

## 3. Security-focused tests

The API tests verify that:

- Private routes reject unauthenticated requests.
- Invalid login credentials are rejected.
- Valid login produces a bearer token.
- Authenticated progress updates succeed.
- Roadmap generation succeeds for feasible inputs.
- Invalid upload type is rejected.
- PDF content with a misleading `.pdf` filename is rejected.
- Account export includes ingestion, plan, review, and audit records; deletion succeeds with foreign keys enabled and removes private objects.
- Failed all-duplicate paper imports leave no additional database resource or private object.
- Roadmap segments never exceed daily capacity and retain the complete concept estimate.

## 4. Required tests for syllabus and exam workflows

Repository tests cover the principal deterministic workflow paths. Additional release coverage remains required for:

- Syllabus-copy processing lifecycle and map-generation idempotency under a real worker/database service combination.
- PDF question-paper rejection for oversized, encrypted, unreadable, and OCR-dependent files across representative parser versions.
- Subject/topic frequency totals, per-year counts, repeated prompt counts, and year-range filters across a reviewed multi-year corpus. Deterministic route coverage exists for mapped/unmapped and quiz/main separation, but corpus-level acceptance remains open.

The dependency-free load smoke test can be run against a local API with `python scripts/load_test.py --requests 50 --workers 5`. A baseline OWASP ZAP scan is available through `scripts/run_dast.ps1` when Docker is available.

## 5. Test gaps

- PostgreSQL and Redis integration tests require service containers and are run by CI.
- OCR execution requires the optional OCR image and an installed Tesseract binary.
- The syllabus-derived concept extraction and paper-to-topic matching require evaluation on an authorized, representative RVCE corpus; source inspection and synthetic examples are not academic validation.
- External penetration testing remains an operational acceptance activity; the repository includes DAST automation and bounded malformed-input checks.
- Browser-level tests require the Playwright package and browser binaries; the checked-in Playwright smoke and accessibility tests run in CI with Chromium provisioning.
- Lighthouse accessibility and performance thresholds are enforced by `.github/workflows/frontend-a11y-performance.yml`; the local shell has not executed the CI-only Lighthouse audit.

The Playwright smoke suite is located in `frontend/e2e/`, is invoked with `npm run test:e2e`, and is part of the frontend CI workflow. CI installs the Chromium browser before execution.
- CMake is exercised by the C++ workflow; direct `g++` compilation remains a local fallback.
- The DAST workflow is scheduled weekly and manually dispatchable. Reports are retained as workflow artifacts.
