from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import uuid4
from pydantic import BaseModel, Field
from typing import List, Optional

from app.core.deps import get_db, require_roles

router = APIRouter(prefix="/stringing/runs", tags=["stringing"])


class RunIn(BaseModel):
	pon_id: str
	meters: float = Field(gt=0, le=10000)
	from_pole: Optional[str] = None
	to_pole: Optional[str] = None
	notes: Optional[str] = None


@router.post("", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])

def create_run(payload: RunIn, db: Session = Depends(get_db)):
	idv = str(uuid4())
	db.execute(
		text(
			"""
		insert into stringing_runs (id, pon_id, meters, from_pole, to_pole, completed_by, completed_at, notes)
		values (:id, :pon, :m, :fp, :tp, null, now(), :n)
		"""
		),
		{"id": idv, "pon": payload.pon_id, "m": payload.meters, "fp": payload.from_pole, "tp": payload.to_pole, "n": payload.notes},
	)
	db.commit()
	return {"ok": True, "id": idv}


class RunOut(BaseModel):
	id: str
	pon_id: str
	meters: float
	from_pole: Optional[str]
	to_pole: Optional[str]
	completed_at: Optional[str]
	notes: Optional[str]


@router.get("", response_model=List[RunOut], dependencies=[Depends(require_roles("ADMIN", "PM", "SITE", "AUDITOR"))])

def list_runs(pon_id: str, db: Session = Depends(get_db)):
	rows = (
		db.execute(text("select * from stringing_runs where pon_id=:p order by completed_at desc"), {"p": pon_id})
		.mappings()
		.all()
	)
	return [dict(r) for r in rows]