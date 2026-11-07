# Logical Data Model

**Document ID:** ILR-DB-DIAG-001
**Version:** 1.2
**Status:** Development baseline
**Last reviewed:** 2026-11-07

This diagram is a high-level relationship view. The SQLAlchemy models, `database/init.sql`, and Alembic migrations remain authoritative for columns, constraints, indexes, and migration history.

```mermaid
erDiagram
  USERS ||--o{ COURSES : owns
  RVCE_SYLLABUS_COURSES o|--o{ COURSES : verifies_origin
  COURSES ||--o{ CONCEPTS : contains
  COURSES ||--o{ ACADEMIC_RESOURCES : stores
  COURSES ||--o{ SYLLABUS_VERSIONS : versions
  SYLLABUS_VERSIONS ||--o{ SYLLABUS_RECORDS : extracts
  ACADEMIC_RESOURCES ||--o{ SYLLABUS_RECORDS : proves
  CONCEPTS ||--o{ TOPIC_PROGRESS : tracks
  USERS ||--o{ TOPIC_PROGRESS : records
  COURSES ||--o{ HISTORICAL_EXAM_QUESTIONS : archives
  COURSES ||--o{ STUDY_PLANS : schedules
```

`COURSES.origin` identifies `personal` or `rvce_catalog`. Only catalog-origin rows carry `catalog_course_id`; personal rows may still use the controlled RVCE branch, scheme, and semester fields as a private learning scope. `HISTORICAL_EXAM_QUESTIONS.mapping_metadata_json` retains the bounded matcher version, decision, margin, explanation, and candidate evidence; review state remains the authority for downstream frequency and roadmap use.
