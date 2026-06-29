"""Settlement Router"""
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
from app.models.settlement import Settlement, CostItem, CostCategory, ExchangeRate, SettlementStatus
from app.models.order import Order, Currency
from app.models.contract import Contract, PaymentRecord
from app.models.procurement import Disbursement
from app.schemas.settlement import (
    SettlementCreate, SettlementUpdate, SettlementResponse, SettlementDetail,
    SettlementApproval, SettlementStatusUpdate,
    CostItemCreate, CostItemUpdate, CostItemResponse,
    CostCategoryCreate, CostCategoryResponse,
    ExchangeRateCreate, ExchangeRateResponse,
    OrderCostSummary
)
from app.schemas.common import PageResponse

router = APIRouter(prefix="/settlements", tags=["结项管理"])


def generate_settlement_no() -> str:
    import datetime
    today = datetime.date.today()
    return f"SET{today.strftime('%Y%m%d')}{int(datetime.datetime.now().timestamp() * 1000) % 10000:04d}"


# Cost Category routes - 必须在 /{settlement_id} 之前定义
@router.get("/categories", response_model=list[CostCategoryResponse])
async def list_cost_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.SETTLEMENT, Action.READ))
):
    """获取费用科目列表"""
    result = await db.execute(select(CostCategory).order_by(CostCategory.sort_order))
    return result.scalars().all()


@router.post("/categories", response_model=CostCategoryResponse)
async def create_cost_category(
    data: CostCategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.SETTLEMENT, Action.CREATE))
):
    """创建费用科目"""
    category = CostCategory(**data.model_dump())
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


# Cost Item routes - 必须在 /{settlement_id} 之前定义
@router.post("/costs", response_model=CostItemResponse)
async def create_cost_item(
    data: CostItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.SETTLEMENT, Action.CREATE))
):
    """录入成本明细"""
    item = CostItem(**data.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    
    category = await db.execute(select(CostCategory).where(CostCategory.id == item.category_id))
    category = category.scalar_one_or_none()
    
    return CostItemResponse(
        **item.__dict__,
        category_name=category.name if category else None
    )


@router.get("/costs", response_model=PageResponse[CostItemResponse])
async def list_cost_items(
    order_id: Optional[int] = Query(None),
    settlement_id: Optional[int] = Query(None),
    category_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.SETTLEMENT, Action.READ))
):
    """获取成本明细列表"""
    query = select(CostItem)
    
    if order_id:
        query = query.where(CostItem.order_id == order_id)
    if settlement_id:
        query = query.where(CostItem.settlement_id == settlement_id)
    if category_id:
        query = query.where(CostItem.category_id == category_id)
    
    query = query.order_by(CostItem.created_at.desc())
    
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0
    
    query = query.offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    items = result.scalars().all()
    
    responses = []
    for item in items:
        category = await db.execute(select(CostCategory).where(CostCategory.id == item.category_id))
        category = category.scalar_one_or_none()
        responses.append(CostItemResponse(
            **item.__dict__,
            category_name=category.name if category else None
        ))
    
    return PageResponse.create(items=responses, total=total, page=page, size=size)


# Exchange Rate routes - 必须在 /{settlement_id} 之前定义
@router.get("/exchange-rates", response_model=list[ExchangeRateResponse])
async def list_exchange_rates(
    from_currency: Optional[Currency] = Query(None),
    to_currency: Optional[Currency] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.SETTLEMENT, Action.READ))
):
    """获取汇率列表"""
    query = select(ExchangeRate)
    if from_currency:
        query = query.where(ExchangeRate.from_currency == from_currency)
    if to_currency:
        query = query.where(ExchangeRate.to_currency == to_currency)
    query = query.order_by(ExchangeRate.effective_date.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/exchange-rates", response_model=ExchangeRateResponse)
async def create_exchange_rate(
    data: ExchangeRateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.SETTLEMENT, Action.CREATE))
):
    """录入汇率"""
    rate = ExchangeRate(**data.model_dump())
    db.add(rate)
    await db.commit()
    await db.refresh(rate)
    return rate


