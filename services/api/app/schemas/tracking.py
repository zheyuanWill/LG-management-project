"""Tracking Schemas"""
from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel, Field

from app.models.tracking import NodeStatus
from app.models.order import ProjectType


class NodeTemplateBase(BaseModel):
    name: str = Field(..., max_length=200)
    project_type: ProjectType
    sort_order: int
    default_days: Optional[int] = None
    description: Optional[str] = None
    is_required: bool = True


class NodeTemplateCreate(NodeTemplateBase):
    pass


class NodeTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    sort_order: Optional[int] = None
    default_days: Optional[int] = None
    description: Optional[str] = None
    is_required: Optional[bool] = None


class NodeTemplateResponse(NodeTemplateBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TrackingNodeBase(BaseModel):
    order_id: int
    template_id: Optional[int] = None
    name: str = Field(..., max_length=200)
    sort_order: int
    assignee_id: Optional[int] = None
    planned_date: Optional[date] = None
    notes: Optional[str] = None


class TrackingNodeCreate(TrackingNodeBase):
    pass


class TrackingNodeUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    sort_order: Optional[int] = None
    assignee_id: Optional[int] = None
    planned_date: Optional[date] = None
    actual_date: Optional[date] = None
    notes: Optional[str] = None


class TrackingNodeResponse(TrackingNodeBase):
    id: int
    status: NodeStatus
    actual_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime
    assignee_name: Optional[str] = None

    class Config:
        from_attributes = True


class TrackingNodeStatusUpdate(BaseModel):
    status: NodeStatus
    actual_date: Optional[date] = None
    notes: Optional[str] = None


class TrackingNodeDetail(TrackingNodeResponse):
    attachments: List[dict] = []


class InitTrackingFromTemplate(BaseModel):
    """从模板初始化跟单节点"""
    order_id: int
    project_type: ProjectType
    start_date: Optional[date] = None

