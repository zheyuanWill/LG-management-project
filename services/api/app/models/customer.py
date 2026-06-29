"""
Customer and Vessel Models
"""
from __future__ import annotations

from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.order import Order


class Customer(Base):
    """客户"""
    __tablename__ = "customers"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    contact_person: Mapped[Optional[str]] = mapped_column(String(100))
    contact_phone: Mapped[Optional[str]] = mapped_column(String(50))
    contact_email: Mapped[Optional[str]] = mapped_column(String(200))
    address: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    vessels: Mapped[List["Vessel"]] = relationship("Vessel", back_populates="customer")
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="customer")


class Vessel(Base):
    """船舶"""
    __tablename__ = "vessels"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    imo_number: Mapped[Optional[str]] = mapped_column(String(50))
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    vessel_type: Mapped[Optional[str]] = mapped_column(String(100))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="vessels")
