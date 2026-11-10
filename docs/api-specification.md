# API Specification

**Document ID:** ILR-API-001
**Version:** 3.1
**Status:** Implementation-complete development baseline
**Last reviewed:** 2026-11-10

## 1. Contract conventions

Base path: `/api/v1`
Content type: `application/json` unless an upload endpoint is explicitly multipart.
Authentication: `Authorization: Bearer <access-token>` for private operations.

Successful responses use the route-specific JSON schema. Validation and authorization failures use FastAPI error responses. Clients must not depend on database identifiers being sequential.

## 2. Endpoint inventory

| Method | Path | Auth | Purpose |
|---|---|---:|---|
| POST | `/auth/register` | No | Register a student |
| POST | `/auth/login` | No | Issue a signed access token |
| GET | `/auth/me` | Yes | Read the authenticated user |
| POST | `/auth/logout` | Yes | Revoke all issued tokens for the authenticated user |
| GET | `/auth/export` | Yes | Export the authenticated user's profile, owned academic provenance, learning records, plans/revisions, review records, and audit events |
| POST | `/auth/delete` | Yes | Permanently delete the authenticated user's dependent database rows and private files after email confirmation |
| GET | `/courses` | Yes | List owned subject workspaces with academic scope, origin, mapped-topic count, and latest syllabus status |
| POST | `/courses` | Yes | Create a personal subject workspace in an optional validated RVCE branch/scheme/semester scope |
| GET | `/concepts?course_id={id}&syllabus_only={bool}` | Yes | List owned concepts, hierarchy, review state, and prerequisites; syllabus-only output omits rejected current topics |
| POST | `/syllabus/analyze` | Yes | Extract bounded topic names, unit/page metadata, and an optional reviewable course-planning profile |
| GET | `/syllabus/sources?course_id={id}` | Yes | List stored syllabus PDF copies for an owned course |
| POST | `/syllabus/sources/upload?course_id={id}` | Yes, multipart | Store a private syllabus PDF copy |
| POST | `/syllabus/sources/{id}/process` | Yes | Extract bounded text from a stored syllabus PDF |
| POST | `/syllabus/sources/{id}/generate-map` | Yes | Create or reuse pending-review concepts with syllabus-version, hierarchy, unit, and source-page provenance; reject a multi-course source that lacks the selected course code |
| GET | `/syllabus/profile?course_id={id}` | Yes | Read the newest extracted course-planning profile, issues, review state, and notes |
| POST | `/syllabus/profile/{version_id}/review` | Yes | Verify, reject, or return a profile to review with bounded course-type, hour, and unit-scope corrections |
| GET | `/syllabus/records?course_id={id}` | Yes | List versioned source-backed syllabus records with confidence and review state |
| POST | `/syllabus/records/{id}/review?status=...` | Yes | Verify, reject, or return a parsed syllabus record to review |
| GET | `/roadmap?course_id={id}&days={n}` | Yes | Preview a feasible 60-minute-per-day schedule for the explicitly selected owned course; full estimates are split into daily segments and the final concept may be shown partially when preview capacity expires |
| GET | `/roadmap/active?course_id={id}` | Yes | Read the newest active owned plan and current session states, optionally including one owned course |
| POST | `/roadmap/generate` | Yes | Persist a reviewed, mode-aware course plan with typed sessions; requires a processed syllabus source and generated concept map |
| POST | `/roadmap/semester/generate` | Yes | Balance an explicit list of owned courses from one program/scheme/semester without inferring options |
| GET | `/roadmap/history` | Yes | List generated roadmap revisions |
| PATCH | `/roadmap/items/{id}` | Yes | Set an owned session to planned, completed, or skipped and optionally record mastery on completion |
| GET | `/resources` | Yes | Legacy resource listing retained for compatibility; not part of the learner workflow |
| POST | `/resources/upload`, `/resources/{id}/process` | Yes | Legacy generic PDF intake and processing retained for compatibility |
| GET/POST | `/resources/{id}/mappings` | Yes | Legacy mapping review retained for compatibility; not part of the learner workflow |
| GET/POST | `/progress` | Yes | Read/update private progress data; retained for API compatibility, not shown in current learner UI |
| GET | `/quizzes/{concept_id}` | Yes | Get an owned concept quiz; retained for API compatibility |
| POST | `/quizzes/{concept_id}/attempts` | Yes | Submit a quiz attempt; retained for API compatibility |
| GET | `/rankings` | Yes | Read the authenticated learner's private aggregate mastery points without exposing other learners |
| GET | `/rankings/concepts` | Yes | Rank owned concepts using native scoring when configured |
| GET | `/metrics` | Optional bearer token | Prometheus-compatible request/status counters; set `METRICS_AUTH_TOKEN` and restrict deployment access |
| GET | `/exams/questions` | Yes | Search course question records by year, prompt, topic, assessment type, and format |
| POST | `/exams/questions/{id}/review?status=...` | Yes | Verify, reject, or return an imported question to review; optionally set a verified `concept_id` or use `clear_concept=true` |
| POST | `/exams/questions` | Instructor/admin | Create one historical exam question record |
| POST | `/exams/import` | Yes, owned course | Import numbered text with structural section/assessment detection, course-code validation, and versioned reviewable matcher evidence |
| POST | `/concepts/{id}/prerequisites/{id}/review?status=...` | Yes | Review an explicit syllabus prerequisite suggestion with cycle validation |
| POST | `/exams/import-pdf?course_id={id}` | Yes, multipart, owned course | Retain one source PDF, exclude scheme/solution pages, parse structural assessment metadata, and validate any printed course code |
| GET | `/exams/papers/{resource_id}` | Yes, owned course | View a retained source paper PDF |
| GET | `/exams/frequency?course_id={id}` | Yes, owned course | Summarize verified current-syllabus-mapped main-question counts with source references; report unmapped main and quiz totals separately |
| GET | `/exams/rankings` | Yes | Rank concepts using verified historical-question frequency and any human-rated difficulty |
| GET/POST | `/admin/users` | Admin | List or create users with server-side roles |
| GET | `/admin/processing` | Admin | Read bounded document-worker queue counts and oldest active job |
| GET | `/catalog/rvce` | No | Read validated RVCE program, scheme, and source metadata |
| GET | `/catalog/rvce/courses` | No | List academically verified RVCE course records with program/scheme/semester filters |
| POST | `/catalog/rvce/courses` | Instructor/admin | Add a source-backed RVCE course record; only admins can mark it academically verified |
| POST | `/catalog/rvce/courses/import` | Admin | Bulk import up to 500 source-backed candidates as pending review |
| GET | `/catalog/rvce/courses/review` | Instructor/admin | List pending RVCE syllabus records for academic review |
| PATCH | `/catalog/rvce/courses/{id}/verification` | Admin | Approve, reject, or return a record to pending review |
| POST | `/catalog/rvce/enroll` | Authenticated user | Add academically verified semester subjects; topics are created only from a stored syllabus copy |

