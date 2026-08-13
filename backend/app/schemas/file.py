from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int | None = None
    project_ship_name: str | None = None
    file_name: str
    file_type: str
    storage_key: str
    file_size: int
    mime_type: str
    uploaded_by: int | None = None
    created_at: datetime


class FileListResponse(BaseModel):
    items: list[FileResponse]
    total: int


class FileUploadResponse(BaseModel):
    id: int
    file_name: str
    file_type: str
    storage_key: str
    file_size: int
    mime_type: str