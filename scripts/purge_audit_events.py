"""Delete durable audit events older than the configured retention window."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import delete

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.core.config import settings  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models import AuditEvent  # noqa: E402


def main() -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=settings.audit_retention_days)
    db = SessionLocal()
    try:
        result = db.execute(delete(AuditEvent).where(AuditEvent.created_at < cutoff))
        db.commit()
        print(f"Deleted {result.rowcount or 0} audit events older than {cutoff.isoformat()}")
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
