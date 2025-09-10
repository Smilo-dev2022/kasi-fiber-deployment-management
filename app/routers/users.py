from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.deps import get_db, require_roles


router = APIRouter(prefix="/users", tags=["users"])


class LocationIn(BaseModel):
    lat: float
    lng: float
    ts: str


@router.post("/location", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE", "SMME"))])
def post_location(payload: LocationIn, db: Session = Depends(get_db)):
    sql = text(
        """
        insert into user_locations (id, user_id, geom, ts)
        values (gen_random_uuid(), NULL, ST_SetSRID(ST_MakePoint(:lng,:lat), 4326), :ts)
        returning id
        """
    )
    row = db.execute(sql, {"lat": payload.lat, "lng": payload.lng, "ts": payload.ts}).first()
    db.commit()
    return {"ok": True, "id": row.id}

