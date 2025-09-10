from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Literal, Optional, List
import uuid
import qrcode
import io
from app.core.deps import get_db, require_roles
from app.models import stock as mstock
 


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
    ids: List[str] = []
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


@router.get("/qr/{code}")
def qr_png(code: str):
    img = qrcode.make(code)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")


@router.post("/scan", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])
def scan(payload: AssetScanIn, db: Session = Depends(get_db)):
    # Using a lightweight direct SQL approach
    asset = db.execute(
        "select id, code, status, pon_id from assets where code=:c",
        {"c": payload.code},
    ).mappings().first()
    if not asset:
        raise HTTPException(404, "Not found")

    new_status = None
    new_pon_id = asset["pon_id"]
    if payload.action == "ISSUE":
        new_status = "Issued"
    elif payload.action == "INSTALL":
        new_status = "Installed"
        if payload.pon_id:
            from uuid import UUID

            new_pon_id = str(UUID(payload.pon_id))
    elif payload.action == "RETURN":
        new_status = "In Store"
        new_pon_id = None
    elif payload.action == "RETIRE":
        new_status = "Retired"

    db.execute(
        "update assets set status=:st, pon_id=:pid where code=:c",
        {"st": new_status, "pid": new_pon_id, "c": payload.code},
    )
    db.commit()
    return {"ok": True, "status": new_status}
