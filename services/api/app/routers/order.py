"""Order and Quote Router

Thin routing layer — business logic is delegated to OrderService and QuoteService.
"""
from typing import Optional
import hashlib
import uuid
from datetime import timedelta
from io import BytesIO

import anyio
from fastapi import APIRouter, Depends, Query, UploadFile, File, Form

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessError
from app.core.deps import get_db
from app.core.rbac import require_permission, Resource, Action
from app.core.config import settings
from app.files.minio_client import _ensure_client
from app.models.file import FileAttachment, FileObjectType
from app.models.user import User
from app.models.customer import Customer, Vessel
from app.models.order import OrderStatus, QuoteStatus, ProjectType
from app.schemas.order import (
    OrderCreate, OrderUpdate, OrderResponse, OrderDetail, OrderStatusUpdate,
    OrderLineItemCreate, OrderLineItemResponse, InquiryCreate,
    QuoteCreate, QuoteUpdate, QuoteResponse, QuoteDetail, QuoteStatusUpdate, QuoteDuplicate,
    QuoteLineItemResponse
)
from app.schemas.common import PageResponse
from app.schemas.file import FileAttachmentResponse
from app.services import order_service, quote_service
from app.services.quote_excel import QuoteExcelConfig, generate_quote_excel_bytes

router = APIRouter(prefix="/orders", tags=["订单管理"])


@router.get("", response_model=PageResponse[OrderResponse])
async def list_orders(
    keyword: Optional[str] = Query(None),
    status: Optional[OrderStatus] = Query(None),
    project_type: Optional[ProjectType] = Query(None),
    customer_id: Optional[int] = Query(None),
    pm_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.ORDER, Action.READ))
):
    """获取订单列表"""
    items, total = await order_service.list_orders(
        db,
        current_user=current_user,
        keyword=keyword,
        status=status,
        project_type=project_type,
        customer_id=customer_id,
        pm_id=pm_id,
        page=page,
        size=size,
    )

    # Batch-load related names
    customer_ids = {o.customer_id for o in items if o.customer_id}
    vessel_ids = {o.vessel_id for o in items if o.vessel_id}
    pm_ids = {o.pm_id for o in items if o.pm_id}

    customers_map: dict[int, str] = {}
    if customer_ids:
        rows = (await db.execute(select(Customer.id, Customer.name).where(Customer.id.in_(customer_ids)))).all()
        customers_map = {r.id: r.name for r in rows}

    vessels_map: dict[int, str] = {}
    if vessel_ids:
        rows = (await db.execute(select(Vessel.id, Vessel.name).where(Vessel.id.in_(vessel_ids)))).all()
        vessels_map = {r.id: r.name for r in rows}

    pm_map: dict[int, str] = {}
    if pm_ids:
        rows = (await db.execute(select(User.id, User.real_name).where(User.id.in_(pm_ids)))).all()
        pm_map = {r.id: r.real_name for r in rows}

    enriched = []
    for o in items:
        resp = OrderResponse.model_validate(o)
        resp.customer_name = customers_map.get(o.customer_id)
        resp.vessel_name = vessels_map.get(o.vessel_id) if o.vessel_id else None
        resp.pm_name = pm_map.get(o.pm_id)
        enriched.append(resp)

    return PageResponse.create(items=enriched, total=total, page=page, size=size)


@router.post("", response_model=OrderResponse)
async def create_order(
    data: OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.ORDER, Action.CREATE))
):
    """创建订单"""
    return await order_service.create_order(
        db,
        current_user=current_user,
        customer_id=data.customer_id,
        vessel_id=data.vessel_id,
        project_type=data.project_type,
        currency=data.currency,
        delivery_date=data.delivery_date,
        notes=data.notes,
        line_items_data=data.line_items or [],
    )


@router.post("/inquiry", response_model=OrderResponse)
async def create_inquiry(
    data: InquiryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.ORDER, Action.CREATE))
):
    """创建询价单（INQUIRY状态，生成RFQ编号）"""
    return await order_service.create_inquiry(
        db,
        current_user=current_user,
        customer_id=data.customer_id,
        vessel_id=data.vessel_id,
        project_type=data.project_type,
        currency=data.currency,
        inquiry_source=data.inquiry_source,
        delivery_date=data.delivery_date,
        notes=data.notes,
        line_items_data=data.line_items or [],
    )


@router.post("/{order_id}/promote", response_model=OrderResponse)
async def promote_to_project(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.ORDER, Action.UPDATE))
):
    """客户接受报价后，生成项目编码"""
    return await order_service.promote_to_project(db, order_id)


