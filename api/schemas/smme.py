from pydantic import BaseModel, EmailStr


class SMMEBase(BaseModel):
    id: int
    name: str
    contact_name: str | None = None
    contact_phone: str | None = None
    contact_email: EmailStr | None = None
    active: bool

    class Config:
        from_attributes = True


class SMMECreate(BaseModel):
    name: str
    contact_name: str | None = None
    contact_phone: str | None = None
    contact_email: EmailStr | None = None
    active: bool = True


class SMMEUpdate(BaseModel):
    contact_name: str | None = None
    contact_phone: str | None = None
    contact_email: EmailStr | None = None
    active: bool | None = None


class SMMEOut(SMMEBase):
    pass

