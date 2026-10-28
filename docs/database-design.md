# Database Design Specification

**Document ID:** ILR-DB-001
**Version:** 2.0
**Status:** Implementation-complete development baseline
**Last reviewed:** 2026-10-28

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

## 4. File data

Private uploads are stored under `storage/uploads` using generated UUID filenames. Metadata and checksums are stored in the database; extracted text is written to `storage/processed` after validated PDF processing. `processed_key` tracks the derived object when S3-compatible storage is enabled. These directories/buckets are not public frontend assets and must use encrypted, access-controlled storage in production.

## 5. Recovery requirements

Production must define database backup frequency, retention, encryption, restore testing, and recovery objectives. Redis data is non-authoritative and may be rebuilt; database and private file storage are authoritative and must be backed up consistently.