@router.get("/order-summary/{order_id}", response_model=OrderCostSummary)
async def get_order_cost_summary(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.SETTLEMENT, Action.READ))
):
    """获取订单成本汇总"""
    # Get order
    order = await db.execute(select(Order).where(Order.id == order_id))
    order = order.scalar_one_or_none()
    if not order:
        raise NotFoundError("订单", order_id)
    
    # Calculate totals
    total_revenue = order.total_amount
    
    # Get received payments
    payments_result = await db.execute(
        select(func.sum(PaymentRecord.amount_cny))
        .where(PaymentRecord.order_id == order_id)
    )
    total_received = payments_result.scalar() or Decimal("0")
    
    # Get costs
    costs_result = await db.execute(
        select(func.sum(CostItem.amount_cny))
        .where(CostItem.order_id == order_id)
    )
    total_cost = costs_result.scalar() or Decimal("0")
    
    # Get disbursements
    disbursements_result = await db.execute(
        select(func.sum(Disbursement.amount_cny))
        .where(Disbursement.order_id == order_id)
    )
    total_disbursed = disbursements_result.scalar() or Decimal("0")
    
    gross_profit = total_revenue - total_cost
    gross_profit_rate = (gross_profit / total_revenue * 100) if total_revenue > 0 else Decimal("0")
    
    return OrderCostSummary(
        order_id=order_id,
        order_no=order.order_no,
        total_revenue=total_revenue,
        total_cost=total_cost,
        gross_profit=gross_profit,
        gross_profit_rate=gross_profit_rate,
        total_received=total_received,
        total_disbursed=total_disbursed,
        receivable=total_revenue - total_received,
        payable=total_cost - total_disbursed
    )


@router.get("/breakeven/{order_id}")
async def get_breakeven(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.SETTLEMENT, Action.READ))
):
    """盈亏平衡点计算"""
    from app.services.settlement_service import settlement_service
    return await settlement_service.calculate_breakeven(db, order_id)


# Settlement CRUD - 动态路由放在最后
@router.get("", response_model=PageResponse[SettlementResponse])
async def list_settlements(
    keyword: Optional[str] = Query(None),
    status: Optional[SettlementStatus] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.SETTLEMENT, Action.READ))
):
    """获取结项列表"""
    query = select(Settlement)
    
    if keyword:
        query = query.where(Settlement.settlement_no.ilike(f"%{keyword}%"))
    if status:
        query = query.where(Settlement.status == status)
    
    query = query.order_by(Settlement.created_at.desc())
    
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0
    
    query = query.offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return PageResponse.create(items=items, total=total, page=page, size=size)


@router.post("", response_model=SettlementResponse)
async def create_settlement(
    data: SettlementCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.SETTLEMENT, Action.CREATE))
):
    """创建结项申请"""
    # Check order exists
    order = await db.execute(select(Order).where(Order.id == data.order_id))
    order = order.scalar_one_or_none()
    if not order:
        raise NotFoundError("订单", data.order_id)
    
    # Check if settlement already exists for this order
    existing = await db.execute(
        select(Settlement).where(Settlement.order_id == data.order_id)
    )
    if existing.scalar_one_or_none():
        raise ConflictError("该订单已有结项申请")
    
    # Calculate financials
    # Get contract amount
    contract = None
    if data.contract_id:
        contract_result = await db.execute(select(Contract).where(Contract.id == data.contract_id))
        contract = contract_result.scalar_one_or_none()
    
    total_revenue = contract.total_amount if contract else order.total_amount
    
    # Get received payments
    payments_result = await db.execute(
        select(func.sum(PaymentRecord.amount_cny))
        .where(PaymentRecord.order_id == data.order_id)
    )
    total_received = payments_result.scalar() or Decimal("0")
    
    # Get costs
    costs_result = await db.execute(
        select(func.sum(CostItem.amount_cny))
        .where(CostItem.order_id == data.order_id)
    )
    total_cost = costs_result.scalar() or Decimal("0")
    
    # Get disbursements
    disbursements_result = await db.execute(
        select(func.sum(Disbursement.amount_cny))
        .where(Disbursement.order_id == data.order_id)
    )
    total_disbursed = disbursements_result.scalar() or Decimal("0")
    
    gross_profit = total_revenue - total_cost
    gross_profit_rate = (gross_profit / total_revenue * 100) if total_revenue > 0 else Decimal("0")
    received_percentage = (total_received / total_revenue * 100) if total_revenue > 0 else Decimal("0")
    
    settlement = Settlement(
        settlement_no=generate_settlement_no(),
        order_id=data.order_id,
        contract_id=data.contract_id,
        status=SettlementStatus.DRAFT,
        total_revenue=total_revenue,
        revenue_currency=order.currency,
        total_revenue_cny=total_revenue,  # Simplified, should convert if different currency
        total_cost=total_cost,
        cost_currency=Currency.CNY,
        total_cost_cny=total_cost,
        total_received=total_received,
        received_percentage=received_percentage,
        total_disbursed=total_disbursed,
        pending_disbursement=total_cost - total_disbursed,
        gross_profit=gross_profit,
        gross_profit_rate=gross_profit_rate,
        applicant_id=current_user.id,
        apply_date=date.today(),
        notes=data.notes
    )
    db.add(settlement)
    await db.commit()
    await db.refresh(settlement)
    return settlement


