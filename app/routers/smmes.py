from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import uuid4
from pydantic import BaseModel
from typing import Optional
from app.core.deps import get_db, require_roles


router = APIRouter(prefix="/smmes", tags=["smmes"])


class SMMEIn(BaseModel):
    name: str
    reg_no: Optional[str] = None
    tax_no: Optional[str] = None
    bbee_level: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    active: bool = True


@router.post("", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def create_smme(payload: SMMEIn, db: Session = Depends(get_db)):
    sid = str(uuid4())
    db.execute(
        text(
            """
      insert into smmes (id, name, reg_no, tax_no, bbee_level, contact_name, contact_email, active)
      values (:id,:n,:r,:t,:b,:cn,:ce,:a)
    """
        ),
        {
            "id": sid,
            "n": payload.name,
            "r": payload.reg_no,
            "t": payload.tax_no,
            "b": payload.bbee_level,
            "cn": payload.contact_name,
            "ce": payload.contact_email,
            "a": payload.active,
        },
    )
    db.commit()
    return {"ok": True, "id": sid}


class LinkIn(BaseModel):
    smme_id: str
    user_id: str
    role: str  # Admin, Supervisor, Worker


@router.post("/link-user", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def link_user(payload: LinkIn, db: Session = Depends(get_db)):
    lid = str(uuid4())
    db.execute(
        text("insert into smme_users (id, smme_id, user_id, role) values (:id,:s,:u,:r)"),
        {"id": lid, "s": payload.smme_id, "u": payload.user_id, "r": payload.role},
    )
    db.commit()
    return {"ok": True, "id": lid}


class DocIn(BaseModel):
    smme_id: str
    type: str
    file_url: str
    valid_to: Optional[str] = None
    verified: bool = False


@router.post("/compliance", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def add_doc(payload: DocIn, db: Session = Depends(get_db)):
    did = str(uuid4())
    db.execute(
        text(
            """
      insert into compliance_docs (id, smme_id, type, file_url, valid_to, verified)
      values (:id,:s,:t,:f,:v,:vr)
    """
        ),
        {
            "id": did,
            "s": payload.smme_id,
            "t": payload.type,
            "f": payload.file_url,
            "v": payload.valid_to,
            "vr": payload.verified,
        },
    )
    db.commit()
    return {"ok": True, "id": did}


@router.get(
    "/compliance-status/{smme_id}", dependencies=[Depends(require_roles("ADMIN", "PM"))]
)
def compliance_status(smme_id: str, db: Session = Depends(get_db)):
    rows = db.execute(
        text(
            """
      select type, verified, valid_to from compliance_docs where smme_id=:s
    """
        ),
        {"s": smme_id},
    ).mappings().all()
    if not rows:
        return {"ok": False, "docs": []}
    from datetime import date as _date

    ok = all(
        r["verified"] and (r["valid_to"] is None or r["valid_to"] >= _date.today())
        for r in rows
    )
    return {"ok": ok, "docs": [dict(r) for r in rows]}

