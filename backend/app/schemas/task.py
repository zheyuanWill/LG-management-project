import enum
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class TaskStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PAUSED = "paused"


class TaskCreate(BaseModel):
    name: str = Field(..., max_length=512)
    planned_end_date: date | None = None
    status: TaskStatus = TaskStatus.NOT_STARTED
    sort_order: int = 0


class TaskUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=512)
    planned_end_date: date | None = None
    status: TaskStatus | None = None
    sort_order: int | None = None


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    name: str
    planned_end_date: date | None = None
    status: str
    sort_order: int
    created_at: datetime
    updated_at: datetime


class TaskDailyUpdateCreate(BaseModel):
    update_date: date
    status: str | None = None
    remark: str | None = None
    audio_duration: int | None = None


class TaskDailyUpdateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    update_date: date
    status: str | None = None
    remark: str | None = None
    audio_duration: int | None = None
    created_at: datetime


class TaskPhotoUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    update_id: int
    storage_key: str
    created_at: datetime