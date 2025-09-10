from typing import Any
from sqlalchemy.orm import Session
from ..models.audit import AuditLog


def audit(db: Session, entity: str, entity_id: Any, action: str, actor_id: int | None, before: dict | None, after: dict | None) -> None:
    log = AuditLog(
        entity=entity,
        entity_id=str(entity_id),
        action=action,
        actor_id=actor_id,
        before=before,
        after=after,
    )
    db.add(log)

