"""Contract Schemas"""
from typing import Optional, List
from decimal import Decimal
from datetime import date, datetime
from pydantic import BaseModel, Field

from app.models.contract import ContractStatus
from app.models.order import Currency


class PaymentPlanBase(BaseModel):
    phase: str = Field(..., max_length=100)
    percentage: Decimal
    planned_amount: Decimal
    planned_date: date
    notes: Optional[str] = None


class PaymentPlanCreate(PaymentPlanBase):
    pass


class PaymentPlanUpdate(BaseModel):
    phase: Optional[str] = Field(None, max_length=100)
    percentage: Optional[Decimal] = None
    planned_amount: Optional[Decimal] = None
    planned_date: Optional[date] = None
    actual_amount: Optional[Decimal] = None
    actual_date: Optional[date] = None
    notes: Optional[str] = None


class PaymentPlanResponse(PaymentPlanBase):
    id: int
    contract_id: int
    actual_amount: Optional[Decimal] = None
    actual_date: Optional[date] = None

    class Config:
        from_attributes = True


class ContractBase(BaseModel):
    order_id: int
    quote_id: Optional[int] = None
    customer_id: int
    title: str = Field(..., max_length=500)
    currency: Currency = Currency.CNY
    total_amount: Decimal
    signed_date: Optional[date] = None
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    payment_terms: Optional[str] = None
    delivery_terms: Optional[str] = None
    warranty_period: Optional[int] = None
    warranty_end_date: Optional[date] = None
    contract_type: Optional[str] = "customer"
    related_contract_id: Optional[int] = None
    notes: Optional[str] = None


class ContractCreate(ContractBase):
    payment_plans: List[PaymentPlanCreate] = []


class ContractUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=500)
    currency: Optional[Currency] = None
    total_amount: Optional[Decimal] = None
    signed_date: Optional[date] = None
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    payment_terms: Optional[str] = None
    delivery_terms: Optional[str] = None
    notes: Optional[str] = None


class ContractResponse(ContractBase):
    id: int
    contract_no: str
    status: ContractStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ContractDetail(ContractResponse):
    payment_plans: List[PaymentPlanResponse] = []
    order_no: Optional[str] = None
    customer_name: Optional[str] = None


class ContractStatusUpdate(BaseModel):
    status: ContractStatus


class PaymentRecordBase(BaseModel):
    contract_id: int
    order_id: int
    amount: Decimal
    currency: Currency = Currency.CNY
    amount_cny: Decimal
    payment_date: date
    payment_method: Optional[str] = Field(None, max_length=100)
    bank_account: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class PaymentRecordCreate(PaymentRecordBase):
    pass


class PaymentRecordResponse(PaymentRecordBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

