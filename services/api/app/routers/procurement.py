"""Procurement Router"""
from typing import Optional
from decimal import Decimal
from datetime import date
from fastapi import APIRouter, Depends, Query
from app.core.exceptions import NotFoundError, ForbiddenError, ConflictError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.deps import get_db
from app.core.rbac import require_permission, Resource, Action
from app.models.user import User, UserRole
from app.models.procurement import Procurement, ProcurementLineItem, Disbursement, ProcurementStatus
from app.models.product import Supplier, Product
from app.models.order import Order
from app.models.inventory import InventoryBatch, InventoryMovement, InventoryMovementType
from app.schemas.procurement import (
    ProcurementCreate, ProcurementUpdate, ProcurementResponse, ProcurementDetail,
    ProcurementStatusUpdate, ProcurementApproval, ProcurementReceive,
    DisbursementCreate, DisbursementResponse
)
from app.schemas.common import PageResponse

router = APIRouter(prefix="/procurements", tags=["采购管理"])


def generate_procurement_no() -> str:
    """生成采购单号"""
    import datetime
    today = datetime.date.today()
    return f"PO{today.strftime('%Y%m%d')}{int(datetime.datetime.now().timestamp() * 1000) % 10000:04d}"


@router.get("", response_model=PageResponse[ProcurementResponse])
async def list_procurements(
    keyword: Optional[str] = Query(None),
    status: Optional[ProcurementStatus] = Query(None),
    supplier_id: Optional[int] = Query(None),
    order_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.PROCUREMENT, Action.READ))
):
    """获取采购单列表"""
    query = select(Procurement)
    
    # PROC 角色只能看自己创建的
    if current_user.role == UserRole.PROC:
        query = query.where(Procurement.created_by == current_user.id)
    
    if keyword:
        query = query.where(Procurement.procurement_no.ilike(f"%{keyword}%"))
    if status:
        query = query.where(Procurement.status == status)
    if supplier_id:
        query = query.where(Procurement.supplier_id == supplier_id)
    if order_id:
        query = query.where(Procurement.order_id == order_id)
    
    query = query.order_by(Procurement.created_at.desc())
    
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0
    
    query = query.offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return PageResponse.create(items=items, total=total, page=page, size=size)


@router.post("", response_model=ProcurementResponse)
async def create_procurement(
    data: ProcurementCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.PROCUREMENT, Action.CREATE))
):
    """创建采购单"""
    # Check supplier exists
    supplier = await db.execute(select(Supplier).where(Supplier.id == data.supplier_id))
    if not supplier.scalar_one_or_none():
        raise NotFoundError("供应商", data.supplier_id)
    
    procurement_no = generate_procurement_no()
    total_amount = Decimal("0")
    
    procurement = Procurement(
        procurement_no=procurement_no,
        supplier_id=data.supplier_id,
        order_id=data.order_id,
        currency=data.currency,
        expected_date=data.expected_date,
        notes=data.notes,
        created_by=current_user.id,
        status=ProcurementStatus.DRAFT,
        total_amount=total_amount
    )
    db.add(procurement)
    await db.flush()
    
    # Add line items
    for item_data in data.line_items:
        amount = item_data.quantity * item_data.unit_price
        total_amount += amount
        line_item = ProcurementLineItem(
            procurement_id=procurement.id,
            product_id=item_data.product_id,
            product_name=item_data.product_name,
            specification=item_data.specification,
            unit=item_data.unit,
            quantity=item_data.quantity,
            unit_price=item_data.unit_price,
            amount=amount,
            notes=item_data.notes
        )
        db.add(line_item)
    
    procurement.total_amount = total_amount
    await db.commit()
    await db.refresh(procurement)
    return procurement


@router.get("/{procurement_id}", response_model=ProcurementDetail)
async def get_procurement(
    procurement_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.PROCUREMENT, Action.READ))
):
    """获取采购单详情"""
    result = await db.execute(
        select(Procurement)
        .options(selectinload(Procurement.line_items))
        .where(Procurement.id == procurement_id)
    )
    procurement = result.scalar_one_or_none()
    if not procurement:
        raise NotFoundError("采购单", procurement_id)
    
    # Get related info
    supplier = await db.execute(select(Supplier).where(Supplier.id == procurement.supplier_id))
    supplier = supplier.scalar_one_or_none()
    
    order = None
    if procurement.order_id:
        order_result = await db.execute(select(Order).where(Order.id == procurement.order_id))
        order = order_result.scalar_one_or_none()
    
    creator = await db.execute(select(User).where(User.id == procurement.created_by))
    creator = creator.scalar_one_or_none()
    
    approver = None
    if procurement.approved_by:
        approver_result = await db.execute(select(User).where(User.id == procurement.approved_by))
        approver = approver_result.scalar_one_or_none()
    
    return ProcurementDetail(
        **procurement.__dict__,
        line_items=[item for item in procurement.line_items],
        supplier_name=supplier.name if supplier else None,
        order_no=order.order_no if order else None,
        creator_name=creator.real_name if creator else None,
        approver_name=approver.real_name if approver else None
    )


