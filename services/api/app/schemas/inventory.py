"""Inventory Schemas"""
from typing import Optional, List
from decimal import Decimal
from datetime import date, datetime
from pydantic import BaseModel, Field

from app.models.inventory import InventoryMovementType
from app.models.order import Currency


class InventoryBatchBase(BaseModel):
    product_id: int
    batch_no: str = Field(..., max_length=50)
    quantity: Decimal
    unit_cost: Decimal
    currency: Currency = Currency.CNY
    expiry_date: Optional[date] = None
    location: Optional[str] = Field(None, max_length=200)
    procurement_id: Optional[int] = None
    notes: Optional[str] = None


class InventoryBatchCreate(InventoryBatchBase):
    pass


class InventoryBatchUpdate(BaseModel):
    quantity: Optional[Decimal] = None
    expiry_date: Optional[date] = None
    location: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = None


class InventoryBatchResponse(InventoryBatchBase):
    id: int
    reserved_quantity: Decimal
    available_quantity: Decimal
    created_at: datetime
    updated_at: datetime
    product_name: Optional[str] = None

    class Config:
        from_attributes = True


class InventoryMovementBase(BaseModel):
    product_id: int
    batch_id: Optional[int] = None
    type: InventoryMovementType
    quantity: Decimal
    order_id: Optional[int] = None
    procurement_id: Optional[int] = None
    notes: Optional[str] = None


class InventoryMovementCreate(InventoryMovementBase):
    pass


class InventoryMovementResponse(InventoryMovementBase):
    id: int
    operator_id: int
    created_at: datetime
    updated_at: datetime
    product_name: Optional[str] = None
    operator_name: Optional[str] = None

    class Config:
        from_attributes = True


class InventoryReservationBase(BaseModel):
    batch_id: int
    order_id: int
    quantity: Decimal
    notes: Optional[str] = None


class InventoryReservationCreate(InventoryReservationBase):
    pass


class InventoryReservationResponse(InventoryReservationBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductInventorySummary(BaseModel):
    """商品库存汇总"""
    product_id: int
    product_code: str
    product_name: str
    total_quantity: Decimal
    total_reserved: Decimal
    available_quantity: Decimal
    batches: List[InventoryBatchResponse] = []

