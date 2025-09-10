from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from .settings import settings
from .db.session import get_db
from .models.user import User
from .models.pon import PON
from .models.smme import SMME
from .models.task import Task


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
ALGORITHM = "HS256"


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).get(int(user_id))
    if user is None:
        raise credentials_exception
    return user


def require_roles(*allowed_roles: str):
    def role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return user

    return role_checker


def forbid_roles(*forbidden: str):
    def role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role in forbidden:
            raise HTTPException(status_code=403, detail="Role not permitted for this action")
        return user

    return role_checker


def has_pon_access(db: Session, user: User, pon_id: int) -> bool:
    if user.role in {"ADMIN", "PM", "AUDITOR"}:
        return True
    if user.role == "SMME":
        return (
            db.query(PON)
            .join(SMME, PON.smme_id == SMME.id)
            .filter(PON.id == pon_id, SMME.user_id == user.id)
            .first()
            is not None
        )
    if user.role == "SITE":
        return (
            db.query(Task)
            .filter(Task.pon_id == pon_id, Task.assigned_to == user.id)
            .first()
            is not None
        )
    return False


def get_pon_or_403(pon_id: int, db: Session, user: User) -> PON:
    pon = db.get(PON, pon_id)
    if not pon:
        raise HTTPException(404, detail="PON not found")
    if not has_pon_access(db, user, pon_id):
        raise HTTPException(403, detail="Not allowed to access this PON")
    return pon

