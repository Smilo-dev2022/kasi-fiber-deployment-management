from datetime import datetime
from sqlalchemy import Enum as SAEnum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from db.base import Base


class TaskStatus(str, enum.Enum):
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    DONE = "Done"
    FAILED = "Failed"


class TaskStep(str, enum.Enum):
    Wayleave = "Wayleave"
    ServicesCheck = "ServicesCheck"
    Kickoff = "Kickoff"
    Permissions = "Permissions"
    PermissionsUpload = "PermissionsUpload"
    PolePlanting = "PolePlanting"
    PolePhotos = "PolePhotos"
    CAC = "CAC"
    Stringing = "Stringing"
    StringingPhotos = "StringingPhotos"
    HomeSignup = "HomeSignup"
    Installation = "Installation"
    Activation = "Activation"
    Invoicing = "Invoicing"


class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    pon_id: Mapped[int] = mapped_column(ForeignKey("pons.id", ondelete="CASCADE"), index=True)
    step: Mapped[TaskStep] = mapped_column(SAEnum(TaskStep, name="task_step"))
    assigned_to: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    smme_id: Mapped[int | None] = mapped_column(ForeignKey("smmes.id"), nullable=True)
    status: Mapped[TaskStatus] = mapped_column(SAEnum(TaskStatus, name="task_status"), default=TaskStatus.PENDING)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    pon = relationship("PON", back_populates="tasks")
