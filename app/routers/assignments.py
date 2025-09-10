from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import uuid4
from app.core.deps import get_db, require_roles
from app.schemas.assignment import AssignmentCreate, AssignmentOut


router = APIRouter(prefix="/assignments", tags=["assignments"])


@router.post("", response_model=AssignmentOut, dependencies=[Depends(require_roles("ADMIN", "PM"))])
def create_assignment(payload: AssignmentCreate, db: Session = Depends(get_db)):
    if not payload.pon_id and not payload.ward:
        raise HTTPException(400, "Either pon_id or ward is required")
    aid = str(uuid4())
    db.execute(
        text(
            """
        insert into assignments (id, org_id, step_type, pon_id, ward)
        values (:id, :org, :st, :pon, :ward)
        """
        ),
        {
            "id": aid,
            "org": str(payload.org_id),
            "st": payload.step_type,
            "pon": str(payload.pon_id) if payload.pon_id else None,
            "ward": payload.ward,
        },
    )
    db.commit()
    row = (
        db.execute(text("select * from assignments where id = :id"), {"id": aid})
        .mappings()
        .first()
    )
    if not row:
        raise HTTPException(500, "Failed to create assignment")
    return dict(row)

