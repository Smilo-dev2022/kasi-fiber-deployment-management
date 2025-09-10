from fastapi import APIRouter, Depends, HTTPException, Response, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Literal, Optional
import uuid
import qrcode
import io
from app.core.deps import get_db, require_roles
from app.models import stock as mstock
from app.models.pon import PON
from sqlalchemy import select


router = APIRouter(prefix="/assets", tags=["assets"])

ASSET_TYPES = ("POLE", "DRUM", "BRACKET", "TENSIONER")
ASSET_STATES = ("In Store", "Issued", "Installed", "Retired")


class AssetBatchIn(BaseModel):
    type: Literal["POLE", "DRUM", "BRACKET", "TENSIONER"]
    sku: str
    count: int


class AssetScanIn(BaseModel):
    code: str
    action: Literal["ISSUE", "INSTALL", "RETURN", "RETIRE"]
    pon_id: Optional[str] = None
    user_id: Optional[str] = None


@router.post("", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def create_batch(payload: AssetBatchIn, db: Session = Depends(get_db)):
    ids = []
    for _ in range(payload.count):
        code = str(uuid.uuid4()).split("-")[0].upper()
        db.execute(
            mstock.sa_insert_assets().values(
                id=uuid.uuid4(), type=payload.type, code=code, sku=payload.sku, status="In Store"
            )
        )
        ids.append(code)
    db.commit()
    return {"codes": ids}


@router.get("/qr/{code}", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE", "SMME"))])
def qr_png(code: str):
    img = qrcode.make(code)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")


@router.post("/scan", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])
def scan(payload: AssetScanIn, db: Session = Depends(get_db)):
    from app.models import stock as stock_models

    Asset = stock_models.Asset  # placeholder for ORM class if created later
    # Without full ORM mapping, fall back to table access
    t = mstock.sa_insert_assets().table
    asset_row = db.execute(select(t).where(t.c.code == payload.code)).mappings().first()
    if not asset_row:
        raise HTTPException(404, "Not found")

    new_values: dict = {}
    if payload.action == "ISSUE":
        new_values["status"] = "Issued"
    elif payload.action == "INSTALL":
        # Prevent INSTALL unless asset status is Issued
        if asset_row["status"] != "Issued":
            raise HTTPException(400, "Asset not issued")
        new_values["status"] = "Installed"
        if payload.pon_id:
            from uuid import UUID

            new_values["pon_id"] = UUID(payload.pon_id)
    elif payload.action == "RETURN":
        new_values["status"] = "In Store"
        new_values["pon_id"] = None
    elif payload.action == "RETIRE":
        new_values["status"] = "Retired"

    if new_values:
        db.execute(t.update().where(t.c.code == payload.code).values(**new_values))
        db.commit()

    status_value = new_values.get("status", asset_row["status"])
    return {"ok": True, "status": status_value}


@router.get("", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])
def list_assets(
    status: str | None = Query(default=None),
    pon_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    t = mstock.sa_insert_assets().table
    stmt = select(t)
    if status:
        stmt = stmt.where(t.c.status == status)
    if pon_id:
        from uuid import UUID

        stmt = stmt.where(t.c.pon_id == UUID(pon_id))
    rows = db.execute(stmt).mappings().all()
    return {"items": [dict(r) for r in rows]}

