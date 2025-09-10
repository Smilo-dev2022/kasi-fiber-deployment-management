from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4
from sqlalchemy.orm import Session
from app.models.audit import AuditEvent


def write_audit(
    db: Session,
    *,
    entity_type: str,
    entity_id: Any,
    action: str,
    by: Optional[str] = None,
    before: Optional[dict] = None,
    after: Optional[dict] = None,
):
    evt = AuditEvent(
        id=uuid4(),
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        at=datetime.now(timezone.utc),
        by=by,
        before=before,
        after=after,
    )
    db.add(evt)
