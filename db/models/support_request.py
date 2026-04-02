from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import BigInteger, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class SupportRequestStatus(str, Enum):
    OPEN = "open"
    ANSWERED = "answered"
    DELETED = "deleted"


class SupportRequest(Base):
    __tablename__ = "support_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    message_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_viewed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    status: Mapped[SupportRequestStatus] = mapped_column(
        SAEnum(
            SupportRequestStatus,
            name="support_request_status",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
        default=SupportRequestStatus.OPEN,
    )

    admin_reply: Mapped[str | None] = mapped_column(Text, nullable=True)
    answered_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    replied_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
