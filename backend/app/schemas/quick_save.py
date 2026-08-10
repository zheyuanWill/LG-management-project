from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class QuickSaveCreate(BaseModel):
    content_type: str = Field(..., max_length=20)
    content_text: str | None = None
    file_key: str | None = Field(default=None, max_length=512)
    recognized_text: str | None = None
    suggested_project_id: int | None = None


class QuickSaveUpdate(BaseModel):
    content_text: str | None = None
    file_key: str | None = Field(default=None, max_length=512)
    recognized_text: str | None = None
    suggested_project_id: int | None = None
    confirmed_project_id: int | None = None
    status: str | None = None


class QuickSaveResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    content_type: str
    content_text: str | None = None
    file_key: str | None = None
    recognized_text: str | None = None
    suggested_project_id: int | None = None
    confirmed_project_id: int | None = None
    status: str
    created_at: datetime