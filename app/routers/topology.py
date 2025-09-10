from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any
from app.core.deps import get_db, require_roles
from app.core.limiter import limiter, key_by_org


router = APIRouter(prefix="/topology", tags=["topology"])


@router.get(
    "/pon/{pon_id}",
    dependencies=[Depends(require_roles("ADMIN", "PM", "SITE", "AUDITOR")), Depends(limiter(30, 60, key_by_org))],
)
def get_topology_for_pon(pon_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    nodes = (
        db.execute(
            text("select * from topo_nodes where pon_id = :p order by code"), {"p": pon_id}
        )
        .mappings()
        .all()
    )

    edges = (
        db.execute(
            text(
                """
                select e.*
                from topo_edges e
                join topo_nodes a on a.id = e.a_id
                join topo_nodes b on b.id = e.b_id
                where a.pon_id = :p and b.pon_id = :p
                """
            ),
            {"p": pon_id},
        )
        .mappings()
        .all()
    )

    return {"nodes": [dict(n) for n in nodes], "edges": [dict(e) for e in edges]}

