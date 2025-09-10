from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from app.core.deps import get_db, require_roles


router = APIRouter(prefix="/closures", tags=["closures"])


class ClosureIn(BaseModel):
    pon_id: UUID
    code: str = Field(min_length=2)
    enclosure_type: Optional[str] = None
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None
    tray_count: int = 0
    status: str = "Planned"


@router.post("", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])
def create_closure(payload: ClosureIn, db: Session = Depends(get_db)):
    sql = text(
        """
      insert into splice_closures (id, pon_id, code, enclosure_type, gps_lat, gps_lng, tray_count, status)
      values (:id, :pon, :code, :type, :lat, :lng, :tc, :st)
    """
    )
    cid = str(uuid4())
    db.execute(
        sql,
        {
            "id": cid,
            "pon": str(payload.pon_id),
            "code": payload.code,
            "type": payload.enclosure_type,
            "lat": payload.gps_lat,
            "lng": payload.gps_lng,
            "tc": payload.tray_count,
            "st": payload.status,
        },
    )
    db.commit()
    return {"ok": True, "id": cid}


@router.get("", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE", "AUDITOR"))])
def list_closures(pon_id: Optional[str] = Query(None), db: Session = Depends(get_db)):
    if pon_id:
        rows = (
            db.execute(
                text("select * from splice_closures where pon_id = :p order by code"),
                {"p": pon_id},
            )
            .mappings()
            .all()
        )
    else:
        rows = (
            db.execute(
                text("select * from splice_closures order by created_at desc limit 200")
            )
            .mappings()
            .all()
        )
    return [dict(r) for r in rows]


class ClosurePatch(BaseModel):
    enclosure_type: Optional[str] = None
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None
    tray_count: Optional[int] = None
    status: Optional[str] = None


@router.patch("/{closure_id}", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])
def update_closure(closure_id: str, payload: ClosurePatch, db: Session = Depends(get_db)):
    sets = []
    params = {"id": closure_id}
    for k, v in payload.dict(exclude_unset=True).items():
        sets.append(f"{k} = :{k}")
        params[k] = v
    if not sets:
        raise HTTPException(400, "No fields to update")
    db.execute(text(f"update splice_closures set {', '.join(sets)} where id = :id"), params)
    db.commit()
    return {"ok": True}

