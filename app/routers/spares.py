from uuid import UUID, uuid4
from datetime import datetime, timezone
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
import os
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.deps import get_db, require_roles
from app.core.limiter import limiter, key_by_org


router = APIRouter(prefix="/spares", tags=["spares"])


class IssueIn(BaseModel):
    store_id: UUID
    sku: str
    qty: int
    incident_id: UUID | None = None
    notes: str | None = None


HEAVY_WRITE_PER_MIN = int(os.getenv("HEAVY_WRITE_PER_ORG_PER_MIN", "120"))
HEAVY_WRITE_WINDOW_SEC = int(os.getenv("HEAVY_WRITE_WINDOW_SEC", "60"))


@router.post(
    "/issue",
    dependencies=[
        Depends(require_roles("ADMIN", "PM", "NOC")),
        Depends(limiter(limit=HEAVY_WRITE_PER_MIN, window_sec=HEAVY_WRITE_WINDOW_SEC, key_fn=key_by_org)),
    ],
)
def issue_spare(payload: IssueIn, db: Session = Depends(get_db)):
    if payload.qty <= 0:
        raise HTTPException(400, "qty must be positive")
    # Check stock
    row = db.execute(
        text("select qty from stock_levels where store_id = :s and sku = :sku for update"),
        {"s": str(payload.store_id), "sku": payload.sku},
    ).first()
    if not row or row[0] < payload.qty:
        raise HTTPException(400, "insufficient stock")
    # Deduct
    db.execute(
        text("update stock_levels set qty = qty - :q where store_id = :s and sku = :sku"),
        {"q": payload.qty, "s": str(payload.store_id), "sku": payload.sku},
    )
    # Record movement
    db.execute(
        text(
            """
            insert into stock_movements (id, store_id, sku, delta_qty, incident_id, notes, created_at)
            values (:id, :s, :sku, :dq, :inc, :n, :ts)
            """
        ),
        {
            "id": str(uuid4()),
            "s": str(payload.store_id),
            "sku": payload.sku,
            "dq": -payload.qty,
            "inc": str(payload.incident_id) if payload.incident_id else None,
            "n": payload.notes,
            "ts": datetime.now(timezone.utc),
        },
    )
    db.commit()
    return {"ok": True}


class ReturnIn(BaseModel):
    store_id: UUID
    sku: str
    qty: int
    incident_id: UUID | None = None
    notes: str | None = None


@router.post(
    "/return",
    dependencies=[
        Depends(require_roles("ADMIN", "PM", "NOC")),
        Depends(limiter(limit=HEAVY_WRITE_PER_MIN, window_sec=HEAVY_WRITE_WINDOW_SEC, key_fn=key_by_org)),
    ],
)
def return_spare(payload: ReturnIn, db: Session = Depends(get_db)):
    if payload.qty <= 0:
        raise HTTPException(400, "qty must be positive")
    # Upsert stock level
    updated = db.execute(
        text("update stock_levels set qty = qty + :q where store_id = :s and sku = :sku"),
        {"q": payload.qty, "s": str(payload.store_id), "sku": payload.sku},
    )
    if updated.rowcount == 0:
        db.execute(
            text("insert into stock_levels (store_id, sku, qty) values (:s, :sku, :q)"),
            {"s": str(payload.store_id), "sku": payload.sku, "q": payload.qty},
        )
    db.execute(
        text(
            """
            insert into stock_movements (id, store_id, sku, delta_qty, incident_id, notes, created_at)
            values (:id, :s, :sku, :dq, :inc, :n, :ts)
            """
        ),
        {
            "id": str(uuid4()),
            "s": str(payload.store_id),
            "sku": payload.sku,
            "dq": payload.qty,
            "inc": str(payload.incident_id) if payload.incident_id else None,
            "n": payload.notes,
            "ts": datetime.now(timezone.utc),
        },
    )
    db.commit()
    return {"ok": True}

