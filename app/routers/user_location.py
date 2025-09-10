from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.deps import get_db, get_current_user


router = APIRouter(prefix="/users", tags=["map"])


class LocIn(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    ts: str | None = None


@router.post("/location")
def save_location(payload: LocIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    gj = {"type":"Point","coordinates":[payload.lng, payload.lat]}
    db.execute(text("insert into user_locations(user_id, geom_geojson, ts) values (:u, :g::jsonb, now())"),
               {"u": str(user.id), "g": __import__("json").dumps(gj)})
    db.commit()
    return {"ok": True}

