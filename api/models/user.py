from datetime import datetime
from sqlalchemy import String, Enum as SAEnum, func
from sqlalchemy.orm import Mapped, mapped_column
import enum
from db.base import Base

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    PM = "PM"
    SITE = "SITE"
    SMME = "SMME"
    AUDITOR = "AUDITOR"

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole, name="user_role"))
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
