
"""
Audit Log Models
"""
from __future__ import annotations

from enum import Enum
from typing import Optional, TYPE_CHECKING
from datetime import datetime

from sqlalchemy import String, Text, ForeignKey, Integer, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class AuditLogAction(str, Enum):
    """审计日志操作类型"""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    STATUS_CHANGE = "STATUS_CHANGE"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    SUBMIT = "SUBMIT"
    AI_DISASSEMBLE = "AI_DISASSEMBLE"
    AI_CONFIRM = "AI_CONFIRM"
    FILE_UPLOAD = "FILE_UPLOAD"
    FILE_DELETE = "FILE_DELETE"
    CREATE_PROCUREMENT = "CREATE_PROCUREMENT"
    CLOSE_RISK = "CLOSE_RISK"
    CLOSE_NCR = "CLOSE_NCR"
    EXPORT_ISO = "EXPORT_ISO"
    PERMISSION_DENIED = "PERMISSION_DENIED"


class AuditLogObjectType(str, Enum):
    """审计日志对象类型"""
    CUSTOMER_VISIT = "CUSTOMER_VISIT"
    SHIPOWNER_BACKGROUND = "SHIPOWNER_BACKGROUND"
    SHIPYARD_INQUIRY = "SHIPYARD_INQUIRY"
    REPAIR_PLAN = "REPAIR_PLAN"
    REPAIR_TASK = "REPAIR_TASK"
    DAILY_REPORT = "DAILY_REPORT"
    PHOTO_EVIDENCE = "PHOTO_EVIDENCE"
    ANOMALY = "ANOMALY"
    NCR = "NCR"
    SPARE_PART_RISK = "SPARE_PART_RISK"
    SUPPLIER_FEEDBACK = "SUPPLIER_FEEDBACK"
    PROJECT_REVIEW = "PROJECT_REVIEW"
    PROCUREMENT = "PROCUREMENT"
    ORDER = "ORDER"
    FILE = "FILE"


class AuditLog(Base):
    """审计日志"""
    __tablename__ = "audit_logs"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    action: Mapped[AuditLogAction] = mapped_column(nullable=False, index=True)
    object_type: Mapped[AuditLogObjectType] = mapped_column(nullable=False, index=True)
    object_id: Mapped[int] = mapped_column(nullable=False, index=True)
    old_status: Mapped[Optional[str]] = mapped_column(String(100))
    new_status: Mapped[Optional[str]] = mapped_column(String(100))
    old_values: Mapped[Optional[dict]] = mapped_column(JSON)
    new_values: Mapped[Optional[dict]] = mapped_column(JSON)
    remarks: Mapped[Optional[str]] = mapped_column(Text)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50))
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Relationships
    user: Mapped["User"] = relationship("User")
