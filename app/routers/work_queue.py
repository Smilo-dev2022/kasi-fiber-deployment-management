from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from app.core.deps import get_db


router = APIRouter(prefix="/work-queue", tags=["work-queue"])


@router.get("")
def get_work_queue(
    db: Session = Depends(get_db),
    x_role: Optional[str] = Header(default=None, alias="X-Role"),
    x_org: Optional[str] = Header(default=None, alias="X-Org"),
):
    # Simple scoping by org and role
    if not x_org:
        return []
    if x_role == "NOC":
        rows = (
            db.execute(text("select * from incidents where status in ('Open','Acknowledged') order by opened_at desc"))
            .mappings()
            .all()
        )
        return [dict(r) for r in rows]
    if x_role == "SalesAgent":
        rows = (
            db.execute(
                text(
                    """
                    select t.* from tasks t
                    where t.step = 'Permissions' and t.status in ('pending','in_progress')
                    order by t.sla_due_at nulls last
                    """
                )
            )
            .mappings()
            .all()
        )
        return [dict(r) for r in rows]
    # Contractors: tasks assigned to their org via assignments
    rows = (
        db.execute(
            text(
                """
                select t.* from tasks t
                join pons p on p.id = t.pon_id
                left join assignments a on a.pon_id = p.id or a.ward_id = p.ward_id
                where a.org_id = :org and a.active = true
                order by t.sla_due_at nulls last
                """
            ),
            {"org": x_org},
        )
        .mappings()
        .all()
    )
    return [dict(r) for r in rows]

