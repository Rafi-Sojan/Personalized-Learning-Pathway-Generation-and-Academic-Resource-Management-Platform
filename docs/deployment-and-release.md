# Deployment and Release Specification

**Document ID:** ILR-REL-001
**Version:** 1.0
**Status:** Development baseline
**Last reviewed:** 2026-10-27

## 1. Supported deployment modes

| Mode | Intended use | Dependencies |
|---|---|---|
| Local no-service | Development and unit testing | Python, Node.js, SQLite |
| Docker Compose | Integrated development or controlled staging | Docker, PostgreSQL, Redis |
| Production | Not yet approved | Managed database, secrets, TLS, observability, backup and recovery |

## 2. Release inputs

A release candidate shall identify the source revision, Python and Node versions, dependency lockfiles, container base image digests or versions, database migration state, and configuration template. Runtime secrets must be supplied outside the repository.

## 3. Release gates

The following checks are required before a release is approved:

1. Backend tests, lint, type checks, and dependency audit pass.
2. Frontend lockfile installation and production build pass.
3. C++ tests pass using the supported compiler/toolchain.
4. Database migrations apply cleanly to an empty database and are reversible or have a documented forward-only recovery plan.
5. API authentication, ownership, upload validation, and rate limiting are tested.
6. Container images are scanned and an SBOM is produced.
7. Secrets, demo accounts, default credentials, and development fallbacks are removed or overridden.
8. A rollback revision and database recovery plan are recorded.

## 4. Deployment procedure

1. Build immutable images from the approved revision.
2. Scan images and dependencies.
3. Provision secrets and private network connectivity.
4. Apply database migrations using a controlled deployment identity.
5. Deploy backend, worker components if enabled, Redis, and frontend.
6. Run health checks and a smoke test against the deployed API.
7. Confirm logs, metrics, rate limiting, and backup jobs.
8. Record the release revision and verification evidence.

## 5. Rollback

Application rollback must use the previous approved image. Database rollback must follow the migration-specific recovery plan; destructive schema reversions must not be attempted without a verified backup. If a security issue is involved, revoke affected secrets and tokens as part of the rollback response.
