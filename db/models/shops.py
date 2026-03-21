from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, ForeignKey, Numeric

from .base import Base


class Shop(Base):
    __tablename__ = "shops"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    address: Mapped[str | None] = mapped_column(String(255))

    base_reward: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)

    city_id: Mapped[int] = mapped_column(
        ForeignKey("cities.id", ondelete="RESTRICT"),  
        nullable=False,
    )

    city: Mapped["City"] = relationship(back_populates="shops")
    tasks: Mapped[list["Task"]] = relationship(back_populates="shop")
