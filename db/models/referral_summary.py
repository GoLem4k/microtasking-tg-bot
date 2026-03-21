from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import BigInteger, Integer, ForeignKey

from .base import Base


class ReferralSummary(Base):
    __tablename__ = "referral_summary"

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    level1_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    level1_earnings: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)

    level2_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    level2_earnings: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)

    user: Mapped["User"] = relationship(back_populates="referral_summary")
