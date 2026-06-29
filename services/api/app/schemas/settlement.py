"""Settlement and Cost Schemas"""
from typing import Optional, List
from decimal import Decimal
from datetime import date, datetime
from pydantic import BaseModel, Field

from app.models.settlement import SettlementStatus
from app.models.order import Currency


class CostCategoryBase(BaseModel):
    name: str = Field(..., max_length=200)
    code: str = Field(..., max_length=50)
    parent_id: Optional[int] = None
    description: Optional[str] = None
    sort_order: int = 0


class CostCategoryCreate(CostCategoryBase):
    pass


class CostCategoryResponse(CostCategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ExchangeRateBase(BaseModel):
    from_currency: Currency
    to_currency: Currency
    rate: Decimal
    effective_date: date


class ExchangeRateCreate(ExchangeRateBase):
    pass


class ExchangeRateResponse(ExchangeRateBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CostItemBase(BaseModel):
    order_id: int
    category_id: int
    description: str = Field(..., max_length=500)
    amount: Decimal
    currency: Currency = Currency.CNY
    amount_cny: Decimal
    tax_rate: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    invoice_no: Optional[str] = Field(None, max_length=100)
    invoice_date: Optional[date] = None
    notes: Optional[str] = None


class CostItemCreate(CostItemBase):
    pass


class CostItemUpdate(BaseModel):
    category_id: Optional[int] = None
    description: Optional[str] = Field(None, max_length=500)
    amount: Optional[Decimal] = None
    currency: Optional[Currency] = None
    amount_cny: Optional[Decimal] = None
    tax_rate: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    invoice_no: Optional[str] = Field(None, max_length=100)
    invoice_date: Optional[date] = None
    notes: Optional[str] = None


class CostItemResponse(CostItemBase):
    id: int
    settlement_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    category_name: Optional[str] = None

    class Config:
        from_attributes = True


class SettlementBase(BaseModel):
    order_id: int
    contract_id: Optional[int] = None
    notes: Optional[str] = None


class SettlementCreate(SettlementBase):
    pass


class SettlementUpdate(BaseModel):
    notes: Optional[str] = None


class SettlementResponse(SettlementBase):
    id: int
    settlement_no: str
    status: SettlementStatus
    total_revenue: Decimal
    revenue_currency: Currency
    total_revenue_cny: Decimal
    total_cost: Decimal
    cost_currency: Currency
    total_cost_cny: Decimal
    total_received: Decimal
    received_percentage: Decimal
    total_disbursed: Decimal
    pending_disbursement: Decimal
    gross_profit: Decimal
    gross_profit_rate: Decimal
    applicant_id: int
    apply_date: date
    approver_id: Optional[int] = None
    approve_date: Optional[date] = None
    reject_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SettlementDetail(SettlementResponse):
    cost_items: List[CostItemResponse] = []
    order_no: Optional[str] = None
    contract_no: Optional[str] = None
    customer_name: Optional[str] = None
    applicant_name: Optional[str] = None
    approver_name: Optional[str] = None


class SettlementApproval(BaseModel):
    approved: bool
    reject_reason: Optional[str] = None


class SettlementStatusUpdate(BaseModel):
    status: SettlementStatus
    reject_reason: Optional[str] = None


class OrderCostSummary(BaseModel):
    """订单成本汇总"""
    order_id: int
    order_no: str
    total_revenue: Decimal
    total_cost: Decimal
    gross_profit: Decimal
    gross_profit_rate: Decimal
    total_received: Decimal
    total_disbursed: Decimal
    receivable: Decimal
    payable: Decimal

