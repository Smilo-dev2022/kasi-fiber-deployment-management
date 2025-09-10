from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional
from uuid import uuid4

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
    smme_id = str(uuid4())
    db.execute(
        text(
            """
        insert into smmes (id, name, reg_no, tax_no, bbee_level, contact_name, contact_email, active)
        values (:id, :n, :r, :t, :b, :cn, :ce, :a)
        """
        ),
        {
            "id": smme_id,
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
    return {"ok": True, "id": smme_id}


@router.get("", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def list_smmes(db: Session = Depends(get_db)):
    rows = db.execute(text("select * from smmes order by name"))
    return [dict(r) for r in rows.mappings().all()]


class LinkUserIn(BaseModel):
    user_id: str
    role: str


@router.post("/{smme_id}/users", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def link_user(smme_id: str, payload: LinkUserIn, db: Session = Depends(get_db)):
    db.execute(
        text(
            "insert into smme_users (id, smme_id, user_id, role) values (gen_random_uuid(), :s, :u, :r)"
        ),
        {"s": smme_id, "u": payload.user_id, "r": payload.role},
    )
    db.commit()
    return {"ok": True}


class ComplianceIn(BaseModel):
    type: str
    file_url: str
    valid_to: Optional[str] = None


@router.post("/{smme_id}/compliance", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def add_compliance(smme_id: str, payload: ComplianceIn, db: Session = Depends(get_db)):
    db.execute(
        text(
            """
        insert into compliance_docs (id, smme_id, type, file_url, valid_to, verified)
        values (gen_random_uuid(), :s, :t, :f, :v, false)
        """
        ),
        {"s": smme_id, "t": payload.type, "f": payload.file_url, "v": payload.valid_to},
    )
    db.commit()
    return {"ok": True}


@router.post("/{smme_id}/compliance/{doc_id}/verify", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def verify_doc(smme_id: str, doc_id: str, db: Session = Depends(get_db)):
    db.execute(text("update compliance_docs set verified=true where id=:id and smme_id=:s"), {"id": doc_id, "s": smme_id})
    db.commit()
    return {"ok": True}


@router.get("/compliance", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def compliance_status(db: Session = Depends(get_db)):
    sql = text(
        """
    select s.id, s.name,
           bool_and(cd.verified and (cd.valid_to is null or cd.valid_to >= current_date)) as compliant
    from smmes s
    left join compliance_docs cd on cd.smme_id = s.id
    group by s.id, s.name
    order by s.name
    """
    )
    rows = db.execute(sql).mappings().all()
    return rows

