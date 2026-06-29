"""Procurement Schemas"""
from typing import Optional, List
from decimal import Decimal
from datetime import date, datetime
from pydantic import BaseModel, Field

from app.models.procurement import ProcurementStatus, ProcurementSource
from app.models.order import Currency


class ProcurementLineItemBase(BaseModel):
    product_id: int
    product_name: str = Field(..., max_length=500)
    specification: Optional[str] = Field(None, max_length=500)
    unit: str = Field(..., max_length=50)
    quantity: Decimal
    unit_price: Decimal
    notes: Optional[str] = None


class ProcurementLineItemCreate(ProcurementLineItemBase):
    pass


class ProcurementLineItemUpdate(BaseModel):
    quantity: Optional[Decimal] = None
    unit_price: Optional[Decimal] = None
    received_quantity: Optional[Decimal] = None
    notes: Optional[str] = None


class ProcurementLineItemResponse(ProcurementLineItemBase):
    id: int
    procurement_id: int
    amount: Decimal
    received_quantity: Decimal

    class Config:
        from_attributes = True


class ProcurementBase(BaseModel):
    supplier_id: int
    order_id: Optional[int] = None
    currency: Currency = Currency.CNY
    expected_date: Optional[date] = None
    notes: Optional[str] = None
    source_type: ProcurementSource = ProcurementSource.NORMAL
    spare_part_risk_id: Optional[int] = None
    repair_task_id: Optional[int] = None
    affects_schedule: bool = False
    risk_resolved: bool = False


class ProcurementCreate(ProcurementBase):
    line_items: List[ProcurementLineItemCreate] = []


class ProcurementUpdate(BaseModel):
    expected_date: Optional[date] = None
    notes: Optional[str] = None
    source_type: Optional[ProcurementSource] = None
    spare_part_risk_id: Optional[int] = None
    repair_task_id: Optional[int] = None
    affects_schedule: Optional[bool] = None
    risk_resolved: Optional[bool] = None


class ProcurementResponse(ProcurementBase):
    id: int
    procurement_no: str
    status: ProcurementStatus
    total_amount: Decimal
    created_by: int
    approved_by: Optional[int] = None
    approved_at: Optional[date] = None
    created_at: datetime
    updated_at: datetime
    risk_resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProcurementDetail(ProcurementResponse):
    line_items: List[ProcurementLineItemResponse] = []
    supplier_name: Optional[str] = None
    order_no: Optional[str] = None
    creator_name: Optional[str] = None
    approver_name: Optional[str] = None


class ProcurementStatusUpdate(BaseModel):
    status: ProcurementStatus


class ProcurementApproval(BaseModel):
    approved: bool
    notes: Optional[str] = None


class ProcurementReceive(BaseModel):
    """收货请求"""
    items: List[dict]  # [{line_item_id: int, quantity: Decimal}]
    notes: Optional[str] = None


class DisbursementBase(BaseModel):
    procurement_id: Optional[int] = None
    order_id: Optional[int] = None
    supplier_id: int
    amount: Decimal
    currency: Currency = Currency.CNY
    amount_cny: Decimal
    payment_date: date
    payment_method: Optional[str] = Field(None, max_length=100)
    invoice_no: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class DisbursementCreate(DisbursementBase):
    pass


class DisbursementResponse(DisbursementBase):
    id: int
    created_at: datetime
    updated_at: datetime
    supplier_name: Optional[str] = None

    class Config:
        from_attributes = True

