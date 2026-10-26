# API Specification

**Document ID:** ILR-API-001
**Version:** 1.0
**Status:** Development baseline
**Last reviewed:** 2026-10-27

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
| GET | `/auth/export` | Yes | Export the authenticated user's data |
| POST | `/auth/delete` | Yes | Permanently delete the authenticated user's data after email confirmation |
| GET/POST | `/courses` | Yes | List or create owned courses |
| GET | `/concepts` | Yes | List owned concepts and prerequisites |
| POST | `/syllabus/analyze` | Yes | Extract topics from bounded text |
| GET | `/roadmap` | Yes | Preview an authenticated study plan |
| POST | `/roadmap/generate` | Yes | Persist a deadline-aware study plan |
| GET | `/roadmap/history` | Yes | List generated roadmap revisions |
| GET | `/resources` | Yes | List owned or public resources |
| POST | `/resources/upload` | Yes | Validate and store a private PDF |
| POST | `/resources/{id}/process` | Yes | Extract text from an owned PDF |
| GET/POST | `/resources/{id}/mappings` | Yes | Review resource-to-concept mappings |
| GET/POST | `/progress` | Yes | Read or update private progress |
| GET | `/quizzes/{concept_id}` | Yes | Get an owned concept quiz |
| POST | `/quizzes/{concept_id}/attempts` | Yes | Submit a quiz attempt |
| GET | `/rankings` | Yes | Read the development leaderboard |
| GET | `/rankings/concepts` | Yes | Rank owned concepts using native scoring when configured |

## 3. Authorization rules

The authenticated user ID is obtained from the verified token and applied server-side to private queries and mutations. A client-supplied owner or user ID must not widen access. Public resource visibility is the only intentional exception to owner filtering.

## 4. Resource processing contract

Upload requests must identify a PDF and remain below the configured size limit. The server generates the storage filename, records a checksum, and writes extracted text to private processed storage. Processing is synchronous in the development baseline; production requires an isolated worker and resource limits.

## 5. Compatibility policy

Breaking changes to paths, authentication, required fields, response meanings, or ownership behavior require a versioned API change or migration notice. New optional fields should be additive. Route tests must be updated with every contract change.
