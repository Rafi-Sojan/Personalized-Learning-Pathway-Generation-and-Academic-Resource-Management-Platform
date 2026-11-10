# RVCE Syllabus Integration Implementation Record

**Document ID:** ILR-IMP-001  
**Version:** 1.8
**Status:** Implemented development workflow; academic acceptance pending  
**Owner:** Project maintainer  
**Last reviewed:** 2026-11-10
**Related records:** ILR-REQ-001, ILR-API-001, ILR-DB-001, ILR-FE-001, ILR-RVCE-001

## 1. Purpose and scope

This record describes the RVCE course-syllabus ingestion and learner onboarding slice: personal subject setup, source inventory, extraction, validation, database persistence, academic review, branch mapping, verified enrollment, CI gates, operating procedure, verification evidence, and outstanding acceptance work. It supplements the system architecture and API/database specifications; it does not claim that learner-created or extracted course records have received RVCE academic approval.

## 2. Delivery summary

The implementation includes guided creation of private branch/scheme/semester subject workspaces, optional immediate syllabus attachment, a SHA-256-verified PDF extraction utility, a source-backed candidate dataset, a conflict quarantine file, a provenance validator, administrator-only batch import, role-gated review and approval, first-year branch mapping, learner enrollment, a learner catalog screen, an administrator review interface, schema migrations, explainable concept matching, reviewed course workload profiles, course-type activity planning, explicit semester scheduling, and CI/release checks. Personal subjects carry `origin=personal`; verified enrollment carries `origin=rvce_catalog` and the source catalog identifier. Neither path creates placeholder concepts; topic records must be generated from a stored syllabus PDF. Stored syllabus parsing is course-scoped, source-identity-aware, and review-gated, while question-paper parsing excludes solution material and requires reviewed current-syllabus mappings before topic frequency is reported. Source unit order and accepted prerequisites are hard roadmap constraints. Part A evidence supports retrieval activities; verified Part B evidence drives main-question priority. Available extracted workload metadata must be verified before it controls persistence.

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
| `backend/migrations/versions/0013_matcher_evidence.py` | Adds durable bounded algorithm/version, decision, margin, explanation, and candidate metadata for historical-question mapping |
| `backend/migrations/versions/0014_course_aware_roadmaps.py` | Adds reviewable syllabus workload profiles, hard unit sequence, course/semester plan scope, typed sessions, source/assessment provenance, and question evidence IDs |

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
| `GET/POST /syllabus/profile...` | Authenticated course owner | Read and review extracted course type, workload, unit scope, source issues, and notes before roadmap persistence |
| `POST /roadmap/generate` | Authenticated course owner | Create a feasible typed course plan from verified current syllabus concepts and reviewed profile metadata |
| `POST /roadmap/semester/generate` | Authenticated course owner | Balance only explicitly selected same-program/scheme/semester subjects |
| `PATCH /roadmap/items/{id}` | Authenticated plan owner | Update session status and optional completion mastery with concept-state recalculation |

All import paths require source filename and page provenance. The backend compares the submitted source identity with `database/rvce_source_documents.json`; malformed or unknown provenance is rejected with `422`. Duplicate records return `409`. Unmapped first-year rows are not published or enrolled.

## 6. Persistence and migration behavior

