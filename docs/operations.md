# Operations and Runbook

**Document ID:** ILR-OPS-001
**Version:** 1.0
**Status:** Development baseline
**Last reviewed:** 2026-10-27

## 1. Operational responsibility

The operator is responsible for configuration, secret provisioning, migrations, health verification, log review, backup verification, and incident escalation. This runbook supports development and controlled staging; it is not a substitute for a production service-level agreement.

## Local no-service development

The API can run with SQLite and the process-local rate-limit fallback:

```bash
python -m venv .venv
# Windows PowerShell
.venv\\Scripts\\Activate.ps1
python -m pip install -r backend/requirements.txt -r ml/requirements.txt
uvicorn app.main:app --reload --app-dir backend
```

Start the frontend separately:

```bash
cd frontend
npm ci
npm run dev
```

The seeded local login is `demo@example.com` / `demo-password`.

## Full Compose stack

```bash
docker compose up --build
```

Services:

| Service | Purpose | Local address |
|---|---|---|
| `frontend` | Vite development UI | `http://localhost:5173` |
| `backend` | FastAPI API | `http://localhost:8000` |
| `worker` | Queued PDF processing worker | internal |
| `postgres` | Persistent relational database | `localhost:5432` |
| `redis` | Rate-limit/cache service | `localhost:6379` |

The database and Redis volumes are named `postgres_data` and `redis_data`. Uploads and processed text are mounted from the repository `storage/` directory. The worker retries queued documents independently of the API process. OCR dependencies in `backend/requirements-ocr.txt` are optional; build `backend/Dockerfile.ocr` from the repository root when an OCR-enabled image is required.

## Configuration

Copy `.env.example` to `.env` for local overrides. Important values include:

- `DATABASE_URL`
- `REDIS_URL`
- `SECRET_KEY`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `FRONTEND_ORIGIN`
- `UPLOAD_DIR`
- `PROCESSED_DIR`
- `MAX_UPLOAD_SIZE_MB`

Never commit `.env` or real credentials.

## Database lifecycle

Development startup creates missing tables automatically. Production does not create tables or seed the demo account; run the checked-in migration first:

```bash
alembic -c backend/alembic.ini upgrade head
```

PostgreSQL remains authoritative. Redis may be flushed or unavailable without destroying progress, quiz, or roadmap records.

Create and restore logical PostgreSQL backups with the repository scripts:

```bash
python scripts/backup_database.py
python scripts/restore_database.py backups/learning-<timestamp>.dump
```

The restore script requires explicit `RESTORE` confirmation. Backup files are ignored by Git and must be encrypted and stored according to the production retention policy.

## Health verification

After startup, verify that the API responds, the interactive documentation loads, the frontend can reach the configured API origin, database migrations are current, and Redis connectivity is either healthy or intentionally operating in fallback mode. Perform an authenticated smoke test for login, a private read, a progress update, and roadmap generation.

The readiness endpoint is `GET /health/ready`; it confirms database connectivity and reports whether Redis is available or the process-local fallback is active.

## Verification commands

```bash
python -m pytest backend/tests ml/tests tests
python -m ruff check backend ml tests
python -m mypy backend/app --ignore-missing-imports
python -m pip install pip-audit
python -m pip_audit -r backend/requirements.txt -r ml/requirements.txt

cd frontend
npm ci
npm run build
npm audit --audit-level=high

cd ../scoring-engine
cmake -S . -B build
cmake --build build --config Release
ctest --test-dir build --build-config Release --output-on-failure
```

## Incident response basics

1. Rotate `SECRET_KEY` to invalidate existing JWTs.
2. Rotate PostgreSQL, Redis, registry, and object-storage credentials.
3. Preserve application, reverse-proxy, and database audit logs.
4. Disable uploads or expensive processing if resource exhaustion is suspected.
5. Rebuild from a clean checkout with fresh dependency audits.
6. Check progress, quiz, resource, and study-plan access logs for cross-user access.

Record the incident date, affected revision, suspected data scope, containment action, credential rotations, recovery point, and follow-up remediation in the project issue tracker.
