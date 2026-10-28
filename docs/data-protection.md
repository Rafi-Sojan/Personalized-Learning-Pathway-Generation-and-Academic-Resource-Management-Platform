# Data Protection and Information Management

**Document ID:** ILR-DATA-001
**Version:** 2.0
**Status:** Implementation-complete development baseline
**Last reviewed:** 2026-10-28

## 1. Data inventory

| Data class | Examples | Required controls |
|---|---|---|
| Identity data | Email address, password hash, user ID | Argon2 hashing, access control, secret handling |
| Learning data | Course enrollment, concept status, quiz attempts, progress | User ownership checks, least privilege, retention policy |
| Academic content | Syllabus text, resource metadata, extracted PDF text | File validation, private storage, checksum, access control |
| Derived data | Roadmaps, rankings, concept matches, estimates | Versioning, explainability, regeneration semantics |
| Operational data | Logs, rate-limit counters, audit events | Redaction, restricted access, retention and deletion |
| Secrets | JWT key, database credentials, Redis credentials | Environment or secret manager only; never commit |

## 2. Ownership model

Users own their courses and associated concepts, resources, progress, and study plans. Public resources may be readable without ownership; private resources require an authenticated owner check. Administrative and instructor operations are enforced by server-side role dependencies; client claims never grant roles.

## 3. Storage rules

- Uploads use generated UUID filenames and are stored outside the public frontend directory.
- The database stores metadata and checksums; processed text is stored separately. `STORAGE_BACKEND=s3` enables an S3-compatible private bucket for uploads and processed output.
- `.env` files, local databases, uploads, processed files, caches, and build artifacts are excluded from version control.
- Production deployments must use encrypted storage and encrypted database connections where supported.

## 4. Retention and deletion

The API provides authenticated data export and email-confirmed account deletion. Account deletion removes owned database records, audit actor records, and associated private upload/processed files. Audit events have configurable retention through `AUDIT_RETENTION_DAYS` and `scripts/purge_audit_events.py`. Production operators must define retention periods for learning records, uploads, logs, and backups and verify deletion across backup/object-storage retention windows.

## 5. Privacy requirements

- Collect only data needed for the learning workflow.
- Do not place passwords, bearer tokens, full uploaded documents, or sensitive learner content in logs.
- Do not use learner data for model evaluation without a documented purpose and appropriate de-identification.
- Provide an export and deletion process before production launch if the system is used with real learner records.
