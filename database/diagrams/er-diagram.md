# Logical Data Model

**Document ID:** ILR-DB-DIAG-001
**Version:** 1.3
**Status:** Development baseline
**Last reviewed:** 2026-11-10

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
  USERS ||--o{ STUDY_PLANS : owns
  COURSES o|--o{ STUDY_PLANS : course_scope
  STUDY_PLANS ||--o{ STUDY_PLAN_ITEMS : contains
  COURSES ||--o{ STUDY_PLAN_ITEMS : identifies_subject
  CONCEPTS ||--o{ STUDY_PLAN_ITEMS : schedules
  SYLLABUS_VERSIONS o|--o{ STUDY_PLAN_ITEMS : provides_source
```

`COURSES.origin` identifies `personal` or `rvce_catalog`. Only catalog-origin rows carry `catalog_course_id`; personal rows may still use the controlled RVCE branch, scheme, and semester fields as a private learning scope. A course-scoped plan has `course_id`; a semester plan leaves the parent course null and stores program/scheme/semester while every item retains a non-null course. `SYLLABUS_VERSIONS.roadmap_profile_json` is controlled by its profile review status and notes. `HISTORICAL_EXAM_QUESTIONS.mapping_metadata_json` retains bounded matcher evidence; review state remains the authority for downstream frequency and roadmap use.
