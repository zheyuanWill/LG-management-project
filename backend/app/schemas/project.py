import enum
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class ProjectType(str, enum.Enum):
    SUPERVISION = "supervision"
    BROKERAGE_SALE = "brokerage_sale"
    BROKERAGE_REPAIR = "brokerage_repair"
    SPARE_PARTS = "spare_parts"


class ProjectStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ProjectCreate(BaseModel):
    type: ProjectType
    ship_name: str = Field(..., max_length=128)
    imo: str | None = Field(default=None, max_length=16)
    owner_id: int | None = None
    planned_completion_date: date | None = None
    remarks: str | None = None


class ProjectUpdate(BaseModel):
    ship_name: str | None = Field(default=None, max_length=128)
    imo: str | None = Field(default=None, max_length=16)
    owner_id: int | None = None
    status: ProjectStatus | None = None
    planned_completion_date: date | None = None
    actual_completion_date: date | None = None
    remarks: str | None = None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_no: str
    type: str
    status: str
    ship_name: str
    imo: str | None = None
    owner_id: int | None = None
    planned_completion_date: date | None = None
    actual_completion_date: date | None = None
    remarks: str | None = None
    created_at: datetime
    updated_at: datetime


class ProjectListResponse(BaseModel):
    items: list[ProjectResponse]
    total: int