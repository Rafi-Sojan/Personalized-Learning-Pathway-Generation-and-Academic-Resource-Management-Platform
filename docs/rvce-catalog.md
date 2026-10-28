# RVCE Syllabus Catalog Specification

**Document ID:** ILR-RVCE-001  
**Version:** 1.0  
**Status:** Catalog metadata implemented; course-row ingestion pending  
**Last reviewed:** 2026-10-28

## 1. Authority

The catalog uses the official [RVCE scheme and syllabus page](https://rvce.edu.in/rvce-scheme-syllabus) as its source index. The source page publishes undergraduate scheme/syllabus links by program, academic year, and semester range. The repository manifest is metadata and provenance; it is not a substitute for the approved syllabus PDFs.

## 2. Implemented controls

- `database/rvce_catalog.json` records RVCE identity, source URL, access date, normalized program codes, scheme years, aliases, semester coverage, and document status.
- `ml/preprocessing/rvce_catalog.py` validates provenance, unique program codes, scheme coverage, and document source metadata.
- `GET /api/v1/catalog/rvce` exposes the validated catalog manifest for the frontend and import tooling.
- `GET /api/v1/catalog/rvce/courses` exposes only `academic_verified` course rows; instructors and administrators can add source-backed records through `POST /api/v1/catalog/rvce/courses`.
- ET/TE is represented as one normalized application code with the source variation retained as an alias; no subject data is inferred from that normalization.
- `database/rvce-course-record.schema.json` defines the source-backed course-row contract.
- `scripts/validate_rvce_courses.py` rejects unknown programs, unsupported schemes, duplicate course identities, invalid credits, missing SHA-256 source checksums, and unverified status values.

## 3. Course-row import contract

Each approved syllabus document must be imported with institution, program code, scheme year, semester, course code, title, credits, category, contact hours, prerequisites, outcomes, source URL, source checksum, and verification status. Rows without source-page evidence remain `pending_review` and must not drive a production roadmap.

## 4. Required RVCE data handoff

To complete the content layer, the project owner must select the target admission cohort, branch/program, and scheme. The corresponding official syllabus documents and approved historical question papers must then be supplied or downloaded through an authorized process. `database/rvce_courses.json` is intentionally an empty, validated handoff file until those source-backed rows are approved.

## 5. Acceptance criteria

The RVCE content release requires 100% source coverage for the selected program/semester scope, duplicate-course review, credit-total reconciliation against the approved scheme, prerequisite review by an academic owner, and benchmark evaluation using a separate reviewed question-paper set.