### 2.1 Subject-workspace contract

`POST /courses` accepts `code`, `title`, optional `description`, and an all-or-none academic scope of `program_code`, `scheme_year`, and `semester`. Program aliases are normalized through the controlled RVCE manifest. The scheme must be listed for the selected branch, or in the common first-year scheme list for semesters 1 and 2. Unsupported combinations return `422`; a duplicate code in the same owner/scope returns `409`.

The endpoint creates `origin=personal` and never creates or approves an `rvce_syllabus_courses` row. Course responses add `program_code`, `scheme_year`, `semester`, `origin`, optional `catalog_course_id`, `syllabus_source_count`, and latest `syllabus_status`. Existing unscoped courses remain readable for compatibility. `POST /catalog/rvce/enroll` is the separate path that materializes academically verified rows with `origin=rvce_catalog` and their source catalog identifier. If an exact personal branch/scheme/semester/course-code workspace already exists, enrollment links and promotes that workspace in place, preserving its private notes, syllabus copies, and derived data instead of creating a duplicate.

First-year records whose branch applicability has not been academically mapped use `program_code=BE-UNMAPPED`. They may be imported and reviewed, but the learner listing and enrollment operations only include the selected branch code. An administrator must include a valid `program_code` in the verification request to record the branch mapping and approve such a row; approval without that mapping returns `422`.

## 3. Authorization rules

The authenticated user ID is obtained from the verified token and applied server-side to private queries and mutations. A client-supplied owner, user ID, or role must not widen access. Public resource visibility is the only intentional exception to owner filtering. Instructor and administrator operations use server-side role dependencies.

## 4. Resource processing contract

Upload requests must identify a PDF and remain below the configured size limit. The server generates the storage filename, records a checksum, and writes extracted text to private processed storage. Processing moves through `uploaded`, `queued`, `processing`, `retryable`, `processed`, or terminal `failed` states. The worker applies the configured attempt, delay, page, extracted-text, and lease-timeout limits; stale `processing` leases are recovered before the next polling cycle. `MAX_PDF_PAGES` defaults to 200 to cover the inventoried 126- and 152-page first-year syllabus books while retaining a finite processing boundary. Manual processing requests reset the retry state. Local background tasks remain available for development.

Syllabus copies use the private PDF lifecycle and are labeled `syllabus_pdf`. Extracted text retains page markers. Versioned records preserve source wording, normalized text, page, confidence, source resource, hierarchy, and review state. Every newly extracted record begins pending review. Labeled outcomes, labs, assessment policy, rubrics, references, and course metadata remain facts or non-topic content and do not become concept nodes. Combined scheme documents are scoped to the selected course code. Prerequisite suggestions are created only from explicit supported language and exact topic matches; they remain proposed until accepted, and acceptance checks for cycles.

### 4.1 Syllabus roadmap-profile contract

