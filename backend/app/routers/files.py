from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.file import File as FileModel
from app.models.user import User
from app.schemas.file import FileListResponse, FileResponse, FileUploadResponse
from app.services.file_service import (
    delete_from_minio,
    detect_file_type,
    get_minio_url,
    upload_to_minio,
    save_file_record,
)

router = APIRouter()


@router.post("/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    project_id: int | None = Form(default=None),
    file_type: str | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    content = await file.read()
    filename = file.filename or "unnamed"

    detected_type = file_type or detect_file_type(filename)
    ext = filename.rsplit(".", 1)[-1] if "." in filename else ""
    storage_key = await upload_to_minio(content, ext=ext)

    mime_type = file.content_type or "application/octet-stream"
    file_record = await save_file_record(
        db=db,
        project_id=project_id,
        file_name=filename,
        file_type=detected_type,
        storage_key=storage_key,
        file_size=len(content),
        mime_type=mime_type,
        uploaded_by=current_user.id,
    )

    return FileUploadResponse(
        file_name=file_record.file_name,
        file_type=file_record.file_type,
        storage_key=file_record.storage_key,
        file_size=file_record.file_size,
        mime_type=file_record.mime_type,
    )


@router.get("", response_model=FileListResponse)
async def list_files(
    project_id: int | None = Query(default=None),
    file_type: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = select(FileModel)
    if project_id is not None:
        query = query.where(FileModel.project_id == project_id)
    if file_type:
        query = query.where(FileModel.file_type == file_type)

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.execute(count_query)
    total = total.scalar() or 0

    query = query.order_by(FileModel.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    files = result.scalars().all()

    return FileListResponse(
        items=[FileResponse.model_validate(f) for f in files],
        total=total,
    )


@router.get("/{file_id}/download")
async def download_file(
    file_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(FileModel).where(FileModel.id == file_id))
    file = result.scalar_one_or_none()
    if file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在")

    url = await get_minio_url(file.storage_key)
    return {
        "file_id": file.id,
        "file_name": file.file_name,
        "download_url": url,
        "expires_in": 3600,
    }


@router.get("/{file_id}/preview")
async def preview_file(
    file_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(FileModel).where(FileModel.id == file_id))
    file = result.scalar_one_or_none()
    if file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在")

    url = await get_minio_url(file.storage_key)
    return {
        "file_id": file.id,
        "file_name": file.file_name,
        "file_type": file.file_type,
        "preview_url": url,
        "mime_type": file.mime_type,
    }


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(FileModel).where(FileModel.id == file_id))
    file = result.scalar_one_or_none()
    if file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在")

    await delete_from_minio(file.storage_key)
    await db.delete(file)