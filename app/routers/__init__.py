from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict

from app.core.deps import require_roles
from app.settings import get_sla_minutes, update_sla_minutes

admin_router = APIRouter(prefix="/admin", tags=["admin"])


class SLAUpdate(BaseModel):
    sla_minutes: Dict[str, int]


@admin_router.get("/sla", dependencies=[Depends(require_roles("ADMIN"))])
def get_sla():
    return {"sla_minutes": get_sla_minutes()}


@admin_router.put("/sla", dependencies=[Depends(require_roles("ADMIN"))])
def put_sla(payload: SLAUpdate):
    return {"sla_minutes": update_sla_minutes(payload.sla_minutes)}
