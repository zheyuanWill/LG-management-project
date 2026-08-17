from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File as UploadFileDep, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.project import Project
from app.models.spare_part import (
    HkSignature,
    Invoice,
    LogisticsNode,
    SparePartDetail,
    SparePartPhoto,
)
from app.models.user import User
from app.schemas.spare_part import (
    HkSignatureCreate,
    HkSignatureResponse,
    InvoiceCreate,
    InvoiceResponse,
    LogisticsNodeCreate,
    LogisticsNodeResponse,
    SparePartDetailCreate,
    SparePartDetailResponse,
    SparePartPhotoCreate,
    SparePartPhotoResponse,
)
from app.services.file_service import upload_to_minio

# 固定物流节点顺序（可视化时间轴用）
LOGISTICS_NODE_ORDER = [
    "ordered",          # 已下单
    "supplier_shipped",  # 供应商已发货
    "in_transit",        # 运输中
    "arrived",           # 已到港
    "warehoused",        # 已入库
    "sent_to_owner",     # 已送船东
    "hk_signed",         # 香港签收
    "settled",           # 已结算
]
VALID_LOGISTICS_NODE_TYPES = set(LOGISTICS_NODE_ORDER)

# 每个节点要求/建议上传的文件说明
NODE_ATTACHMENT_HINT = {
    "supplier_shipped": "供应商发货单",
    "hk_signed": "香港签收单",
    "settled": "结算单/发票",
}

router = APIRouter()