@router.get("/{order_id}", response_model=OrderDetail)
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.ORDER, Action.READ))
):
    """获取订单详情"""
    detail = await order_service.get_order_detail(db, order_id)
    order = detail["order"]
    return OrderDetail.model_validate({
        "id": order.id,
        "order_no": order.order_no,
        "inquiry_no": getattr(order, "inquiry_no", None),
        "project_code": getattr(order, "project_code", None),
        "customer_id": order.customer_id,
        "vessel_id": order.vessel_id,
        "project_type": order.project_type,
        "status": order.status,
        "currency": order.currency,
        "total_amount": order.total_amount,
        "delivery_date": order.delivery_date,
        "pm_id": order.pm_id,
        "inquiry_source": getattr(order, "inquiry_source", None),
        "risk_level": getattr(order, "risk_level", None),
        "cancellation_reason": getattr(order, "cancellation_reason", None),
        "cancellation_category": getattr(order, "cancellation_category", None),
        "notes": order.notes,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
        "line_items": [OrderLineItemResponse.model_validate(i) for i in order.line_items],
        "customer_name": detail["customer_name"],
        "vessel_name": detail["vessel_name"],
        "pm_name": detail["pm_name"],
    })


@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: int,
    data: OrderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.ORDER, Action.UPDATE))
):
    """更新订单"""
    return await order_service.update_order(
        db, order_id, current_user,
        data=data.model_dump(exclude_unset=True),
    )


@router.put("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: int,
    data: OrderStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.ORDER, Action.UPDATE))
):
    """更新订单状态"""
    return await order_service.update_status(
        db, order_id, data.status, operator_id=current_user.id,
        cancellation_reason=data.cancellation_reason,
        cancellation_category=data.cancellation_category,
    )


@router.post("/{order_id}/line-items", response_model=OrderLineItemResponse)
async def add_order_line_item(
    order_id: int,
    data: OrderLineItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.ORDER, Action.UPDATE))
):
    """添加订单明细"""
    return await order_service.add_line_item(db, order_id, data)


@router.delete("/{order_id}/line-items/{item_id}")
async def delete_order_line_item(
    order_id: int,
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.ORDER, Action.DELETE))
):
    """删除订单明细"""
    return await order_service.delete_line_item(db, order_id, item_id)


# ---------------------------------------------------------------------------
# Quote routes — delegated to QuoteService
# ---------------------------------------------------------------------------
quote_router = APIRouter(prefix="/quotes", tags=["报价管理"])


@quote_router.get("", response_model=PageResponse[QuoteResponse])
async def list_quotes(
    order_id: Optional[int] = Query(None),
    status: Optional[QuoteStatus] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.QUOTE, Action.READ))
):
    """获取报价列表"""
    items, total = await quote_service.list_quotes(
        db, order_id=order_id, status=status, page=page, size=size,
    )
    return PageResponse.create(items=items, total=total, page=page, size=size)


@quote_router.post("", response_model=QuoteResponse)
async def create_quote(
    data: QuoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.QUOTE, Action.CREATE))
):
    """创建报价"""
    return await quote_service.create_quote(
        db,
        order_id=data.order_id,
        currency=data.currency,
        valid_until=data.valid_until,
        notes=data.notes,
        line_items_data=data.line_items,
    )


@quote_router.get("/{quote_id}", response_model=QuoteDetail)
async def get_quote(
    quote_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.QUOTE, Action.READ))
):
    """获取报价详情"""
    detail = await quote_service.get_quote_detail(db, quote_id)
    quote = detail["quote"]
    return QuoteDetail.model_validate({
        "id": quote.id,
        "quote_no": quote.quote_no,
        "order_id": quote.order_id,
        "version": quote.version,
        "status": quote.status,
        "currency": quote.currency,
        "total_amount": quote.total_amount,
        "valid_until": quote.valid_until,
        "notes": quote.notes,
        "feedback": quote.feedback,
        "created_at": quote.created_at,
        "updated_at": quote.updated_at,
        "line_items": [QuoteLineItemResponse.model_validate(item) for item in quote.line_items],
        "order_no": detail["order_no"],
        "customer_name": detail["customer_name"],
    })


