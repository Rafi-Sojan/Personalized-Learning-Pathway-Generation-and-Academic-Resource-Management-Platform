# RVCE Syllabus Integration Implementation Record

**Document ID:** ILR-IMP-001  
**Version:** 1.1
**Status:** Implemented development workflow; academic acceptance pending  
**Owner:** Project maintainer  
**Last reviewed:** 2026-11-01  
**Related records:** ILR-REQ-001, ILR-API-001, ILR-DB-001, ILR-FE-001, ILR-RVCE-001

## 1. Purpose and scope

This record describes the RVCE course-syllabus ingestion and learner enrollment slice: source inventory, extraction, validation, database persistence, academic review, branch mapping, enrollment, CI gates, operating procedure, verification evidence, and outstanding acceptance work. It supplements the system architecture and API/database specifications; it does not claim that extracted course records have received RVCE academic approval.

## 2. Delivery summary

The implementation includes a SHA-256-verified PDF extraction utility, a source-backed candidate dataset, a conflict quarantine file, a provenance validator, administrator-only batch import, role-gated review and approval, first-year branch mapping, learner enrollment, a learner catalog screen, an administrator review interface, schema migration, and CI/release checks.

The current source set contains eight inventoried PDFs. Extraction produced 207 non-conflicting candidate rows and quarantined two rows sharing a course identity but carrying different titles. Every candidate retains scheme, semester, course code, title, credit tuple total, source filename, source page, checksum, and source-index URL. Category and total contact hours are included when explicitly extractable. Unparsed outcomes and prerequisite relationships remain empty and must not be inferred from this dataset.

## 3. Controlled data artifacts

| Artifact | Purpose |
|---|---|
| `database/rvce_catalog.json` | Normalized RVCE programs, aliases, and supported scheme years |
| `database/rvce_source_documents.json` | Inventoried PDF paths, SHA-256 values, page counts, sizes, scope, and official source URL |
| `database/rvce_course_candidates.json` | Non-conflicting extracted records in `pending_review` status |
| `database/rvce_course_conflicts.json` | Quarantined same-identity records requiring academic reconciliation |
| `database/rvce-course-record.schema.json` | JSON Schema for the source-backed course record contract |
| `database/init.sql` | Fresh-database representation of the syllabus table |
| `backend/migrations/versions/0007_rvce_syllabus_courses.py` | Creates the syllabus record table |
| `backend/migrations/versions/0008_rvce_source_page.py` | Adds source filename and page provenance columns |

The source manifest records a source folder label for reproducibility. Runtime imports use the configured source-root path and verify bytes against the recorded SHA-256 value before extracting a PDF.

## 4. Data and approval lifecycle

1. The operator supplies the local RVCE syllabus directory to the extraction command.
2. The extractor checks each inventoried PDF fingerprint before reading pages.
3. A page becomes a candidate only when a course title, course code, and L:T:P credit tuple are explicitly present. Semester is read from the page or bounded by the source manifest.
4. Same program/scheme/semester/course-code identities with differing titles are written to the conflict quarantine; they are not included in the import file.
5. The validator checks supported program/scheme/semester combinations, identity uniqueness, review status, official URL, source filename, checksum, page bounds, and required values.
6. An administrator imports candidates. The endpoint rechecks source membership, checksum, page range, and official URL, and forces all imported rows to `pending_review`.
7. An instructor or administrator can inspect pending records and their source provenance. An administrator can approve, reject, or return a row to pending review.
8. First-year rows use `BE-UNMAPPED`. Approval requires an administrator-supplied RVCE program code; the API checks the target scheme and duplicate identity before saving the branch mapping.
9. Learner catalog queries omit unresolved records. Enrollment only uses approved, branch-mapped rows and creates learner-owned course, starter concept, and syllabus-version records.

## 5. HTTP contract and authorization

All paths below are relative to `/api/v1`.

| Method and path | Access | Contract |
|---|---|---|
| `GET /catalog/rvce` | Public metadata | Return normalized program aliases and scheme support |
| `GET /catalog/rvce/courses` | Public verified catalog | List approved, branch-mapped rows using optional program, scheme, and semester filters |
| `POST /catalog/rvce/courses` | Instructor or administrator | Create one source-validated record; only administrators may create an approved record |
| `POST /catalog/rvce/courses/import` | Administrator | Import 1–500 rows per request; all rows are forced to pending review |
| `GET /catalog/rvce/courses/review` | Instructor or administrator | Return the pending academic review queue |
| `PATCH /catalog/rvce/courses/{id}/verification` | Administrator | Set review state; include `program_code` to map an unresolved first-year record during approval |
| `POST /catalog/rvce/enroll` | Authenticated learner, instructor, or administrator | Materialize approved courses for a valid program/scheme/semester into the caller's account |

All import paths require source filename and page provenance. The backend compares the submitted source identity with `database/rvce_source_documents.json`; malformed or unknown provenance is rejected with `422`. Duplicate records return `409`. Unmapped first-year rows are not published or enrolled.

