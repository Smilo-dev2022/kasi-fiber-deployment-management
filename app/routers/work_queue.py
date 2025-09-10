from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from app.core.deps import get_db, require_roles


router = APIRouter(prefix="/work-queue", tags=["work-queue"])


@router.get("", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE", "NOC", "AUDITOR", "SMME"))])
def get_work_queue(db: Session = Depends(get_db), x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"), x_role: Optional[str] = Header(default=None, alias="X-Role")):
    # Scope by organization and role: tasks and incidents assigned to the org
    results = {"tasks": [], "incidents": []}

    if x_org_id:
        tasks = (
            db.execute(
                text(
                    """
                select t.* from tasks t
                where (t.status is null or t.status not in ('Done'))
                and exists (
                  select 1 from assignments a
                  where a.org_id = :org
                  and (
                    (a.pon_id is not null and a.pon_id = t.pon_id)
                    or (a.ward is not null and a.ward = (select ward from pons p where p.id = t.pon_id))
                  )
                )
                order by coalesce(t.sla_due_at, now()) asc
                """
                ),
                {"org": x_org_id},
            )
            .mappings()
            .all()
        )
        results["tasks"] = [dict(r) for r in tasks]

        incidents = (
            db.execute(
                text(
                    """
                select i.* from incidents i
                where i.status in ('Open','Acknowledged')
                and (i.assigned_org_id = :org or exists (
                  select 1 from assignments a
                  where a.org_id = :org
                  and (
                    (i.pon_id is not null and a.pon_id = i.pon_id)
                    or (i.pon_id is not null and a.ward is not null and a.ward = (select ward from pons p where p.id = i.pon_id))
                  )
                ))
                order by coalesce(i.due_at, i.opened_at) asc
                """
                ),
                {"org": x_org_id},
            )
            .mappings()
            .all()
        )
        results["incidents"] = [dict(r) for r in incidents]

    return results

