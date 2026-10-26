# Security Audit and Operating Posture

**Document ID:** ILR-AUD-001
**Version:** 1.0
**Status:** Development audit
**Last reviewed:** 2026-10-27

## Scope

The audit covers the FastAPI API, frontend toolchain, upload path, database boundaries, Redis integration, containers, and GitHub Actions. It is a source review plus local tests; it is not a penetration test or a production certification.

## Assessment conclusion

The baseline contains meaningful development controls, but it is not production-approved. The highest-priority closure items are patched runtime/toolchain alignment, secret removal, isolated document processing, container scanning/SBOM generation, centralized audit logging, backup and restore verification, and external security testing.

## Controls currently implemented

### Identity and access

- Registration validates email format and password length.
- Passwords are stored as Argon2 hashes, never plaintext.
- Login returns signed JWT access tokens with configurable expiry.
- Private routes reject missing, invalid, or expired tokens.
- User-owned objects are filtered by authenticated user ID.
- Progress and quiz attempts are scoped to the authenticated user.

### Input and file handling

- Syllabus text is bounded to 200,000 characters.
- PDF uploads require a `.pdf` extension and `application/pdf` content type.
- Upload size is bounded by `MAX_UPLOAD_SIZE_MB`.
- Storage filenames are generated UUIDs rather than client filenames.
- SHA-256 checksums are recorded.
- PDF extraction writes derived text to a private processed directory.
- Uploads are not exposed as public static files.

### Infrastructure

- CORS origins are configuration-driven rather than wildcarded.
- API responses include baseline security headers.
- Rate limiting uses Redis when available and falls back to process-local enforcement.
- PostgreSQL and Redis Compose ports bind to localhost for local development.
- The backend container runs as a non-root user.

## Toolchain advisory boundary

`npm audit` reports vulnerabilities in the application dependency graph described by `frontend/package-lock.json`. It does not prove that the installed npm CLI or Node.js runtime is secure.

The development machine was observed using Node `v24.11.1` and npm `11.6.2`. Node.js published a security release for the 22.x, 24.x, and 26.x lines on 21 October 2026. Node 24.22.1 contains fixes for the listed high-severity DNS, TLS, and Brotli issues. Upgrade local Node before deployment and keep CI/container versions on a patched supported release line.

- [Node.js October 2026 security release](https://nodejs.org/en/blog/vulnerability/october-2026-security-releases)
- [Node.js 24.22.1 security fixes](https://nodejs.org/en/blog/release/v24.22.1)
- [npm CLI 11.21.1 release](https://github.com/npm/cli/releases/tag/v11.21.1)

The frontend Dockerfile is pinned to Node `22.23.4`, but the CI workflow should remain synchronized with that patched toolchain. Keep npm itself pinned or explicitly upgraded in CI rather than relying on the runner image default.

## Residual risks

- The Compose development secret must not be reused outside local development.
- JWT revocation/logout is not server-managed; short expiry and secret rotation are the available controls.
- PDF processing is synchronous and should move to a resource-limited worker for hostile or high-volume input.
- OCR is not enabled and must be isolated before being added.
- GitHub Actions are referenced by major tags rather than immutable commit SHAs.
- Container image scanning and SBOM publication are not yet part of CI.
- No external penetration test, DAST scan, or production database backup drill has been performed.

## Release checklist

Before deployment:

1. Set a high-entropy `SECRET_KEY` and production `ENVIRONMENT`.
2. Upgrade Node and npm to patched supported versions.
3. Run Python and npm advisory scans against fresh lockfiles.
4. Run Alembic migrations against PostgreSQL.
5. Replace the demo account and Compose credentials.
6. Restrict CORS to the deployed frontend origin.
7. Keep Redis and PostgreSQL on private networks.
8. Add image scanning, SBOM generation, backups, monitoring, and alerting.
