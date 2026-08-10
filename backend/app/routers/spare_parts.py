from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File as UploadFileDep, status
from sqlalchemy import select
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

VALID_LOGISTICS_NODE_TYPES = {
    "ordered",
    "supplier_shipped",
    "in_transit",
    "arrived",
    "warehoused",
    "sent_to_owner",
    "hk_signed",
    "settled",
}

router = APIRouter()


@router.get(
    "/projects/{project_id}/spare-parts",
    response_model=SparePartDetailResponse,
)
async def get_spare_part_detail(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(SparePartDetail).where(SparePartDetail.project_id == project_id)
    )
    detail = result.scalar_one_or_none()
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="备件信息不存在")
    return SparePartDetailResponse.model_validate(detail)


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
    "/projects/{project_id}/spare-parts",
    response_model=SparePartDetailResponse,
)
async def update_spare_part_detail(
    project_id: int,
    payload: SparePartDetailCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(SparePartDetail).where(SparePartDetail.project_id == project_id)
    )
    detail = result.scalar_one_or_none()
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="备件信息不存在")

    detail.item_name = payload.item_name
    if payload.model_or_drawing is not None:
        detail.model_or_drawing = payload.model_or_drawing
    if payload.quantity is not None:
        detail.quantity = payload.quantity
    await db.flush()
    return SparePartDetailResponse.model_validate(detail)


@router.delete(
    "/projects/{project_id}/spare-parts",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_spare_part_detail(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(SparePartDetail).where(SparePartDetail.project_id == project_id)
    )
    detail = result.scalar_one_or_none()
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="备件信息不存在")
    await db.delete(detail)


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
    nodes = result.scalars().all()
    return [LogisticsNodeResponse.model_validate(n) for n in nodes]


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

    if payload.node_type not in VALID_LOGISTICS_NODE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的节点类型。有效类型: {', '.join(sorted(VALID_LOGISTICS_NODE_TYPES))}",
        )

    node = LogisticsNode(
        project_id=project_id,
        node_type=payload.node_type,
        node_date=payload.node_date,
        tracking_no=payload.tracking_no,
        remark=payload.remark,
        attachment_key=payload.attachment_key,
    )
    db.add(node)
    await db.flush()
    return LogisticsNodeResponse.model_validate(node)


@router.patch(
    "/projects/{project_id}/logistics/{node_id}",
    response_model=LogisticsNodeResponse,
)
async def update_logistics_node(
    project_id: int,
    node_id: int,
    payload: LogisticsNodeCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(LogisticsNode).where(
            LogisticsNode.id == node_id,
            LogisticsNode.project_id == project_id,
        )
    )
    node = result.scalar_one_or_none()
    if node is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="物流节点不存在")

    if payload.node_type not in VALID_LOGISTICS_NODE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的节点类型。有效类型: {', '.join(sorted(VALID_LOGISTICS_NODE_TYPES))}",
        )

    node.node_type = payload.node_type
    node.node_date = payload.node_date
    node.tracking_no = payload.tracking_no
    node.remark = payload.remark
    node.attachment_key = payload.attachment_key
    await db.flush()
    return LogisticsNodeResponse.model_validate(node)


@router.get(
    "/projects/{project_id}/hk-signatures",
    response_model=HkSignatureResponse,
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="签收单不存在")
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


@router.get(
    "/projects/{project_id}/invoices",
    response_model=InvoiceResponse,
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="发票信息不存在")
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