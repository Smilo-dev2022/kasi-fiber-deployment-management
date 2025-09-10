from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from app.core.deps import get_db, get_current_user
from app.models.user import User


router = APIRouter(prefix="/work-queue", tags=["work-queue"])


@router.get("")
def my_queue(
    scope: Optional[str] = Query(None, description="Civil, Technical, Maintenance"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.org_id:
        return {"tasks": [], "incidents": []}

    params = {"org": str(user.org_id)}
    scope_filter = ""
    if scope:
        scope_filter = " and a.scope = :sc "
        params["sc"] = scope

    tasks = (
        db.execute(
            text(
                f"""
      select t.id, t.step, t.status, p.pon_number, p.ward, t.sla_due_at, t.breached
      from tasks t
      join pons p on p.id = t.pon_id
      left join assignments a on a.pon_id = p.id and a.active = true
      where t.assigned_org_id = :org {scope_filter} and t.status <> 'Done'
      order by t.sla_due_at nulls last, t.started_at nulls last
    """
            ),
            params,
        )
        .mappings()
        .all()
    )

    incidents = (
        db.execute(
            text(
                """
      select i.id, i.severity, i.category, i.title, i.status, i.due_at, p.pon_number, p.ward
      from incidents i
      left join pons p on p.id = i.pon_id
      where i.assigned_org_id = :org and i.status in ('Open','Acknowledged')
      order by i.due_at nulls last, i.opened_at desc
    """
            ),
            {"org": str(user.org_id)},
        )
        .mappings()
        .all()
    )

    return {"tasks": [dict(r) for r in tasks], "incidents": [dict(r) for r in incidents]}

