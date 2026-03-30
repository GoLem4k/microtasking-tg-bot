from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import BigInteger, Integer, String, DateTime, Enum, ForeignKey, Numeric, Boolean
from datetime import datetime


class Base(DeclarativeBase):
    pass
