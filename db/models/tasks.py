from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Integer, String, ForeignKey, Numeric, DateTime, Enum as SAEnum, Text, Boolean
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class TaskStatus(str, Enum):
    ACTIVE = "active"
    HIDDEN = "hidden"
    COMPLETED = "completed"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    note: Mapped[str | None] = mapped_column(String, nullable=True)

    city_id: Mapped[int | None] = mapped_column(
        ForeignKey("cities.id", ondelete="SET NULL"),
        nullable=True,
    )

    shop_id: Mapped[int | None] = mapped_column(
        ForeignKey("shops.id", ondelete="SET NULL"),
        nullable=True,
    )

    reward: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=0,
    )

    max_completions: Mapped[int] = mapped_column(Integer, nullable=False)

    current_completions: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    available_from: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    available_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    status: Mapped[TaskStatus] = mapped_column(
        SAEnum(TaskStatus, name="task_status"),
        nullable=False,
        default=TaskStatus.ACTIVE,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    city: Mapped["City"] = relationship(back_populates="tasks")
    shop: Mapped["Shop"] = relationship(back_populates="tasks")

    submissions: Mapped[list["TaskSubmission"]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
    )
