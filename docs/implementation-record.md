# RVCE Syllabus Integration Implementation Record

**Document ID:** ILR-IMP-001  
**Version:** 1.5
**Status:** Implemented development workflow; academic acceptance pending  
**Owner:** Project maintainer  
**Last reviewed:** 2026-11-07
**Related records:** ILR-REQ-001, ILR-API-001, ILR-DB-001, ILR-FE-001, ILR-RVCE-001

## 1. Purpose and scope

This record describes the RVCE course-syllabus ingestion and learner onboarding slice: personal subject setup, source inventory, extraction, validation, database persistence, academic review, branch mapping, verified enrollment, CI gates, operating procedure, verification evidence, and outstanding acceptance work. It supplements the system architecture and API/database specifications; it does not claim that learner-created or extracted course records have received RVCE academic approval.

## 2. Delivery summary

The implementation includes guided creation of private branch/scheme/semester subject workspaces, optional immediate syllabus attachment, a SHA-256-verified PDF extraction utility, a source-backed candidate dataset, a conflict quarantine file, a provenance validator, administrator-only batch import, role-gated review and approval, first-year branch mapping, learner enrollment, a learner catalog screen, an administrator review interface, schema migration, and CI/release checks. Personal subjects carry `origin=personal`; verified enrollment carries `origin=rvce_catalog` and the source catalog identifier. Neither path creates placeholder concepts; topic records must be generated from a stored syllabus PDF. Stored syllabus parsing is course-scoped and review-gated, while question-paper parsing excludes solution material and requires reviewed current-syllabus mappings before topic frequency is reported.

The current source set contains eight inventoried PDFs. Extraction produced 207 non-conflicting candidate rows and quarantined two rows sharing a course identity but carrying different titles. Every candidate retains scheme, semester, course code, title, credit tuple total, source filename, source page, checksum, and source-index URL. Category and total contact hours are included when explicitly extractable. Unparsed outcomes and prerequisite relationships remain empty and must not be inferred from this dataset.

## 3. Controlled data artifacts

| Artifact | Purpose |
|---|---|
| `database/rvce_catalog.json` | Normalized RVCE programs, aliases, and supported scheme years |
| `database/rvce_source_documents.json` | Inventoried PDF paths, SHA-256 values, page counts, sizes, scope, and official source URL |
| `database/rvce_course_candidates.json` | Non-conflicting extracted records in `pending_review` status |
| `database/rvce_course_conflicts.json` | Quarantined same-identity records requiring academic reconciliation |
| `database/rvce-course-record.schema.json` | JSON Schema for the source-backed course record contract |
| `database/init.sql` | SQLite-compatible reference snapshot of all current model tables and columns; Alembic remains deployment authority |
| `backend/migrations/versions/0007_rvce_syllabus_courses.py` | Creates the syllabus record table |
| `backend/migrations/versions/0008_rvce_source_page.py` | Adds source filename and page provenance columns |
| `backend/migrations/versions/0009_concept_syllabus_provenance.py` | Adds syllabus-version, unit, and page provenance to mapped concepts |
| `backend/migrations/versions/0010_exam_question_sections.py` | Separates Part A quiz entries from Part B main questions in the paper archive |
| `backend/migrations/versions/0011_ingestion_provenance_review.py` | Adds versioned syllabus records, concept estimates/parentage, reviewable prerequisites, and historical-paper provenance/review metadata |
| `backend/migrations/versions/0012_course_academic_scope.py` | Adds learner-course branch/scheme/semester scope, personal/catalog origin, catalog provenance, indexes, and duplicate guards |

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
9. Learner catalog queries omit unresolved records. Enrollment only uses approved, branch-mapped rows and creates learner-owned course and syllabus-version records. Learners then attach the syllabus copy for concept generation.
10. Independently of catalog publication, a learner may create a personal subject workspace using only branch/scheme/semester values validated by the manifest and attach a private syllabus. This path does not create, approve, or mutate a catalog row.

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
| `POST /courses` | Authenticated user | Create a personal subject workspace under a manifest-validated branch/scheme/semester; never publish a catalog row |
| `GET /courses` | Authenticated user | Return owned subjects with academic scope, origin, mapped-topic count, and latest syllabus-copy status |
| `POST /syllabus/sources/upload?course_id=...` | Authenticated course owner | Store the optional first or subsequent private syllabus copy |

All import paths require source filename and page provenance. The backend compares the submitted source identity with `database/rvce_source_documents.json`; malformed or unknown provenance is rejected with `422`. Duplicate records return `409`. Unmapped first-year rows are not published or enrolled.

## 6. Persistence and migration behavior

`rvce_syllabus_courses` stores program, scheme, semester, course identity, title, credits, category, optional contact hours, JSON prerequisites/outcomes, source URL, SHA-256 checksum, source filename, source page, verification state, and creation time. The database enforces uniqueness across program, scheme year, semester, and course code. Learner `courses` store optional academic scope, origin, and optional catalog provenance; uniqueness guards duplicate personal scope identities and repeated materialization of one catalog row. Migration `0008_rvce_source_page` is guarded when adding columns to support databases where the columns may already exist. Migration `0012_course_academic_scope` similarly supports older databases and fresh metadata-bootstrap databases. Apply migrations using the repository's normal Alembic upgrade procedure before deploying the API.