## 6. Persistence and migration behavior

`rvce_syllabus_courses` stores program, scheme, semester, course identity, title, credits, category, optional contact hours, JSON prerequisites/outcomes, source URL, SHA-256 checksum, source filename, source page, verification state, and creation time. The database enforces uniqueness across program, scheme year, semester, and course code. Migration `0008_rvce_source_page` is guarded when adding columns to support databases where the columns may already exist. Apply migrations using the repository's normal Alembic upgrade procedure before deploying the API.

The learner enrollment operation is idempotent for a learner and course scope: existing course records are returned as existing rather than duplicated. Newly created courses receive a starter concept named after the syllabus course and a syllabus-version label. Detailed concept decomposition and prerequisite graph generation remain a subsequent content workflow; extracted rows do not fabricate these relationships.

## 7. Operator procedure

### 7.1 Regenerate and validate candidates

From the repository root, set `RVCE_SYLLABUS_DIR` to the directory containing the inventoried PDFs and run:

```powershell
$env:RVCE_SYLLABUS_DIR = 'C:\path\to\Rvce syllabus'
make extract-rvce
```

Inspect both generated JSON files and the candidate count. If a PDF changed, extraction stops until the source inventory is intentionally refreshed and reviewed.

### 7.2 Import for review

Start the migrated backend, sign in as an administrator, and submit the candidate file:

```powershell
python scripts/import_rvce_candidates.py --token <admin-access-token>
```

The script submits bounded batches. It stops on the first API error and reports the HTTP response. Re-importing an already imported identity is rejected as a duplicate; do not treat that response as an all-or-nothing rollback across prior successful batches.

### 7.3 Review and enroll

Open **Administration → RVCE syllabus review queue**. Inspect course identity and source filename/page/checksum. Resolve title conflicts outside the batch file through an academic owner, then update the controlled data and revalidate. Select a branch for each `BE-UNMAPPED` first-year row before approval. Learners then select program, scheme, and semester from **RVCE syllabus** and add approved course rows.

## 8. Verification record

The repository checks run for this implementation report:

| Check | Result |
|---|---|
| PDF source fingerprint and candidate extraction | Passed; 207 candidates produced and two conflicting rows quarantined |
| `scripts/validate_rvce_courses.py` | Passed; 207 source-backed records |
| `scripts/verify_release.py` | Passed; controlled artifact inventory, Python function docstrings, and pinned workflow actions checked |
| Backend and ML test suites plus cross-module API tests | Passed; 19 passed, 1 skipped (optional integration test requires its external service) |
| Ruff over backend, ML, and tests | Passed |
| mypy over `backend/app` | Passed; 52 source files checked |
| Python `compileall` over backend, ML, tests, and scripts | Passed |
| Learning-quality regression benchmark | Passed; mapping F1, ranking NDCG, and historical-ranking NDCG each scored 1.0 against the configured 0.80 minimum |
| Python dependency audit | Passed; no known vulnerabilities across backend, OCR, storage, and ML requirement sets after remediation |
| npm dependency audit | Passed; zero vulnerabilities after updating Playwright |
| Frontend production build and bundle check | Passed; 22 JavaScript assets within configured bundle budget |
| Frontend Playwright browser acceptance | All four tests reported passing with patched Playwright 1.64.1; the local runner did not exit after reporting results, and local Node 24.11.1 is below the declared minimum, so the pinned-toolchain CI run remains authoritative |
| Native scoring-engine test | Passed with g++ C++17, `-Wall -Wextra -Werror` |
| Function-comment coverage | Passed; enforced by `scripts/verify_release.py` |
| Independent dependency/image audit and Compose staging checks | Defined in release workflow; not run locally in this environment |
| External RVCE academic, legal/privacy, security, accessibility, and production release approval | Pending; tracked in `remaining-targets.md` |

The **Release gates** workflow installs pinned dependencies and runs backend, ML, RVCE data-validation, release, frontend, C++, and Compose runtime/restore checks. The local outcomes above are developer-environment evidence; the workflow run and its artifacts must be attached to the release record before approval.

## 9. Acceptance gaps and release limits

The repository implementation is not equivalent to an academically accepted RVCE catalog or production release. Required acceptance work is:

- Select the target admission cohort, branch, and scheme scope.
- Have an RVCE academic owner review all applicable rows, reconcile the two quarantined title conflicts, verify credit interpretation/totals, and map first-year rows to every applicable branch.
- Confirm complete syllabus coverage for the selected scope. The current eight-file set covers selected first-year, Aerospace, AI & ML, Biotechnology, and Civil documents; it is not a full institutional catalog.
- Supply an authorized, licensed, reviewed historical exam corpus and record evaluation results against it.
- Complete independent security acceptance, privacy/legal approval, deployed staging performance evidence, and manual accessibility/release-owner acceptance as recorded in ILR-REQ-001 and the release-control documents.

No production approval is granted by this implementation record.
