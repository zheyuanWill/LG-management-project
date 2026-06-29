"""Inventory Router"""
from typing import Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, Query
from app.core.exceptions import NotFoundError, ForbiddenError, ConflictError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.deps import get_db
from app.core.rbac import require_permission, Resource, Action
from app.models.user import User, UserRole
from app.models.inventory import InventoryBatch, InventoryMovement, InventoryReservation, InventoryMovementType
from app.models.product import Product
from app.models.order import Order
from app.schemas.inventory import (
    InventoryBatchCreate, InventoryBatchUpdate, InventoryBatchResponse,
    InventoryMovementCreate, InventoryMovementResponse,
    InventoryReservationCreate, InventoryReservationResponse,
    ProductInventorySummary
)
from app.schemas.common import PageResponse

router = APIRouter(prefix="/inventory", tags=["库存管理"])


@router.get("/batches", response_model=PageResponse[InventoryBatchResponse])
async def list_inventory_batches(
    product_id: Optional[int] = Query(None),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.INVENTORY, Action.READ))
):
    """获取库存批次列表"""
    query = select(InventoryBatch)
    
    if product_id:
        query = query.where(InventoryBatch.product_id == product_id)
    
    if keyword:
        # Join product table for keyword search
        query = query.join(Product).where(
            Product.name.ilike(f"%{keyword}%") | 
            Product.code.ilike(f"%{keyword}%") |
            InventoryBatch.batch_no.ilike(f"%{keyword}%")
        )
    
    query = query.order_by(InventoryBatch.created_at.desc())
    
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0
    
    query = query.offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    batches = result.scalars().all()
    
    # Batch-load product names to avoid N+1 queries
    product_ids = list({b.product_id for b in batches if b.product_id})
    products_map: dict = {}
    if product_ids:
        products_result = await db.execute(
            select(Product).where(Product.id.in_(product_ids))
        )
        products_map = {p.id: p for p in products_result.scalars().all()}
    
    responses = []
    for batch in batches:
        product = products_map.get(batch.product_id)
        responses.append(
            InventoryBatchResponse(
                **batch.__dict__,
                available_quantity=batch.quantity - batch.reserved_quantity,
                product_name=product.name if product else None
            )
        )
    
    return PageResponse.create(items=responses, total=total, page=page, size=size)


@router.post("/batches", response_model=InventoryBatchResponse)
async def create_inventory_batch(
    data: InventoryBatchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.INVENTORY, Action.CREATE))
):
    """创建库存批次（手动入库）"""
    # Only OPS can create inventory
    if current_user.role not in [UserRole.OPS, UserRole.OWNER]:
        raise ForbiddenError("无权创建库存")
    
    # Check product exists
    product = await db.execute(select(Product).where(Product.id == data.product_id))
    product = product.scalar_one_or_none()
    if not product:
        raise NotFoundError("商品", data.product_id)
    
    batch = InventoryBatch(
        product_id=data.product_id,
        batch_no=data.batch_no,
        quantity=data.quantity,
        unit_cost=data.unit_cost,
        currency=data.currency,
        expiry_date=data.expiry_date,
        location=data.location,
        procurement_id=data.procurement_id,
        notes=data.notes
    )
    db.add(batch)
    
    # Create movement record
    movement = InventoryMovement(
        product_id=data.product_id,
        type=InventoryMovementType.IN,
        quantity=data.quantity,
        operator_id=current_user.id,
        notes=f"手动入库 - {data.batch_no}"
    )
    db.add(movement)
    
    await db.commit()
    await db.refresh(batch)
    
    return InventoryBatchResponse(
        **batch.__dict__,
        available_quantity=batch.quantity - batch.reserved_quantity,
        product_name=product.name
    )


@router.put("/batches/{batch_id}", response_model=InventoryBatchResponse)
async def update_inventory_batch(
    batch_id: int,
    data: InventoryBatchUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.INVENTORY, Action.UPDATE))
):
    """更新库存批次"""
    result = await db.execute(select(InventoryBatch).where(InventoryBatch.id == batch_id))
    batch = result.scalar_one_or_none()
    if not batch:
        raise NotFoundError("库存批次", batch_id)
    
    # Track quantity change
    old_quantity = batch.quantity
    
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(batch, key, value)
    
    # If quantity changed, create adjustment movement
    if data.quantity is not None and data.quantity != old_quantity:
        diff = data.quantity - old_quantity
        movement = InventoryMovement(
            product_id=batch.product_id,
            batch_id=batch.id,
            type=InventoryMovementType.ADJUST,
            quantity=diff,
            operator_id=current_user.id,
            notes=f"库存调整 - {batch.batch_no}"
        )
        db.add(movement)
    
    await db.commit()
    await db.refresh(batch)
    
    product = await db.execute(select(Product).where(Product.id == batch.product_id))
    product = product.scalar_one_or_none()
    
    return InventoryBatchResponse(
        **batch.__dict__,
        available_quantity=batch.quantity - batch.reserved_quantity,
        product_name=product.name if product else None
    )


@router.get("/movements", response_model=PageResponse[InventoryMovementResponse])
async def list_inventory_movements(
    product_id: Optional[int] = Query(None),
    batch_id: Optional[int] = Query(None),
    type: Optional[InventoryMovementType] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.INVENTORY, Action.READ))
):
    """获取库存变动记录"""
    query = select(InventoryMovement)
    
    if product_id:
        query = query.where(InventoryMovement.product_id == product_id)
    if batch_id:
        query = query.where(InventoryMovement.batch_id == batch_id)
    if type:
        query = query.where(InventoryMovement.type == type)
    
    query = query.order_by(InventoryMovement.created_at.desc())
    
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0
    
    query = query.offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    movements = result.scalars().all()
    
    responses = []
    for m in movements:
        product = await db.execute(select(Product).where(Product.id == m.product_id))
        product = product.scalar_one_or_none()
        operator = await db.execute(select(User).where(User.id == m.operator_id))
        operator = operator.scalar_one_or_none()
        responses.append(
            InventoryMovementResponse(
                **m.__dict__,
                product_name=product.name if product else None,
                operator_name=operator.real_name if operator else None
            )
        )
    
    return PageResponse.create(items=responses, total=total, page=page, size=size)


