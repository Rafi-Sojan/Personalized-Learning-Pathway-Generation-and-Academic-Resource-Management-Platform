# Database Design Specification

**Document ID:** ILR-DB-001
**Version:** 2.2
**Status:** Implementation-complete development baseline
**Last reviewed:** 2026-11-01

## 1. Authority and persistence

The relational contract is represented by SQLAlchemy models, `database/init.sql`, and the Alembic migration under `backend/migrations/versions`. Alembic is authoritative for deployed schema evolution. SQLite is used for zero-service development; PostgreSQL is the Compose and intended production database.

## 2. Ownership and relationships

Users own courses. Courses own concepts and resources. Prerequisite edges connect concepts within a course. Progress, quiz attempts, and study plans are scoped to users. Roadmap items are persisted derived data and can be regenerated from progress, availability, deadlines, and dependencies. Study plan revisions preserve generated snapshots, resource-concept mappings preserve review state, confidence, source, and reviewer, historical exam questions preserve source/year and concept evidence, and audit events preserve security/product events until retention cleanup.

## 3. Integrity requirements

- Foreign keys shall preserve parent-child ownership relationships.
- Prerequisite mutations shall reject cycles before persistence.
- Unique constraints shall prevent duplicate identity and relationship records where defined by the model.
- Progress values shall be validated within their schema ranges.
- Stored filenames shall be generated identifiers, never raw client filenames.
- Schema changes shall be introduced through reviewed migrations rather than ad hoc production table creation.
- Roadmap regeneration shall supersede the prior active plan and create a revision snapshot.
- Resource mappings shall be unique per resource/concept pair and use explicit proposed, accepted, or rejected states.
- Resource processing state shall record attempts, bounded error detail, active-start time, next retry time, and successful completion time so worker recovery is auditable.
- A worker lease that exceeds `DOCUMENT_WORKER_TIMEOUT_SECONDS` shall be reclaimed on the next worker polling cycle and recorded as retryable or terminal failure according to the attempt limit.
- RVCE syllabus identity is unique by program, scheme year, semester, and course code. Imported rows retain source PDF filename, page, SHA-256 checksum, and a pending, verified, or rejected review state.
- `BE-UNMAPPED` RVCE first-year rows are excluded from learner catalog and enrollment queries. An administrator must map the record to an RVCE program before approval; duplicate branch identities are rejected.

## 4. RVCE syllabus records

`rvce_syllabus_courses` is the source-backed syllabus table. It stores program and scheme identity, semester, course title/code, credit and contact-hour metadata, category, prerequisite/outcome JSON, source URL, source checksum, relative PDF filename, page number, verification state, and creation timestamp. Migration `0007_rvce_syllabus_courses.py` creates the table; `0008_rvce_source_page.py` adds source-page provenance. The source manifest and course-row schema are versioned under `database/`.

Import validation requires the file path and checksum to match the inventoried RVCE source manifest, the page to fall within the recorded PDF page count, and the source URL to equal the official RVCE syllabus index. Academic approval remains a human review action.

## 5. File data

Private uploads are stored under `storage/uploads` using generated UUID filenames. Metadata, checksums, and processing lifecycle fields are stored in `academic_resources`; extracted text is written to `storage/processed` after validated PDF processing. `processed_key` tracks the derived object when S3-compatible storage is enabled. These directories/buckets are not public frontend assets and must use encrypted, access-controlled storage in production.

## 6. Recovery requirements

Production must define database backup frequency, retention, encryption, restore testing, and recovery objectives. Redis data is non-authoritative and may be rebuilt; database and private file storage are authoritative and must be backed up consistently.
