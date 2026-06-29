"""Product and Supplier Router"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, UploadFile, File
from app.core.exceptions import NotFoundError, ConflictError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.deps import get_db
from app.core.rbac import require_permission, Resource, Action
from app.models.user import User
from app.models.product import Product, Supplier, SupplierQuote, SupplierType, SupplierCategory
from app.schemas.product import (
    ProductCreate, ProductUpdate, ProductResponse, ProductWithSupplierQuotes,
    SupplierCreate, SupplierUpdate, SupplierResponse,
    SupplierQuoteCreate, SupplierQuoteUpdate, SupplierQuoteResponse,
    SupplierCategoryCreate, SupplierCategoryUpdate, SupplierCategoryResponse, SupplierCategoryTree,
)
from app.schemas.common import PageResponse

router = APIRouter(prefix="/products", tags=["商品管理"])
supplier_router = APIRouter(prefix="/suppliers", tags=["供应商管理"])
category_router = APIRouter(prefix="/supplier-categories", tags=["供应商分类"])


@router.get("", response_model=PageResponse[ProductResponse])
async def list_products(
    keyword: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.PRODUCT, Action.READ))
):
    """获取商品列表"""
    query = select(Product)
    
    if keyword:
        query = query.where(
            Product.name.ilike(f"%{keyword}%") | 
            Product.code.ilike(f"%{keyword}%")
        )
    if category:
        query = query.where(Product.category == category)
    
    query = query.order_by(Product.created_at.desc())
    
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0
    
    query = query.offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return PageResponse.create(items=items, total=total, page=page, size=size)


@router.post("", response_model=ProductResponse)
async def create_product(
    data: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.PRODUCT, Action.CREATE))
):
    """创建商品"""
    existing = await db.execute(select(Product).where(Product.code == data.code))
    if existing.scalar_one_or_none():
        raise ConflictError("商品编码已存在")
    
    product = Product(**data.model_dump())
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


@router.get("/{product_id}", response_model=ProductWithSupplierQuotes)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.PRODUCT, Action.READ))
):
    """获取商品详情"""
    result = await db.execute(
        select(Product)
        .options(selectinload(Product.supplier_quotes))
        .where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise NotFoundError("商品", product_id)
    
    # Get supplier names
    supplier_quotes = []
    for sq in product.supplier_quotes:
        supplier = await db.execute(select(Supplier).where(Supplier.id == sq.supplier_id))
        supplier = supplier.scalar_one_or_none()
        supplier_quotes.append(
            SupplierQuoteResponse(
                **sq.__dict__,
                supplier_name=supplier.name if supplier else None,
                product_name=product.name
            )
        )
    
    return ProductWithSupplierQuotes(
        **product.__dict__,
        supplier_quotes=supplier_quotes
    )


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    data: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.PRODUCT, Action.UPDATE))
):
    """更新商品"""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise NotFoundError("商品", product_id)
    
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(product, key, value)
    
    await db.commit()
    await db.refresh(product)
    return product


@router.delete("/{product_id}")
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.PRODUCT, Action.DELETE))
):
    """删除商品"""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise NotFoundError("商品", product_id)
    
    await db.delete(product)
    await db.commit()
    return {"message": "删除成功"}


# Supplier match
@supplier_router.get("/match", response_model=List[SupplierResponse])
async def match_suppliers_endpoint(
    category_ids: str = Query(..., description="逗号分隔的分类ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.SUPPLIER, Action.READ))
):
    """根据分类自动匹配合格供应商"""
    from app.services.supplier_match_service import match_suppliers
    ids = [int(x.strip()) for x in category_ids.split(",") if x.strip()]
    items = await match_suppliers(db, ids)
    return items


# Supplier routes
@supplier_router.get("", response_model=PageResponse[SupplierResponse])
async def list_suppliers(
    keyword: Optional[str] = Query(None),
    type: Optional[SupplierType] = Query(None),
    is_preferred: Optional[bool] = Query(None),
    category_id: Optional[int] = Query(None, description="按分类ID筛选（支持一级或二级）"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.SUPPLIER, Action.READ))
):
    """获取供应商列表（支持按分类筛选）"""
    filters = []
    if keyword:
        filters.append(Supplier.name.ilike(f"%{keyword}%") | Supplier.code.ilike(f"%{keyword}%"))
    if type:
        filters.append(Supplier.type == type)
    if is_preferred is not None:
        filters.append(Supplier.is_preferred == is_preferred)
    if category_id is not None:
        # 如果选的是一级分类，把其下所有二级ID也纳入筛选
        cat = (await db.execute(select(SupplierCategory).where(SupplierCategory.id == category_id))).scalar_one_or_none()
        if cat and cat.level == 1:
            child_ids = (await db.execute(
                select(SupplierCategory.id).where(SupplierCategory.parent_id == category_id)
            )).scalars().all()
            all_ids = [category_id, *child_ids]
            filters.append(Supplier.categories.any(SupplierCategory.id.in_(all_ids)))
        else:
            filters.append(Supplier.categories.any(SupplierCategory.id == category_id))

    count_q = select(func.count(Supplier.id)).where(*filters)
    total = (await db.execute(count_q)).scalar() or 0

    query = (
        select(Supplier)
        .options(selectinload(Supplier.categories))
        .where(*filters)
        .order_by(Supplier.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    result = await db.execute(query)
    items = result.unique().scalars().all()

    return PageResponse.create(items=items, total=total, page=page, size=size)


@supplier_router.post("", response_model=SupplierResponse)
async def create_supplier(
    data: SupplierCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.SUPPLIER, Action.CREATE))
):
    """创建供应商（可同时关联分类）"""
    existing = await db.execute(select(Supplier).where(Supplier.code == data.code))
    if existing.scalar_one_or_none():
        raise ConflictError("供应商编码已存在")

    payload = data.model_dump(exclude={"category_ids"})
    supplier = Supplier(**payload)

    if data.category_ids:
        cats = (await db.execute(
            select(SupplierCategory).where(SupplierCategory.id.in_(data.category_ids))
        )).scalars().all()
        supplier.categories = list(cats)

    db.add(supplier)
    await db.commit()
    await db.refresh(supplier, attribute_names=["categories"])
    return supplier


@supplier_router.get("/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(
    supplier_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.SUPPLIER, Action.READ))
):
    """获取供应商详情"""
    result = await db.execute(
        select(Supplier).options(selectinload(Supplier.categories)).where(Supplier.id == supplier_id)
    )
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise NotFoundError("供应商", supplier_id)
    return supplier


@supplier_router.put("/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    supplier_id: int,
    data: SupplierUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.SUPPLIER, Action.UPDATE))
):
    """更新供应商（可更新分类关联）"""
    result = await db.execute(
        select(Supplier).options(selectinload(Supplier.categories)).where(Supplier.id == supplier_id)
    )
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise NotFoundError("供应商", supplier_id)

    update_data = data.model_dump(exclude_unset=True, exclude={"category_ids"})
    for key, value in update_data.items():
        setattr(supplier, key, value)

    if data.category_ids is not None:
        cats = (await db.execute(
            select(SupplierCategory).where(SupplierCategory.id.in_(data.category_ids))
        )).scalars().all()
        supplier.categories = list(cats)

    await db.commit()
    await db.refresh(supplier, attribute_names=["categories"])
    return supplier


@supplier_router.delete("/{supplier_id}")
async def delete_supplier(
    supplier_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.SUPPLIER, Action.DELETE))
):
    """删除供应商"""
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise NotFoundError("供应商", supplier_id)
    
    await db.delete(supplier)
    await db.commit()
    return {"message": "删除成功"}


# Supplier Quote routes
@supplier_router.post("/quotes", response_model=SupplierQuoteResponse)
async def create_supplier_quote(
    data: SupplierQuoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.SUPPLIER, Action.CREATE))
):
    """创建供应商报价"""
    # Check supplier exists
    supplier = await db.execute(select(Supplier).where(Supplier.id == data.supplier_id))
    if not supplier.scalar_one_or_none():
        raise NotFoundError("供应商", data.supplier_id)
    
    # Check product exists
    product = await db.execute(select(Product).where(Product.id == data.product_id))
    if not product.scalar_one_or_none():
        raise NotFoundError("商品", data.product_id)
    
    quote = SupplierQuote(**data.model_dump())
    db.add(quote)
    await db.commit()
    await db.refresh(quote)
    return quote


@supplier_router.get("/{supplier_id}/quotes", response_model=List[SupplierQuoteResponse])
async def list_supplier_quotes(
    supplier_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.SUPPLIER, Action.READ))
):
    """获取供应商的报价列表"""
    result = await db.execute(
        select(SupplierQuote).where(SupplierQuote.supplier_id == supplier_id)
    )
    quotes = result.scalars().all()
    
    # Get product names
    quote_responses = []
    for q in quotes:
        product = await db.execute(select(Product).where(Product.id == q.product_id))
        product = product.scalar_one_or_none()
        quote_responses.append(
            SupplierQuoteResponse(
                **q.__dict__,
                product_name=product.name if product else None
            )
        )
    
    return quote_responses


@supplier_router.put("/quotes/{quote_id}", response_model=SupplierQuoteResponse)
async def update_supplier_quote(
    quote_id: int,
    data: SupplierQuoteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.SUPPLIER, Action.UPDATE))
):
    """更新供应商报价"""
    result = await db.execute(select(SupplierQuote).where(SupplierQuote.id == quote_id))
    quote = result.scalar_one_or_none()
    if not quote:
        raise NotFoundError("报价", quote_id)
    
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(quote, key, value)
    
    await db.commit()
    await db.refresh(quote)
    return quote


@supplier_router.delete("/quotes/{quote_id}")
async def delete_supplier_quote(
    quote_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.SUPPLIER, Action.DELETE))
):
    """删除供应商报价"""
    result = await db.execute(select(SupplierQuote).where(SupplierQuote.id == quote_id))
    quote = result.scalar_one_or_none()
    if not quote:
        raise NotFoundError("报价", quote_id)
    
    await db.delete(quote)
    await db.commit()
    return {"message": "删除成功"}


@supplier_router.post("/quotes/import")
async def import_supplier_quotes(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.SUPPLIER, Action.CREATE))
):
    """批量导入供应商报价 (Excel: supplier_id, product_id, unit_price, currency, lead_time)"""
    import io
    try:
        import openpyxl
    except ImportError:
        return {"error": "openpyxl not installed"}

    content = await file.read()
    wb = openpyxl.load_workbook(io.BytesIO(content))
    ws = wb.active
    rows = list(ws.iter_rows(min_row=2, values_only=True))
    created = 0
    from decimal import Decimal
    from app.models.order import Currency

    for row in rows:
        if not row or len(row) < 3:
            continue
        supplier_id, product_id, unit_price = int(row[0]), int(row[1]), Decimal(str(row[2]))
        currency_str = str(row[3]).upper() if len(row) > 3 and row[3] else "CNY"
        lead_time = int(row[4]) if len(row) > 4 and row[4] else None

        sq = SupplierQuote(
            supplier_id=supplier_id,
            product_id=product_id,
            unit_price=unit_price,
            currency=Currency(currency_str) if currency_str in [c.value for c in Currency] else Currency.CNY,
            lead_time=lead_time,
        )
        db.add(sq)
        created += 1

    await db.commit()
    return {"message": f"成功导入 {created} 条报价", "count": created}


# ---------------------------------------------------------------------------
# Supplier Category routes
# ---------------------------------------------------------------------------

@category_router.get("/tree", response_model=List[SupplierCategoryTree])
async def get_category_tree(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.SUPPLIER, Action.READ))
):
    """获取供应商分类树（一级→二级）"""
    result = await db.execute(
        select(SupplierCategory)
        .options(selectinload(SupplierCategory.children))
        .where(SupplierCategory.level == 1)
        .order_by(SupplierCategory.sort_order)
    )
    roots = result.unique().scalars().all()
    return roots


@category_router.get("", response_model=List[SupplierCategoryResponse])
async def list_categories(
    level: Optional[int] = Query(None, ge=1, le=2),
    parent_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.SUPPLIER, Action.READ))
):
    """获取供应商分类列表（可按 level / parent_id 筛选）"""
    query = select(SupplierCategory).order_by(SupplierCategory.level, SupplierCategory.sort_order)
    if level is not None:
        query = query.where(SupplierCategory.level == level)
    if parent_id is not None:
        query = query.where(SupplierCategory.parent_id == parent_id)
    result = await db.execute(query)
    return result.scalars().all()


@category_router.post("", response_model=SupplierCategoryResponse)
async def create_category(
    data: SupplierCategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.SUPPLIER, Action.CREATE))
):
    """创建供应商分类"""
    existing = await db.execute(select(SupplierCategory).where(SupplierCategory.code == data.code))
    if existing.scalar_one_or_none():
        raise ConflictError("分类编码已存在")
    if data.level == 2 and data.parent_id is None:
        raise ConflictError("二级分类必须指定一级分类 parent_id")
    cat = SupplierCategory(**data.model_dump())
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return cat


@category_router.put("/{category_id}", response_model=SupplierCategoryResponse)
async def update_category(
    category_id: int,
    data: SupplierCategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.SUPPLIER, Action.UPDATE))
):
    """更新供应商分类"""
    result = await db.execute(select(SupplierCategory).where(SupplierCategory.id == category_id))
    cat = result.scalar_one_or_none()
    if not cat:
        raise NotFoundError("分类", category_id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(cat, key, value)
    await db.commit()
    await db.refresh(cat)
    return cat


@category_router.delete("/{category_id}")
async def delete_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.SUPPLIER, Action.DELETE))
):
    """删除供应商分类"""
    result = await db.execute(select(SupplierCategory).where(SupplierCategory.id == category_id))
    cat = result.scalar_one_or_none()
    if not cat:
        raise NotFoundError("分类", category_id)
    await db.delete(cat)
    await db.commit()
    return {"message": "删除成功"}

