"""
Inventory Models
"""
from __future__ import annotations

from enum import Enum
from typing import Optional, TYPE_CHECKING
from decimal import Decimal
from datetime import date

from sqlalchemy import String, Text, ForeignKey, Numeric, Date, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.order import Currency

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.procurement import Procurement
    from app.models.order import Order
    from app.models.user import User


class InventoryMovementType(str, Enum):
    """库存变动类型"""
    IN = "IN"
    OUT = "OUT"
    RESERVE = "RESERVE"
    RELEASE = "RELEASE"
    ADJUST = "ADJUST"


class InventoryBatch(Base):
    """库存批次"""
    __tablename__ = "inventory_batches"

    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    batch_no: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    reserved_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    currency: Mapped[Currency] = mapped_column(SQLEnum(Currency, create_type=False), default=Currency.CNY)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date)
    location: Mapped[Optional[str]] = mapped_column(String(200))
    procurement_id: Mapped[Optional[int]] = mapped_column(ForeignKey("procurements.id"))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="inventory_batches")
    procurement: Mapped[Optional["Procurement"]] = relationship("Procurement")

    @property
    def available_quantity(self) -> Decimal:
        return self.quantity - self.reserved_quantity


class InventoryMovement(Base):
    """库存变动记录"""
    __tablename__ = "inventory_movements"

    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    batch_id: Mapped[Optional[int]] = mapped_column(ForeignKey("inventory_batches.id"))
    type: Mapped[InventoryMovementType] = mapped_column(SQLEnum(InventoryMovementType, create_type=False), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    order_id: Mapped[Optional[int]] = mapped_column(ForeignKey("orders.id"))
    procurement_id: Mapped[Optional[int]] = mapped_column(ForeignKey("procurements.id"))
    operator_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    product: Mapped["Product"] = relationship("Product")
    batch: Mapped[Optional["InventoryBatch"]] = relationship("InventoryBatch")
    order: Mapped[Optional["Order"]] = relationship("Order")
    procurement: Mapped[Optional["Procurement"]] = relationship("Procurement")
    operator: Mapped["User"] = relationship("User")


class InventoryReservation(Base):
    """库存预留"""
    __tablename__ = "inventory_reservations"

    batch_id: Mapped[int] = mapped_column(ForeignKey("inventory_batches.id"), nullable=False)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    batch: Mapped["InventoryBatch"] = relationship("InventoryBatch")
    order: Mapped["Order"] = relationship("Order")
