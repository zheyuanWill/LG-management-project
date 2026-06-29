"""
Tracking Models
"""
from __future__ import annotations

from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from datetime import date

from sqlalchemy import String, Text, ForeignKey, Integer, Date, Boolean, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.order import ProjectType

if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.user import User
    from app.models.file import FileAttachment


class NodeStatus(str, Enum):
    """节点状态"""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    OVERDUE = "OVERDUE"
    SKIPPED = "SKIPPED"


class NodeTemplate(Base):
    """节点模板"""
    __tablename__ = "node_templates"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    project_type: Mapped[ProjectType] = mapped_column(SQLEnum(ProjectType, create_type=False), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    default_days: Mapped[Optional[int]] = mapped_column(Integer)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True)


class TrackingNode(Base):
    """项目跟单节点"""
    __tablename__ = "tracking_nodes"

    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    template_id: Mapped[Optional[int]] = mapped_column(ForeignKey("node_templates.id"))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[NodeStatus] = mapped_column(SQLEnum(NodeStatus, create_type=False), default=NodeStatus.PENDING)
    assignee_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    planned_date: Mapped[Optional[date]] = mapped_column(Date)
    actual_date: Mapped[Optional[date]] = mapped_column(Date)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="tracking_nodes")
    template: Mapped[Optional["NodeTemplate"]] = relationship("NodeTemplate")
    assignee: Mapped[Optional["User"]] = relationship("User")
