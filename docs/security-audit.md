# Security Audit and Operating Posture

**Document ID:** ILR-AUD-001
**Version:** 2.0
**Status:** Development audit with implementation closure
**Last reviewed:** 2026-10-28

## Scope

The audit covers the FastAPI API, frontend toolchain, upload path, database boundaries, Redis integration, containers, and GitHub Actions. It is a source review plus local tests; it is not a penetration test or a production certification.

## Assessment conclusion

The implementation closes the repository-owned hardening targets. It remains a development baseline rather than a production certification because external penetration testing, operator-controlled infrastructure, and release approval are outside source changes.

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
- Queued processing verifies the stored file checksum before extraction.
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

The frontend Dockerfile and CI workflow are pinned to Node `24.22.1` with npm `11.21.1`. Keep npm explicitly upgraded in CI and container builds rather than relying on the runner image default.

## Residual risks

- The Compose development secret must not be reused outside local development.
- JWT revocation/logout is not server-managed; short expiry and secret rotation are the available controls.
- PDF processing is queued and has a worker path; production deployments still need operator-configured job-level monitoring, retry alerting, and an S3-compatible bucket if local storage is not appropriate.
- OCR is optional and isolated behind bounded page/text limits; the Tesseract binary must be patched and monitored in production.
- GitHub Actions are pinned to immutable commit SHAs with release comments; Dependabot is configured to propose updates.
- Container image scanning and SBOM publication are now part of the security workflow; all GitHub Actions references are pinned to immutable commit SHAs.
- Request audit logging with request IDs is emitted without credentials or document contents, and durable audit events have configurable retention and purge support.
- DAST is automated through `.github/workflows/dast.yml` and `scripts/run_dast.ps1`; an external penetration test remains an acceptance activity.
- S3-compatible storage is supported through `STORAGE_BACKEND=s3`; credentials and bucket lifecycle policies remain operator-managed.

## Release checklist

Before deployment:

1. Set a high-entropy `SECRET_KEY` and production `ENVIRONMENT`.
2. Upgrade Node and npm to patched supported versions.
3. Run Python and npm advisory scans against fresh lockfiles.
4. Run Alembic migrations against PostgreSQL.
5. Replace the demo account and Compose credentials.
6. Restrict CORS to the deployed frontend origin.
7. Keep Redis and PostgreSQL on private networks.
8. Review image scan and DAST results, retain SBOM artifacts, run `scripts/backup_database.py` and a confirmed restore drill, and verify monitoring and alerting.
