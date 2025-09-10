from fastapi import Depends, Request
from sqlalchemy.orm import Session
from app.core.deps import get_db, with_tenant_db


def db_dep(request: Request, db: Session = Depends(get_db)):
    tenant_id = getattr(request.state, "tenant_id", None)
    if tenant_id:
        return with_tenant_db(db, tenant_id)
    return db
