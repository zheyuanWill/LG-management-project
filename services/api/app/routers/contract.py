"""Contract Router

Thin routing layer — business logic is delegated to ContractService.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.deps import get_db
from app.core.rbac import require_permission, Resource, Action
from app.core.exceptions import NotFoundError, ConflictError
from app.models.user import User
from app.models.contract import Contract, PaymentPlan, PaymentRecord, ContractStatus
from app.models.order import Order
from app.schemas.contract import (
    ContractCreate, ContractUpdate, ContractResponse, ContractDetail,
    ContractStatusUpdate, PaymentPlanUpdate, PaymentPlanResponse,
    PaymentRecordCreate, PaymentRecordResponse
)
from app.schemas.common import PageResponse
from app.services import contract_service

router = APIRouter(prefix="/contracts", tags=["合同管理"])


@router.get("", response_model=PageResponse[ContractResponse])
async def list_contracts(
    keyword: Optional[str] = Query(None),
    status: Optional[ContractStatus] = Query(None),
    customer_id: Optional[int] = Query(None),
    order_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.CONTRACT, Action.READ))
):
    """获取合同列表"""
    items, total = await contract_service.list_contracts(
        db,
        keyword=keyword,
        status=status,
        customer_id=customer_id,
        order_id=order_id,
        page=page,
        size=size,
    )
    return PageResponse.create(items=items, total=total, page=page, size=size)


@router.post("", response_model=ContractResponse)
async def create_contract(
    data: ContractCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.CONTRACT, Action.CREATE))
):
    """创建合同"""
    # Check order exists
    order = await db.execute(select(Order).where(Order.id == data.order_id))
    if not order.scalar_one_or_none():
        raise NotFoundError("订单", data.order_id)

    contract_no = contract_service.generate_contract_no()

    contract = Contract(
        contract_no=contract_no,
        order_id=data.order_id,
        quote_id=data.quote_id,
        customer_id=data.customer_id,
        title=data.title,
        currency=data.currency,
        total_amount=data.total_amount,
        signed_date=data.signed_date,
        effective_date=data.effective_date,
        expiry_date=data.expiry_date,
        payment_terms=data.payment_terms,
        delivery_terms=data.delivery_terms,
        warranty_period=data.warranty_period,
        warranty_end_date=data.warranty_end_date,
        contract_type=data.contract_type or "customer",
        related_contract_id=data.related_contract_id,
        notes=data.notes,
        status=ContractStatus.DRAFT
    )
    db.add(contract)
    await db.flush()

    # Add payment plans
    for plan_data in data.payment_plans:
        plan = PaymentPlan(
            contract_id=contract.id,
            phase=plan_data.phase,
            percentage=plan_data.percentage,
            planned_amount=plan_data.planned_amount,
            planned_date=plan_data.planned_date,
            notes=plan_data.notes
        )
        db.add(plan)

    await db.commit()
    await db.refresh(contract)
    return contract


@router.get("/{contract_id}", response_model=ContractDetail)
async def get_contract(
    contract_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.CONTRACT, Action.READ))
):
    """获取合同详情"""
    detail = await contract_service.get_contract_detail(db, contract_id)
    contract = detail["contract"]

    return ContractDetail.model_validate({
        "id": contract.id,
        "contract_no": contract.contract_no,
        "order_id": contract.order_id,
        "quote_id": contract.quote_id,
        "customer_id": contract.customer_id,
        "title": contract.title,
        "status": contract.status,
        "currency": contract.currency,
        "total_amount": contract.total_amount,
        "signed_date": contract.signed_date,
        "effective_date": contract.effective_date,
        "expiry_date": contract.expiry_date,
        "payment_terms": contract.payment_terms,
        "delivery_terms": contract.delivery_terms,
        "notes": contract.notes,
        "created_at": contract.created_at,
        "updated_at": contract.updated_at,
        "payment_plans": [PaymentPlanResponse.model_validate(p) for p in contract.payment_plans],
        "order_no": detail["order_no"],
        "customer_name": detail["customer_name"],
    })


@router.put("/{contract_id}", response_model=ContractResponse)
async def update_contract(
    contract_id: int,
    data: ContractUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.CONTRACT, Action.UPDATE))
):
    """更新合同"""
    contract = await contract_service.get_by_id(db, contract_id)

    if contract.status not in [ContractStatus.DRAFT, ContractStatus.PENDING_APPROVAL]:
        raise ConflictError("只能修改草稿或待审批状态的合同")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(contract, key, value)

    await db.commit()
    await db.refresh(contract)
    return contract


@router.put("/{contract_id}/status", response_model=ContractResponse)
async def update_contract_status(
    contract_id: int,
    data: ContractStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.CONTRACT, Action.UPDATE))
):
    """更新合同状态"""
    contract = await contract_service.update_status(db, contract_id, data.status)
    await db.commit()
    await db.refresh(contract)

    try:
        from app.services.workflow_hooks import on_entity_status_change
        if contract.order_id:
            await on_entity_status_change(
                db, entity_type="contract", entity_id=contract.id,
                new_status=data.status.value if hasattr(data.status, 'value') else str(data.status),
                order_id=contract.order_id,
                operator_id=current_user.id,
            )
    except Exception:
        pass

    return contract


@router.put("/{contract_id}/payment-plans/{plan_id}", response_model=PaymentPlanResponse)
async def update_payment_plan(
    contract_id: int,
    plan_id: int,
    data: PaymentPlanUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.CONTRACT, Action.UPDATE))
):
    """更新回款计划"""
    result = await db.execute(
        select(PaymentPlan).where(
            PaymentPlan.id == plan_id,
            PaymentPlan.contract_id == contract_id
        )
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise NotFoundError("回款计划", plan_id)

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(plan, key, value)

    await db.commit()
    await db.refresh(plan)
    return plan


# Payment Record routes
@router.post("/{contract_id}/payments", response_model=PaymentRecordResponse)
async def create_payment_record(
    contract_id: int,
    data: PaymentRecordCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.CONTRACT, Action.UPDATE))
):
    """录入回款记录"""
    record = await contract_service.create_payment_record(
        db,
        contract_id,
        current_user,
        order_id=data.order_id,
        amount=data.amount,
        currency=data.currency,
        amount_cny=data.amount_cny,
        payment_date=data.payment_date,
        payment_method=data.payment_method,
        bank_account=data.bank_account,
        notes=data.notes,
    )
    await db.commit()
    await db.refresh(record)

    try:
        from app.integrations.kingdee.sync_service import KingdeeSyncService
        from app.integrations.kingdee import mapper
        from app.models.customer import Customer
        from sqlalchemy import select as _sel

        customer = (await db.execute(
            _sel(Customer).join(Contract, Contract.customer_id == Customer.id).where(Contract.id == contract_id)
        )).scalar_one_or_none()
        if customer:
            payload = mapper.map_payment_received_voucher(record, customer)
            svc = KingdeeSyncService()
            from app.models.sync_log import SyncLog, SyncDirection, SyncStatus
            log = SyncLog(
                entity_type="payment",
                entity_id=record.id,
                kingdee_doc_type="voucher",
                direction=SyncDirection.LG_TO_JDY,
                status=SyncStatus.PENDING,
                request_payload=payload.model_dump(),
            )
            db.add(log)
            await db.flush()
            try:
                resp = await svc.client.post(
                    "/jdyaccouting/voucher",
                    json=[payload.model_dump()],
                    params={"mode": "1"},
                )
                log.response_payload = resp
                items = resp.get("list", [])
                first = items[0] if items else {}
                if resp.get("code") == 0 and first.get("code", -1) == 0:
                    log.status = SyncStatus.SUCCESS
                    log.kingdee_doc_no = str(first.get("vchId", ""))
                else:
                    log.status = SyncStatus.FAILED
                    log.error_message = first.get("msg", resp.get("msg", ""))
            except Exception as inner_exc:
                log.status = SyncStatus.FAILED
                log.error_message = str(inner_exc)
            await db.commit()
    except Exception as exc:
        import logging
        logging.getLogger("kingdee.sync").warning("Payment #%d auto-sync failed: %s", record.id, exc)

    return record


@router.get("/{contract_id}/payments", response_model=list[PaymentRecordResponse])
async def list_payment_records(
    contract_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.CONTRACT, Action.READ))
):
    """获取合同回款记录"""
    result = await db.execute(
        select(PaymentRecord).where(PaymentRecord.contract_id == contract_id)
        .order_by(PaymentRecord.payment_date.desc())
    )
    return result.scalars().all()
