from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column
from db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    entity: Mapped[str] = mapped_column(String(100))
    entity_id: Mapped[int]
    action: Mapped[str] = mapped_column(String(50))
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    before: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    after: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    at: Mapped[datetime] = mapped_column(server_default=func.now())

