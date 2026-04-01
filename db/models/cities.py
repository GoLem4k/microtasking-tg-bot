from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String

from .base import Base


class City(Base):
    __tablename__ = "cities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    users: Mapped[list["User"]] = relationship(back_populates="city")
    shops: Mapped[list["Shop"]] = relationship(back_populates="city")
    tasks: Mapped[list["Task"]] = relationship(back_populates="city")
