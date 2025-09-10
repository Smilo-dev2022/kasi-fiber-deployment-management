import hashlib
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.core.deps import get_scoped_db, require_roles
from app.models.orgs import ApiToken
import uuid


router = APIRouter(prefix="/tokens", tags=["auth"])


@router.post("/create", dependencies=[Depends(require_roles("ADMIN"))])
def create_token(org_id: str, name: str, scope: str, token_plain: str, db: Session = Depends(get_scoped_db)):
    if scope not in ("read", "write", "finance"):
        raise HTTPException(400, "Invalid scope")
    token_hash = hashlib.sha256(token_plain.encode()).hexdigest()
    t = ApiToken(id=uuid.uuid4(), org_id=org_id, name=name, scope=scope, token_hash=token_hash)
    db.add(t)
    db.commit()
    db.refresh(t)
    return {"id": str(t.id)}


def verify_token(db: Session, token: str, required_scope: str | None = None) -> ApiToken | None:
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    q = db.query(ApiToken).filter(ApiToken.token_hash == token_hash).filter(ApiToken.scope != "revoked")
    tok = q.first()
    if not tok:
        return None
    if required_scope == "write" and tok.scope not in ("write",):
        return None
    if required_scope == "read" and tok.scope not in ("read", "write"):
        return None
    if required_scope == "finance" and tok.scope != "finance":
        return None
    return tok

