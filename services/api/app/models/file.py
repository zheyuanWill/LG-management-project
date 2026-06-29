"""
File Attachment Models
"""
from __future__ import annotations

from enum import Enum
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Text, ForeignKey, Integer, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class FileObjectType(str, Enum):
    """附件对象类型"""
    ORDER = "ORDER"
    QUOTE = "QUOTE"
    CONTRACT = "CONTRACT"
    PROCUREMENT = "PROCUREMENT"
    TRACKING_NODE = "TRACKING_NODE"
    SETTLEMENT = "SETTLEMENT"
    INVOICE = "INVOICE"
    BILL_OF_LADING = "BILL_OF_LADING"
    ACCEPTANCE = "ACCEPTANCE"
    PHOTO = "PHOTO"
    RISK_ASSESSMENT = "RISK_ASSESSMENT"
    CONTRACT_REVIEW = "CONTRACT_REVIEW"
    QUALITY_INSPECTION = "QUALITY_INSPECTION"
    PROJECT_CHANGE = "PROJECT_CHANGE"
    PROJECT_CLOSURE = "PROJECT_CLOSURE"
    COMPLAINT = "COMPLAINT"
    SUPPLIER_ADMISSION = "SUPPLIER_ADMISSION"
    KNOWLEDGE = "KNOWLEDGE"
    OTHER = "OTHER"
    # 修船相关
    CUSTOMER_VISIT = "CUSTOMER_VISIT"
    SHIPOWNER_BACKGROUND = "SHIPOWNER_BACKGROUND"
    SHIPYARD_INQUIRY = "SHIPYARD_INQUIRY"
    REPAIR_PLAN = "REPAIR_PLAN"
    DAILY_REPORT = "DAILY_REPORT"
    PHOTO_EVIDENCE = "PHOTO_EVIDENCE"
    ANOMALY = "ANOMALY"
    NCR = "NCR"
    NCR_BEFORE = "NCR_BEFORE"
    NCR_AFTER = "NCR_AFTER"
    SPARE_PART_RISK = "SPARE_PART_RISK"
    SPARE_PART_NAMEPLATE = "SPARE_PART_NAMEPLATE"
    SPARE_PART_OLD = "SPARE_PART_OLD"
    DRAWING_MANUAL = "DRAWING_MANUAL"
    ENTRY_MEETING_MINUTES = "ENTRY_MEETING_MINUTES"
    SHIPYARD_QUOTE = "SHIPYARD_QUOTE"
    ISO_ARCHIVE = "ISO_ARCHIVE"
    PROJECT_REVIEW = "PROJECT_REVIEW"


class FileAttachment(Base):
    """文件附件"""
    __tablename__ = "file_attachments"

    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    original_name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_key: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(200), nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    sha1: Mapped[Optional[str]] = mapped_column(String(40))
    object_type: Mapped[FileObjectType] = mapped_column(SQLEnum(FileObjectType, create_type=False), nullable=False)
    object_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    uploader_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    thumbnail_key: Mapped[Optional[str]] = mapped_column(String(500))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    uploader: Mapped["User"] = relationship("User")
