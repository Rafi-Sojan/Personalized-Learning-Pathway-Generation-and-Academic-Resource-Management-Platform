# Database Design Specification

**Document ID:** ILR-DB-001
**Version:** 2.6
**Status:** Implementation-complete development baseline
**Last reviewed:** 2026-11-06

## 1. Authority and persistence

The relational contract is represented by SQLAlchemy models, the SQLite-compatible reference snapshot in `database/init.sql`, and Alembic migrations under `backend/migrations/versions`. Alembic is authoritative for deployed schema evolution. SQLite is used for zero-service development; PostgreSQL is the Compose and intended production database. SQLite connections explicitly enable foreign-key enforcement so local tests expose referential-integrity failures instead of masking them.

## 2. Ownership and relationships

Users own courses. Each course owns concepts, syllabus versions, and private source resources. `syllabus_records` retains per-version extracted topic/subtopic, unit-hour, outcome, laboratory, metadata, and assessment-policy text with source resource, page, confidence, and review status. Concepts retain parent-subtopic relationships and estimated minutes derived from unit hours when available. Accepted prerequisite edges constrain roadmaps; proposed source-backed edges require review and cycle validation. Progress, quiz attempts, historical papers, and study plans remain separate learner data. Historical exam questions retain source document/resource, page, year, part, question number/subpart, marks, declared assessment type/format, optional human-rated difficulty, concept mapping confidence, and review state. Only verified mapped main questions contribute to historical rankings; learner quiz attempts never enter that evidence set. Audit events preserve security/product events until retention cleanup. Legacy resource-to-concept mapping tables remain for compatibility.

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
- Concepts with no `syllabus_version_id` are legacy or manually created records; syllabus maps, roadmap generation, and inferred past-paper attribution use only concepts with source syllabus provenance.
- `BE-UNMAPPED` RVCE first-year rows are excluded from learner catalog and enrollment queries. An administrator must map the record to an RVCE program before approval; duplicate branch identities are rejected.
- Account deletion removes plan children, progress and attempts, historical questions, syllabus records, mappings, prerequisites, resources, concepts, syllabus versions, courses, audit actor rows, and the user in dependency-safe order. Surviving mapping reviews by the deleted user are anonymized.

## 4. RVCE syllabus records

`rvce_syllabus_courses` is the source-backed academic catalog table. It stores program and scheme identity, semester, course title/code, credit and contact-hour metadata, category, prerequisite/outcome JSON, source URL, source checksum, relative PDF filename, page number, verification state, and creation timestamp. Migrations `0007` and `0008` create and extend this catalog provenance. Migration `0009` adds syllabus provenance to concepts; `0010` adds question section fields; `0011_ingestion_provenance_review` adds versioned syllabus extraction records, subtopic parentage, unit-derived estimate fields, reviewable prerequisites, and historical question-paper provenance and review metadata. See `docs/syllabus-and-paper-ingestion.md` for import and review rules.

## 5. File data

Private syllabus copies are stored under `storage/uploads` using generated server-side filenames. Metadata, checksums, and processing lifecycle fields are stored in `academic_resources`; extracted text is written to `storage/processed` after validated PDF processing. `processed_key` tracks the derived object when S3-compatible storage is enabled. Past-paper PDFs are size/page bounded, retained as private `historical_exam_pdf` resources, and served only to authorized course owners. Parsed question rows link back to the source resource and page. These directories/buckets are not public frontend assets and must use encrypted, access-controlled storage in production.

## 6. Recovery requirements

Production must define database backup frequency, retention, encryption, restore testing, and recovery objectives. Redis data is non-authoritative and may be rebuilt; database and private file storage are authoritative and must be backed up consistently.

The 2026-11-06 schema consistency check executed `database/init.sql` in an in-memory SQLite database and compared every table and column against SQLAlchemy metadata; all 16 modeled tables matched. This check validates the reference snapshot only and does not replace Alembic upgrade testing on PostgreSQL.