@quote_router.put("/{quote_id}/status", response_model=QuoteResponse)
async def update_quote_status(
    quote_id: int,
    data: QuoteStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.QUOTE, Action.UPDATE))
):
    """更新报价状态"""
    quote = await quote_service.update_quote_status(
        db, quote_id, data.status, data.feedback,
    )

    # Auto-send quote email when status set to SENT
    if data.status == QuoteStatus.SENT and quote.order_id:
        try:
            from app.services.email_service import email_service
            from app.models.order import Order
            _order = (await db.execute(select(Order).where(Order.id == quote.order_id))).scalar_one_or_none()
            if _order:
                _cust = (await db.execute(select(Customer).where(Customer.id == _order.customer_id))).scalar_one_or_none()
                if _cust and getattr(_cust, 'contact_email', None):
                    await email_service.send_quote_email(
                        _cust.contact_email, _cust.name, quote.quote_no, str(quote.total_amount)
                    )
        except Exception:
            pass

    # Auto-promote to project when quote is accepted
    if data.status == QuoteStatus.ACCEPTED and quote.order_id:
        try:
            await order_service.promote_to_project(db, quote.order_id)
        except Exception:
            pass

    try:
        from app.services.workflow_hooks import on_entity_status_change
        if quote.order_id:
            await on_entity_status_change(
                db, entity_type="quote", entity_id=quote.id,
                new_status=data.status.value if hasattr(data.status, 'value') else str(data.status),
                order_id=quote.order_id,
                operator_id=current_user.id,
            )
    except Exception:
        pass

    return quote


@quote_router.post("/{quote_id}/submit-approval")
async def submit_quote_for_approval(
    quote_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.QUOTE, Action.UPDATE))
):
    """提交报价审批 — 根据毛利率分段自动判断审批级别"""
    return await quote_service.submit_for_approval(db, quote_id, current_user.id)


@quote_router.post("/{quote_id}/duplicate", response_model=QuoteResponse)
async def duplicate_quote(
    quote_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.QUOTE, Action.CREATE))
):
    """复制报价创建新版本"""
    return await quote_service.duplicate_quote(db, quote_id)


@quote_router.post("/{quote_id}/excel/generate", response_model=FileAttachmentResponse)
async def generate_quote_excel(
    quote_id: int,
    template_file: UploadFile = File(...),
    steel_source_file: UploadFile = File(...),
    mach_wdr_file: UploadFile = File(...),
    mach_tariff_file: UploadFile = File(...),
    preserve_marker: str = Form("THE LIST IS UNTIL"),
    steel_sheet_keywords: str = Form("steel,procida"),
    steel_part_keyword: str = Form("PART1"),
    steel_style_row: int = Form(30),
    mach_sheet_keywords: str = Form("mach,procida"),
    mach_tariff_sheet_name: str = Form("Quote"),
    mach_tariff_row_start: int = Form(616),
    mach_tariff_row_end: int = Form(632),
    notes: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.QUOTE, Action.UPDATE))
):
    await quote_service.get_by_id(db, quote_id)

    template_bytes = await template_file.read()
    steel_bytes = await steel_source_file.read()
    mach_wdr_bytes = await mach_wdr_file.read()
    mach_tariff_bytes = await mach_tariff_file.read()

    cfg = QuoteExcelConfig(
        steel_sheet_keywords=tuple(k.strip() for k in steel_sheet_keywords.split(",") if k.strip()),
        steel_part_keyword=steel_part_keyword,
        steel_style_row=steel_style_row,
        mach_sheet_keywords=tuple(k.strip() for k in mach_sheet_keywords.split(",") if k.strip()),
        mach_tariff_sheet_name=mach_tariff_sheet_name,
        mach_tariff_row_range=(mach_tariff_row_start, mach_tariff_row_end),
        preserve_marker=preserve_marker,
    )

    output_bytes = await anyio.to_thread.run_sync(
        generate_quote_excel_bytes,
        template_bytes=template_bytes,
        steel_source_bytes=steel_bytes,
        mach_wdr_bytes=mach_wdr_bytes,
        mach_tariff_bytes=mach_tariff_bytes,
        config=cfg,
    )

    file_key = f"{FileObjectType.QUOTE.value}/{quote_id}/{uuid.uuid4().hex}.xlsx"
    file_size = len(output_bytes)
    sha1 = hashlib.sha1(output_bytes).hexdigest()

    content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    try:
        _ensure_client().put_object(
            settings.MINIO_BUCKET,
            file_key,
            BytesIO(output_bytes),
            file_size,
            content_type=content_type,
        )
    except Exception as e:
        raise BusinessError(code="UPLOAD_FAILED", message=f"保存失败: {str(e)}", status_code=500)

    attachment = FileAttachment(
        file_name=file_key.split("/")[-1],
        original_name=f"quote_{quote_id}.xlsx",
        file_key=file_key,
        mime_type=content_type,
        size=file_size,
        sha1=sha1,
        object_type=FileObjectType.QUOTE,
        object_id=quote_id,
        uploader_id=current_user.id,
        notes=notes,
    )
    db.add(attachment)
    await db.commit()
    await db.refresh(attachment)

    url = _ensure_client().presigned_get_object(
        settings.MINIO_BUCKET,
        file_key,
        expires=timedelta(hours=1),
    )

    return FileAttachmentResponse(
        **attachment.__dict__,
        uploader_name=current_user.real_name,
        url=url,
    )