# ── 备件（一项目多个）─────────────────────────────────────
@router.get(
    "/projects/{project_id}/spare-parts",
    response_model=list[SparePartDetailResponse],
)
async def list_spare_part_details(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")

    result = await db.execute(
        select(SparePartDetail)
        .where(SparePartDetail.project_id == project_id)
        .order_by(SparePartDetail.id)
    )
    return [SparePartDetailResponse.model_validate(d) for d in result.scalars().all()]


@router.post(
    "/projects/{project_id}/spare-parts",
    response_model=SparePartDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_spare_part_detail(
    project_id: int,
    payload: SparePartDetailCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")

    detail = SparePartDetail(
        project_id=project_id,
        item_name=payload.item_name,
        model_or_drawing=payload.model_or_drawing,
        quantity=payload.quantity,
    )
    db.add(detail)
    await db.flush()
    return SparePartDetailResponse.model_validate(detail)


@router.patch(
    "/projects/{project_id}/spare-parts/{spare_id}",
    response_model=SparePartDetailResponse,
)
async def update_spare_part_detail(
    project_id: int,
    spare_id: int,
    payload: SparePartDetailCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    detail = await _get_spare_part(db, project_id, spare_id)
    detail.item_name = payload.item_name
    if payload.model_or_drawing is not None:
        detail.model_or_drawing = payload.model_or_drawing
    if payload.quantity is not None:
        detail.quantity = payload.quantity
    await db.flush()
    return SparePartDetailResponse.model_validate(detail)


@router.delete(
    "/projects/{project_id}/spare-parts/{spare_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_spare_part_detail(
    project_id: int,
    spare_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    detail = await _get_spare_part(db, project_id, spare_id)
    await db.delete(detail)


# ── 备件照片（logo/loading 等）────────────────────────────
@router.post(
    "/projects/{project_id}/spare-photos",
    response_model=SparePartPhotoResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_spare_photo(
    project_id: int,
    photo_type: str = Query(..., pattern="^(logo|loading)$"),
    file: UploadFile = UploadFileDep(...),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")

    content = await file.read()
    ext = file.filename.rsplit(".", 1)[-1] if file.filename and "." in file.filename else "jpg"
    storage_key = await upload_to_minio(content, ext=ext)

    photo = SparePartPhoto(
        project_id=project_id,
        photo_type=photo_type,
        storage_key=storage_key,
    )
    db.add(photo)
    await db.flush()
    return SparePartPhotoResponse.model_validate(photo)


# ── 物流节点（按备件维度）──────────────────────────────────
@router.get(
    "/projects/{project_id}/spare-parts/{spare_id}/logistics",
    response_model=list[LogisticsNodeResponse],
)
async def list_spare_logistics_nodes(
    project_id: int,
    spare_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    await _get_spare_part(db, project_id, spare_id)
    result = await db.execute(
        select(LogisticsNode)
        .where(LogisticsNode.spare_part_id == spare_id)
        .order_by(LogisticsNode.node_date)
    )
    return [LogisticsNodeResponse.model_validate(n) for n in result.scalars().all()]


@router.post(
    "/projects/{project_id}/spare-parts/{spare_id}/logistics",
    response_model=LogisticsNodeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_spare_logistics_node(
    project_id: int,
    spare_id: int,
    payload: LogisticsNodeCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    await _get_spare_part(db, project_id, spare_id)
    _validate_node_type(payload.node_type)

    node = LogisticsNode(
        project_id=project_id,
        spare_part_id=spare_id,
        node_type=payload.node_type,
        node_date=payload.node_date,
        tracking_no=payload.tracking_no,
        remark=payload.remark,
        attachment_key=payload.attachment_key,
        attachments=payload.attachments,
    )
    db.add(node)
    await db.flush()
    return LogisticsNodeResponse.model_validate(node)


@router.patch(
    "/projects/{project_id}/spare-parts/{spare_id}/logistics/{node_id}",
    response_model=LogisticsNodeResponse,
)
async def update_spare_logistics_node(
    project_id: int,
    spare_id: int,
    node_id: int,
    payload: LogisticsNodeCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    await _get_spare_part(db, project_id, spare_id)
    _validate_node_type(payload.node_type)

    node = await _get_node(db, spare_id, node_id)
    node.node_type = payload.node_type
    node.node_date = payload.node_date
    node.tracking_no = payload.tracking_no
    node.remark = payload.remark
    node.attachment_key = payload.attachment_key
    if payload.attachments is not None:
        node.attachments = payload.attachments
    await db.flush()
    return LogisticsNodeResponse.model_validate(node)


@router.delete(
    "/projects/{project_id}/spare-parts/{spare_id}/logistics/{node_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_spare_logistics_node(
    project_id: int,
    spare_id: int,
    node_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    await _get_spare_part(db, project_id, spare_id)
    node = await _get_node(db, spare_id, node_id)
    await db.delete(node)


# ── 节点完成 / 撤销（级联：以 LOGISTICS_NODE_ORDER 为步骤顺序）────
@router.post(
    "/projects/{project_id}/spare-parts/{spare_id}/logistics/{node_id}/complete",
    response_model=list[LogisticsNodeResponse],
)
async def complete_spare_logistics_node(
    project_id: int,
    spare_id: int,
    node_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    await _get_spare_part(db, project_id, spare_id)
    return await _cascade_node_completion(db, project_id, spare_id, node_id, True)


@router.post(
    "/projects/{project_id}/spare-parts/{spare_id}/logistics/{node_id}/reopen",
    response_model=list[LogisticsNodeResponse],
)
async def reopen_spare_logistics_node(
    project_id: int,
    spare_id: int,
    node_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    await _get_spare_part(db, project_id, spare_id)
    return await _cascade_node_completion(db, project_id, spare_id, node_id, False)


# ── 兼容：项目级物流（未挂具体备件）────────────────────────
@router.get(
    "/projects/{project_id}/logistics",
    response_model=list[LogisticsNodeResponse],
)
async def list_logistics_nodes(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")

    result = await db.execute(
        select(LogisticsNode)
        .where(LogisticsNode.project_id == project_id)
        .order_by(LogisticsNode.node_date)
    )
    return [LogisticsNodeResponse.model_validate(n) for n in result.scalars().all()]


@router.post(
    "/projects/{project_id}/logistics",
    response_model=LogisticsNodeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_logistics_node(
    project_id: int,
    payload: LogisticsNodeCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")

    _validate_node_type(payload.node_type)

    node = LogisticsNode(
        project_id=project_id,
        spare_part_id=payload.spare_part_id,
        node_type=payload.node_type,
        node_date=payload.node_date,
        tracking_no=payload.tracking_no,
        remark=payload.remark,
        attachment_key=payload.attachment_key,
        attachments=payload.attachments,
    )
    db.add(node)
    await db.flush()
    return LogisticsNodeResponse.model_validate(node)


@router.post(
    "/projects/{project_id}/logistics/{node_id}/complete",
    response_model=list[LogisticsNodeResponse],
)
async def complete_logistics_node(
    project_id: int,
    node_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    await _require_project(db, project_id)
    return await _cascade_node_completion(db, project_id, None, node_id, True)


@router.post(
    "/projects/{project_id}/logistics/{node_id}/reopen",
    response_model=list[LogisticsNodeResponse],
)
async def reopen_logistics_node(
    project_id: int,
    node_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    await _require_project(db, project_id)
    return await _cascade_node_completion(db, project_id, None, node_id, False)


# ── HK 签收单 ─────────────────────────────────────────────
@router.get(
    "/projects/{project_id}/hk-signatures",
    response_model=Optional[HkSignatureResponse],
)
async def get_hk_signature(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(HkSignature).where(HkSignature.project_id == project_id)
    )
    signature = result.scalar_one_or_none()
    if signature is None:
        return None
    return HkSignatureResponse.model_validate(signature)


@router.post(
    "/projects/{project_id}/hk-signatures",
    response_model=HkSignatureResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_hk_signature(
    project_id: int,
    payload: HkSignatureCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")

    signature = HkSignature(
        project_id=project_id,
        signature_file_key=payload.signature_file_key,
        signed_at=payload.signed_at,
    )
    db.add(signature)
    await db.flush()
    return HkSignatureResponse.model_validate(signature)


@router.patch(
    "/projects/{project_id}/hk-signatures",
    response_model=HkSignatureResponse,
)
async def update_hk_signature(
    project_id: int,
    payload: HkSignatureCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(HkSignature).where(HkSignature.project_id == project_id)
    )
    signature = result.scalar_one_or_none()
    if signature is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="签收单不存在")

    if payload.signature_file_key is not None:
        signature.signature_file_key = payload.signature_file_key
    if payload.signed_at is not None:
        signature.signed_at = payload.signed_at
    await db.flush()
    return HkSignatureResponse.model_validate(signature)


@router.delete(
    "/projects/{project_id}/hk-signatures",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_hk_signature(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(HkSignature).where(HkSignature.project_id == project_id)
    )
    signature = result.scalar_one_or_none()
    if signature is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="签收单不存在")
    await db.delete(signature)


# ── 发票 ─────────────────────────────────────────────────
@router.get(
    "/projects/{project_id}/invoices",
    response_model=Optional[InvoiceResponse],
)
async def get_invoice(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Invoice).where(Invoice.project_id == project_id)
    )
    invoice = result.scalar_one_or_none()
    if invoice is None:
        return None
    return InvoiceResponse.model_validate(invoice)


@router.post(
    "/projects/{project_id}/invoices",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_invoice(
    project_id: int,
    payload: InvoiceCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")

    invoice = Invoice(
        project_id=project_id,
        title=payload.title,
        tax_number=payload.tax_number,
        amount=payload.amount,
        purpose=payload.purpose,
    )
    db.add(invoice)
    await db.flush()
    return InvoiceResponse.model_validate(invoice)


@router.patch(
    "/projects/{project_id}/invoices",
    response_model=InvoiceResponse,
)
async def update_invoice(
    project_id: int,
    payload: InvoiceCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Invoice).where(Invoice.project_id == project_id)
    )
    invoice = result.scalar_one_or_none()
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="发票信息不存在")

    if payload.title is not None:
        invoice.title = payload.title
    if payload.tax_number is not None:
        invoice.tax_number = payload.tax_number
    if payload.amount is not None:
        invoice.amount = payload.amount
    if payload.purpose is not None:
        invoice.purpose = payload.purpose
    await db.flush()
    return InvoiceResponse.model_validate(invoice)


@router.delete(
    "/projects/{project_id}/invoices",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_invoice(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Invoice).where(Invoice.project_id == project_id)
    )
    invoice = result.scalar_one_or_none()
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="发票信息不存在")
    await db.delete(invoice)


# ── 辅助 ─────────────────────────────────────────────────
def _node_order_index(node_type: str) -> int:
    return (
        LOGISTICS_NODE_ORDER.index(node_type)
        if node_type in LOGISTICS_NODE_ORDER
        else len(LOGISTICS_NODE_ORDER)
    )


def _node_sort_key(node: LogisticsNode) -> tuple:
    return (_node_order_index(node.node_type), node.node_date, node.id)


async def _cascade_node_completion(
    db: AsyncSession,
    project_id: int,
    spare_part_id: int | None,
    target_node_id: int,
    complete: bool,
) -> list[LogisticsNode]:
    """级联标记完成/撤销。

    complete=True  : 把目标节点及其「之前」所有节点（同 project+spare 分组）标记 completed。
    complete=False : 把目标节点及其「之后」所有节点标记未完成（撤销）。
    """
    conditions = [LogisticsNode.project_id == project_id]
    if spare_part_id is None:
        conditions.append(LogisticsNode.spare_part_id.is_(None))
    else:
        conditions.append(LogisticsNode.spare_part_id == spare_part_id)
    result = await db.execute(select(LogisticsNode).where(and_(*conditions)))
    nodes = result.scalars().all()
    target = next((n for n in nodes if n.id == target_node_id), None)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="物流节点不存在")
    target_key = _node_sort_key(target)
    for n in nodes:
        key = _node_sort_key(n)
        if complete:
            if key <= target_key:
                n.completed = True
        else:
            if key >= target_key:
                n.completed = False
    await db.flush()
    return [LogisticsNodeResponse.model_validate(n) for n in nodes]


async def _require_project(db: AsyncSession, project_id: int) -> None:
    result = await db.execute(select(Project).where(Project.id == project_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")


async def _get_spare_part(db: AsyncSession, project_id: int, spare_id: int) -> SparePartDetail:
    result = await db.execute(
        select(SparePartDetail).where(
            SparePartDetail.id == spare_id,
            SparePartDetail.project_id == project_id,
        )
    )
    detail = result.scalar_one_or_none()
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="备件不存在")
    return detail


async def _get_node(db: AsyncSession, spare_id: int, node_id: int) -> LogisticsNode:
    result = await db.execute(
        select(LogisticsNode).where(
            LogisticsNode.id == node_id,
            LogisticsNode.spare_part_id == spare_id,
        )
    )
    node = result.scalar_one_or_none()
    if node is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="物流节点不存在")
    return node


def _validate_node_type(node_type: str) -> None:
    if node_type not in VALID_LOGISTICS_NODE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的节点类型。有效类型(按顺序): {', '.join(LOGISTICS_NODE_ORDER)}",
        )