Map generation persists an extracted profile when source evidence is available. The profile records course-code aliases, classified course type, category, L:T:P credits, L/T/P/EL modality hours, ordered units with source page/hour/scope, outcomes, assessment components/format, CIE/SEE marks, and extraction issues. `GET /syllabus/profile` returns:

```json
{
  "available": true,
  "syllabus_version_id": "...",
  "status": "pending_review",
  "profile": {"course_type": "programming", "units": []},
  "review_notes": ""
}
```

The review request requires `status` (`verified`, `rejected`, or `pending_review`). Optional corrections are `course_type`, `lecture_hours`, `tutorial_hours`, `practical_hours`, `experiential_hours`, `unit_hours`, `unit_assessment_scopes`, and `review_notes`. Hour values are finite and bounded from 0 to 1000. Unit-hour and scope keys must reference an extracted unit label; scope values are `both`, `cie_only`, or `see_only`. Ownership is resolved through the syllabus version's course. Verification recalculates concept estimates; it does not approve the RVCE catalog row or silently resolve a source warning.

### 4.2 Roadmap generation contract

`POST /roadmap/generate` accepts `course_id`, optional `start_date`, required `target_date`, `daily_minutes`, `revision_minutes`, `mode`, and `unavailable_weekdays`. Dates are inclusive and cannot be in the past; weekdays use Python numbering Monday `0` through Sunday `6`. Modes are `full_term`, `cie`, `see`, and `revision`. A persisted plan must fit all included activity demand and reserved revision time. When an extracted profile exists, it must be verified. Compatibility data with no extracted profile uses the generic activity fallback.

`POST /roadmap/semester/generate` uses the same date/capacity fields and an explicit unique `course_ids` array of 1–16 owned courses. Every selected course must have a processed syllabus and verified current concepts. All courses must share non-null `program_code`, `scheme_year`, and `semester`; mixed or unscoped selections return `422`. The endpoint never chooses an elective or fills a semester automatically.

Responses persist `algorithm_version=rvce-activity-roadmap-v3` and contain plan scope/mode/dates, daily/revision minutes, unavailable weekdays, and typed items. Each item identifies its course, concept, activity, modality, unit, source page, assessment scope, syllabus version, evidence-question IDs, date, minutes, status, and explanation. Accepted prerequisites and source unit order are hard constraints. Verified Part B/main questions affect evidence priority; Part A/quiz IDs support retrieval activities. A reviewed CIE-only unit is omitted from SEE coverage and revision. `GET /roadmap/active` restores this contract after navigation; without `course_id` it returns the newest active plan or `null`, and with `course_id` it also matches semester plans containing that owned course.

`PATCH /roadmap/items/{id}` accepts `status` and optional `mastery_score` from 0–100. Mastery is valid only for `completed`. A concept is complete only after every session for that concept in the plan is complete; reopening or skipping a session recalculates progress and concept state. The update is owner-scoped through the parent plan.

Existing plans retain their stored algorithm version.

Historical-paper PDFs are retained as private `historical_exam_pdf` resources. The uploader supplies fallback assessment type, question format, and Part A quiz treatment. Strong printed CIE/SEE and Part headings override those fallbacks, while prompt wording is never used to infer assessment identity. Scheme, solution, answer-key, and model-answer page ranges are excluded. Imported question rows retain page, printed number, subpart, and marks where recognized and remain pending review. A printed course code that does not match the selected course causes a `422` response. Concept suggestions consider only verified concepts in the current syllabus version and are withheld when weak or ambiguous. Responses add `mapping_metadata`: decision status, matcher version, score margin, explanation, and bounded ranked candidates. `mapping_confidence` is a relevance score and may be present for an abstained row; it is not an approval or calibrated probability. Only verified, mapped main questions contribute to topic frequency and roadmap evidence. See `docs/syllabus-and-paper-ingestion.md` for workflow details and known extraction limits.

`GET /exams/frequency` returns `question_count`, `main_question_count`, `mapped_main_question_count`, `unmapped_main_question_count`, and `quiz_count` for the active filters. Each topic entry includes its concept ID/name, total and per-year counts, last-seen year, repeated-prompt count, documented marks, and supporting question/source coordinates. Unmapped verified rows are reported in the aggregate but never emitted as a synthetic topic. The question review endpoint accepts either `concept_id=<verified-current-syllabus-concept>` or `clear_concept=true`; a manual assignment records confidence `1.0` and `human-review` metadata.

If a PDF import fails or contains only duplicate questions, the newly written object and uncommitted resource row are removed. Account exports include source-backed syllabus records, historical questions and their matcher evidence, study-plan algorithm versions, plan items/revisions, mappings, and audit events. Account deletion removes those records in foreign-key-safe order, anonymizes any surviving review references to the deleted user, invalidates user caches, and then removes owned private objects.
## 5. Compatibility policy

Breaking changes to paths, authentication, required fields, response meanings, or ownership behavior require a versioned API change or migration notice. New optional fields should be additive. Route tests must be updated with every contract change.