The learner enrollment operation is idempotent for a learner and course scope: existing course records are returned as existing rather than duplicated. If the learner already created the exact scoped personal subject, verified enrollment links that workspace to the approved catalog row in place and retains its notes and learning data. Newly created or newly linked catalog courses receive a syllabus-version label when none exists, but no placeholder concept. Concepts and prerequisite proposals are created only from the learner's stored and processed syllabus copy.

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

### 7.4 Create a personal subject workspace

Open **My subjects**, select the RVCE branch, semester, and available scheme, and enter the subject code/title. A syllabus PDF may be attached in the same form; if the upload fails after subject creation, the UI retains and links to the created workspace so the learner can retry. The resulting personal label is intentional and must not be changed to verified unless the subject is materialized from an academically approved catalog row.

## 8. Verification record

The repository checks recorded for this implementation report are listed below. Rows dated 2026-11-07 were rerun against the current working tree; earlier point-in-time audit evidence must still be repeated by the Release gates workflow for a named candidate.

| Check | Result |
|---|---|
| PDF source fingerprint and candidate extraction | Passed; 207 candidates produced and two conflicting rows quarantined |
| `scripts/validate_rvce_courses.py` | Passed; 207 source-backed records |
| `scripts/verify_release.py` | Passed 2026-11-07; 62 controlled artifacts, 271 Python docstrings, 78 frontend function comments, two C++ declarations, and pinned workflow actions checked |
| Backend and ML test suites plus cross-module API tests | Passed 2026-11-07; 39 passed, one PostgreSQL/Redis integration test skipped because services were not enabled |
| Ruff over backend, ML, tests, and `conftest.py` | Passed 2026-11-07 |
| mypy over `backend/app` | Passed 2026-11-07; 52 source files checked |
| Python `compileall` over backend, ML, tests, and scripts | Passed |
| Learning-quality regression benchmark | Passed; mapping F1, ranking NDCG, and historical-ranking NDCG each scored 1.0 against the configured 0.80 minimum |
| Python dependency audit | Previously passed after remediation; not rerun in the 2026-11-06 local pass |
| npm dependency audit | Previously passed after the Playwright update; not rerun in the 2026-11-06 local pass |
| Frontend production build and bundle check | Passed 2026-11-07; 20 JavaScript assets within the configured bundle budget |
| Frontend Playwright browser acceptance | Seven scenarios reported `ok` on 2026-11-07, including login redirect and branch-scoped subject creation; the below-policy Node 24.11.1/npm 11.6.2 full runner required termination after reporting. The targeted subject scenario exited cleanly, targeted login reported `ok`, and an isolated live walkthrough completed; pinned CI remains clean-exit authority |
| Native scoring-engine test | Passed 2026-11-06 with g++ C++17, `-Wall -Wextra -Werror` |
| SQL reference and migration consistency | Passed 2026-11-07; all tables, columns, and 45 indexes across 16 SQLAlchemy models matched `database/init.sql`, and migration `0012` passed fresh, legacy, downgrade, and re-upgrade checks |
| Root local database migration | Backed up as `learning.db.before-0012.bak`, upgraded from `0011` to head `0012`, and verified with the existing course preserved as personal origin |
| Supplied question-paper parser check | Passed 2026-11-07 for declared course `21CS45`; 64 rows: 19 quiz, 45 main, 32 CIE/test, 32 SEE, zero scheme/solution contamination |
| Supplied AI syllabus parser check | Passed 2026-11-07 for `AI253IA`; 106 concepts: 19 roots and 87 children, zero outcome/lab/rubric/marks contamination |
| Function-comment coverage | Passed 2026-11-07; enforced by `scripts/verify_release.py` |
| Independent dependency/image audit and Compose staging checks | Defined in release workflow; not run locally in this environment |
| External RVCE academic, legal/privacy, security, accessibility, and production release approval | Pending; tracked in `remaining-targets.md` |

The **Release gates** workflow installs pinned dependencies and runs backend, ML, RVCE data-validation, release, frontend, C++, and Compose runtime/restore checks. The local outcomes above are developer-environment evidence; the workflow run and its artifacts must be attached to the release record before approval. The supplied question packet declares `21CS45`, while the checked syllabus section is `AI253IA`; the course-identity guard deliberately prevents cross-subject mapping. The supplied-document counts are parser conformance observations, not a claim that the documents are licensed for a production corpus or that an RVCE reviewer accepted every extracted row.

## 9. Acceptance gaps and release limits

The repository implementation is not equivalent to an academically accepted RVCE catalog or production release. Required acceptance work is:

- Select the target admission cohort, branch, and scheme scope.
- Have an RVCE academic owner review all applicable rows, reconcile the two quarantined title conflicts, verify credit interpretation/totals, and map first-year rows to every applicable branch.
- Confirm complete syllabus coverage for the selected scope. The current eight-file set covers selected first-year, Aerospace, AI & ML, Biotechnology, and Civil documents; it is not a full institutional catalog.
- Supply an authorized, licensed, reviewed historical exam corpus and record evaluation results against it.
- Complete independent security acceptance, privacy/legal approval, deployed staging performance evidence, and manual accessibility/release-owner acceptance as recorded in ILR-REQ-001 and the release-control documents.

No production approval is granted by this implementation record.
