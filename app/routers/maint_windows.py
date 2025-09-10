from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.deps import get_scoped_db, require_roles
import uuid
from app.models.maint import MaintWindow
from app.schemas.maint import MaintWindowCreate, MaintWindowOut


router = APIRouter(prefix="/maint-windows", tags=["maintenance"])


@router.post("", response_model=MaintWindowOut, dependencies=[Depends(require_roles("ADMIN", "PM", "NOC"))])
def create_maint_window(payload: MaintWindowCreate, db: Session = Depends(get_scoped_db)):
    mw = MaintWindow(id=uuid.uuid4(), **payload.dict())
    db.add(mw)
    db.commit()
    db.refresh(mw)
    return mw

