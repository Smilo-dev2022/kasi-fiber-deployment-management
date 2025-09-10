from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional
from uuid import uuid4

from app.core.deps import get_db, require_roles


router = APIRouter(prefix="/stock", tags=["stock"])


class SKUIn(BaseModel):
    code: str
    name: str
    unit: str
    min_level: float = 0
    reorder_level: float = 0


@router.post("/skus", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def add_sku(payload: SKUIn, db: Session = Depends(get_db)):
    db.execute(
        text(
            "insert into skus (id, code, name, unit, min_level, reorder_level) values (gen_random_uuid(), :c, :n, :u, :m, :r)"
        ),
        {"c": payload.code, "n": payload.name, "u": payload.unit, "m": payload.min_level, "r": payload.reorder_level},
    )
    db.commit()
    return {"ok": True}


class StoreIn(BaseModel):
    name: str
    address: Optional[str] = None


@router.post("/stores", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def add_store(payload: StoreIn, db: Session = Depends(get_db)):
    db.execute(text("insert into stores (id, name, address) values (gen_random_uuid(), :n, :a)"), {"n": payload.name, "a": payload.address})
    db.commit()
    return {"ok": True}


class BatchIn(BaseModel):
    sku_id: str
    qty: float
    store_id: str
    received_at: Optional[str] = None
    supplier: Optional[str] = None


@router.post("/batches", dependencies=[Depends(require_roles("ADMIN", "PM", "STORE"))])
def receive_batch(payload: BatchIn, db: Session = Depends(get_db)):
    db.execute(
        text(
            """
        insert into stock_batches (id, sku_id, qty, store_id, received_at, supplier)
        values (gen_random_uuid(), :s, :q, :st, :ra, :sup)
        """
        ),
        {"s": payload.sku_id, "q": payload.qty, "st": payload.store_id, "ra": payload.received_at, "sup": payload.supplier},
    )
    db.commit()
    return {"ok": True}


class MoveIn(BaseModel):
    sku_id: str
    qty: float
    from_store_id: Optional[str] = None
    to_store_id: Optional[str] = None
    pon_id: Optional[str] = None
    asset_code: Optional[str] = None


@router.post("/moves", dependencies=[Depends(require_roles("ADMIN", "PM", "STORE", "SITE"))])
def create_move(payload: MoveIn, db: Session = Depends(get_db)):
    # Guard: prevent negative balance at from_store
    if payload.from_store_id:
        bal = db.execute(
            text(
                """
            with recv as (
              select coalesce(sum(qty),0) as q from stock_batches where sku_id=:s and store_id=:st
            ),
            moved_out as (
              select coalesce(sum(qty),0) as q from stock_moves where sku_id=:s and from_store_id=:st
            ),
            moved_in as (
              select coalesce(sum(qty),0) as q from stock_moves where sku_id=:s and to_store_id=:st
            )
            select (recv.q + moved_in.q - moved_out.q) as bal from recv, moved_out, moved_in
            """
            ),
            {"s": payload.sku_id, "st": payload.from_store_id},
        ).scalar()
        if bal is not None and bal < payload.qty:
            raise HTTPException(400, "Insufficient stock (negative balance guard)")

    db.execute(
        text(
            """
        insert into stock_moves (id, sku_id, qty, from_store_id, to_store_id, pon_id, asset_code)
        values (gen_random_uuid(), :s, :q, :fs, :ts, :p, :a)
        """
        ),
        {
            "s": payload.sku_id,
            "q": payload.qty,
            "fs": payload.from_store_id,
            "ts": payload.to_store_id,
            "p": payload.pon_id,
            "a": payload.asset_code,
        },
    )
    db.commit()
    return {"ok": True}


@router.get("/levels", dependencies=[Depends(require_roles("ADMIN", "PM", "STORE"))])
def levels(store_id: str, sku: Optional[str] = Query(default=None), db: Session = Depends(get_db)):
    sql = text(
        """
    with recv as (
      select sku_id, coalesce(sum(qty),0) as qty from stock_batches where store_id=:st group by sku_id
    ),
    moved_out as (
      select sku_id, coalesce(sum(qty),0) as qty from stock_moves where from_store_id=:st group by sku_id
    ),
    moved_in as (
      select sku_id, coalesce(sum(qty),0) as qty from stock_moves where to_store_id=:st group by sku_id
    ),
    k as (
      select id as sku_id, code, name, unit from skus
    )
    select k.code, k.name, k.unit, coalesce(r.qty,0) + coalesce(mi.qty,0) - coalesce(mo.qty,0) as balance
    from k
    left join recv r on r.sku_id = k.sku_id
    left join moved_out mo on mo.sku_id = k.sku_id
    left join moved_in mi on mi.sku_id = k.sku_id
    where (:code is null or k.code = :code)
    order by k.code
    """
    )
    rows = db.execute(sql, {"st": store_id, "code": sku}).mappings().all()
    return rows

