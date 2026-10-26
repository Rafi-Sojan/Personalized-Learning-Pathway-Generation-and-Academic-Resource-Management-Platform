# Data Protection and Information Management

**Document ID:** ILR-DATA-001
**Version:** 1.0
**Status:** Development baseline
**Last reviewed:** 2026-10-27

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

Users own their courses and associated concepts, resources, progress, and study plans. Public resources may be readable without ownership; private resources require an authenticated owner check. Administrative or instructor roles are not implemented in the current baseline and must not be simulated by client claims.

## 3. Storage rules

- Uploads use generated UUID filenames and are stored outside the public frontend directory.
- The database stores metadata and checksums; processed text is stored separately.
- `.env` files, local databases, uploads, processed files, caches, and build artifacts are excluded from version control.
- Production deployments must use encrypted storage and encrypted database connections where supported.

## 4. Retention and deletion

The API now provides authenticated data export and email-confirmed account deletion. Account deletion removes owned database records and associated private upload/processed files. Before production use, the owner must still define retention periods for accounts, learning records, uploaded resources, extracted text, logs, and backups, and verify deletion across backups and object storage.

## 5. Privacy requirements

- Collect only data needed for the learning workflow.
- Do not place passwords, bearer tokens, full uploaded documents, or sensitive learner content in logs.
- Do not use learner data for model evaluation without a documented purpose and appropriate de-identification.
- Provide an export and deletion process before production launch if the system is used with real learner records.
