"""
Order and Quote Models
"""
from __future__ import annotations

from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from decimal import Decimal
from datetime import date

from sqlalchemy import String, Text, ForeignKey, Numeric, Date, Integer, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.customer import Customer, Vessel
    from app.models.user import User
    from app.models.product import Product
    from app.models.contract import Contract
    from app.models.tracking import TrackingNode


class ProjectType(str, Enum):
    """项目种类"""
    TECHNICAL_SERVICE = "TECHNICAL_SERVICE"
    SUPERVISION = "SUPERVISION"
    SPARE_PARTS = "SPARE_PARTS"
    IMPORT_EXPORT_AGENT = "IMPORT_EXPORT_AGENT"
    BROKERAGE = "BROKERAGE"
    AGENCY_FEE = "AGENCY_FEE"


class OrderStatus(str, Enum):
    """订单状态"""
    INQUIRY = "INQUIRY"
    DRAFT = "DRAFT"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class QuoteStatus(str, Enum):
    """报价状态"""
    DRAFT = "DRAFT"
    SENT = "SENT"
    FEEDBACK = "FEEDBACK"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class Currency(str, Enum):
    """币种"""
    CNY = "CNY"
    USD = "USD"
    EUR = "EUR"
    JPY = "JPY"
    HKD = "HKD"


class Order(Base):
    """订单"""
    __tablename__ = "orders"

    order_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    vessel_id: Mapped[Optional[int]] = mapped_column(ForeignKey("vessels.id"))
    project_type: Mapped[ProjectType] = mapped_column(SQLEnum(ProjectType, create_type=False), nullable=False)
    status: Mapped[OrderStatus] = mapped_column(SQLEnum(OrderStatus, create_type=False), default=OrderStatus.INQUIRY)
    currency: Mapped[Currency] = mapped_column(SQLEnum(Currency, create_type=False), default=Currency.CNY)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    delivery_date: Mapped[Optional[date]] = mapped_column(Date)
    pm_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="orders")
    vessel: Mapped[Optional["Vessel"]] = relationship("Vessel")
    pm: Mapped["User"] = relationship("User")
    line_items: Mapped[List["OrderLineItem"]] = relationship(
        "OrderLineItem", back_populates="order", cascade="all, delete-orphan"
    )
    quotes: Mapped[List["Quote"]] = relationship("Quote", back_populates="order")
    contracts: Mapped[List["Contract"]] = relationship("Contract", back_populates="order")
    tracking_nodes: Mapped[List["TrackingNode"]] = relationship("TrackingNode", back_populates="order")


class OrderLineItem(Base):
    """订单明细"""
    __tablename__ = "order_line_items"

    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    product_id: Mapped[Optional[int]] = mapped_column(ForeignKey("products.id"))
    product_name: Mapped[str] = mapped_column(String(500), nullable=False)
    specification: Mapped[Optional[str]] = mapped_column(String(500))
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="line_items")
    product: Mapped[Optional["Product"]] = relationship("Product")


class Quote(Base):
    """报价"""
    __tablename__ = "quotes"

    quote_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[QuoteStatus] = mapped_column(SQLEnum(QuoteStatus, create_type=False), default=QuoteStatus.DRAFT)
    currency: Mapped[Currency] = mapped_column(SQLEnum(Currency, create_type=False), default=Currency.CNY)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    valid_until: Mapped[Optional[date]] = mapped_column(Date)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    feedback: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="quotes")
    line_items: Mapped[List["QuoteLineItem"]] = relationship(
        "QuoteLineItem", back_populates="quote", cascade="all, delete-orphan"
    )


class QuoteLineItem(Base):
    """报价明细"""
    __tablename__ = "quote_line_items"

    quote_id: Mapped[int] = mapped_column(ForeignKey("quotes.id"), nullable=False)
    product_id: Mapped[Optional[int]] = mapped_column(ForeignKey("products.id"))
    product_name: Mapped[str] = mapped_column(String(500), nullable=False)
    specification: Mapped[Optional[str]] = mapped_column(String(500))
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    quote: Mapped["Quote"] = relationship("Quote", back_populates="line_items")
