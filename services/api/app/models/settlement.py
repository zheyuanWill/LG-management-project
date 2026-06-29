"""
Settlement Models
"""
from __future__ import annotations

from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from decimal import Decimal
from datetime import date

from sqlalchemy import String, Text, ForeignKey, Numeric, Date, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.order import Currency

if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.contract import Contract
    from app.models.user import User


class SettlementStatus(str, Enum):
    """结项状态"""
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVING = "APPROVING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    COMPLETED = "COMPLETED"


class CostCategory(Base):
    """费用科目"""
    __tablename__ = "cost_categories"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("cost_categories.id"))
    description: Mapped[Optional[str]] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(default=0)


class ExchangeRate(Base):
    """汇率"""
    __tablename__ = "exchange_rates"

    from_currency: Mapped[Currency] = mapped_column(SQLEnum(Currency, create_type=False), nullable=False)
    to_currency: Mapped[Currency] = mapped_column(SQLEnum(Currency, create_type=False), nullable=False)
    rate: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)


class Settlement(Base):
    """结项"""
    __tablename__ = "settlements"

    settlement_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    contract_id: Mapped[Optional[int]] = mapped_column(ForeignKey("contracts.id"))
    status: Mapped[SettlementStatus] = mapped_column(SQLEnum(SettlementStatus, create_type=False), default=SettlementStatus.DRAFT)

    # 收入
    total_revenue: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    revenue_currency: Mapped[Currency] = mapped_column(SQLEnum(Currency, create_type=False), default=Currency.CNY)
    total_revenue_cny: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)

    # 成本
    total_cost: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    cost_currency: Mapped[Currency] = mapped_column(SQLEnum(Currency, create_type=False), default=Currency.CNY)
    total_cost_cny: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)

    # 回款
    total_received: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    received_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)

    # 付款
    total_disbursed: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    pending_disbursement: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)

    # 利润
    gross_profit: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    gross_profit_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)

    # 审批
    applicant_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    apply_date: Mapped[date] = mapped_column(Date, nullable=False)
    approver_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    approve_date: Mapped[Optional[date]] = mapped_column(Date)
    reject_reason: Mapped[Optional[str]] = mapped_column(Text)

    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    order: Mapped["Order"] = relationship("Order")
    contract: Mapped[Optional["Contract"]] = relationship("Contract")
    applicant: Mapped["User"] = relationship("User", foreign_keys=[applicant_id])
    approver: Mapped[Optional["User"]] = relationship("User", foreign_keys=[approver_id])
    cost_items: Mapped[List["CostItem"]] = relationship("CostItem", back_populates="settlement")


class CostItem(Base):
    """成本明细"""
    __tablename__ = "cost_items"

    settlement_id: Mapped[Optional[int]] = mapped_column(ForeignKey("settlements.id"))
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("cost_categories.id"), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[Currency] = mapped_column(SQLEnum(Currency, create_type=False), default=Currency.CNY)
    amount_cny: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    tax_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    tax_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    invoice_no: Mapped[Optional[str]] = mapped_column(String(100))
    invoice_date: Mapped[Optional[date]] = mapped_column(Date)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    settlement: Mapped[Optional["Settlement"]] = relationship("Settlement", back_populates="cost_items")
    order: Mapped["Order"] = relationship("Order")
    category: Mapped["CostCategory"] = relationship("CostCategory")
