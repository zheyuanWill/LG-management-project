"""
Notification Models
"""
from __future__ import annotations

from enum import Enum
from typing import Optional, TYPE_CHECKING
from datetime import datetime

from sqlalchemy import String, Text, ForeignKey, Boolean, Enum as SQLEnum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class NotificationType(str, Enum):
    """通知类型"""
    APPROVAL = "APPROVAL"      # 审批类
    OVERDUE = "OVERDUE"        # 逾期提醒
    PAYMENT = "PAYMENT"        # 回款通知
    REMINDER = "REMINDER"      # 一般提醒
    SYSTEM = "SYSTEM"          # 系统通知
    INFO = "INFO"              # 一般信息
    # 修船相关通知类型
    DAILY_REPORT = "DAILY_REPORT"      # 日报提醒
    RISK_NOTIFY = "RISK_NOTIFY"        # 风险通知
    ANOMALY = "ANOMALY"          # 异常通知
    NCR_ALERT = "NCR_ALERT"          # NCR提醒
    SPARE_PART = "SPARE_PART"        # 备件风险通知
    SUPPLIER_FEEDBACK = "SUPPLIER_FEEDBACK"  # 供应商反馈


class Notification(Base):
    """通知消息"""
    __tablename__ = "notifications"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    type: Mapped[NotificationType] = mapped_column(SQLEnum(NotificationType, create_type=False), default=NotificationType.INFO)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # 关联实体（可选）
    related_type: Mapped[Optional[str]] = mapped_column(String(50))  # order, procurement, settlement, etc.
    related_id: Mapped[Optional[int]] = mapped_column()
    
    # Relationships
    user: Mapped["User"] = relationship("User")
