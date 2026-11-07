# Test and Verification Specification

**Document ID:** ILR-TST-001
**Version:** 2.7
**Status:** Implementation-complete development baseline
**Last reviewed:** 2026-11-07

## 1. Verification objectives

Testing shall verify functional behavior, authorization boundaries, data validation, deterministic learning logic, native scoring behavior, build reproducibility, and deployment configuration. Passing tests do not constitute a security certification or production readiness approval.

## 2. Current checks

The 2026-11-07 local verification includes:

- `python -m pytest backend/tests ml/tests tests -q`: 55 passed and one PostgreSQL/Redis integration test skipped because `INTEGRATION_TESTS` was not enabled.
- Focused regressions cover seed-free account/course setup, complete account export and foreign-key-safe deletion, external review anonymization, private-file deletion, multi-day roadmap segmentation, partial-preview disclosure, duplicate-paper object cleanup, Python/native scoring parity, solution-page exclusion, RVCE question-number variants, printed CIE/SEE detection, strict paper/course identity, hierarchical syllabus parsing, and manual question remapping.
- Course-onboarding regressions cover RVCE alias normalization, branch/scheme validation, duplicate subject rejection, personal-origin responses, syllabus upload status, verified-enrollment catalog provenance, and the configured page limit against the inventoried syllabus books.
- Learning-engine v2 regressions cover specific-versus-generic concepts, derived acronyms, multi-topic ambiguity, hierarchy context, same-name ambiguity, OCR/spelling damage, no-evidence abstention, bounded matcher metadata, source-aware concept identity, taxonomy-driven classification, crosswalk validation, deterministic graph order, downstream unlock priority, and cycle rejection.
- Ruff passed across backend, ML, tests, and the root test configuration. Mypy passed across 52 backend source files.
- The computed eight-case matcher fixture passed precision, recall/F1, exact/status/abstention accuracy, and MRR at `1.0`, with `0.625` accepted-match coverage. The fixture is synthetic regression evidence only.
- `scripts/verify_release.py` passed with 65 controlled artifacts, 320 Python docstrings, 78 frontend function comments, two C++ API comments, immutable workflow pins, the service-test import path, and a digest-pinned frontend runtime checked.
- The TypeScript/Vite production build passed and 20 JavaScript assets stayed within the bundle budget.
- All seven Playwright scenarios reported `ok`, including accessibility, successful-login redirect, syllabus intake, the legacy resource redirect, and branch-scoped personal-subject creation. The full process used local Node 24.11.1/npm 11.6.2, which are below the declared minimum, and required termination after reporting. The targeted subject scenario exited cleanly; targeted login also reported `ok` but retained the same runner-exit limitation. A live isolated-database walkthrough verified login, creation, origin labeling, syllabus deep linking, and empty verified-catalog behavior. The pinned CI toolchain remains required for clean candidate acceptance.
- `database/init.sql` matched every SQLAlchemy table, column, and named index across the 16-table/45-index model. Migration `0013_matcher_evidence` passed a fresh-database upgrade, downgrade to `0012`, and re-upgrade on SQLite. Upgrading both an isolated copy and the root local `0012` database retained all six historical-question rows with non-null metadata. The candidate PostgreSQL migration gate remains required.
- The prior 2026-11-06 native scorer test compiled and ran with `g++ -std=c++17 -Wall -Wextra -Werror`; native tests were not rerun on 2026-11-07.

Two supplied RVCE-format PDFs were also used for deterministic, read-only parser checks. The 20-page combined CIE/scheme/SEE packet explicitly declares `21CS45` and produced 64 question rows: 19 Part A quiz items, 45 main questions, 32 CIE/test rows, and 32 SEE rows, with zero scheme/solution prompts. Selecting course `AI253IA` from the separate supplied 96-page 2022 AI/ML third-year scheme produced 106 teaching concepts: 19 roots and 87 children, with zero outcome, lab, rubric, or marks-distribution concepts. The course-identity guard prevents these two different subjects from being combined. These checks establish behavior on the observed layouts only; they are not a human-annotated precision/recall benchmark, source-authorization decision, or academic acceptance.

The failed GitHub integration run `42335747397` was reproduced locally without `PYTHONPATH=backend`: collection/setup and session teardown both failed with `ModuleNotFoundError: app`. The same command with the path configured reached the expected service-gated skip, and the integration workflow now supplies that path. A real PostgreSQL/Redis rerun remains required because this workstation does not provide Docker services. The failed security run `42335747431` was also reproduced: Trivy reported 67 fixed HIGH/CRITICAL findings for the former frontend runtime and zero for the exact replacement digest. Dependency audits, Compose runtime checks, DAST, Lighthouse, backup/restore, and the complete Release gates workflow were not otherwise executed in this local pass. Their CI and external evidence requirements remain open.

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
- The browser suite includes a mocked personal-subject flow that selects a branch scope, creates the subject, and checks the returned academic metadata; the pinned CI Node/Chromium toolchain remains the clean-exit authority.
- Lighthouse accessibility and performance thresholds are enforced by `.github/workflows/frontend-a11y-performance.yml`; the local shell has not executed the CI-only Lighthouse audit.

The Playwright smoke suite is located in `frontend/e2e/`, is invoked with `npm run test:e2e`, and is part of the frontend CI workflow. CI installs the Chromium browser before execution.
- CMake is exercised by the C++ workflow; direct `g++` compilation remains a local fallback.
- The DAST workflow is scheduled weekly and manually dispatchable. Reports are retained as workflow artifacts.
