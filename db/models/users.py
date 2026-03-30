from enum import Enum

from sqlalchemy import BigInteger, Integer, String, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.mysql import DATETIME
from datetime import datetime
from typing import Optional

from .base import Base


class UserStatus(str, Enum):
    USER = "user"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    username: Mapped[str] = mapped_column(String(255), unique=True, index=True)

    status: Mapped[UserStatus] = mapped_column(
        SAEnum(UserStatus, name="user_status"),
        nullable=False,
        default=UserStatus.USER,
    )

    city_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("cities.id", ondelete="SET NULL"),
        nullable=True,
    )

    ref_parent_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6),
        default=datetime.utcnow,
        nullable=False,
    )

    balance: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)

    city: Mapped[Optional["City"]] = relationship(back_populates="users")

    ref_parent: Mapped[Optional["User"]] = relationship(
        "User",
        remote_side="User.id",
        back_populates="ref_children",
    )
    ref_children: Mapped[list["User"]] = relationship(
        "User",
        back_populates="ref_parent",
        cascade="all, delete-orphan",
    )

    referral_summary: Mapped["ReferralSummary"] = relationship(
        "ReferralSummary",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    task_submissions: Mapped[list["TaskSubmission"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
