# Security Baseline

**Document ID:** ILR-SEC-001
**Version:** 2.0
**Status:** Implementation-complete development baseline
**Last reviewed:** 2026-10-28

The development API uses short-lived signed JWTs, Argon2 password hashing, ownership checks, upload limits, request throttling, and baseline security headers. The demo seed account is `demo@example.com` with password `demo-password`; it is for local development only and must be changed or removed before deployment.

## Mandatory production controls

- Provide a high-entropy secret through a secret manager or protected environment configuration.
- Use PostgreSQL with restricted network access and TLS where supported.
- Keep uploads outside public executable paths and process them in an isolated, resource-limited worker.
- Place Redis behind a private network and treat it as non-authoritative.
- Terminate TLS at the edge and configure a strict frontend origin.
- Pin container and action dependencies and scan images before release.
- Retain centralized request/audit logging, monitoring, alerting, backup, and restore verification.
- Define privacy retention, deletion, and export procedures for learner records.
- Run the production process only after migrations have been applied; production startup does not create schema or seed demo data.
- Enforce student, instructor, and administrator roles server-side; never trust a browser-supplied role.
- Use the S3-compatible storage backend for durable private document storage when local volumes are not acceptable.
- Protect `/metrics` behind the internal network or authenticated monitoring gateway; it is intentionally excluded from the public OpenAPI contract.
