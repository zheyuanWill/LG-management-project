"""
修船监修模块数据库模型 - 简化版

核心数据模型：
1. Project - 修船项目（一条船的一次修理任务）
2. Task - AI生成的任务（执行单元）
3. DailyLog - 监修记录（监修工每日填写）
4. DailyLogAttachment - 监修记录附件
5. Issue - 问题/风险（AI识别或手工创建）
"""
from __future__ import annotations

from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from datetime import date, datetime

from sqlalchemy import (
    String, Text, ForeignKey, Date, Integer,
    Boolean, Enum as SQLEnum, DateTime
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.order import Order


class ProjectStatus(str, Enum):
    """项目状态"""
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class TaskCategory(str, Enum):
    """任务类别"""
    ENGINE = "ENGINE"
    ELECTRICAL = "ELECTRICAL"
    HULL = "HULL"
    PAINTING = "PAINTING"
    PIPING = "PIPING"
    DECK = "DECK"
    SAFETY = "SAFETY"
    CLASS_SURVEY = "CLASS_SURVEY"
    OTHER = "OTHER"


class IssueType(str, Enum):
    """问题类型"""
    QUALITY = "QUALITY"
    SCHEDULE = "SCHEDULE"
    SAFETY = "SAFETY"
    SUPPLY = "SUPPLY"
    OTHER = "OTHER"


class IssueSeverity(str, Enum):
    """问题严重程度"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IssueStatus(str, Enum):
    """问题状态"""
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class Project(Base):
    """修船项目"""
    __tablename__ = "sr_projects"

    project_name: Mapped[str] = mapped_column(String(200), nullable=False)
    vessel_name: Mapped[str] = mapped_column(String(200), nullable=False)
    order_id: Mapped[Optional[int]] = mapped_column(ForeignKey("orders.id"), index=True)
    ship_owner: Mapped[Optional[str]] = mapped_column(String(200))
    shipyard: Mapped[Optional[str]] = mapped_column(String(200))
    dock_in_date: Mapped[Optional[date]] = mapped_column(Date)
    dock_out_date: Mapped[Optional[date]] = mapped_column(Date)
    repair_specification: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        SQLEnum(ProjectStatus, create_type=False),
        default=ProjectStatus.NOT_STARTED
    )
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])
    order: Mapped[Optional["Order"]] = relationship("Order")
    tasks: Mapped[List["Task"]] = relationship(
        "Task", back_populates="project", cascade="all, delete-orphan"
    )
    daily_logs: Mapped[List["DailyLog"]] = relationship(
        "DailyLog", back_populates="project", cascade="all, delete-orphan"
    )
    issues: Mapped[List["Issue"]] = relationship(
        "Issue", back_populates="project", cascade="all, delete-orphan"
    )


class Task(Base):
    """修船任务"""
    __tablename__ = "sr_tasks"

    project_id: Mapped[int] = mapped_column(ForeignKey("sr_projects.id"), nullable=False)
    task_name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    category: Mapped[str] = mapped_column(
        SQLEnum(TaskCategory, create_type=False),
        default=TaskCategory.OTHER
    )
    status: Mapped[str] = mapped_column(
        SQLEnum(TaskStatus, create_type=False),
        default=TaskStatus.PENDING
    )
    planned_start: Mapped[Optional[date]] = mapped_column(Date)
    planned_end: Mapped[Optional[date]] = mapped_column(Date)
    actual_start: Mapped[Optional[date]] = mapped_column(Date)
    actual_end: Mapped[Optional[date]] = mapped_column(Date)
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    project: Mapped["Project"] = relationship("Project", back_populates="tasks")
    issues: Mapped[List["Issue"]] = relationship("Issue", back_populates="task")


class DailyLog(Base):
    """监修记录"""
    __tablename__ = "sr_daily_logs"

    project_id: Mapped[int] = mapped_column(ForeignKey("sr_projects.id"), nullable=False)
    log_date: Mapped[date] = mapped_column(Date, nullable=False)
    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    work_done: Mapped[Optional[str]] = mapped_column(Text)
    discoveries: Mapped[Optional[str]] = mapped_column(Text)
    tomorrow_plan: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    ai_processed: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    ai_summary: Mapped[Optional[str]] = mapped_column(Text)

    project: Mapped["Project"] = relationship("Project", back_populates="daily_logs")
    reporter: Mapped["User"] = relationship("User", foreign_keys=[reporter_id])
    attachments: Mapped[List["DailyLogAttachment"]] = relationship(
        "DailyLogAttachment", back_populates="daily_log", cascade="all, delete-orphan"
    )
    issues: Mapped[List["Issue"]] = relationship("Issue", back_populates="source_log")


class DailyLogAttachment(Base):
    """监修记录附件"""
    __tablename__ = "sr_daily_log_attachments"

    daily_log_id: Mapped[int] = mapped_column(ForeignKey("sr_daily_logs.id"), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str] = mapped_column(String(200), nullable=False)
    file_size: Mapped[Optional[int]] = mapped_column(Integer)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text)

    daily_log: Mapped["DailyLog"] = relationship("DailyLog", back_populates="attachments")


class Issue(Base):
    """问题/风险"""
    __tablename__ = "sr_issues"

    project_id: Mapped[int] = mapped_column(ForeignKey("sr_projects.id"), nullable=False)
    task_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sr_tasks.id"))
    daily_log_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sr_daily_logs.id"))
    issue_type: Mapped[str] = mapped_column(
        SQLEnum(IssueType, create_type=False),
        default=IssueType.OTHER
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(
        SQLEnum(IssueSeverity, create_type=False),
        default=IssueSeverity.MEDIUM
    )
    status: Mapped[str] = mapped_column(
        SQLEnum(IssueStatus, create_type=False),
        default=IssueStatus.OPEN
    )
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    resolved_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))

    project: Mapped["Project"] = relationship("Project", back_populates="issues")
    task: Mapped[Optional["Task"]] = relationship("Task", back_populates="issues")
    source_log: Mapped[Optional["DailyLog"]] = relationship("DailyLog", back_populates="issues")
    resolver: Mapped[Optional["User"]] = relationship("User", foreign_keys=[resolved_by])
