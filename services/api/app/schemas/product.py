"""Product and Supplier Schemas"""
from typing import Optional, List
from decimal import Decimal
from datetime import date, datetime
from pydantic import BaseModel, Field

from app.models.product import SupplierType
from app.models.order import Currency


# ---------------------------------------------------------------------------
# Supplier Category
# ---------------------------------------------------------------------------

class SupplierCategoryBase(BaseModel):
    name: str = Field(..., max_length=100)
    code: str = Field(..., max_length=50)
    level: int = Field(..., ge=1, le=2)
    parent_id: Optional[int] = None
    sort_order: int = 0
    description: Optional[str] = Field(None, max_length=500)


class SupplierCategoryCreate(SupplierCategoryBase):
    pass


class SupplierCategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    sort_order: Optional[int] = None
    description: Optional[str] = Field(None, max_length=500)


class SupplierCategoryResponse(SupplierCategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SupplierCategoryTree(SupplierCategoryResponse):
    """带子分类的树形结构"""
    children: List["SupplierCategoryTree"] = []


# ---------------------------------------------------------------------------
# Supplier
# ---------------------------------------------------------------------------

class SupplierCategoryBrief(BaseModel):
    """供应商响应中内嵌的分类简要信息"""
    id: int
    name: str
    code: str
    level: int
    parent_id: Optional[int] = None

    class Config:
        from_attributes = True


class SupplierBase(BaseModel):
    name: str = Field(..., max_length=200)
    code: str = Field(..., max_length=50)
    type: SupplierType
    contact_person: Optional[str] = Field(None, max_length=100)
    contact_phone: Optional[str] = Field(None, max_length=50)
    contact_email: Optional[str] = Field(None, max_length=200)
    address: Optional[str] = None
    bank_account: Optional[str] = Field(None, max_length=100)
    bank_name: Optional[str] = Field(None, max_length=200)
    tax_id: Optional[str] = Field(None, max_length=50)
    is_preferred: bool = False
    notes: Optional[str] = None


class SupplierCreate(SupplierBase):
    category_ids: List[int] = Field(default_factory=list, description="关联的分类ID列表")


class SupplierUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    type: Optional[SupplierType] = None
    contact_person: Optional[str] = Field(None, max_length=100)
    contact_phone: Optional[str] = Field(None, max_length=50)
    contact_email: Optional[str] = Field(None, max_length=200)
    address: Optional[str] = None
    bank_account: Optional[str] = Field(None, max_length=100)
    bank_name: Optional[str] = Field(None, max_length=200)
    tax_id: Optional[str] = Field(None, max_length=50)
    is_preferred: Optional[bool] = None
    notes: Optional[str] = None
    category_ids: Optional[List[int]] = Field(None, description="更新关联的分类ID列表")


class SupplierResponse(SupplierBase):
    id: int
    qualification_status: Optional[str] = None
    business_license: Optional[str] = None
    industry_qualification: Optional[str] = None
    admission_date: Optional[str] = None
    last_evaluation_date: Optional[str] = None
    evaluation_score: Optional[Decimal] = None
    evaluation_level: Optional[str] = None
    categories: List[SupplierCategoryBrief] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    name: str = Field(..., max_length=500)
    code: str = Field(..., max_length=50)
    specification: Optional[str] = Field(None, max_length=500)
    unit: str = Field(..., max_length=50)
    brand: Optional[str] = Field(None, max_length=200)
    hs_code: Optional[str] = Field(None, max_length=20)
    tax_refund_rate: Optional[Decimal] = None
    shelf_life: Optional[int] = None
    category: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=500)
    specification: Optional[str] = Field(None, max_length=500)
    unit: Optional[str] = Field(None, max_length=50)
    brand: Optional[str] = Field(None, max_length=200)
    hs_code: Optional[str] = Field(None, max_length=20)
    tax_refund_rate: Optional[Decimal] = None
    shelf_life: Optional[int] = None
    category: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SupplierQuoteBase(BaseModel):
    supplier_id: int
    product_id: int
    unit_price: Decimal
    currency: Currency = Currency.CNY
    min_quantity: Optional[Decimal] = None
    lead_time: Optional[int] = None
    valid_until: Optional[date] = None
    is_preferred: bool = False
    notes: Optional[str] = None


class SupplierQuoteCreate(SupplierQuoteBase):
    pass


class SupplierQuoteUpdate(BaseModel):
    unit_price: Optional[Decimal] = None
    currency: Optional[Currency] = None
    min_quantity: Optional[Decimal] = None
    lead_time: Optional[int] = None
    valid_until: Optional[date] = None
    is_preferred: Optional[bool] = None
    notes: Optional[str] = None


class SupplierQuoteResponse(SupplierQuoteBase):
    id: int
    created_at: datetime
    updated_at: datetime
    supplier_name: Optional[str] = None
    product_name: Optional[str] = None

    class Config:
        from_attributes = True


class ProductWithSupplierQuotes(ProductResponse):
    supplier_quotes: List[SupplierQuoteResponse] = []

