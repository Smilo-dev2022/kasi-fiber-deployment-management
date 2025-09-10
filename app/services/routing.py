from datetime import datetime, timezone, timedelta
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.pon import PON
from app.models.incident import Incident
from app.models.task import Task


SCOPE_BY_STEP = {
    "MarkOut": "Civil",
    "TrenchOpen": "Civil",
    "BeddingAndDuct": "Civil",
    "Backfill": "Civil",
    "Reinstatement": "Civil",
    "PolePlanting": "Technical",
    "PolePhotos": "Technical",
    "CAC": "Technical",
    "Stringing": "Technical",
    "StringingPhotos": "Technical",
    "Splicing": "Technical",
    "Installation": "Technical",
    "Activation": "Technical",
    "Maintenance": "Maintenance",
}


def find_assignment_org_id(db: Session, pon_id: Optional[UUID], ward: Optional[str], scope: str) -> Optional[UUID]:
    from sqlalchemy import text

    if pon_id:
        row = db.execute(
            text(
                "select org_id from assignments where active = true and scope = :s and pon_id = :p order by priority asc limit 1"
            ),
            {"s": scope, "p": str(pon_id)},
        ).first()
        if row:
            return row[0]

    if ward:
        row = db.execute(
            text(
                "select org_id from assignments where active = true and scope = :s and ward = :w order by priority asc limit 1"
            ),
            {"s": scope, "w": ward},
        ).first()
        if row:
            return row[0]
    return None


def contract_sla_minutes(db: Session, org_id: UUID, severity: str) -> int:
    from sqlalchemy import text

    row = (
        db.execute(
            text(
                """
            select sla_minutes_p1, sla_minutes_p2, sla_minutes_p3, sla_minutes_p4
            from contracts where active = true and org_id = :o
            order by created_at desc limit 1
        """
            ),
            {"o": str(org_id)},
        )
        .mappings()
        .first()
    )
    if not row:
        return {"P1": 120, "P2": 240, "P3": 1440, "P4": 4320}[severity]
    return {
        "P1": row["sla_minutes_p1"],
        "P2": row["sla_minutes_p2"],
        "P3": row["sla_minutes_p3"],
        "P4": row["sla_minutes_p4"],
    }[severity]


def route_incident(db: Session, inc: Incident, pon: Optional[PON]) -> None:
    ward = pon.ward if pon else None
    scope = "Maintenance" if inc.category in ("Power", "Device", "Capacity", "Link") else "Technical"
    org_id = find_assignment_org_id(db, inc.pon_id, ward, scope)
    if org_id:
        inc.assigned_org_id = org_id
        mins = contract_sla_minutes(db, org_id, inc.severity)
        inc.severity_sla_minutes = mins
        inc.due_at = datetime.now(timezone.utc) + timedelta(minutes=mins)


def route_task(db: Session, task: Task, pon: PON) -> None:
    scope = SCOPE_BY_STEP.get(task.step)
    if not scope:
        return
    org_id = find_assignment_org_id(db, pon.id, pon.ward, scope)
    if org_id:
        task.assigned_org_id = org_id

