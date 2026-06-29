"""
Workflow Models — Visual workflow orchestration for business processes.

Supports:
- Templates: reusable workflow definitions with visual layout
- Instances: running executions of templates bound to orders
- Audit logs: detailed trail of every state transition
"""
from __future__ import annotations

from enum import Enum
from typing import Optional, TYPE_CHECKING
from datetime import datetime

from sqlalchemy import (
    String, Text, ForeignKey, Integer, Boolean, JSON,
    DateTime, Enum as SQLEnum, Float,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.user import User


class WorkflowStatus(str, Enum):
    """工作流实例状态"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class WorkflowNodeStatus(str, Enum):
    """工作流节点执行状态"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    SKIPPED = "SKIPPED"
    FAILED = "FAILED"
    WAITING = "WAITING"  # For parallel gateway join — waiting for all predecessors


class WorkflowTemplate(Base):
    """工作流模板 — 存储可视化编排的流程定义"""
    __tablename__ = "workflow_templates"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    project_type: Mapped[Optional[str]] = mapped_column(String(50))
    definition: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))

    # Relationships
    creator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by])
    instances: Mapped[list["WorkflowInstance"]] = relationship(
        "WorkflowInstance", back_populates="template"
    )


class WorkflowInstance(Base):
    """工作流实例 — 某个订单的流程执行状态"""
    __tablename__ = "workflow_instances"

    template_id: Mapped[int] = mapped_column(ForeignKey("workflow_templates.id"), nullable=False)
    order_id: Mapped[Optional[int]] = mapped_column(ForeignKey("orders.id"))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[WorkflowStatus] = mapped_column(
        SQLEnum(WorkflowStatus, create_type=False), default=WorkflowStatus.PENDING
    )
    current_node_id: Mapped[Optional[str]] = mapped_column(String(100))
    node_states: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    definition_snapshot: Mapped[Optional[dict]] = mapped_column(JSON)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    started_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))

    # Relationships
    template: Mapped["WorkflowTemplate"] = relationship(
        "WorkflowTemplate", back_populates="instances"
    )
    order: Mapped[Optional["Order"]] = relationship("Order")
    starter: Mapped[Optional["User"]] = relationship("User", foreign_keys=[started_by])
    audit_logs: Mapped[list["WorkflowAuditLog"]] = relationship(
        "WorkflowAuditLog", back_populates="instance", order_by="WorkflowAuditLog.created_at"
    )


class WorkflowAuditLog(Base):
    """工作流审计日志 — 记录每一次状态变更的完整审计轨迹"""
    __tablename__ = "workflow_audit_logs"

    instance_id: Mapped[int] = mapped_column(
        ForeignKey("workflow_instances.id", ondelete="CASCADE"), nullable=False
    )
    node_id: Mapped[Optional[str]] = mapped_column(String(100))
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    # e.g. "node_advance", "node_skip", "condition_evaluate", "timer_fire",
    #       "instance_start", "instance_complete", "instance_cancel"
    old_status: Mapped[Optional[str]] = mapped_column(String(30))
    new_status: Mapped[Optional[str]] = mapped_column(String(30))
    operator_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    details: Mapped[Optional[dict]] = mapped_column(JSON)
    # Stores context like condition expression, result, timer duration, etc.

    # Relationships
    instance: Mapped["WorkflowInstance"] = relationship(
        "WorkflowInstance", back_populates="audit_logs"
    )
    operator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[operator_id])
