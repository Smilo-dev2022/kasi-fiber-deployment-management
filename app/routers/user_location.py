from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import uuid4
from app.core.deps import get_db, require_roles


router = APIRouter(prefix="/users", tags=["map"])


class LocIn(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    ts: str | None = None


@router.post("/location", dependencies=[Depends(require_roles("ADMIN", "PM", "NOC", "SITE"))])
def save_location(payload: LocIn, db: Session = Depends(get_db)):
    # In this codebase, we rely on X-Role header-based auth; for user identity, a simple header-based stub
    # could be added later. For now, store anonymous user_id as a generated UUID to avoid blocking.
    gj = {"type": "Point", "coordinates": [payload.lng, payload.lat]}
    db.execute(
        text(
            "insert into user_locations(id, user_id, geom_geojson, ts) values (:id, :u, :g::jsonb, now())"
        ),
        {"id": str(uuid4()), "u": str(uuid4()), "g": __import__("json").dumps(gj)},
    )
    db.commit()
    return {"ok": True}