@router.get("/{settlement_id}", response_model=SettlementDetail)
async def get_settlement(
    settlement_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.SETTLEMENT, Action.READ))
):
    """获取结项详情"""
    result = await db.execute(
        select(Settlement)
        .options(selectinload(Settlement.cost_items))
        .where(Settlement.id == settlement_id)
    )
    settlement = result.scalar_one_or_none()
    if not settlement:
        raise NotFoundError("结项", settlement_id)
    
    # Get related info
    order = await db.execute(select(Order).where(Order.id == settlement.order_id))
    order = order.scalar_one_or_none()
    
    contract = None
    if settlement.contract_id:
        contract_result = await db.execute(select(Contract).where(Contract.id == settlement.contract_id))
        contract = contract_result.scalar_one_or_none()
    
    applicant = await db.execute(select(User).where(User.id == settlement.applicant_id))
    applicant = applicant.scalar_one_or_none()
    
    approver = None
    if settlement.approver_id:
        approver_result = await db.execute(select(User).where(User.id == settlement.approver_id))
        approver = approver_result.scalar_one_or_none()
    
    # Get cost items with category names
    cost_items = []
    for item in settlement.cost_items:
        category = await db.execute(select(CostCategory).where(CostCategory.id == item.category_id))
        category = category.scalar_one_or_none()
        cost_items.append(CostItemResponse(
            **item.__dict__,
            category_name=category.name if category else None
        ))
    
    return SettlementDetail(
        **settlement.__dict__,
        cost_items=cost_items,
        order_no=order.order_no if order else None,
        contract_no=contract.contract_no if contract else None,
        applicant_name=applicant.real_name if applicant else None,
        approver_name=approver.real_name if approver else None
    )


@router.post("/{settlement_id}/submit", response_model=SettlementResponse)
async def submit_settlement(
    settlement_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.SETTLEMENT, Action.UPDATE))
):
    """提交结项审批"""
    result = await db.execute(select(Settlement).where(Settlement.id == settlement_id))
    settlement = result.scalar_one_or_none()
    if not settlement:
        raise NotFoundError("结项", settlement_id)
    
    if settlement.status != SettlementStatus.DRAFT:
        raise ConflictError("只能提交草稿状态的结项")
    
    settlement.status = SettlementStatus.PENDING_APPROVAL
    await db.commit()
    await db.refresh(settlement)
    return settlement


@router.post("/{settlement_id}/approve", response_model=SettlementResponse)
async def approve_settlement(
    settlement_id: int,
    data: SettlementApproval,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.SETTLEMENT, Action.APPROVE))
):
    """审批结项"""
    # Only OWNER or FIN can approve
    if current_user.role not in [UserRole.OWNER, UserRole.FIN]:
        raise ForbiddenError("无权审批结项")
    
    result = await db.execute(select(Settlement).where(Settlement.id == settlement_id))
    settlement = result.scalar_one_or_none()
    if not settlement:
        raise NotFoundError("结项", settlement_id)
    
    if settlement.status != SettlementStatus.PENDING_APPROVAL:
        raise ConflictError("只能审批待审批状态的结项")
    
    if data.approved:
        settlement.status = SettlementStatus.APPROVED
    else:
        settlement.status = SettlementStatus.REJECTED
        settlement.reject_reason = data.reject_reason
    
    settlement.approver_id = current_user.id
    settlement.approve_date = date.today()
    
    await db.commit()
    await db.refresh(settlement)

    try:
        from app.services.workflow_hooks import on_entity_status_change
        if settlement.order_id:
            await on_entity_status_change(
                db, entity_type="settlement", entity_id=settlement.id,
                new_status=settlement.status.value,
                order_id=settlement.order_id,
                operator_id=current_user.id,
            )
    except Exception:
        pass

    if settlement.status == SettlementStatus.APPROVED:
        try:
            from app.integrations.kingdee.sync_service import KingdeeSyncService
            svc = KingdeeSyncService()
            await svc.sync_settlement(db, settlement.id)
            await db.commit()
        except Exception as exc:
            import logging
            logging.getLogger("kingdee.sync").warning("Settlement #%d auto-sync failed: %s", settlement.id, exc)

    return settlement



