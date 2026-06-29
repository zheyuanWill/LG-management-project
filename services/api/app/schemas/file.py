"""File Attachment Schemas"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.file import FileObjectType


class FileAttachmentBase(BaseModel):
    file_name: str = Field(..., max_length=500)
    original_name: str = Field(..., max_length=500)
    file_key: str = Field(..., max_length=500)
    mime_type: str = Field(..., max_length=200)
    size: int
    sha1: Optional[str] = Field(None, max_length=40)
    object_type: FileObjectType
    object_id: int
    thumbnail_key: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None


class FileAttachmentCreate(BaseModel):
    object_type: FileObjectType
    object_id: int
    notes: Optional[str] = None


class FileAttachmentResponse(FileAttachmentBase):
    id: int
    uploader_id: int
    created_at: datetime
    updated_at: datetime
    uploader_name: Optional[str] = None
    url: Optional[str] = None
    thumbnail_url: Optional[str] = None

    class Config:
        from_attributes = True


class UploadUrlRequest(BaseModel):
    """获取上传URL请求"""
    filename: str
    content_type: str
    object_type: FileObjectType
    object_id: int


class UploadUrlResponse(BaseModel):
    """获取上传URL响应"""
    upload_url: str
    file_key: str


class OfflineSyncRequest(BaseModel):
    """离线同步请求"""
    files: list[dict]  # [{local_id, file_key, object_type, object_id, timestamp}]


class OfflineSyncResponse(BaseModel):
    """离线同步响应"""
    success: list[str]  # local_ids
    failed: list[dict]  # [{local_id, error}]