@router.put("/{procurement_id}", response_model=ProcurementResponse)
async def update_procurement(
    procurement_id: int,
    data: ProcurementUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.PROCUREMENT, Action.UPDATE))
):
    """更新采购单"""
    result = await db.execute(select(Procurement).where(Procurement.id == procurement_id))
    procurement = result.scalar_one_or_none()
    if not procurement:
        raise NotFoundError("采购单", procurement_id)
    
    if procurement.status != ProcurementStatus.DRAFT:
        raise ConflictError("只能修改草稿状态的采购单")
    
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(procurement, key, value)
    
    await db.commit()
    await db.refresh(procurement)
    return procurement


@router.post("/{procurement_id}/submit", response_model=ProcurementResponse)
async def submit_procurement(
    procurement_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.PROCUREMENT, Action.UPDATE))
):
    """提交采购单审批"""
    result = await db.execute(select(Procurement).where(Procurement.id == procurement_id))
    procurement = result.scalar_one_or_none()
    if not procurement:
        raise NotFoundError("采购单", procurement_id)
    
    if procurement.status != ProcurementStatus.DRAFT:
        raise ConflictError("只能提交草稿状态的采购单")
    
    procurement.status = ProcurementStatus.PENDING_APPROVAL
    await db.commit()
    await db.refresh(procurement)

    try:
        from app.services.workflow_hooks import on_entity_status_change
        await on_entity_status_change(
            db, entity_type="procurement", entity_id=procurement.id,
            new_status=procurement.status.value, order_id=procurement.order_id,
            operator_id=current_user.id,
        )
    except Exception:
        pass

    return procurement


@router.post("/{procurement_id}/approve", response_model=ProcurementResponse)
async def approve_procurement(
    procurement_id: int,
    data: ProcurementApproval,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.PROCUREMENT, Action.APPROVE))
):
    """审批采购单"""
    # Only OWNER or PM can approve
    if current_user.role not in [UserRole.OWNER, UserRole.PM]:
        raise ForbiddenError("无权审批采购单")
    
    result = await db.execute(select(Procurement).where(Procurement.id == procurement_id))
    procurement = result.scalar_one_or_none()
    if not procurement:
        raise NotFoundError("采购单", procurement_id)
    
    if procurement.status != ProcurementStatus.PENDING_APPROVAL:
        raise ConflictError("只能审批待审批状态的采购单")
    
    if data.approved:
        procurement.status = ProcurementStatus.APPROVED
        procurement.approved_by = current_user.id
        procurement.approved_at = date.today()
    else:
        procurement.status = ProcurementStatus.DRAFT
    
    await db.commit()
    await db.refresh(procurement)

    try:
        from app.services.workflow_hooks import on_entity_status_change
        await on_entity_status_change(
            db, entity_type="procurement", entity_id=procurement.id,
            new_status=procurement.status.value, order_id=procurement.order_id,
            operator_id=current_user.id,
        )
    except Exception:
        pass

    return procurement


@router.post("/{procurement_id}/order", response_model=ProcurementResponse)
async def mark_procurement_ordered(
    procurement_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.PROCUREMENT, Action.UPDATE))
):
    """标记采购单已下单"""
    result = await db.execute(select(Procurement).where(Procurement.id == procurement_id))
    procurement = result.scalar_one_or_none()
    if not procurement:
        raise NotFoundError("采购单", procurement_id)
    
    if procurement.status != ProcurementStatus.APPROVED:
        raise ConflictError("只能将已审批状态的采购单标记为已下单")
    
    procurement.status = ProcurementStatus.ORDERED
    await db.commit()
    await db.refresh(procurement)

    try:
        from app.services.workflow_hooks import on_entity_status_change
        await on_entity_status_change(
            db, entity_type="procurement", entity_id=procurement.id,
            new_status=procurement.status.value, order_id=procurement.order_id,
            operator_id=current_user.id,
        )
    except Exception:
        pass

    return procurement


