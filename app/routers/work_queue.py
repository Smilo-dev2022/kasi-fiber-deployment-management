from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from app.core.deps import get_db, require_roles


router = APIRouter(prefix="/work-queue", tags=["work"])


@router.get("", dependencies=[Depends(require_roles("ADMIN", "PMO", "NOC", "ContractorAdmin", "CivilLead", "SpliceLead", "MaintenanceTech", "SalesAgent"))])
def get_work_queue(
    db: Session = Depends(get_db),
    x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"),
    x_role: Optional[str] = Header(default=None, alias="X-Role"),
):
    # Incidents assigned to org
    inc_rows = (
        db.execute(
            text(
                """
        select id::text, title, severity, category, status, due_at
        from incidents
        where (:org is null or assigned_org_id = :org)
        order by coalesce(due_at, now()) asc nulls last
      """
            ),
            {"org": x_org_id},
        )
        .mappings()
        .all()
    )

    # Tasks based on assignments table for org and role step mapping
    # Map roles to steps roughly
    role_to_steps = {
        "CivilLead": ["Trenching", "Chambers", "Reinstatement"],
        "SpliceLead": ["Splicing", "Testing"],
        "MaintenanceTech": ["Maintenance"],
        "SalesAgent": ["Permissions"],
        "ContractorAdmin": ["Trenching", "Chambers", "Reinstatement", "Splicing", "Maintenance"],
    }
    steps = role_to_steps.get(x_role or "", [])
    task_rows = (
        db.execute(
            text(
                """
        select t.id::text, t.step, t.status, t.sla_due_at, t.pon_id::text
        from tasks t
        join assignments a on a.pon_id = t.pon_id and (:org is null or a.org_id = :org)
        where (:steps is null or t.step = any(string_to_array(:steps, ',')))
        order by coalesce(t.sla_due_at, now()) asc nulls last
      """
            ),
            {"org": x_org_id, "steps": ",".join(steps) if steps else None},
        )
        .mappings()
        .all()
    )

    return {"incidents": [dict(r) for r in inc_rows], "tasks": [dict(r) for r in task_rows]}

