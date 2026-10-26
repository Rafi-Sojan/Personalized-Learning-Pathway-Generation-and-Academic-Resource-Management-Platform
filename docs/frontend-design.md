# Frontend Design Specification

**Document ID:** ILR-FE-001
**Version:** 1.0
**Status:** Development baseline
**Last reviewed:** 2026-10-27

## 1. Scope

The frontend is a React, Vite, and TypeScript single-page application. It provides the learner-facing workflow for authentication, course discovery, concept exploration, roadmap review, resources, quizzes, and progress.

## 2. Structure

| Area | Location | Responsibility |
|---|---|---|
| Application shell | `frontend/src/App.tsx` | Routing, authenticated layout, and navigation |
| Pages | `frontend/src/pages/` | Route-level screens |
| Reusable UI | `frontend/src/components/` | Cards, lists, maps, progress, quizzes, and empty states |
| API clients | `frontend/src/services/` | Typed HTTP calls and token handling |
| Types | `frontend/src/types/` | Shared client-side contracts |
| Styling | `frontend/src/styles.css` | Global visual system and responsive layout |
| Async hook | `frontend/src/hooks/useAsync.ts` | Loading, error, and result state |

## 3. User journeys

1. A learner registers or signs in through `Login.tsx`.
2. The client stores the short-lived access token and sends it as a bearer token.
3. The dashboard summarizes available course, roadmap, and progress information.
4. The learner navigates to a course, reviews concepts and prerequisite relationships, and opens resources or quizzes.
5. The learner requests or reviews a dated study roadmap.
6. Progress updates are submitted to the authenticated API and reflected in progress views.

## 4. Client behavior requirements

- The client shall not embed secrets or trust user-provided authorization claims.
- API failures shall be surfaced as recoverable UI errors rather than silently ignored.
- Authenticated routes shall redirect unauthenticated users to the login page.
- User-controlled text shall be rendered as text, not injected as HTML.
- API contract changes shall update the corresponding service and type definitions together.
- Loading and empty states shall be represented for screens that depend on remote data.

## 5. Build and delivery

The production build is generated with `npm run build` and served from the frontend container. The Docker image uses a multi-stage Node build and a static web server runtime. CI performs dependency installation from `package-lock.json` and runs the production build.

Route-level lazy loading is implemented to reduce the initial bundle. The concept map and progress visualization chunks remain the largest page-specific assets and should be monitored in production.

## 6. Accessibility and usability backlog

The baseline adds labeled navigation, icon-button names, semantic status/error announcements, and account form labels. A formal accessibility review covering keyboard navigation, focus order, color contrast, responsive behavior, and screen-reader behavior is still required.
