# Frontend Design Specification

**Document ID:** ILR-FE-001
**Version:** 2.7
**Status:** Implementation-complete development baseline
**Last reviewed:** 2026-11-10

## 1. Scope

The frontend is a React, Vite, and TypeScript single-page application for the RVCE syllabus workflow. Learners can create a private subject workspace under a controlled RVCE branch, scheme, and semester, optionally attach its syllabus in the same form, process the copy, inspect source-aware mapped topics, generate a study roadmap, and parse question papers to review topic frequency. The learner navigation contains Dashboard, My subjects, RVCE syllabus, Syllabus copies, Concept map, Study roadmap, Question frequency, and Account. Quizzes and progress tracking are not exposed in the learner UI; their backend endpoints and stored data remain for compatibility. Resource catalog management and AI-generated concept links are outside this release.

The shared API client converts FastAPI string and validation-array `detail` responses into readable UI messages. The production Nginx response policy supplies browser security headers; deployments using an API origin other than the documented same-host/localhost baseline must update `connect-src` with the approved API origin.

## 2. Structure

| Area | Location | Responsibility |
|---|---|---|
| Application shell | `frontend/src/App.tsx` | Routing, authenticated layout, and navigation |
| Pages | `frontend/src/pages/` | Route-level screens |
| Reusable UI | `frontend/src/components/` | Cards, lists, concept maps, roadmap items, and empty states |
| API clients | `frontend/src/services/` | Typed HTTP calls and token handling |
| Types | `frontend/src/types/` | Shared client-side contracts |
| Styling | `frontend/src/styles.css` | Global visual system and responsive layout |
| Async hook | `frontend/src/hooks/useAsync.ts` | Loading, error, and result state |

## 3. User journeys

1. A learner registers or signs in through `Login.tsx`.
2. The client stores the short-lived access token and sends it as a bearer token.
3. The dashboard summarizes live subject, syllabus-mapped topic, and roadmap counts.
4. In **My subjects**, the learner selects a manifest-backed RVCE branch, supported scheme, and semester, enters subject identity, and may attach a PDF immediately. The screen labels the result as personal unless it came from a verified catalog enrollment.
5. In **RVCE syllabus**, the learner sees the exact approved rows available in a selected scope before enrolling them. An empty approved scope links back to personal subject setup without implying verification.
6. The syllabus route accepts `course_id` in the URL, selects that owned subject, stores its syllabus PDF, and processes it into page-tagged text.
7. The learner generates source-aware concepts, reviews unit/page provenance in the map, and verifies the extracted course-planning profile. The profile panel exposes course type, L/T/P/EL hours, ordered units, CIE/SEE scope, source warnings, and review notes.
8. The learner generates a course plan or explicitly selects same-branch/scheme/semester subjects for a balanced semester plan. They choose full-term, CIE, SEE, or revision mode; date range; daily capacity; reserved revision time; and unavailable weekdays.
9. Typed roadmap cards show subject, activity, modality, unit, assessment scope, source page, evidence count, duration, status, and rationale. The newest active plan and unavailable-day constraints reload after navigation. The learner can complete a session and optionally submit a mastery score.
10. The learner uploads past-paper PDFs for parsing, searches question records, and filters subject/topic frequency by year. Part A is stored as quiz items; Part B is counted as main questions for topic-frequency analytics.
11. Administrators can provision users with server-enforced roles and review RVCE syllabus candidates with their source provenance. A first-year `BE-UNMAPPED` candidate requires an RVCE program mapping before approval.

## 4. Client behavior requirements

- The client shall not embed secrets or trust user-provided authorization claims.
- API failures shall be surfaced as recoverable UI errors rather than silently ignored.
- Authenticated routes shall redirect unauthenticated users to the login page.
- A `401` from a protected API call shall clear the stale local session and return the learner to sign-in; invalid login credentials remain visible on the login form.
- User-controlled text shall be rendered as text, not injected as HTML.
- API contract changes shall update the corresponding service and type definitions together.
- Loading and empty states shall be represented for screens that depend on remote data.
- Personal subject creation shall use catalogued branch and scheme values, surface partial syllabus-upload failures without losing the created subject, and never label the subject academically verified.
- Verified catalog enrollment shall be disabled when the selected scope contains no approved course rows.
- Dashboard counts shall be derived from authenticated API data; demo-only dates and activity values must not be presented as learner facts.
- Concept map entries shall show the syllabus unit and source page when available. Missing provenance is represented as unavailable and must not be fabricated.
- Roadmap generation shall use only syllabus-derived concepts and require a processed syllabus copy plus a generated concept map for the selected course.
- A persisted roadmap shall not use an available extracted planning profile until the learner verifies it; source warnings shall remain visible during review.
- Semester generation shall require explicit course selections from one branch, scheme, and semester. The client shall not infer electives or option groups.
- Roadmap controls shall expose mode, inclusive date range, daily capacity, revision minutes, and unavailable weekdays, and shall display infeasibility or profile-review errors returned by the API.
- Session controls shall support complete, skip, restore, and reopen states. Mastery shall be sent only with `completed`, and the UI shall explain that a concept closes only after all its sessions are complete.
- SEE views shall not display a reviewed CIE-only unit returned by the backend. The client shall display backend assessment scope and never infer exclusions from labels.
- Question-paper import shall accept bounded PDF files and associate extracted prompts with the selected course subject; topic frequency shall expose year counts and repeated prompt counts.
- AI-generated website links are not part of this release. Their provider, credentials, grounding, link validation, and review behavior require a later approved design.

## 5. Build and delivery

The production build is generated with `npm run build` and served from the frontend container. The Docker image uses a multi-stage Node build and a static web server runtime. CI performs dependency installation from `package-lock.json` and runs the production build.

Route-level lazy loading is implemented to reduce the initial bundle. The concept map and question-frequency page chunks should be monitored in production.

## 6. Accessibility and usability backlog

The baseline adds labeled navigation, icon-button names, semantic status/error announcements, account form labels, keyboard smoke coverage, and a CI Lighthouse accessibility audit. The release owner must review focus order, color contrast, responsive behavior, and screen-reader behavior on the deployed theme.
