"""Process queued PDF resources.

Run once with ``python scripts/process_documents.py --once`` or continuously
with ``python scripts/process_documents.py --loop``.
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from sqlalchemy import or_, select

from app.db.session import SessionLocal
from app.models import Resource
from app.services.document_processing import process_resource_by_id, recover_stale_resources


def process_once() -> int:
    recover_stale_resources()
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        ids = list(
            db.scalars(
                select(Resource.id)
                .where(
                    Resource.processing_status.in_(["queued", "retryable"]),
                    or_(Resource.processing_next_attempt_at.is_(None), Resource.processing_next_attempt_at <= now),
                )
                .order_by(Resource.created_at)
                .limit(10)
            ).all()
        )
    finally:
        db.close()
    return sum(1 for resource_id in ids if process_resource_by_id(resource_id))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--loop", action="store_true")
    parser.add_argument("--interval", type=float, default=5.0)
    args = parser.parse_args()
    if not args.once and not args.loop:
        parser.error("choose --once or --loop")
    while True:
        process_once()
        if not args.loop:
            return 0
        time.sleep(max(args.interval, 0.5))


if __name__ == "__main__":
    raise SystemExit(main())
