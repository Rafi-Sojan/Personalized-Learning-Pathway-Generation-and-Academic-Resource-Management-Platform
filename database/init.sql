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

CREATE TABLE IF NOT EXISTS resources (
  id TEXT PRIMARY KEY,
  concept_id TEXT REFERENCES concepts(id),
  title TEXT NOT NULL,
  kind TEXT NOT NULL,
  url TEXT NOT NULL,
  duration_minutes INTEGER NOT NULL DEFAULT 0
);
