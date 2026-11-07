# Database Design Specification

**Document ID:** ILR-DB-001
**Version:** 2.8
**Status:** Implementation-complete development baseline
**Last reviewed:** 2026-11-07

## 1. Authority and persistence

The relational contract is represented by SQLAlchemy models, the SQLite-compatible reference snapshot in `database/init.sql`, and Alembic migrations under `backend/migrations/versions`. Alembic is authoritative for deployed schema evolution. SQLite is used for zero-service development; PostgreSQL is the Compose and intended production database. SQLite connections explicitly enable foreign-key enforcement so local tests expose referential-integrity failures instead of masking them.

## 2. Ownership and relationships

Users own courses. A course may carry an RVCE `program_code`, `scheme_year`, and `semester`. `origin` distinguishes a learner-created personal workspace from a verified-catalog enrollment, and `catalog_course_id` links only the latter to its source-backed `rvce_syllabus_courses` row. Each course owns concepts, syllabus versions, and private source resources. `syllabus_records` retains per-version extracted topic/subtopic, unit-hour, outcome, laboratory, metadata, and assessment-policy text with source resource, page, confidence, and review status. Concepts retain parent-subtopic relationships and estimated minutes derived from unit hours when available. Accepted prerequisite edges constrain roadmaps; proposed source-backed edges require review and cycle validation. Progress, quiz attempts, historical papers, and study plans remain separate learner data. Historical exam questions retain source document/resource, page, year, part, question number/subpart, marks, declared assessment type/format, optional human-rated difficulty, concept-mapping relevance score, bounded versioned matcher metadata, and review state. Only verified mapped main questions contribute to historical rankings; learner quiz attempts never enter that evidence set. Audit events preserve security/product events until retention cleanup. Legacy resource-to-concept mapping tables remain for compatibility.

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
- A learner may have one subject code per branch/scheme/semester scope and one materialized course per verified catalog row. Personal workspaces do not satisfy or mutate academic catalog verification.
- Concepts with no `syllabus_version_id` are legacy or manually created records; syllabus maps, roadmap generation, and inferred past-paper attribution use only concepts with source syllabus provenance.
- Matcher metadata shall contain bounded decision evidence and candidate identifiers without duplicating question prompt text. It cannot bypass `pending_review` or create frequency evidence on its own.
- `BE-UNMAPPED` RVCE first-year rows are excluded from learner catalog and enrollment queries. An administrator must map the record to an RVCE program before approval; duplicate branch identities are rejected.
- Account deletion removes plan children, progress and attempts, historical questions, syllabus records, mappings, prerequisites, resources, concepts, syllabus versions, courses, audit actor rows, and the user in dependency-safe order. Surviving mapping reviews by the deleted user are anonymized.

## 4. RVCE syllabus records

`rvce_syllabus_courses` is the source-backed academic catalog table. It stores program and scheme identity, semester, course title/code, credit and contact-hour metadata, category, prerequisite/outcome JSON, source URL, source checksum, relative PDF filename, page number, verification state, and creation timestamp. Migrations `0007` and `0008` create and extend this catalog provenance. Migration `0009` adds syllabus provenance to concepts; `0010` adds question section fields; `0011_ingestion_provenance_review` adds versioned syllabus extraction records, subtopic parentage, unit-derived estimate fields, reviewable prerequisites, and historical question-paper provenance and review metadata. Migration `0012_course_academic_scope` adds course branch/scheme/semester scope, personal-versus-catalog origin, catalog provenance, indexes, and duplicate guards. Migration `0013_matcher_evidence` adds non-null `mapping_metadata_json` to historical questions with an empty-object default and no destructive backfill. See `docs/syllabus-and-paper-ingestion.md` for import and review rules.

## 5. File data

Private syllabus copies are stored under `storage/uploads` using generated server-side filenames. Metadata, checksums, and processing lifecycle fields are stored in `academic_resources`; extracted text is written to `storage/processed` after validated PDF processing. `processed_key` tracks the derived object when S3-compatible storage is enabled. Past-paper PDFs are size/page bounded, retained as private `historical_exam_pdf` resources, and served only to authorized course owners. Parsed question rows link back to the source resource and page. These directories/buckets are not public frontend assets and must use encrypted, access-controlled storage in production.

## 6. Recovery requirements

Production must define database backup frequency, retention, encryption, restore testing, and recovery objectives. Redis data is non-authoritative and may be rebuilt; database and private file storage are authoritative and must be backed up consistently.

The 2026-11-07 schema consistency check executed `database/init.sql` in an in-memory SQLite database and compared every table, column, and named index against SQLAlchemy metadata; all 16 modeled tables and 45 indexes matched. Migration `0013` passed fresh-database upgrade, downgrade, and re-upgrade checks on SQLite. An isolated copy of the root `0012` database retained all six historical-question rows and backfilled `{}` metadata. These checks do not replace the PostgreSQL migration gate in the candidate workflow.
