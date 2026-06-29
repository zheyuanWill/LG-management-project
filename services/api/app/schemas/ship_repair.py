"""
修船监修模块 Pydantic Schemas - V2 简化版
"""
from typing import Optional, List, Any
from datetime import date, datetime
from pydantic import BaseModel, Field


# ==================== Project ====================

class ProjectCreate(BaseModel):
    project_name: str = Field(..., max_length=200)
    vessel_name: str = Field(..., max_length=200)
    order_id: Optional[int] = None
    ship_owner: Optional[str] = Field(None, max_length=200)
    shipyard: Optional[str] = Field(None, max_length=200)
    dock_in_date: Optional[date] = None
    dock_out_date: Optional[date] = None
    repair_specification: Optional[str] = None


class ProjectUpdate(BaseModel):
    project_name: Optional[str] = Field(None, max_length=200)
    vessel_name: Optional[str] = Field(None, max_length=200)
    order_id: Optional[int] = None
    ship_owner: Optional[str] = Field(None, max_length=200)
    shipyard: Optional[str] = Field(None, max_length=200)
    dock_in_date: Optional[date] = None
    dock_out_date: Optional[date] = None
    repair_specification: Optional[str] = None
    status: Optional[str] = None


class ProjectResponse(BaseModel):
    id: int
    project_name: str
    vessel_name: str
    order_id: Optional[int] = None
    order_no: Optional[str] = None
    customer_name: Optional[str] = None
    ship_owner: Optional[str] = None
    shipyard: Optional[str] = None
    dock_in_date: Optional[date] = None
    dock_out_date: Optional[date] = None
    repair_specification: Optional[str] = None
    status: str
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectDetailResponse(ProjectResponse):
    task_count: int = 0
    task_completed: int = 0
    task_in_progress: int = 0
    open_issues: int = 0
    high_severity_issues: int = 0


# ==================== Task ====================

class TaskCreate(BaseModel):
    task_name: str = Field(..., max_length=500)
    description: Optional[str] = None
    category: str = "OTHER"
    planned_start: Optional[date] = None
    planned_end: Optional[date] = None
    notes: Optional[str] = None


class TaskUpdate(BaseModel):
    task_name: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    planned_start: Optional[date] = None
    planned_end: Optional[date] = None
    actual_start: Optional[date] = None
    actual_end: Optional[date] = None
    notes: Optional[str] = None
    sort_order: Optional[int] = None


class TaskResponse(BaseModel):
    id: int
    project_id: int
    task_name: str
    description: Optional[str] = None
    category: str
    status: str
    planned_start: Optional[date] = None
    planned_end: Optional[date] = None
    actual_start: Optional[date] = None
    actual_end: Optional[date] = None
    ai_generated: bool
    sort_order: int
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== DailyLog ====================

class DailyLogCreate(BaseModel):
    log_date: date
    work_done: Optional[str] = None
    discoveries: Optional[str] = None
    tomorrow_plan: Optional[str] = None
    notes: Optional[str] = None


class DailyLogUpdate(BaseModel):
    work_done: Optional[str] = None
    discoveries: Optional[str] = None
    tomorrow_plan: Optional[str] = None
    notes: Optional[str] = None


class DailyLogAttachmentResponse(BaseModel):
    id: int
    daily_log_id: int
    file_path: str
    file_name: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DailyLogResponse(BaseModel):
    id: int
    project_id: int
    log_date: date
    reporter_id: int
    work_done: Optional[str] = None
    discoveries: Optional[str] = None
    tomorrow_plan: Optional[str] = None
    notes: Optional[str] = None
    ai_processed: bool
    ai_processed_at: Optional[datetime] = None
    ai_summary: Optional[str] = None
    attachments: List[DailyLogAttachmentResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Issue ====================

class IssueCreate(BaseModel):
    task_id: Optional[int] = None
    issue_type: str = "OTHER"
    title: str = Field(..., max_length=500)
    description: Optional[str] = None
    severity: str = "MEDIUM"


class IssueUpdate(BaseModel):
    task_id: Optional[int] = None
    issue_type: Optional[str] = None
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    resolution_notes: Optional[str] = None


class IssueResponse(BaseModel):
    id: int
    project_id: int
    task_id: Optional[int] = None
    daily_log_id: Optional[int] = None
    issue_type: str
    title: str
    description: Optional[str] = None
    severity: str
    status: str
    ai_generated: bool
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== AI Responses ====================

class AITaskGenerationResponse(BaseModel):
    tasks_created: int
    tasks: List[TaskResponse]


class AIProcessLogResponse(BaseModel):
    tasks_updated: List[dict] = Field(default_factory=list)
    issues_created: List[dict] = Field(default_factory=list)
    summary: str = ""


class AIReportResponse(BaseModel):
    report_date: Optional[str] = None
    content: str
    sections: Optional[dict] = None
