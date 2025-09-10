from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import uuid4
from pydantic import BaseModel
from typing import Optional
from app.core.deps import get_db, require_roles


router = APIRouter(prefix="/stock", tags=["stock"])


class SKUIn(BaseModel):
    code: str
    name: str
    unit: str
    min_level: int = 0
    reorder_level: int = 0


@router.post("/skus", dependencies=[Depends(require_roles("ADMIN", "PM", "STORE"))])
def create_sku(payload: SKUIn, db: Session = Depends(get_db)):
    sid = str(uuid4())
    db.execute(
        text(
            """
      insert into skus (id, code, name, unit, min_level, reorder_level)
      values (:id,:c,:n,:u,:m,:r)
    """
        ),
        {
            "id": sid,
            "c": payload.code,
            "n": payload.name,
            "u": payload.unit,
            "m": payload.min_level,
            "r": payload.reorder_level,
        },
    )
    db.commit()
    return {"ok": True, "id": sid}


class StoreIn(BaseModel):
    name: str
    address: Optional[str] = None


@router.post("/stores", dependencies=[Depends(require_roles("ADMIN", "PM", "STORE"))])
def create_store(payload: StoreIn, db: Session = Depends(get_db)):
    sid = str(uuid4())
    db.execute(
        text("insert into stores (id, name, address) values (:id,:n,:a)"),
        {"id": sid, "n": payload.name, "a": payload.address},
    )
    db.commit()
    return {"ok": True, "id": sid}


class BatchIn(BaseModel):
    sku_id: str
    store_id: str
    qty: int
    supplier: Optional[str] = None
    note: Optional[str] = None


@router.post("/batches", dependencies=[Depends(require_roles("ADMIN", "PM", "STORE"))])
def receive_batch(payload: BatchIn, db: Session = Depends(get_db)):
    bid = str(uuid4())
    db.execute(
        text(
            """
      insert into stock_batches (id, sku_id, store_id, qty, supplier, note)
      values (:id,:s,:st,:q,:sup,:n)
    """
        ),
        {
            "id": bid,
            "s": payload.sku_id,
            "st": payload.store_id,
            "q": payload.qty,
            "sup": payload.supplier,
            "n": payload.note,
        },
    )
    db.commit()
    return {"ok": True, "id": bid}


class MoveIn(BaseModel):
    sku_id: str
    qty: int
    from_store_id: Optional[str] = None
    to_store_id: Optional[str] = None
    pon_id: Optional[str] = None
    asset_code: Optional[str] = None
    note: Optional[str] = None


def _balance(db: Session, sku: str, store: str) -> int:
    got = db.execute(
        text(
            """
      select coalesce((select sum(qty) from stock_batches where sku_id=:s and store_id=:st),0)
         + coalesce((select sum(case when to_store_id=:st then qty else 0 end) - sum(case when from_store_id=:st then qty else 0 end) from stock_moves where sku_id=:s),0)
    """
        ),
        {"s": sku, "st": store},
    ).scalar_one()
    return int(got)


@router.post("/moves", dependencies=[Depends(require_roles("ADMIN", "PM", "STORE", "SITE"))])
def move(payload: MoveIn, db: Session = Depends(get_db)):
    if payload.from_store_id:
        bal = _balance(db, payload.sku_id, payload.from_store_id)
        if payload.qty > bal:
            raise HTTPException(400, f"Insufficient stock. Balance {bal}")
    mid = str(uuid4())
    db.execute(
        text(
            """
      insert into stock_moves (id, sku_id, qty, from_store_id, to_store_id, pon_id, asset_code, note)
      values (:id,:s,:q,:fs,:ts,:p,:a,:n)
    """
        ),
        {
            "id": mid,
            "s": payload.sku_id,
            "q": payload.qty,
            "fs": payload.from_store_id,
            "ts": payload.to_store_id,
            "p": payload.pon_id,
            "a": payload.asset_code,
            "n": payload.note,
        },
    )
    db.commit()
    return {"ok": True, "id": mid}


@router.get("/levels", dependencies=[Depends(require_roles("ADMIN", "PM", "STORE"))])
def levels(store_id: str = Query(...), sku_id: Optional[str] = Query(None), db: Session = Depends(get_db)):
    if sku_id:
        bal = _balance(db, sku_id, store_id)
        return {"store_id": store_id, "sku_id": sku_id, "balance": bal}
    rows = db.execute(
        text(
            """
      with s as (
        select sku_id, coalesce(sum(qty),0) as b from stock_batches where store_id=:st group by sku_id
      ),
      m as (
        select sku_id,
               coalesce(sum(case when to_store_id=:st then qty else 0 end),0) -
               coalesce(sum(case when from_store_id=:st then qty else 0 end),0) as mv
        from stock_moves group by sku_id
      )
      select k.id as sku_id, k.code, k.name, coalesce(s.b,0)+coalesce(m.mv,0) as balance
      from skus k
      left join s on s.sku_id=k.id
      left join m on m.sku_id=k.id
      order by k.code
    """
        ),
        {"st": store_id},
    ).mappings().all()
    return [dict(r) for r in rows]

