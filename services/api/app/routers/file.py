"""File Attachment Router"""
from typing import Optional
import uuid
import hashlib
from datetime import timedelta
from fastapi import APIRouter, Depends, UploadFile, File, Form, Query
from app.core.exceptions import NotFoundError, BusinessError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.deps import get_db
from app.core.rbac import require_permission, Resource, Action
from app.core.config import settings
from app.files.minio_client import _ensure_client
from app.models.user import User
from app.models.file import FileAttachment, FileObjectType
from app.schemas.file import (
    FileAttachmentCreate, FileAttachmentResponse,
    UploadUrlRequest, UploadUrlResponse,
    OfflineSyncRequest, OfflineSyncResponse
)

router = APIRouter(prefix="/files", tags=["附件管理"])


@router.post("/upload", response_model=FileAttachmentResponse)
async def upload_file(
    file: UploadFile = File(...),
    object_type: FileObjectType = Form(...),
    object_id: int = Form(...),
    notes: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.FILE, Action.CREATE))
):
    """上传文件"""
    # Generate unique file key
    ext = file.filename.split(".")[-1] if "." in file.filename else ""
    file_key = f"{object_type.value}/{object_id}/{uuid.uuid4().hex}.{ext}"
    
    # Read file content
    content = await file.read()
    file_size = len(content)
    sha1 = hashlib.sha1(content).hexdigest()
    
    # Upload to MinIO
    try:
        await file.seek(0)
        _ensure_client().put_object(
            settings.MINIO_BUCKET,
            file_key,
            file.file,
            file_size,
            content_type=file.content_type
        )
    except Exception as e:
        raise BusinessError(code="UPLOAD_FAILED", message=f"上传失败: {str(e)}", status_code=500)
    
    # Create attachment record
    attachment = FileAttachment(
        file_name=file_key.split("/")[-1],
        original_name=file.filename,
        file_key=file_key,
        mime_type=file.content_type,
        size=file_size,
        sha1=sha1,
        object_type=object_type,
        object_id=object_id,
        uploader_id=current_user.id,
        notes=notes
    )
    db.add(attachment)
    await db.commit()
    await db.refresh(attachment)
    
    # Generate URL
    url = _ensure_client().presigned_get_object(
        settings.MINIO_BUCKET,
        file_key,
        expires=timedelta(hours=1)
    )
    
    return FileAttachmentResponse(
        **attachment.__dict__,
        uploader_name=current_user.real_name,
        url=url
    )


@router.post("/presigned-url", response_model=UploadUrlResponse)
async def get_presigned_upload_url(
    data: UploadUrlRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.FILE, Action.CREATE))
):
    """获取预签名上传URL（用于移动端离线上传）"""
    ext = data.filename.split(".")[-1] if "." in data.filename else ""
    file_key = f"{data.object_type.value}/{data.object_id}/{uuid.uuid4().hex}.{ext}"
    
    try:
        upload_url = _ensure_client().presigned_put_object(
            settings.MINIO_BUCKET,
            file_key,
            expires=timedelta(hours=24)
        )
    except Exception as e:
        raise BusinessError(code="PRESIGN_FAILED", message=f"生成上传URL失败: {str(e)}", status_code=500)
    
    return UploadUrlResponse(
        upload_url=upload_url,
        file_key=file_key
    )


@router.post("/confirm-upload", response_model=FileAttachmentResponse)
async def confirm_upload(
    file_key: str,
    original_name: str,
    mime_type: str,
    size: int,
    object_type: FileObjectType,
    object_id: int,
    sha1: Optional[str] = None,
    notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.FILE, Action.CREATE))
):
    """确认上传完成（用于预签名URL上传后）"""
    attachment = FileAttachment(
        file_name=file_key.split("/")[-1],
        original_name=original_name,
        file_key=file_key,
        mime_type=mime_type,
        size=size,
        sha1=sha1,
        object_type=object_type,
        object_id=object_id,
        uploader_id=current_user.id,
        notes=notes
    )
    db.add(attachment)
    await db.commit()
    await db.refresh(attachment)
    
    url = _ensure_client().presigned_get_object(
        settings.MINIO_BUCKET,
        file_key,
        expires=timedelta(hours=1)
    )
    
    return FileAttachmentResponse(
        **attachment.__dict__,
        uploader_name=current_user.real_name,
        url=url
    )


