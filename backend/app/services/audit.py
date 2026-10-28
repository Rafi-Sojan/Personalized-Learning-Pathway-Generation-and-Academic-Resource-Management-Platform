"""Durable audit-event recording with bounded metadata."""

import json
from collections.abc import Mapping

from sqlalchemy.orm import Session

from app.models import AuditEvent


def record_event(db: Session, event_type: str, actor_id: str | None = None, request_id: str | None = None, metadata: Mapping[str, object] | None = None) -> None:
    safe_metadata = {str(key): str(value)[:500] for key, value in (metadata or {}).items()}
    db.add(AuditEvent(actor_id=actor_id, event_type=event_type, request_id=request_id, metadata_json=json.dumps(safe_metadata, sort_keys=True)))
