"""
Sync Log Model — tracks every data synchronisation attempt with Kingdee.

Each row represents one API call (or intended call) and its outcome,
enabling retry, auditing, and troubleshooting.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional
from datetime import datetime

from sqlalchemy import String, Text, Integer, DateTime, JSON, Enum as SQLEnum, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SyncDirection(str, Enum):
    LG_TO_JDY = "lg_to_jdy"
    JDY_TO_LG = "jdy_to_lg"


class SyncStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class SyncLog(Base):
    __tablename__ = "sync_logs"

    entity_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True,
        comment="LG entity type: order, procurement, settlement, customer, supplier, product",
    )
    entity_id: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True,
        comment="LG record ID",
    )
    kingdee_doc_type: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="Kingdee document type: sale_order, purchase_instock, voucher, customer, supplier, product",
    )
    kingdee_doc_no: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="Document number returned by Kingdee",
    )
    direction: Mapped[str] = mapped_column(
        SQLEnum(SyncDirection, create_type=False), nullable=False, default=SyncDirection.LG_TO_JDY,
    )
    status: Mapped[str] = mapped_column(
        SQLEnum(SyncStatus, create_type=False), nullable=False, default=SyncStatus.PENDING, index=True,
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
    )
    request_payload: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True,
        comment="JSON body sent to Kingdee (for debugging)",
    )
    response_payload: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True,
        comment="JSON body received from Kingdee",
    )
    retry_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
    )