`rvce_syllabus_courses` stores program, scheme, semester, course identity, title, credits, category, optional contact hours, JSON prerequisites/outcomes, source URL, SHA-256 checksum, source filename, source page, verification state, and creation time. The database enforces uniqueness across program, scheme year, semester, and course code. Learner `courses` store optional academic scope, origin, and optional catalog provenance; uniqueness guards duplicate personal scope identities and repeated materialization of one catalog row. Historical questions store bounded matcher evidence in `mapping_metadata_json`. Syllabus versions store bounded profile JSON/status/notes; concepts store source unit sequence; plan items always identify their course and retain activity, modality, source, scope, and evidence identifiers. Migration `0008_rvce_source_page` is guarded when adding columns to support databases where the columns may already exist. Migrations `0012`, `0013`, and `0014` preserve older records with bounded backfills. Apply migrations using the repository's normal Alembic upgrade procedure before deploying the API.

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
| `scripts/verify_release.py` | Passed 2026-11-07 after CI remediation; 65 controlled artifacts, 320 Python docstrings, 78 frontend function comments, two C++ declarations, pinned workflow actions, service-test path configuration, and the digest-pinned frontend runtime checked |
| Backend and ML test suites plus cross-module API tests | Passed 2026-11-07 after learning-engine v2; 55 passed, one PostgreSQL/Redis integration test skipped because services were not enabled |
| Ruff over backend, ML, tests, and `conftest.py` | Passed 2026-11-07 |
| mypy over `backend/app` | Passed 2026-11-07; 52 source files checked |
| Python `compileall` over backend, ML, tests, and scripts | Passed |
| Course-aware roadmap implementation check | 2026-11-10: Python compilation, `scripts/verify_release.py` (73 controlled artifacts, 393 Python docstrings, 91 frontend function comments, two C++ API comments), frontend production build with its 20-asset bundle budget, and the 16-table/48-index SQL bootstrap check passed; parser/profile and pure scheduler smoke checks produced the expected aliases, unit order, typed activity minutes, evidence split, and mastery factors |
| Expanded Python/API roadmap regressions | Added for profile review gating, workload anomalies, hard unit order, CIE/SEE exclusion, Part A/B evidence, typed activities, mastery/reopen behavior, semester balancing, and infeasibility; not executed locally because the available MSYS Python cannot install the pinned binary dependencies, so CI remains the authority |
| Migration `0014` lifecycle | Upgrade/downgrade/re-upgrade steps added to backend and release workflows; local execution pending a compatible SQLAlchemy/Alembic runtime and PostgreSQL candidate gate |
| Learning-quality regression benchmark | Passed; the computed eight-case matcher fixture scored 1.0 for precision, recall/F1, accuracy, abstention/status accuracy, and MRR with 0.625 coverage; mapping F1 and ranking NDCG metrics also passed. This is synthetic regression evidence only. |
| Python dependency audit | Previously passed after remediation; not rerun in the 2026-11-06 local pass |
| npm dependency audit | Previously passed after the Playwright update; not rerun in the 2026-11-06 local pass |
| Frontend production build and bundle check | Passed 2026-11-07; 20 JavaScript assets within the configured bundle budget |
| Backend service integration workflow | GitHub run `42335747397` failed because the integration step omitted `PYTHONPATH=backend`; the failure was reproduced locally as two `ModuleNotFoundError: app` errors, the workflow now supplies the path, and a service-backed CI rerun is pending |
| Frontend runtime image scan | GitHub run `42335747431` failed on `nginx:1.29.2-alpine`; local Trivy `0.76.2` reproduced 64 HIGH and three CRITICAL fixed findings, while the exact replacement `nginx:1.30.6-alpine` digest reported zero HIGH/CRITICAL fixed findings; CI rerun pending |
| Frontend Playwright browser acceptance | Seven scenarios reported `ok` on 2026-11-07, including login redirect and branch-scoped subject creation; the below-policy Node 24.11.1/npm 11.6.2 full runner required termination after reporting. The targeted subject scenario exited cleanly, targeted login reported `ok`, and an isolated live walkthrough completed; pinned CI remains clean-exit authority |
| Native scoring-engine test | Passed 2026-11-06 with g++ C++17, `-Wall -Wextra -Werror` |
| SQL reference and migration consistency | `database/init.sql` matched all columns and named indexes in the 16-table/45-index model. Migration `0013` passed fresh SQLite upgrade, downgrade to `0012`, re-upgrade, and an isolated legacy-copy check that retained all six historical-question rows with `{}` metadata; PostgreSQL candidate verification remains a release gate. |
| Root local database migration | Backed up as `learning.db.before-0012.bak`, upgraded from `0011` to head `0012`, and verified with the existing course preserved as personal origin |
| Root database state after learning-engine v2 | Upgraded from `0012` to `0013_matcher_evidence` before the 2026-11-07 local API run; all six historical-question rows were retained with non-null matcher metadata. Staging and production databases still require their own controlled migration. |
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
