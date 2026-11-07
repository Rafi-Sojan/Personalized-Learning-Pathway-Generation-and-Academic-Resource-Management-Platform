# RVCE Syllabus Catalog Specification

**Document ID:** ILR-RVCE-001  
**Version:** 1.2
**Status:** PDF candidates extracted; academic verification pending
**Last reviewed:** 2026-11-07

## 1. Authority

The catalog uses the official [RVCE scheme and syllabus page](https://rvce.edu.in/rvce-scheme-syllabus) as its source index. The source page publishes undergraduate scheme/syllabus links by program, academic year, and semester range. The repository manifest records metadata and provenance. Course candidates were extracted from all eight supplied PDFs; they have not been academically approved.

## 2. Implemented controls

- `database/rvce_catalog.json` records RVCE identity, source URL, access date, normalized program codes, scheme years, aliases, semester coverage, and document status.
- `database/rvce_source_documents.json` records the eight supplied PDFs with page counts and SHA-256 fingerprints so imported records can be traced to unchanged source files.
- `database/rvce_course_candidates.json` contains extracted, pending-review detail-page rows. Duplicate code identities with conflicting titles are excluded into `database/rvce_course_conflicts.json` for academic reconciliation.
- `ml/preprocessing/rvce_catalog.py` validates provenance, unique program codes, scheme coverage, and document source metadata.
- `GET /api/v1/catalog/rvce` exposes the validated catalog manifest for the frontend and import tooling.
- `GET /api/v1/catalog/rvce/courses` exposes only `academic_verified` course rows; instructors and administrators can add source-backed records through `POST /api/v1/catalog/rvce/courses`.
- `GET /api/v1/catalog/rvce/courses/review` lists pending candidates for instructors and admins; only admins can approve or reject them using `PATCH /api/v1/catalog/rvce/courses/{id}/verification`. An unresolved first-year row requires a valid `program_code` in the approval request, which records the branch mapping before publication.
- The administrator screen exposes the review queue with source provenance and requires a branch choice before approving a `BE-UNMAPPED` first-year record.
- Extracted candidates retain the supplied PDF's relative filename, page, SHA-256 checksum, and official RVCE source index. First-year records use `BE-UNMAPPED` until an academic reviewer reconciles branch applicability against the stream tables; they cannot be enrolled into a learner's branch-specific course list.
- `POST /api/v1/catalog/rvce/courses/import` accepts candidate batches of at most 500 and forces every record into `pending_review`; `PATCH` is required for admin approval.
- `scripts/import_rvce_candidates.py --token <admin-token>` submits the generated candidate file in bounded batches. Once approved, a learner can use `POST /api/v1/catalog/rvce/enroll` to materialize source-linked subject workspaces. Enrollment creates no placeholder concepts; concepts still require the learner's stored and processed syllabus copy.
- **My subjects** also permits a learner to create a private branch/scheme/semester workspace and attach a syllabus. That record has `origin=personal`, does not insert into this catalog, and must not be cited as academic verification. The branch and scheme choices still come from the controlled manifest.
- ET/TE is represented as one normalized application code with the source variation retained as an alias; no subject data is inferred from that normalization.
- `database/rvce-course-record.schema.json` defines the source-backed course-row contract.
- `scripts/validate_rvce_courses.py` rejects unknown programs, unsupported schemes, duplicate course identities, invalid credits, missing SHA-256 source checksums, and unverified status values.

## 3. Course-row import contract

Each approved syllabus document must be imported with institution, program code, scheme year, semester, course code, title, credits, category, contact hours, prerequisites, outcomes, source URL, source checksum, and verification status. Rows without source-page evidence remain `pending_review` and must not drive a production roadmap.

## 4. Required RVCE data handoff

To complete the content layer, the project owner must select the target admission cohort, branch/program, and scheme. The corresponding official syllabus documents and approved historical question papers must then be supplied or downloaded through an authorized process. `database/rvce_courses.json` is intentionally an empty, validated handoff file until those source-backed rows are approved. First-year candidates must additionally be mapped to applicable streams before publication.

## 5. Acceptance criteria

The current extraction produced 207 unique review candidates and quarantined two rows where the same program/scheme/semester/course code has different titles. The RVCE content release requires 100% source coverage for the selected program/semester scope, conflict resolution, duplicate-course review, credit-total reconciliation against the approved scheme, prerequisite review by an academic owner, and benchmark evaluation using a separate reviewed question-paper set.
