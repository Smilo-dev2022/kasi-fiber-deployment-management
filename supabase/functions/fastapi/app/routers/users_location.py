from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timezone

from app.core.deps import get_db, require_roles


router = APIRouter(prefix="/users", tags=["users"])


class LocationIn(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    ts: datetime | None = None


@router.post("/location", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE", "SMME"))])
def post_location(payload: LocationIn, db: Session = Depends(get_db)):
    ts = payload.ts or datetime.now(timezone.utc)
    db.execute(
        text(
            "insert into user_locations (id, user_id, geom, ts) values (gen_random_uuid(), gen_random_uuid(), ST_SetSRID(ST_MakePoint(:lng, :lat), 4326), :ts)"
        ),
        {"lat": payload.lat, "lng": payload.lng, "ts": ts},
    )
    db.commit()
    return {"ok": True}

