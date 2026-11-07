-- SQLite-compatible reference snapshot of the current relational model.
-- Alembic under backend/migrations remains authoritative for every deployed database.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'student',
  token_version INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS rvce_syllabus_courses (
  id TEXT PRIMARY KEY,
  program_code TEXT NOT NULL,
  scheme_year INTEGER NOT NULL,
  semester INTEGER NOT NULL CHECK (semester BETWEEN 1 AND 8),
  course_code TEXT NOT NULL,
  title TEXT NOT NULL,
  credits REAL NOT NULL CHECK (credits > 0),
  category TEXT NOT NULL DEFAULT '',
  contact_hours REAL,
  prerequisites_json TEXT NOT NULL DEFAULT '[]',
  outcomes_json TEXT NOT NULL DEFAULT '[]',
  source_url TEXT NOT NULL,
  source_checksum TEXT NOT NULL,
  source_filename TEXT NOT NULL DEFAULT '',
  source_page INTEGER,
  verification_status TEXT NOT NULL DEFAULT 'pending_review',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (program_code, scheme_year, semester, course_code)
);

CREATE TABLE IF NOT EXISTS courses (
  id TEXT PRIMARY KEY,
  owner_id TEXT NOT NULL REFERENCES users(id),
  code TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  program_code TEXT,
  scheme_year INTEGER,
  semester INTEGER CHECK (semester BETWEEN 1 AND 8),
  origin TEXT NOT NULL DEFAULT 'personal',
  catalog_course_id TEXT REFERENCES rvce_syllabus_courses(id),
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (owner_id, program_code, scheme_year, semester, code),
  UNIQUE (owner_id, catalog_course_id)
);

