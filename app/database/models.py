from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import TIMESTAMP
from typing import Optional
from datetime import datetime

from app.services.utils import now_time

class Base(DeclarativeBase):
    pass


class Apartment(Base): # Таблица квартир
    __tablename__ = "apartments"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String)
    address: Mapped[str] = mapped_column(String)
    rent: Mapped[int] = mapped_column(default=0)
    due_day: Mapped[int] = mapped_column(default=1)
    debt: Mapped[int] = mapped_column(default=0)
    comment: Mapped[str] = mapped_column(Text, default="")


class Contact(Base): # Таблица контактов с привязкой к квартире
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    apartment_id: Mapped[int] = mapped_column(ForeignKey("apartments.id"))
    name: Mapped[str] = mapped_column(String(100))  # Имя (напр. "Иван")
    phone: Mapped[str] = mapped_column(String(20)) # Телефон
    role: Mapped[str] = mapped_column(String(50))  # Роль (напр. "Владелец")

class MeterReading(Base):
    __tablename__ = "meter_readings"

    id: Mapped[int] = mapped_column(primary_key=True)
    apartment_id: Mapped[int] = mapped_column(ForeignKey("apartments.id"))
    hot_water: Mapped[int] = mapped_column()
    cold_water: Mapped[int] = mapped_column()
    electricity: Mapped[int] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True, precision=0), 
        default=lambda: now_time())


class Tariff(Base):
    __tablename__ = "tariffs"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    value: Mapped[float] = mapped_column()


class History(Base):
    __tablename__ = "history"

    id: Mapped[int] = mapped_column(primary_key=True)
    apartment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("apartments.id"), nullable=True)
    user: Mapped[str] = mapped_column()
    action: Mapped[str] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True, precision=0), 
        default=lambda: now_time())