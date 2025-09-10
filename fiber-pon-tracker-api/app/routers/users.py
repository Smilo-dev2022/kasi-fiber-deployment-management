from fastapi import APIRouter, Depends
from app.core.deps import get_current_user
from app.models.user import User


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"id": str(user.id), "name": user.name, "role": user.role, "email": user.email}