@router.post("/reserve", response_model=InventoryReservationResponse)
async def reserve_inventory(
    data: InventoryReservationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.INVENTORY, Action.UPDATE))
):
    """预留库存"""
    # Check batch exists and has enough quantity
    batch = await db.execute(select(InventoryBatch).where(InventoryBatch.id == data.batch_id))
    batch = batch.scalar_one_or_none()
    if not batch:
        raise NotFoundError("库存批次", data.batch_id)
    
    available = batch.quantity - batch.reserved_quantity
    if data.quantity > available:
        raise ConflictError(f"可用库存不足，当前可用: {available}")
    
    # Check order exists
    order = await db.execute(select(Order).where(Order.id == data.order_id))
    if not order.scalar_one_or_none():
        raise NotFoundError("订单", data.order_id)
    
    reservation = InventoryReservation(
        batch_id=data.batch_id,
        order_id=data.order_id,
        quantity=data.quantity,
        notes=data.notes
    )
    db.add(reservation)
    
    # Update batch reserved quantity
    batch.reserved_quantity += data.quantity
    
    # Create movement record
    movement = InventoryMovement(
        product_id=batch.product_id,
        batch_id=batch.id,
        type=InventoryMovementType.RESERVE,
        quantity=data.quantity,
        order_id=data.order_id,
        operator_id=current_user.id,
        notes=f"订单预留 - 订单ID: {data.order_id}"
    )
    db.add(movement)
    
    await db.commit()
    await db.refresh(reservation)
    return reservation


@router.post("/release/{reservation_id}", response_model=InventoryReservationResponse)
async def release_reservation(
    reservation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.INVENTORY, Action.UPDATE))
):
    """释放预留"""
    reservation = await db.execute(
        select(InventoryReservation).where(InventoryReservation.id == reservation_id)
    )
    reservation = reservation.scalar_one_or_none()
    if not reservation:
        raise NotFoundError("预留记录", reservation_id)
    
    # Get batch
    batch = await db.execute(select(InventoryBatch).where(InventoryBatch.id == reservation.batch_id))
    batch = batch.scalar_one_or_none()
    
    # Update batch reserved quantity
    batch.reserved_quantity -= reservation.quantity
    
    # Create movement record
    movement = InventoryMovement(
        product_id=batch.product_id,
        batch_id=batch.id,
        type=InventoryMovementType.RELEASE,
        quantity=reservation.quantity,
        order_id=reservation.order_id,
        operator_id=current_user.id,
        notes=f"释放预留 - 订单ID: {reservation.order_id}"
    )
    db.add(movement)
    
    # Delete reservation
    await db.delete(reservation)
    await db.commit()
    
    return reservation


@router.post("/outbound")
async def outbound_inventory(
    batch_id: int,
    quantity: Decimal,
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.INVENTORY, Action.UPDATE))
):
    """出库"""
    # Only OPS can outbound
    if current_user.role not in [UserRole.OPS, UserRole.OWNER]:
        raise ForbiddenError("无权出库")
    
    batch = await db.execute(select(InventoryBatch).where(InventoryBatch.id == batch_id))
    batch = batch.scalar_one_or_none()
    if not batch:
        raise NotFoundError("库存批次", batch_id)
    
    if batch.quantity < quantity:
        raise ConflictError("库存不足")
    
    # Update batch quantity
    batch.quantity -= quantity
    if batch.reserved_quantity > batch.quantity:
        batch.reserved_quantity = batch.quantity
    
    # Create movement record
    movement = InventoryMovement(
        product_id=batch.product_id,
        batch_id=batch.id,
        type=InventoryMovementType.OUT,
        quantity=quantity,
        order_id=order_id,
        operator_id=current_user.id,
        notes=f"出库 - 订单ID: {order_id}"
    )
    db.add(movement)
    
    await db.commit()
    return {"message": "出库成功"}


@router.get("/summary", response_model=list[ProductInventorySummary])
async def get_inventory_summary(
    keyword: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.INVENTORY, Action.READ))
):
    """获取库存汇总"""
    query = select(Product)
    
    if keyword:
        query = query.where(
            Product.name.ilike(f"%{keyword}%") | 
            Product.code.ilike(f"%{keyword}%")
        )
    
    result = await db.execute(query.limit(100))
    products = result.scalars().all()
    
    summaries = []
    for product in products:
        batches_result = await db.execute(
            select(InventoryBatch).where(
                InventoryBatch.product_id == product.id,
                InventoryBatch.quantity > 0
            )
        )
        batches = batches_result.scalars().all()
        
        total_quantity = sum(b.quantity for b in batches)
        total_reserved = sum(b.reserved_quantity for b in batches)
        
        if total_quantity > 0:
            summaries.append(ProductInventorySummary(
                product_id=product.id,
                product_code=product.code,
                product_name=product.name,
                total_quantity=total_quantity,
                total_reserved=total_reserved,
                available_quantity=total_quantity - total_reserved,
                batches=[
                    InventoryBatchResponse(
                        **b.__dict__,
                        available_quantity=b.quantity - b.reserved_quantity,
                        product_name=product.name
                    ) for b in batches
                ]
            ))
    
    return summaries

