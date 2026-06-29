"""
Procurement Models
"""
from __future__ import annotations

from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from decimal import Decimal
from datetime import date, datetime

from sqlalchemy import String, Text, ForeignKey, Numeric, Date, Enum as SQLEnum, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.order import Currency

if TYPE_CHECKING:
    from app.models.product import Supplier, Product
    from app.models.order import Order
    from app.models.user import User


class ProcurementSource(str, Enum):
    """采购单来源"""
    NORMAL = "NORMAL"
    SPARE_PART_RISK = "SPARE_PART_RISK"
    FACTORY_REPAIR = "FACTORY_REPAIR"
    EXPORT_TAX_REFUND = "EXPORT_TAX_REFUND"


class ProcurementStatus(str, Enum):
    """采购单状态"""
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    ORDERED = "ORDERED"
    PARTIAL_RECEIVED = "PARTIAL_RECEIVED"
    RECEIVED = "RECEIVED"
    CANCELLED = "CANCELLED"


class Procurement(Base):
    """采购单"""
    __tablename__ = "procurements"

    procurement_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"), nullable=False)
    order_id: Mapped[Optional[int]] = mapped_column(ForeignKey("orders.id"))
    status: Mapped[ProcurementStatus] = mapped_column(SQLEnum(ProcurementStatus, create_type=False), default=ProcurementStatus.DRAFT)
    currency: Mapped[Currency] = mapped_column(SQLEnum(Currency, create_type=False), default=Currency.CNY)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    expected_date: Mapped[Optional[date]] = mapped_column(Date)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    approved_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    approved_at: Mapped[Optional[date]] = mapped_column(Date)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # 修船模块新增字段
    source_type: Mapped[ProcurementSource] = mapped_column(SQLEnum(ProcurementSource, create_type=False), default=ProcurementSource.NORMAL)
    spare_part_risk_id: Mapped[Optional[int]] = mapped_column(ForeignKey("spare_part_risks.id"))
    repair_task_id: Mapped[Optional[int]] = mapped_column(ForeignKey("repair_tasks.id"))
    affects_schedule: Mapped[bool] = mapped_column(default=False)
    risk_resolved: Mapped[bool] = mapped_column(default=False)
    risk_resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    supplier: Mapped["Supplier"] = relationship("Supplier")
    order: Mapped[Optional["Order"]] = relationship("Order")
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])
    approver: Mapped[Optional["User"]] = relationship("User", foreign_keys=[approved_by])
    line_items: Mapped[List["ProcurementLineItem"]] = relationship(
        "ProcurementLineItem", back_populates="procurement", cascade="all, delete-orphan"
    )
    disbursements: Mapped[List["Disbursement"]] = relationship("Disbursement", back_populates="procurement")


class ProcurementLineItem(Base):
    """采购单明细"""
    __tablename__ = "procurement_line_items"

    procurement_id: Mapped[int] = mapped_column(ForeignKey("procurements.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    product_name: Mapped[str] = mapped_column(String(500), nullable=False)
    specification: Mapped[Optional[str]] = mapped_column(String(500))
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    received_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    procurement: Mapped["Procurement"] = relationship("Procurement", back_populates="line_items")
    product: Mapped["Product"] = relationship("Product")


class Disbursement(Base):
    """付款记录"""
    __tablename__ = "disbursements"

    procurement_id: Mapped[Optional[int]] = mapped_column(ForeignKey("procurements.id"))
    order_id: Mapped[Optional[int]] = mapped_column(ForeignKey("orders.id"))
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[Currency] = mapped_column(SQLEnum(Currency, create_type=False), default=Currency.CNY)
    amount_cny: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    payment_method: Mapped[Optional[str]] = mapped_column(String(100))
    invoice_no: Mapped[Optional[str]] = mapped_column(String(100))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    procurement: Mapped[Optional["Procurement"]] = relationship("Procurement", back_populates="disbursements")
    order: Mapped[Optional["Order"]] = relationship("Order")
    supplier: Mapped["Supplier"] = relationship("Supplier")