@router.get("", response_model=list[FileAttachmentResponse])
async def list_files(
    object_type: FileObjectType = Query(...),
    object_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.FILE, Action.READ))
):
    """获取对象的附件列表"""
    result = await db.execute(
        select(FileAttachment).where(
            FileAttachment.object_type == object_type,
            FileAttachment.object_id == object_id
        ).order_by(FileAttachment.created_at.desc())
    )
    attachments = result.scalars().all()
    
    responses = []
    for att in attachments:
        uploader = await db.execute(select(User).where(User.id == att.uploader_id))
        uploader = uploader.scalar_one_or_none()
        
        url = _ensure_client().presigned_get_object(
            settings.MINIO_BUCKET,
            att.file_key,
            expires=timedelta(hours=1)
        )
        
        responses.append(FileAttachmentResponse(
            **att.__dict__,
            uploader_name=uploader.real_name if uploader else None,
            url=url
        ))
    
    return responses


@router.get("/{file_id}", response_model=FileAttachmentResponse)
async def get_file(
    file_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.FILE, Action.READ))
):
    """获取文件详情"""
    result = await db.execute(select(FileAttachment).where(FileAttachment.id == file_id))
    attachment = result.scalar_one_or_none()
    if not attachment:
        raise NotFoundError("文件", file_id)
    
    uploader = await db.execute(select(User).where(User.id == attachment.uploader_id))
    uploader = uploader.scalar_one_or_none()
    
    url = _ensure_client().presigned_get_object(
        settings.MINIO_BUCKET,
        attachment.file_key,
        expires=timedelta(hours=1)
    )
    
    return FileAttachmentResponse(
        **attachment.__dict__,
        uploader_name=uploader.real_name if uploader else None,
        url=url
    )


@router.delete("/{file_id}")
async def delete_file(
    file_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.FILE, Action.DELETE))
):
    """删除文件"""
    result = await db.execute(select(FileAttachment).where(FileAttachment.id == file_id))
    attachment = result.scalar_one_or_none()
    if not attachment:
        raise NotFoundError("文件", file_id)
    
    # Delete from MinIO
    try:
        _ensure_client().remove_object(settings.MINIO_BUCKET, attachment.file_key)
    except Exception:
        pass  # Ignore MinIO errors
    
    await db.delete(attachment)
    await db.commit()
    return {"message": "删除成功"}


@router.post("/offline-sync", response_model=OfflineSyncResponse)
async def offline_sync(
    data: OfflineSyncRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.FILE, Action.CREATE))
):
    """离线文件同步（批量确认上传）"""
    success = []
    failed = []
    
    for file_info in data.files:
        try:
            local_id = file_info.get("local_id")
            file_key = file_info.get("file_key")
            object_type = FileObjectType(file_info.get("object_type"))
            object_id = file_info.get("object_id")
            
            # Check if file exists in MinIO
            try:
                _ensure_client().stat_object(settings.MINIO_BUCKET, file_key)
            except Exception:
                failed.append({"local_id": local_id, "error": "文件不存在"})
                continue
            
            # Check if attachment already exists
            existing = await db.execute(
                select(FileAttachment).where(FileAttachment.file_key == file_key)
            )
            if existing.scalar_one_or_none():
                success.append(local_id)
                continue
            
            # Create attachment record
            attachment = FileAttachment(
                file_name=file_key.split("/")[-1],
                original_name=file_info.get("original_name", file_key.split("/")[-1]),
                file_key=file_key,
                mime_type=file_info.get("mime_type", "application/octet-stream"),
                size=file_info.get("size", 0),
                sha1=file_info.get("sha1"),
                object_type=object_type,
                object_id=object_id,
                uploader_id=current_user.id
            )
            db.add(attachment)
            success.append(local_id)
        except Exception as e:
            failed.append({"local_id": file_info.get("local_id"), "error": str(e)})
    
    await db.commit()
    return OfflineSyncResponse(success=success, failed=failed)

