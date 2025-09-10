from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from sqlalchemy import select
from typing import Optional
from app.core.deps import get_scoped_db, require_roles
from app.models.spares import StockLevel, SpareIssue, SpareReturn
import uuid


router = APIRouter(prefix="/spares", tags=["spares"])


@router.post("/issue", dependencies=[Depends(require_roles("ADMIN", "PM", "NOC", "SITE"))])
def issue_spare(store_id: str, sku: str, qty: int, incident_id: Optional[str] = None, db: Session = Depends(get_scoped_db)):
    sl = db.execute(select(StockLevel).where(StockLevel.store_id == UUID(store_id), StockLevel.sku == sku)).scalar_one_or_none()
    if not sl or sl.qty < qty:
        raise HTTPException(400, "Insufficient stock")
    sl.qty -= qty
    issue = SpareIssue(id=uuid.uuid4(), store_id=UUID(store_id), sku=sku, qty=qty, incident_id=UUID(incident_id) if incident_id else None)
    db.add(issue)
    db.commit()
    return {"ok": True}


@router.post("/return", dependencies=[Depends(require_roles("ADMIN", "PM", "NOC", "SITE"))])
def return_spare(store_id: str, sku: str, qty: int, incident_id: Optional[str] = None, db: Session = Depends(get_scoped_db)):
    sl = db.execute(select(StockLevel).where(StockLevel.store_id == UUID(store_id), StockLevel.sku == sku)).scalar_one_or_none()
    if not sl:
        sl = StockLevel(store_id=UUID(store_id), sku=sku, qty=0)
        db.add(sl)
    sl.qty += qty
    ret = SpareReturn(id=uuid.uuid4(), store_id=UUID(store_id), sku=sku, qty=qty, incident_id=UUID(incident_id) if incident_id else None)
    db.add(ret)
    db.commit()
    return {"ok": True}

