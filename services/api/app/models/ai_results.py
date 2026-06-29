"""
AI 功能结果持久化
"""
from __future__ import annotations

from enum import Enum
from typing import Optional, List
from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, Integer, Boolean, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AIToolType(str, Enum):
    """AI 工具类型"""
    REPAIR_PLAN_DISASSEMBLY = "REPAIR_PLAN_DISASSEMBLY"
    MANHOUR_ESTIMATION = "MANHOUR_ESTIMATION"
    SPARE_PART_PREDICTION = "SPARE_PART_PREDICTION"
    RISK_IDENTIFICATION = "RISK_IDENTIFICATION"
    DAILY_REPORT_GENERATION = "DAILY_REPORT_GENERATION"
    INCIDENT_ANALYSIS = "INCIDENT_ANALYSIS"
    SUPPLIER_QUOTE_ANALYSIS = "SUPPLIER_QUOTE_ANALYSIS"
    PROCUREMENT_DECISION = "PROCUREMENT_DECISION"
    PROJECT_STATUS_ANALYSIS = "PROJECT_STATUS_ANALYSIS"
    PROJECT_REVIEW = "PROJECT_REVIEW"


class AIResult(Base):
    """AI 功能执行结果"""
    __tablename__ = "ai_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tool_type: Mapped[str] = mapped_column(String(100), nullable=False)
    order_id: Mapped[Optional[int]] = mapped_column(ForeignKey("orders.id"))
    procurement_id: Mapped[Optional[int]] = mapped_column(ForeignKey("procurements.id"))

    input_data: Mapped[Optional[dict]] = mapped_column(JSON)
    output_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    execution_time_seconds: Mapped[Optional[float]] = mapped_column(Integer)
    is_success: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")

    # Relationships
    order: Mapped[Optional["Order"]] = relationship("Order", foreign_keys=[order_id])
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])
