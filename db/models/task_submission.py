from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Integer, String, ForeignKey, Numeric, DateTime, Enum as SAEnum, Text, Boolean
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

class SubmissionStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class TaskSubmission(Base):
    __tablename__ = "task_submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
    )

    screenshot_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    status: Mapped[SubmissionStatus] = mapped_column(
        SAEnum(SubmissionStatus, name="submission_status"),
        nullable=False,
        default=SubmissionStatus.IN_PROGRESS,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user: Mapped["User"] = relationship(back_populates="task_submissions")
    task: Mapped["Task"] = relationship(back_populates="submissions")
