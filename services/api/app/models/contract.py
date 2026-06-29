"""
Contract Models
"""
from __future__ import annotations

from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from decimal import Decimal
from datetime import date

from sqlalchemy import String, Text, ForeignKey, Numeric, Date, Integer, Enum as SQLEnum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.order import Currency

if TYPE_CHECKING:
    from app.models.order import Order, Quote
    from app.models.customer import Customer
    from app.models.user import User


class ContractStatus(str, Enum):
    """合同状态"""
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    EFFECTIVE = "EFFECTIVE"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    TERMINATED = "TERMINATED"


class Contract(Base):
    """合同"""
    __tablename__ = "contracts"

    contract_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    quote_id: Mapped[Optional[int]] = mapped_column(ForeignKey("quotes.id"))
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[ContractStatus] = mapped_column(SQLEnum(ContractStatus, create_type=False), default=ContractStatus.DRAFT)
    currency: Mapped[Currency] = mapped_column(SQLEnum(Currency, create_type=False), default=Currency.CNY)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    signed_date: Mapped[Optional[date]] = mapped_column(Date)
    effective_date: Mapped[Optional[date]] = mapped_column(Date)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date)
    payment_terms: Mapped[Optional[str]] = mapped_column(Text)
    delivery_terms: Mapped[Optional[str]] = mapped_column(Text)
    warranty_period: Mapped[Optional[int]] = mapped_column(Integer)
    warranty_end_date: Mapped[Optional[date]] = mapped_column(Date)
    contract_type: Mapped[Optional[str]] = mapped_column(String(20), default="customer")
    related_contract_id: Mapped[Optional[int]] = mapped_column(ForeignKey("contracts.id"))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="contracts")
    quote: Mapped[Optional["Quote"]] = relationship("Quote")
    customer: Mapped["Customer"] = relationship("Customer")
    payment_plans: Mapped[List["PaymentPlan"]] = relationship(
        "PaymentPlan", back_populates="contract", cascade="all, delete-orphan"
    )
    payment_records: Mapped[List["PaymentRecord"]] = relationship("PaymentRecord", back_populates="contract")


class PaymentPlan(Base):
    """回款计划"""
    __tablename__ = "payment_plans"

    contract_id: Mapped[int] = mapped_column(ForeignKey("contracts.id"), nullable=False)
    phase: Mapped[str] = mapped_column(String(100), nullable=False)
    percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    planned_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    planned_date: Mapped[date] = mapped_column(Date, nullable=False)
    actual_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    actual_date: Mapped[Optional[date]] = mapped_column(Date)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    contract: Mapped["Contract"] = relationship("Contract", back_populates="payment_plans")


class PaymentRecord(Base):
    """回款记录"""
    __tablename__ = "payment_records"

    contract_id: Mapped[int] = mapped_column(ForeignKey("contracts.id"), nullable=False)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[Currency] = mapped_column(SQLEnum(Currency, create_type=False), default=Currency.CNY)
    amount_cny: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    payment_method: Mapped[Optional[str]] = mapped_column(String(100))
    bank_account: Mapped[Optional[str]] = mapped_column(String(100))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    contract: Mapped["Contract"] = relationship("Contract", back_populates="payment_records")
    order: Mapped["Order"] = relationship("Order")


class CollectionRecord(Base):
    """催收记录"""
    __tablename__ = "collection_records"

    payment_plan_id: Mapped[int] = mapped_column(ForeignKey("payment_plans.id"), nullable=False)
    contract_id: Mapped[int] = mapped_column(ForeignKey("contracts.id"), nullable=False)
    collection_date: Mapped[date] = mapped_column(Date, nullable=False)
    method: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text)
    collector_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    next_followup_date: Mapped[Optional[date]] = mapped_column(Date)

    payment_plan: Mapped["PaymentPlan"] = relationship("PaymentPlan")
    contract: Mapped["Contract"] = relationship("Contract")
    collector: Mapped[Optional["User"]] = relationship("User")
