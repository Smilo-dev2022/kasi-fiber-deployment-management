from datetime import datetime
from sqlalchemy import String, Integer, Boolean, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.base import Base


class PON(Base):
    __tablename__ = "pons"
    id: Mapped[int] = mapped_column(primary_key=True)
    pon_number: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    ward: Mapped[str | None] = mapped_column(String(100))
    street_area: Mapped[str | None] = mapped_column(String(255))
    homes_passed: Mapped[int | None] = mapped_column(Integer)
    poles_planned: Mapped[int | None] = mapped_column(Integer)
    poles_planted: Mapped[int | None] = mapped_column(Integer, default=0)
    cac_passed: Mapped[bool] = mapped_column(Boolean, default=False)
    stringing_done: Mapped[bool] = mapped_column(Boolean, default=False)
    photos_uploaded: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(32), default="Not Started", index=True)
    smme_id: Mapped[int | None] = mapped_column(ForeignKey("smmes.id"))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    tasks = relationship("Task", back_populates="pon", cascade="all, delete-orphan")
    photos = relationship("Photo", back_populates="pon", cascade="all, delete-orphan")
    cac_checks = relationship("CACCheck", back_populates="pon", cascade="all, delete-orphan")
    stringing_runs = relationship("StringingRun", back_populates="pon", cascade="all, delete-orphan")

__table_args__ = (Index("ix_pon_status_smme", "status", "smme_id"),)
