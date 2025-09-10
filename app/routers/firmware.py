from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.deps import get_scoped_db, require_roles


router = APIRouter(prefix="/firmware", tags=["firmware"])


@router.post("/plan", dependencies=[Depends(require_roles("ADMIN", "PM", "NOC"))])
def plan_firmware(db: Session = Depends(get_scoped_db)):
    return {"ok": True, "message": "Planning stub"}


@router.post("/execute", dependencies=[Depends(require_roles("ADMIN", "PM", "NOC"))])
def execute_firmware(db: Session = Depends(get_scoped_db)):
    return {"ok": True, "message": "Execute stub"}

