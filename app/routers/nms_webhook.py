from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from uuid import UUID, uuid4
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.models.incident import Incident


router = APIRouter(prefix="/nms", tags=["nms-webhook"])


class LibreAlert(BaseModel):
    # Accept a generic alert payload from LibreNMS or Zabbix
    device_id: Optional[str] = None  # Our device UUID if known
    pon_id: Optional[str] = None
    title: str
    message: Optional[str] = None
    severity: str  # P1..P4 mapped by sender or a rule
    category: Optional[str] = None
    state: str  # firing|resolved
    fingerprint: Optional[str] = None  # stable key for dedup


@router.post("/alert")
def receive_alert(payload: LibreAlert, db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    # Simple dedup: find latest open incident with same title/category/device and leave it open
    q = db.query(Incident).filter(Incident.status.in_(["Open", "Acknowledged", "InProgress"]))
    if payload.device_id:
        q = q.filter(Incident.device_id == UUID(payload.device_id))
    if payload.category:
        q = q.filter(Incident.category == payload.category)
    if payload.title:
        q = q.filter(Incident.title == payload.title)
    existing = q.order_by(Incident.opened_at.desc()).first()

    if payload.state.lower() == "firing":
        if existing:
            return {"id": str(existing.id), "status": existing.status}
        # Create new incident
        inc = Incident(
            id=uuid4(),
            severity=payload.severity,
            category=payload.category,
            status="Open",
            title=payload.title,
            description=payload.message,
            device_id=UUID(payload.device_id) if payload.device_id else None,
            pon_id=UUID(payload.pon_id) if payload.pon_id else None,
            opened_at=now,
        )
        db.add(inc)
        db.commit()
        return {"id": str(inc.id), "status": inc.status}
    else:
        # Resolve existing if present
        if existing:
            if not existing.resolved_at:
                existing.resolved_at = now
            existing.status = "Resolved"
            db.commit()
            return {"id": str(existing.id), "status": existing.status}
        return {"ok": True}

