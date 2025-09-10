from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import uuid4
from pydantic import BaseModel
from typing import List
from app.core.deps import get_db, require_roles


router = APIRouter(prefix="/photo-tags", tags=["photos"])


class TagIn(BaseModel):
    name: str
    required_for_step: str | None = None


@router.post("", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def create_tag(payload: TagIn, db: Session = Depends(get_db)):
    tid = str(uuid4())
    db.execute(
        text("insert into photo_tags (id, name, required_for_step) values (:id,:n,:r)"),
        {"id": tid, "n": payload.name, "r": payload.required_for_step},
    )
    db.commit()
    return {"ok": True, "id": tid}


class LinkIn(BaseModel):
    photo_id: str
    tag_ids: List[str]


@router.post("/link", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])
def link_tags(payload: LinkIn, db: Session = Depends(get_db)):
    for t in payload.tag_ids:
        db.execute(
            text("insert into photo_tag_links (photo_id, tag_id) values (:p,:t) on conflict do nothing"),
            {"p": payload.photo_id, "t": t},
        )
    db.commit()
    return {"ok": True}