-- These nullable provenance links form a cycle. SQLite permits forward
-- references; deployed PostgreSQL schemas are created in Alembic order.
CREATE TABLE IF NOT EXISTS academic_resources (
  id TEXT PRIMARY KEY,
  course_id TEXT REFERENCES courses(id),
  concept_id TEXT REFERENCES concepts(id),
  title TEXT NOT NULL,
  kind TEXT NOT NULL,
  url TEXT NOT NULL DEFAULT '',
  storage_key TEXT,
  processed_key TEXT,
  checksum TEXT,
  duration_minutes INTEGER NOT NULL DEFAULT 0,
  processing_status TEXT NOT NULL DEFAULT 'ready',
  processing_attempts INTEGER NOT NULL DEFAULT 0,
  processing_error TEXT,
  processing_started_at TIMESTAMP,
  processing_next_attempt_at TIMESTAMP,
  processed_at TIMESTAMP,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS syllabus_versions (
  id TEXT PRIMARY KEY,
  course_id TEXT NOT NULL REFERENCES courses(id),
  label TEXT NOT NULL,
  source_resource_id TEXT REFERENCES academic_resources(id),
  effective_from DATE,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS concepts (
  id TEXT PRIMARY KEY,
  course_id TEXT NOT NULL REFERENCES courses(id),
  name TEXT NOT NULL,
  difficulty INTEGER NOT NULL DEFAULT 1 CHECK (difficulty BETWEEN 1 AND 5),
  status TEXT NOT NULL DEFAULT 'not_started',
  unit_label TEXT,
  source_page INTEGER,
  syllabus_version_id TEXT REFERENCES syllabus_versions(id),
  parent_concept_id TEXT REFERENCES concepts(id),
  estimated_minutes INTEGER
);

CREATE TABLE IF NOT EXISTS concept_prerequisites (
  concept_id TEXT NOT NULL REFERENCES concepts(id),
  prerequisite_id TEXT NOT NULL REFERENCES concepts(id),
  status TEXT NOT NULL DEFAULT 'accepted',
  source_page INTEGER,
  confidence REAL,
  rationale TEXT NOT NULL DEFAULT '',
  PRIMARY KEY (concept_id, prerequisite_id)
);

CREATE TABLE IF NOT EXISTS syllabus_records (
  id TEXT PRIMARY KEY,
  syllabus_version_id TEXT NOT NULL REFERENCES syllabus_versions(id),
  source_resource_id TEXT NOT NULL REFERENCES academic_resources(id),
  course_id TEXT NOT NULL REFERENCES courses(id),
  record_type TEXT NOT NULL DEFAULT 'topic',
  source_page INTEGER,
  source_text TEXT NOT NULL,
  normalized_text TEXT NOT NULL,
  unit_label TEXT,
  parent_label TEXT,
  hours REAL,
  confidence REAL NOT NULL DEFAULT 0.5,
  review_status TEXT NOT NULL DEFAULT 'pending_review',
  mapped_concept_id TEXT REFERENCES concepts(id)
);

CREATE TABLE IF NOT EXISTS resource_concept_mappings (
  id TEXT PRIMARY KEY,
  resource_id TEXT NOT NULL REFERENCES academic_resources(id),
  concept_id TEXT NOT NULL REFERENCES concepts(id),
  confidence REAL,
  status TEXT NOT NULL DEFAULT 'proposed',
  source TEXT NOT NULL DEFAULT 'manual',
  reviewed_by TEXT REFERENCES users(id),
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (resource_id, concept_id)
);

CREATE TABLE IF NOT EXISTS historical_exam_questions (
  id TEXT PRIMARY KEY,
  course_id TEXT NOT NULL REFERENCES courses(id),
  source TEXT NOT NULL,
  source_document TEXT NOT NULL DEFAULT '',
  source_resource_id TEXT REFERENCES academic_resources(id),
  exam_year INTEGER NOT NULL,
  prompt TEXT NOT NULL,
  concept_id TEXT REFERENCES concepts(id),
  topic_label TEXT NOT NULL DEFAULT 'general',
  difficulty INTEGER,
  paper_part TEXT,
  question_kind TEXT NOT NULL DEFAULT 'main',
  question_number TEXT,
  subpart TEXT,
  marks REAL,
  source_page INTEGER,
  assessment_type TEXT NOT NULL DEFAULT 'unknown',
  question_format TEXT NOT NULL DEFAULT 'unknown',
  mapping_confidence REAL,
  review_status TEXT NOT NULL DEFAULT 'pending_review',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_events (
  id TEXT PRIMARY KEY,
  actor_id TEXT REFERENCES users(id),
  event_type TEXT NOT NULL,
  request_id TEXT,
  metadata_json TEXT NOT NULL DEFAULT '{}',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS topic_progress (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(id),
  concept_id TEXT NOT NULL REFERENCES concepts(id),
  completed BOOLEAN NOT NULL DEFAULT FALSE,
  score REAL,
  last_studied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (user_id, concept_id)
);

CREATE TABLE IF NOT EXISTS quiz_attempts (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(id),
  concept_id TEXT NOT NULL REFERENCES concepts(id),
  answer_index INTEGER NOT NULL,
  correct BOOLEAN NOT NULL,
  score REAL NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS study_plans (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(id),
  course_id TEXT NOT NULL REFERENCES courses(id),
  target_date DATE NOT NULL,
  daily_minutes INTEGER NOT NULL,
  algorithm_version TEXT NOT NULL DEFAULT 'heuristic-v1',
  status TEXT NOT NULL DEFAULT 'active',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS study_plan_items (
  id TEXT PRIMARY KEY,
  plan_id TEXT NOT NULL REFERENCES study_plans(id),
  concept_id TEXT NOT NULL REFERENCES concepts(id),
  scheduled_date DATE NOT NULL,
  minutes INTEGER NOT NULL,
  sequence INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'planned',
  explanation TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS study_plan_revisions (
  id TEXT PRIMARY KEY,
  plan_id TEXT NOT NULL REFERENCES study_plans(id),
  revision_number INTEGER NOT NULL,
  event TEXT NOT NULL DEFAULT 'generated',
  snapshot TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users(email);
CREATE INDEX IF NOT EXISTS ix_courses_owner_id ON courses(owner_id);
CREATE INDEX IF NOT EXISTS ix_courses_code ON courses(code);
CREATE INDEX IF NOT EXISTS ix_courses_program_code ON courses(program_code);
CREATE INDEX IF NOT EXISTS ix_courses_origin ON courses(origin);
CREATE INDEX IF NOT EXISTS ix_courses_catalog_course_id ON courses(catalog_course_id);
CREATE INDEX IF NOT EXISTS ix_rvce_syllabus_courses_program_code ON rvce_syllabus_courses(program_code);
CREATE INDEX IF NOT EXISTS ix_rvce_syllabus_courses_scheme_year ON rvce_syllabus_courses(scheme_year);
CREATE INDEX IF NOT EXISTS ix_rvce_syllabus_courses_semester ON rvce_syllabus_courses(semester);
CREATE INDEX IF NOT EXISTS ix_rvce_syllabus_courses_course_code ON rvce_syllabus_courses(course_code);
CREATE INDEX IF NOT EXISTS ix_rvce_syllabus_courses_verification_status ON rvce_syllabus_courses(verification_status);
CREATE INDEX IF NOT EXISTS ix_concepts_course_id ON concepts(course_id);
CREATE INDEX IF NOT EXISTS ix_concepts_syllabus_version_id ON concepts(syllabus_version_id);
CREATE INDEX IF NOT EXISTS ix_concepts_parent_concept_id ON concepts(parent_concept_id);
CREATE INDEX IF NOT EXISTS ix_concept_prerequisites_status ON concept_prerequisites(status);
CREATE INDEX IF NOT EXISTS ix_academic_resources_course_id ON academic_resources(course_id);
CREATE INDEX IF NOT EXISTS ix_academic_resources_concept_id ON academic_resources(concept_id);
CREATE INDEX IF NOT EXISTS ix_syllabus_versions_course_id ON syllabus_versions(course_id);
CREATE INDEX IF NOT EXISTS ix_syllabus_records_course_id ON syllabus_records(course_id);
CREATE INDEX IF NOT EXISTS ix_syllabus_records_syllabus_version_id ON syllabus_records(syllabus_version_id);
CREATE INDEX IF NOT EXISTS ix_syllabus_records_source_resource_id ON syllabus_records(source_resource_id);
CREATE INDEX IF NOT EXISTS ix_syllabus_records_record_type ON syllabus_records(record_type);
CREATE INDEX IF NOT EXISTS ix_syllabus_records_review_status ON syllabus_records(review_status);
CREATE INDEX IF NOT EXISTS ix_syllabus_records_mapped_concept_id ON syllabus_records(mapped_concept_id);
CREATE INDEX IF NOT EXISTS ix_historical_exam_questions_course_id ON historical_exam_questions(course_id);
CREATE INDEX IF NOT EXISTS ix_historical_exam_questions_exam_year ON historical_exam_questions(exam_year);
CREATE INDEX IF NOT EXISTS ix_historical_exam_questions_concept_id ON historical_exam_questions(concept_id);
CREATE INDEX IF NOT EXISTS ix_historical_exam_questions_source_resource_id ON historical_exam_questions(source_resource_id);
CREATE INDEX IF NOT EXISTS ix_historical_exam_questions_question_kind ON historical_exam_questions(question_kind);
CREATE INDEX IF NOT EXISTS ix_historical_exam_questions_assessment_type ON historical_exam_questions(assessment_type);
CREATE INDEX IF NOT EXISTS ix_historical_exam_questions_review_status ON historical_exam_questions(review_status);
CREATE INDEX IF NOT EXISTS ix_resource_concept_mappings_resource_id ON resource_concept_mappings(resource_id);
CREATE INDEX IF NOT EXISTS ix_resource_concept_mappings_concept_id ON resource_concept_mappings(concept_id);
CREATE INDEX IF NOT EXISTS ix_topic_progress_user_id ON topic_progress(user_id);
CREATE INDEX IF NOT EXISTS ix_topic_progress_concept_id ON topic_progress(concept_id);
CREATE INDEX IF NOT EXISTS ix_quiz_attempts_user_id ON quiz_attempts(user_id);
CREATE INDEX IF NOT EXISTS ix_quiz_attempts_concept_id ON quiz_attempts(concept_id);
CREATE INDEX IF NOT EXISTS ix_study_plans_user_id ON study_plans(user_id);
CREATE INDEX IF NOT EXISTS ix_study_plans_course_id ON study_plans(course_id);
CREATE INDEX IF NOT EXISTS ix_study_plan_items_plan_id ON study_plan_items(plan_id);
CREATE INDEX IF NOT EXISTS ix_study_plan_items_concept_id ON study_plan_items(concept_id);
CREATE INDEX IF NOT EXISTS ix_study_plan_revisions_plan_id ON study_plan_revisions(plan_id);
CREATE INDEX IF NOT EXISTS ix_audit_events_actor_id ON audit_events(actor_id);
CREATE INDEX IF NOT EXISTS ix_audit_events_event_type ON audit_events(event_type);
CREATE INDEX IF NOT EXISTS ix_audit_events_created_at ON audit_events(created_at);
