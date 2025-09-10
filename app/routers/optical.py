from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_roles
from app.models.optical import OpticalReading
from app.schemas.optical import OpticalIn


router = APIRouter(prefix="/optical", tags=["optical"])


@router.post("", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])
def record(opt: OpticalIn, db: Session = Depends(get_db)):
    rec = OpticalReading(**opt.dict())
    db.add(rec)
    db.commit()
    return {"ok": True}

