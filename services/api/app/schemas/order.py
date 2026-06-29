"""Order and Quote Schemas"""
from typing import Optional, List
from decimal import Decimal
from datetime import date, datetime
from pydantic import BaseModel, Field

from app.models.order import ProjectType, OrderStatus, QuoteStatus, Currency


class OrderLineItemBase(BaseModel):
    product_id: Optional[int] = None
    product_name: str = Field(..., max_length=500)
    specification: Optional[str] = Field(None, max_length=500)
    unit: str = Field(..., max_length=50)
    quantity: Decimal
    unit_price: Decimal
    notes: Optional[str] = None


class OrderLineItemCreate(OrderLineItemBase):
    pass


class OrderLineItemUpdate(BaseModel):
    product_id: Optional[int] = None
    product_name: Optional[str] = Field(None, max_length=500)
    specification: Optional[str] = Field(None, max_length=500)
    unit: Optional[str] = Field(None, max_length=50)
    quantity: Optional[Decimal] = None
    unit_price: Optional[Decimal] = None
    notes: Optional[str] = None


class OrderLineItemResponse(OrderLineItemBase):
    id: int
    order_id: int
    amount: Decimal

    class Config:
        from_attributes = True


class OrderBase(BaseModel):
    customer_id: int
    vessel_id: Optional[int] = None
    project_type: ProjectType
    currency: Currency = Currency.CNY
    delivery_date: Optional[date] = None
    notes: Optional[str] = None


class OrderCreate(OrderBase):
    line_items: Optional[List[OrderLineItemCreate]] = []


class OrderUpdate(BaseModel):
    vessel_id: Optional[int] = None
    project_type: Optional[ProjectType] = None
    currency: Optional[Currency] = None
    delivery_date: Optional[date] = None
    notes: Optional[str] = None


class OrderResponse(OrderBase):
    id: int
    order_no: str
    status: OrderStatus
    total_amount: Decimal
    pm_id: int
    created_at: datetime
    updated_at: datetime
    customer_name: Optional[str] = None
    vessel_name: Optional[str] = None
    pm_name: Optional[str] = None

    class Config:
        from_attributes = True


class OrderDetail(OrderResponse):
    line_items: List[OrderLineItemResponse] = []
    customer_name: Optional[str] = None
    vessel_name: Optional[str] = None
    pm_name: Optional[str] = None


class InquiryCreate(OrderBase):
    """创建询价单"""
    inquiry_source: Optional[str] = None
    line_items: Optional[List[OrderLineItemCreate]] = []


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
    cancellation_reason: Optional[str] = None
    cancellation_category: Optional[str] = None


# Quote Schemas
class QuoteLineItemBase(BaseModel):
    product_id: Optional[int] = None
    product_name: str = Field(..., max_length=500)
    specification: Optional[str] = Field(None, max_length=500)
    unit: str = Field(..., max_length=50)
    quantity: Decimal
    unit_price: Decimal
    notes: Optional[str] = None


class QuoteLineItemCreate(QuoteLineItemBase):
    pass


class QuoteLineItemResponse(QuoteLineItemBase):
    id: int
    quote_id: int
    amount: Decimal

    class Config:
        from_attributes = True


class QuoteBase(BaseModel):
    order_id: int
    currency: Currency = Currency.CNY
    valid_until: Optional[date] = None
    notes: Optional[str] = None


class QuoteCreate(QuoteBase):
    line_items: List[QuoteLineItemCreate] = []


class QuoteUpdate(BaseModel):
    currency: Optional[Currency] = None
    valid_until: Optional[date] = None
    notes: Optional[str] = None
    feedback: Optional[str] = None


class QuoteResponse(QuoteBase):
    id: int
    quote_no: str
    version: int
    status: QuoteStatus
    total_amount: Decimal
    feedback: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class QuoteDetail(QuoteResponse):
    line_items: List[QuoteLineItemResponse] = []
    order_no: Optional[str] = None
    customer_name: Optional[str] = None


class QuoteStatusUpdate(BaseModel):
    status: QuoteStatus
    feedback: Optional[str] = None


class QuoteDuplicate(BaseModel):
    """Create new version from existing quote"""
    source_quote_id: int

