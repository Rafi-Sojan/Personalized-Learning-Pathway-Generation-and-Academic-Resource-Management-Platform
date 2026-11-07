# Frontend Design Specification

**Document ID:** ILR-FE-001
**Version:** 2.5
**Status:** Implementation-complete development baseline
**Last reviewed:** 2026-11-06

## 1. Scope

The frontend is a React, Vite, and TypeScript single-page application for the RVCE syllabus workflow. Learners select an RVCE subject, upload and process a syllabus copy, inspect source-aware mapped topics, generate a study roadmap, and parse question papers to review topic frequency. The learner navigation contains Dashboard, My subjects, RVCE syllabus, Syllabus copies, Concept map, Study roadmap, Question frequency, and Account. Quizzes and progress tracking are not exposed in the learner UI; their backend endpoints and stored data remain for compatibility. Resource catalog management and AI-generated concept links are outside this release.

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
4. The learner stores a course syllabus PDF and processes it into page-tagged text.
5. The learner generates source-aware concepts and reviews unit/page provenance in the map.
6. The learner generates a dated roadmap from syllabus-derived concepts.
7. The learner uploads past-paper PDFs for parsing, searches question records, and filters subject/topic frequency by year. Part A is stored as quiz items; Part B is counted as main questions for topic-frequency analytics.
8. Administrators can provision users with server-enforced roles and review RVCE syllabus candidates with their source provenance. A first-year `BE-UNMAPPED` candidate requires an RVCE program mapping before approval.

## 4. Client behavior requirements

- The client shall not embed secrets or trust user-provided authorization claims.
- API failures shall be surfaced as recoverable UI errors rather than silently ignored.
- Authenticated routes shall redirect unauthenticated users to the login page.
- A `401` from a protected API call shall clear the stale local session and return the learner to sign-in; invalid login credentials remain visible on the login form.
- User-controlled text shall be rendered as text, not injected as HTML.
- API contract changes shall update the corresponding service and type definitions together.
- Loading and empty states shall be represented for screens that depend on remote data.
- Dashboard counts shall be derived from authenticated API data; demo-only dates and activity values must not be presented as learner facts.
- Concept map entries shall show the syllabus unit and source page when available. Missing provenance is represented as unavailable and must not be fabricated.
- Roadmap generation shall use only syllabus-derived concepts and require a processed syllabus copy plus a generated concept map for the selected course.
- Question-paper import shall accept bounded PDF files and associate extracted prompts with the selected course subject; topic frequency shall expose year counts and repeated prompt counts.
- AI-generated website links are not part of this release. Their provider, credentials, grounding, link validation, and review behavior require a later approved design.

## 5. Build and delivery

The production build is generated with `npm run build` and served from the frontend container. The Docker image uses a multi-stage Node build and a static web server runtime. CI performs dependency installation from `package-lock.json` and runs the production build.

Route-level lazy loading is implemented to reduce the initial bundle. The concept map and question-frequency page chunks should be monitored in production.

## 6. Accessibility and usability backlog

The baseline adds labeled navigation, icon-button names, semantic status/error announcements, account form labels, keyboard smoke coverage, and a CI Lighthouse accessibility audit. The release owner must review focus order, color contrast, responsive behavior, and screen-reader behavior on the deployed theme.
