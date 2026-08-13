from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.file import File as FileModel
from app.models.project import Project
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
        id=file_record.id,
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

    # 批量查询关联项目的船名
    project_ids = list(set(f.project_id for f in files if f.project_id))
    ship_name_map: dict[int, str] = {}
    if project_ids:
        pr = await db.execute(
            select(Project.id, Project.ship_name).where(Project.id.in_(project_ids))
        )
        ship_name_map = {row[0]: row[1] for row in pr.all()}

    return FileListResponse(
        items=[
            FileResponse(
                id=f.id,
                project_id=f.project_id,
                project_ship_name=ship_name_map.get(f.project_id) if f.project_id else None,
                file_name=f.file_name,
                file_type=f.file_type,
                storage_key=f.storage_key,
                file_size=f.file_size,
                mime_type=f.mime_type,
                uploaded_by=f.uploaded_by,
                created_at=f.created_at,
            )
            for f in files
        ],
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


@router.post("/url")
async def get_file_url_by_key(
    payload: dict,
    _: User = Depends(get_current_user),
):
    """按 storage_key (MinIO key) 获取下载/预览 URL。

    适用于不经过 files 表、直接以 storage_key 存储的文件
    （MOA 合同、物流附件、完工单、验收单、知识库文档等）。
    返回 download_url 与 preview_url（同一 presigned URL，可直接用于
    <a download> 或 <iframe>/<img> 预览）。
    """
    storage_key = payload.get("storage_key") or payload.get("file_key")
    if not storage_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="缺少 storage_key")

    try:
        url = await get_minio_url(storage_key)
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在或已失效")

    filename = storage_key.rsplit("/", 1)[-1]
    return {
        "storage_key": storage_key,
        "file_name": filename,
        "download_url": url,
        "preview_url": url,
        "expires_in": 3600,
    }


@router.get("/url")
async def get_file_url_by_key_query(
    storage_key: str,
    _: User = Depends(get_current_user),
):
    """GET 版本：按 storage_key 获取下载/预览 URL（前端 <img>/<iframe> 直接引用）。"""
    try:
        url = await get_minio_url(storage_key)
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在或已失效")

    filename = storage_key.rsplit("/", 1)[-1]
    return {
        "storage_key": storage_key,
        "file_name": filename,
        "download_url": url,
        "preview_url": url,
        "expires_in": 3600,
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