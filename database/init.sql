-- Reference bootstrap schema. Alembic under backend/migrations is authoritative for deployed databases.

CREATE TABLE IF NOT EXISTS courses (
  id TEXT PRIMARY KEY,
  code TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS concepts (
  id TEXT PRIMARY KEY,
  course_id TEXT NOT NULL REFERENCES courses(id),
  name TEXT NOT NULL,
  difficulty INTEGER NOT NULL CHECK (difficulty BETWEEN 1 AND 5),
  status TEXT NOT NULL DEFAULT 'not_started'
);

CREATE TABLE IF NOT EXISTS concept_prerequisites (
  concept_id TEXT NOT NULL REFERENCES concepts(id),
  prerequisite_id TEXT NOT NULL REFERENCES concepts(id),
  PRIMARY KEY (concept_id, prerequisite_id)
);

CREATE TABLE IF NOT EXISTS resources (
  id TEXT PRIMARY KEY,
  concept_id TEXT REFERENCES concepts(id),
  title TEXT NOT NULL,
  kind TEXT NOT NULL,
  url TEXT NOT NULL,
  duration_minutes INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS syllabus_versions (
  id TEXT PRIMARY KEY,
  course_id TEXT NOT NULL REFERENCES courses(id),
  label TEXT NOT NULL,
  source_resource_id TEXT REFERENCES resources(id),
  effective_from DATE,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'student',
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

CREATE TABLE IF NOT EXISTS quiz_attempts (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(id),
  concept_id TEXT NOT NULL REFERENCES concepts(id),
  answer_index INTEGER NOT NULL,
  correct BOOLEAN NOT NULL,
  score REAL NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS historical_exam_questions (
  id TEXT PRIMARY KEY,
  course_id TEXT NOT NULL REFERENCES courses(id),
  source TEXT NOT NULL,
  exam_year INTEGER NOT NULL,
  prompt TEXT NOT NULL,
  concept_id TEXT REFERENCES concepts(id),
  topic_label TEXT NOT NULL DEFAULT 'general',
  difficulty INTEGER NOT NULL DEFAULT 1,
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
