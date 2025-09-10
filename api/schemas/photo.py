from datetime import datetime
from pydantic import BaseModel, AnyHttpUrl


class PhotoBase(BaseModel):
    id: int
    pon_id: int
    task_id: int | None = None
    url: AnyHttpUrl | str
    kind: str
    taken_at: datetime | None = None
    uploaded_by: int | None = None

    class Config:
        from_attributes = True


class PhotoCreate(BaseModel):
    pon_id: int
    task_id: int | None = None
    url: AnyHttpUrl | str
    kind: str
    taken_at: datetime | None = None


class PhotoOut(PhotoBase):
    pass