@router.post("/{procurement_id}/receive", response_model=ProcurementResponse)
async def receive_procurement(
    procurement_id: int,
    data: ProcurementReceive,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.PROCUREMENT, Action.UPDATE))
):
    """收货"""
    result = await db.execute(
        select(Procurement)
        .options(selectinload(Procurement.line_items))
        .where(Procurement.id == procurement_id)
    )
    procurement = result.scalar_one_or_none()
    if not procurement:
        raise NotFoundError("采购单", procurement_id)
    
    if procurement.status not in [ProcurementStatus.ORDERED, ProcurementStatus.PARTIAL_RECEIVED]:
        raise ConflictError("只能对已下单或部分收货状态的采购单收货")
    
    # OPS 角色才能收货
    if current_user.role not in [UserRole.OPS, UserRole.OWNER]:
        raise ForbiddenError("无权收货")
    
    # Process each item
    all_received = True
    import datetime
    batch_no = f"BATCH{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    for receive_item in data.items:
        line_item_id = receive_item.get("line_item_id")
        quantity = Decimal(str(receive_item.get("quantity", 0)))
        
        # Find line item
        line_item = next((li for li in procurement.line_items if li.id == line_item_id), None)
        if not line_item:
            continue
        
        # Update received quantity
        line_item.received_quantity += quantity
        
        if line_item.received_quantity < line_item.quantity:
            all_received = False
        
        # Create inventory batch
        inv_batch = InventoryBatch(
            product_id=line_item.product_id,
            batch_no=batch_no,
            quantity=quantity,
            unit_cost=line_item.unit_price,
            currency=procurement.currency,
            procurement_id=procurement.id
        )
        db.add(inv_batch)
        
        # Create inventory movement
        movement = InventoryMovement(
            product_id=line_item.product_id,
            type=InventoryMovementType.IN,
            quantity=quantity,
            procurement_id=procurement.id,
            order_id=procurement.order_id,
            operator_id=current_user.id,
            notes=f"采购入库 - {procurement.procurement_no}"
        )
        db.add(movement)
    
    # Update procurement status
    if all_received:
        procurement.status = ProcurementStatus.RECEIVED
    else:
        procurement.status = ProcurementStatus.PARTIAL_RECEIVED
    
    await db.commit()
    await db.refresh(procurement)

    try:
        from app.services.workflow_hooks import on_entity_status_change
        await on_entity_status_change(
            db, entity_type="procurement", entity_id=procurement.id,
            new_status=procurement.status.value, order_id=procurement.order_id,
            operator_id=current_user.id,
        )
    except Exception:
        pass

    if procurement.status == ProcurementStatus.RECEIVED:
        try:
            from app.integrations.kingdee.sync_service import KingdeeSyncService
            svc = KingdeeSyncService()
            await svc.sync_procurement_received(db, procurement.id)
            await db.commit()
        except Exception as exc:
            import logging
            logging.getLogger("kingdee.sync").warning("Procurement #%d auto-sync failed: %s", procurement.id, exc)

    return procurement


# Disbursement routes
@router.post("/{procurement_id}/disbursements", response_model=DisbursementResponse)
async def create_disbursement(
    procurement_id: int,
    data: DisbursementCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.PROCUREMENT, Action.UPDATE))
):
    """录入付款记录"""
    # Only FIN can record disbursements
    if current_user.role not in [UserRole.FIN, UserRole.OWNER]:
        raise ForbiddenError("无权录入付款")
    
    # Check procurement exists
    procurement = await db.execute(select(Procurement).where(Procurement.id == procurement_id))
    procurement = procurement.scalar_one_or_none()
    if not procurement:
        raise NotFoundError("采购单", procurement_id)
    
    disbursement = Disbursement(
        procurement_id=procurement_id,
        order_id=data.order_id,
        supplier_id=data.supplier_id,
        amount=data.amount,
        currency=data.currency,
        amount_cny=data.amount_cny,
        payment_date=data.payment_date,
        payment_method=data.payment_method,
        invoice_no=data.invoice_no,
        notes=data.notes
    )
    db.add(disbursement)
    await db.commit()
    await db.refresh(disbursement)

    try:
        from app.services.workflow_hooks import on_entity_status_change
        order_id = data.order_id or procurement.order_id
        if order_id:
            await on_entity_status_change(
                db, entity_type="disbursement", entity_id=disbursement.id,
                new_status="PAID", order_id=order_id,
                operator_id=current_user.id,
            )
    except Exception:
        pass

    try:
        from app.integrations.kingdee.sync_service import KingdeeSyncService
        svc = KingdeeSyncService()
        await svc.sync_disbursement(db, disbursement.id)
        await db.commit()
    except Exception as exc:
        import logging
        logging.getLogger("kingdee.sync").warning("Disbursement #%d auto-sync failed: %s", disbursement.id, exc)

    # Get supplier name
    supplier = await db.execute(select(Supplier).where(Supplier.id == disbursement.supplier_id))
    supplier = supplier.scalar_one_or_none()
    
    return DisbursementResponse(
        **disbursement.__dict__,
        supplier_name=supplier.name if supplier else None
    )


@router.get("/{procurement_id}/disbursements", response_model=list[DisbursementResponse])
async def list_disbursements(
    procurement_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.PROCUREMENT, Action.READ))
):
    """获取采购单付款记录"""
    result = await db.execute(
        select(Disbursement).where(Disbursement.procurement_id == procurement_id)
        .order_by(Disbursement.payment_date.desc())
    )
    disbursements = result.scalars().all()
    
    responses = []
    for d in disbursements:
        supplier = await db.execute(select(Supplier).where(Supplier.id == d.supplier_id))
        supplier = supplier.scalar_one_or_none()
        responses.append(
            DisbursementResponse(
                **d.__dict__,
                supplier_name=supplier.name if supplier else None
            )
        )
    
    return responses

