"""
Product and Supplier Models
"""
from __future__ import annotations

from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from decimal import Decimal
from datetime import date

from sqlalchemy import String, Text, ForeignKey, Numeric, Date, Integer, Boolean, Enum as SQLEnum, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.order import Currency

if TYPE_CHECKING:
    from app.models.inventory import InventoryBatch


class SupplierType(str, Enum):
    """供应商类型"""
    GOODS = "GOODS"
    SERVICE = "SERVICE"


# Many-to-many: Supplier <-> SupplierCategory
supplier_category_link = Table(
    "supplier_category_links",
    Base.metadata,
    Column("supplier_id", Integer, ForeignKey("suppliers.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", Integer, ForeignKey("supplier_categories.id", ondelete="CASCADE"), primary_key=True),
)


class SupplierCategory(Base):
    """供应商分类（两级树形结构）
    level=1 一级分类（服务种类）：备件、维修、检测…
    level=2 二级分类（项目大类）：甲板舾装、柴油机…
    """
    __tablename__ = "supplier_categories"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("supplier_categories.id"), index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[Optional[str]] = mapped_column(String(500))

    parent: Mapped[Optional["SupplierCategory"]] = relationship(
        "SupplierCategory", remote_side="SupplierCategory.id", back_populates="children",
    )
    children: Mapped[List["SupplierCategory"]] = relationship(
        "SupplierCategory", back_populates="parent", cascade="all, delete-orphan",
    )
    suppliers: Mapped[List["Supplier"]] = relationship(
        "Supplier", secondary=supplier_category_link, back_populates="categories",
    )


class Supplier(Base):
    """供应商/服务商"""
    __tablename__ = "suppliers"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    type: Mapped[SupplierType] = mapped_column(SQLEnum(SupplierType, create_type=False), nullable=False)
    contact_person: Mapped[Optional[str]] = mapped_column(String(100))
    contact_phone: Mapped[Optional[str]] = mapped_column(String(50))
    contact_email: Mapped[Optional[str]] = mapped_column(String(200))
    address: Mapped[Optional[str]] = mapped_column(Text)
    bank_account: Mapped[Optional[str]] = mapped_column(String(100))
    bank_name: Mapped[Optional[str]] = mapped_column(String(200))
    tax_id: Mapped[Optional[str]] = mapped_column(String(50))
    is_preferred: Mapped[bool] = mapped_column(Boolean, default=False)
    qualification_status: Mapped[Optional[str]] = mapped_column(String(20), default="QUALIFIED")
    business_license: Mapped[Optional[str]] = mapped_column(String(200))
    industry_qualification: Mapped[Optional[str]] = mapped_column(Text)
    admission_date: Mapped[Optional[date]] = mapped_column(Date)
    last_evaluation_date: Mapped[Optional[date]] = mapped_column(Date)
    evaluation_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    evaluation_level: Mapped[Optional[str]] = mapped_column(String(20))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    quotes: Mapped[List["SupplierQuote"]] = relationship("SupplierQuote", back_populates="supplier")
    categories: Mapped[List["SupplierCategory"]] = relationship(
        "SupplierCategory", secondary=supplier_category_link, back_populates="suppliers",
    )


class Product(Base):
    """商品"""
    __tablename__ = "products"

    name: Mapped[str] = mapped_column(String(500), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    specification: Mapped[Optional[str]] = mapped_column(String(500))
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    brand: Mapped[Optional[str]] = mapped_column(String(200))
    hs_code: Mapped[Optional[str]] = mapped_column(String(20))
    tax_refund_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    shelf_life: Mapped[Optional[int]] = mapped_column(Integer)  # 保质期（天）
    category: Mapped[Optional[str]] = mapped_column(String(100))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    supplier_quotes: Mapped[List["SupplierQuote"]] = relationship("SupplierQuote", back_populates="product")
    inventory_batches: Mapped[List["InventoryBatch"]] = relationship("InventoryBatch", back_populates="product")


class SupplierQuote(Base):
    """供应商报价"""
    __tablename__ = "supplier_quotes"

    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    currency: Mapped[Currency] = mapped_column(SQLEnum(Currency, create_type=False), default=Currency.CNY)
    min_quantity: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4))
    lead_time: Mapped[Optional[int]] = mapped_column(Integer)  # 交货期（天）
    valid_until: Mapped[Optional[date]] = mapped_column(Date)
    is_preferred: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    supplier: Mapped["Supplier"] = relationship("Supplier", back_populates="quotes")
    product: Mapped["Product"] = relationship("Product", back_populates="supplier_quotes")
