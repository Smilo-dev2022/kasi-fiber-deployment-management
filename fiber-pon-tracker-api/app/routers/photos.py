from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.deps import get_db, require_roles
from app.services.s3 import get_signed_put_url


router = APIRouter(prefix="/photos", tags=["photos"])


class SignIn(BaseModel):
    key: str
    content_type: str


class SignOut(BaseModel):
    url: str


@router.post("/sign", response_model=SignOut, dependencies=[Depends(require_roles("ADMIN","PM","SITE","SMME"))])
def sign_upload(data: SignIn):
    return SignOut(url=get_signed_put_url(data.key, data.content_type))
