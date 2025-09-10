from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Literal, Optional
from app.core.deps import get_db, require_roles
from app.models.smme import SMME


router = APIRouter(prefix="/rate-cards", tags=["rate-cards"])


class RateIn(BaseModel):
    smme_id: str
    step: Literal["PolePlanting", "Stringing", "CA"]
    unit: Literal["per_pole", "per_meter", "per_check"]
    rate_cents: int
    active: bool = True
    valid_from: str
    valid_to: Optional[str] = None


@router.post("", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def create_rate(payload: RateIn, db: Session = Depends(get_db)):
    db.execute(
        """
        insert into rate_cards (id, smme_id, step, unit, rate_cents, active, valid_from, valid_to)
        values (gen_random_uuid(), :s, :st, :u, :r, :a, :vf, :vt)
        """,
        {
            "s": payload.smme_id,
            "st": payload.step,
            "u": payload.unit,
            "r": payload.rate_cents,
            "a": payload.active,
            "vf": payload.valid_from,
            "vt": payload.valid_to,
        },
    )
    db.commit()
    return {"ok": True}

