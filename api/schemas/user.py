from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: str | None = None
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserOut(UserBase):
    pass


class Token(BaseModel):
    access_token: str
    token_type: str

