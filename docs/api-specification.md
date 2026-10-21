# API specification

Base URL: `/api/v1`

| Method | Path | Purpose |
|---|---|---|
| POST | `/auth/login` | Demo login/token |
| GET | `/courses` | List courses |
| GET | `/concepts` | List concepts, optionally by course |
| POST | `/syllabus/analyze` | Extract syllabus topics |
| GET | `/roadmap` | Generate a dated study plan |
| GET | `/resources` | List learning resources |
| GET/POST | `/progress` | Read or update progress |
| GET | `/quizzes/{concept_id}` | Get a concept quiz |
