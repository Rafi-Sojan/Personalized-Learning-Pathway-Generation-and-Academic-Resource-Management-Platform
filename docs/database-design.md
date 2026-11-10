# Database Design Specification

**Document ID:** ILR-DB-001
**Version:** 2.9
**Status:** Implementation-complete development baseline
**Last reviewed:** 2026-11-10

## 1. Authority and persistence

The relational contract is represented by SQLAlchemy models, the SQLite-compatible reference snapshot in `database/init.sql`, and Alembic migrations under `backend/migrations/versions`. Alembic is authoritative for deployed schema evolution. SQLite is used for zero-service development; PostgreSQL is the Compose and intended production database. SQLite connections explicitly enable foreign-key enforcement so local tests expose referential-integrity failures instead of masking them.

## 2. Ownership and relationships

Users own courses. A course may carry an RVCE `program_code`, `scheme_year`, and `semester`. `origin` distinguishes a learner-created personal workspace from a verified-catalog enrollment, and `catalog_course_id` links only the latter to its source-backed `rvce_syllabus_courses` row. Each course owns concepts, syllabus versions, and private source resources. `syllabus_versions` stores the extracted planning profile JSON, review status, and reviewer notes. `syllabus_records` retains per-version extracted topic/subtopic, unit-hour, outcome, laboratory, metadata, and assessment-policy text with source resource, page, confidence, and review status. Concepts retain parent-subtopic relationships, source unit sequence, and reviewed workload estimates. Accepted prerequisite edges constrain roadmaps; proposed source-backed edges require review and cycle validation. Progress, quiz attempts, historical papers, and study plans remain separate learner data. Historical exam questions retain source document/resource, page, year, part, question number/subpart, marks, declared assessment type/format, optional human-rated difficulty, concept-mapping relevance score, bounded versioned matcher metadata, and review state. Only verified mapped main questions contribute to historical rankings; learner quiz attempts never enter that evidence set. Study plans can be course- or semester-scoped and retain mode, inclusive date range, daily capacity, revision allocation, unavailable weekdays as bounded JSON, academic scope, algorithm version, and status. Every study-plan item retains a non-null course, optional syllabus version, typed activity/modality, unit/page provenance, assessment scope, supporting question IDs, duration, order, status, and explanation. Audit events preserve security/product events until retention cleanup. Legacy resource-to-concept mapping tables remain for compatibility.

## 3. Integrity requirements

- Foreign keys shall preserve parent-child ownership relationships.
- Prerequisite mutations shall reject cycles before persistence.
- Unique constraints shall prevent duplicate identity and relationship records where defined by the model.
- Progress values shall be validated within their schema ranges.
- Stored filenames shall be generated identifiers, never raw client filenames.
- Schema changes shall be introduced through reviewed migrations rather than ad hoc production table creation.
- Roadmap regeneration shall supersede the prior active plan and create a revision snapshot.
- Every persisted roadmap item shall identify its course even when the parent plan is semester-scoped.
- Extracted course-planning metadata shall remain review-gated; profile verification is not RVCE catalog approval.
- A session mastery score shall be accepted only with an owned completed roadmap item.
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

`rvce_syllabus_courses` is the source-backed academic catalog table. It stores program and scheme identity, semester, course title/code, credit and contact-hour metadata, category, prerequisite/outcome JSON, source URL, source checksum, relative PDF filename, page number, verification state, and creation timestamp. Migrations `0007` and `0008` create and extend this catalog provenance. Migration `0009` adds syllabus provenance to concepts; `0010` adds question section fields; `0011_ingestion_provenance_review` adds versioned syllabus extraction records, subtopic parentage, unit-derived estimate fields, reviewable prerequisites, and historical question-paper provenance and review metadata. Migration `0012_course_academic_scope` adds course branch/scheme/semester scope, personal-versus-catalog origin, catalog provenance, indexes, and duplicate guards. Migration `0013_matcher_evidence` adds non-null `mapping_metadata_json` to historical questions with an empty-object default and no destructive backfill. Migration `0014_course_aware_roadmaps` adds reviewable syllabus planning profiles, concept unit sequence, course/semester plan scope and mode, restorable unavailable-weekday constraints, typed plan-item provenance/evidence, and profile/scope/item indexes. It backfills plan start dates from prior target dates and item course IDs from their concepts before enforcing non-null values. Its downgrade maps a semester plan to its first ordered item course so the older non-null course contract can be restored; a verified backup is mandatory before production downgrade. See `docs/syllabus-and-paper-ingestion.md` for import and review rules.

## 5. File data

Private syllabus copies are stored under `storage/uploads` using generated server-side filenames. Metadata, checksums, and processing lifecycle fields are stored in `academic_resources`; extracted text is written to `storage/processed` after validated PDF processing. `processed_key` tracks the derived object when S3-compatible storage is enabled. Past-paper PDFs are size/page bounded, retained as private `historical_exam_pdf` resources, and served only to authorized course owners. Parsed question rows link back to the source resource and page. These directories/buckets are not public frontend assets and must use encrypted, access-controlled storage in production.

## 6. Recovery requirements

Production must define database backup frequency, retention, encryption, restore testing, and recovery objectives. Redis data is non-authoritative and may be rebuilt; database and private file storage are authoritative and must be backed up consistently.

The 2026-11-07 schema consistency check covered the pre-roadmap-v3 16-table/45-index schema and migration `0013`. The 2026-11-10 reference snapshot retains 16 tables and declares 48 named indexes after `0014`. Python compilation and controlled-artifact verification passed locally; fresh upgrade, downgrade to `0013`, re-upgrade, model/snapshot comparison, and PostgreSQL application are CI/candidate gates and must not be recorded as passed until observed in a compatible dependency environment.
