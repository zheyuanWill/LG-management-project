"""
ISO 9001 Process Models

Covers: risk assessment, inquiry records, supplier comparison,
contract review, project changes, quality inspection,
project acceptance, project closure, complaints,
satisfaction surveys, supplier admission, supplier evaluation,
change logs, and number sequences.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from decimal import Decimal
from datetime import date, datetime

from sqlalchemy import (
    String, Text, ForeignKey, Numeric, Date, Integer,
    Boolean, Enum as SQLEnum, DateTime, JSON, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.customer import Customer
    from app.models.product import Supplier
    from app.models.user import User
    from app.models.contract import Contract


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class RiskLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class ApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class InquiryMethod(str, Enum):
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    CHAT = "CHAT"

class InspectionResult(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    CONDITIONAL = "CONDITIONAL"

class ComplaintStatus(str, Enum):
    RECEIVED = "RECEIVED"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"

class SurveyStatus(str, Enum):
    DRAFT = "DRAFT"
    SENT = "SENT"
    RESPONDED = "RESPONDED"
    CLOSED = "CLOSED"

class SupplierQualification(str, Enum):
    PENDING = "PENDING"
    QUALIFIED = "QUALIFIED"
    OBSERVED = "OBSERVED"
    ELIMINATED = "ELIMINATED"

class EvaluationLevel(str, Enum):
    EXCELLENT = "EXCELLENT"
    QUALIFIED = "QUALIFIED"
    OBSERVED = "OBSERVED"
    ELIMINATED = "ELIMINATED"

class ChangeType(str, Enum):
    REQUIREMENT = "REQUIREMENT"
    PRICE = "PRICE"
    SCHEDULE = "SCHEDULE"
    SCOPE = "SCOPE"

class ClosureStatus(str, Enum):
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    CLOSED = "CLOSED"

class CancellationCategory(str, Enum):
    PRICE = "PRICE"
    DELIVERY = "DELIVERY"
    REQUIREMENT_CHANGE = "REQUIREMENT_CHANGE"
    COMPETITOR = "COMPETITOR"
    OTHER = "OTHER"


# ---------------------------------------------------------------------------
# Number Sequence (for generating sequential IDs like RFQ-MT26001A)
# ---------------------------------------------------------------------------

class NumberSequence(Base):
    """编号序列，用于生成各种业务单号"""
    __tablename__ = "number_sequences"
    __table_args__ = (UniqueConstraint("prefix", name="uq_number_sequences_prefix"),)

    prefix: Mapped[str] = mapped_column(String(30), nullable=False)
    current_value: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


# ---------------------------------------------------------------------------
# 1-4: Inquiry Risk Assessment (询价风险评估表 - 模板#7)
# ---------------------------------------------------------------------------

class InquiryRiskAssessment(Base):
    """询价风险评估"""
    __tablename__ = "inquiry_risk_assessments"

    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    customer_credit: Mapped[Optional[str]] = mapped_column(SQLEnum(RiskLevel, create_type=False))
    project_feasibility: Mapped[Optional[str]] = mapped_column(SQLEnum(RiskLevel, create_type=False))
    payment_risk: Mapped[Optional[str]] = mapped_column(SQLEnum(RiskLevel, create_type=False))
    overall_risk: Mapped[Optional[str]] = mapped_column(SQLEnum(RiskLevel, create_type=False))
    assessment_notes: Mapped[Optional[str]] = mapped_column(Text)
    assessor_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    approved_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(
        SQLEnum(ApprovalStatus, create_type=False), default=ApprovalStatus.PENDING
    )

    order: Mapped["Order"] = relationship("Order", foreign_keys=[order_id])
    assessor: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assessor_id])
    approver: Mapped[Optional["User"]] = relationship("User", foreign_keys=[approved_by])


# ---------------------------------------------------------------------------
# 2-3: Inquiry Record (对外询价记录)
# ---------------------------------------------------------------------------

class InquiryRecord(Base):
    """对外询价记录"""
    __tablename__ = "inquiry_records"

    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"), nullable=False)
    inquiry_method: Mapped[str] = mapped_column(
        SQLEnum(InquiryMethod, create_type=False), default=InquiryMethod.EMAIL
    )
    inquiry_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    responded: Mapped[bool] = mapped_column(Boolean, default=False)
    response_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    order: Mapped["Order"] = relationship("Order", foreign_keys=[order_id])
    supplier: Mapped["Supplier"] = relationship("Supplier", foreign_keys=[supplier_id])


# ---------------------------------------------------------------------------
# 3-3: Supplier Comparison (比价记录)
# ---------------------------------------------------------------------------

class SupplierComparison(Base):
    """供应商比价记录"""
    __tablename__ = "supplier_comparisons"

    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(200))
    selected_supplier_id: Mapped[Optional[int]] = mapped_column(ForeignKey("suppliers.id"))
    selection_reason: Mapped[Optional[str]] = mapped_column(Text)
    comparison_data: Mapped[Optional[dict]] = mapped_column(JSON)
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))

    order: Mapped["Order"] = relationship("Order", foreign_keys=[order_id])
    selected_supplier: Mapped[Optional["Supplier"]] = relationship(
        "Supplier", foreign_keys=[selected_supplier_id]
    )
    creator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by])


# ---------------------------------------------------------------------------
# 7-5: Contract Review (合同评审表 - 模板#8)
# ---------------------------------------------------------------------------

class ContractReview(Base):
    """合同评审"""
    __tablename__ = "contract_reviews"

    contract_id: Mapped[int] = mapped_column(ForeignKey("contracts.id"), nullable=False)
    delivery_review: Mapped[Optional[str]] = mapped_column(Text)
    payment_review: Mapped[Optional[str]] = mapped_column(Text)
    technical_review: Mapped[Optional[str]] = mapped_column(Text)
    penalty_review: Mapped[Optional[str]] = mapped_column(Text)
    warranty_review: Mapped[Optional[str]] = mapped_column(Text)
    conclusion: Mapped[str] = mapped_column(
        String(20), default="PENDING"
    )
    reviewers: Mapped[Optional[dict]] = mapped_column(JSON)
    review_date: Mapped[Optional[date]] = mapped_column(Date)

    contract: Mapped["Contract"] = relationship("Contract", foreign_keys=[contract_id])


# ---------------------------------------------------------------------------
# 8-4: Project Change (项目变更确认单 - 模板#10)
# ---------------------------------------------------------------------------

class ProjectChange(Base):
    """项目变更"""
    __tablename__ = "project_changes"

    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    change_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    change_type: Mapped[str] = mapped_column(SQLEnum(ChangeType, create_type=False), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    impact_analysis: Mapped[Optional[str]] = mapped_column(Text)
    customer_confirmation: Mapped[bool] = mapped_column(Boolean, default=False)
    confirmation_date: Mapped[Optional[date]] = mapped_column(Date)
    confirmation_file_id: Mapped[Optional[int]] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(
        SQLEnum(ApprovalStatus, create_type=False), default=ApprovalStatus.PENDING
    )
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))

    order: Mapped["Order"] = relationship("Order", foreign_keys=[order_id])
    creator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by])


# ---------------------------------------------------------------------------
# 8-2: Quality Inspection (质量检验)
# ---------------------------------------------------------------------------

class QualityInspection(Base):
    """质量检验"""
    __tablename__ = "quality_inspections"

    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    procurement_id: Mapped[Optional[int]] = mapped_column(ForeignKey("procurements.id"))
    inspection_type: Mapped[str] = mapped_column(String(50), nullable=False)
    inspection_date: Mapped[Optional[date]] = mapped_column(Date)
    result: Mapped[Optional[str]] = mapped_column(SQLEnum(InspectionResult, create_type=False))
    inspector_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    findings: Mapped[Optional[str]] = mapped_column(Text)
    report_data: Mapped[Optional[dict]] = mapped_column(JSON)

    order: Mapped["Order"] = relationship("Order", foreign_keys=[order_id])
    inspector: Mapped[Optional["User"]] = relationship("User", foreign_keys=[inspector_id])


# ---------------------------------------------------------------------------
# 9-1: Project Acceptance (项目验收确认单 - 模板#11)
# ---------------------------------------------------------------------------

class ProjectAcceptance(Base):
    """项目验收"""
    __tablename__ = "project_acceptances"

    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    acceptance_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    acceptance_type: Mapped[str] = mapped_column(String(20), nullable=False)
    acceptance_date: Mapped[Optional[date]] = mapped_column(Date)
    customer_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    confirmation_method: Mapped[Optional[str]] = mapped_column(String(20))
    confirmation_date: Mapped[Optional[date]] = mapped_column(Date)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="PENDING")

    order: Mapped["Order"] = relationship("Order", foreign_keys=[order_id])


# ---------------------------------------------------------------------------
# 9-3/9-4: Project Closure (项目关闭表 - 模板#12, 含项目总结)
# ---------------------------------------------------------------------------

class ProjectClosure(Base):
    """项目关闭"""
    __tablename__ = "project_closures"

    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False, unique=True)
    closure_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    all_payments_settled: Mapped[bool] = mapped_column(Boolean, default=False)
    all_receivables_collected: Mapped[bool] = mapped_column(Boolean, default=False)
    documents_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    archive_location: Mapped[Optional[str]] = mapped_column(String(200))
    lessons_learned: Mapped[Optional[str]] = mapped_column(Text)
    improvement_suggestions: Mapped[Optional[str]] = mapped_column(Text)
    closed_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    approved_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(
        SQLEnum(ClosureStatus, create_type=False), default=ClosureStatus.DRAFT
    )

    order: Mapped["Order"] = relationship("Order", foreign_keys=[order_id])
    closer: Mapped[Optional["User"]] = relationship("User", foreign_keys=[closed_by])
    approver: Mapped[Optional["User"]] = relationship("User", foreign_keys=[approved_by])


# ---------------------------------------------------------------------------
# 10-1: Complaint (客户投诉处理记录表 - 模板#13)
# ---------------------------------------------------------------------------

class Complaint(Base):
    """客户投诉"""
    __tablename__ = "complaints"

    complaint_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    order_id: Mapped[Optional[int]] = mapped_column(ForeignKey("orders.id"))
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    source: Mapped[str] = mapped_column(SQLEnum(InquiryMethod, create_type=False), default=InquiryMethod.EMAIL)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    investigation: Mapped[Optional[str]] = mapped_column(Text)
    resolution: Mapped[Optional[str]] = mapped_column(Text)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    customer_feedback: Mapped[Optional[str]] = mapped_column(Text)
    handler_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    sla_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(
        SQLEnum(ComplaintStatus, create_type=False), default=ComplaintStatus.RECEIVED
    )
    period_no_complaint: Mapped[bool] = mapped_column(Boolean, default=False)

    order: Mapped[Optional["Order"]] = relationship("Order", foreign_keys=[order_id])
    customer: Mapped["Customer"] = relationship("Customer", foreign_keys=[customer_id])
    handler: Mapped[Optional["User"]] = relationship("User", foreign_keys=[handler_id])


# ---------------------------------------------------------------------------
# 10-3: Satisfaction Survey (客户满意度调查表 - 模板#14)
# ---------------------------------------------------------------------------

class SatisfactionSurvey(Base):
    """客户满意度调查"""
    __tablename__ = "satisfaction_surveys"

    survey_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    service_quality: Mapped[Optional[int]] = mapped_column(Integer)
    response_speed: Mapped[Optional[int]] = mapped_column(Integer)
    price_reasonability: Mapped[Optional[int]] = mapped_column(Integer)
    communication: Mapped[Optional[int]] = mapped_column(Integer)
    overall_satisfaction: Mapped[Optional[int]] = mapped_column(Integer)
    comments: Mapped[Optional[str]] = mapped_column(Text)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(
        SQLEnum(SurveyStatus, create_type=False), default=SurveyStatus.DRAFT
    )

    customer: Mapped["Customer"] = relationship("Customer", foreign_keys=[customer_id])


# ---------------------------------------------------------------------------
# 11-1: Supplier Admission (供应商准入审批表 - 模板#15)
# ---------------------------------------------------------------------------

class SupplierAdmission(Base):
    """供应商准入审批"""
    __tablename__ = "supplier_admissions"

    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"), nullable=False)
    business_license_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    industry_qualification_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    case_references: Mapped[Optional[str]] = mapped_column(Text)
    trial_evaluation: Mapped[Optional[str]] = mapped_column(Text)
    trial_result: Mapped[Optional[str]] = mapped_column(String(20))
    approval_status: Mapped[str] = mapped_column(
        SQLEnum(ApprovalStatus, create_type=False), default=ApprovalStatus.PENDING
    )
    approved_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    supplier: Mapped["Supplier"] = relationship("Supplier", foreign_keys=[supplier_id])
    approver: Mapped[Optional["User"]] = relationship("User", foreign_keys=[approved_by])


# ---------------------------------------------------------------------------
# 11-2: Supplier Evaluation (供应商年度评价表 - 模板#16)
# ---------------------------------------------------------------------------

class SupplierEvaluation(Base):
    """供应商年度评价"""
    __tablename__ = "supplier_evaluations"

    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    quality_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    delivery_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    price_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    service_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    total_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    level: Mapped[Optional[str]] = mapped_column(SQLEnum(EvaluationLevel, create_type=False))
    evaluator_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    evaluation_date: Mapped[Optional[date]] = mapped_column(Date)
    notified_supplier: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    supplier: Mapped["Supplier"] = relationship("Supplier", foreign_keys=[supplier_id])
    evaluator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[evaluator_id])


# ---------------------------------------------------------------------------
# 5-2: Change Log (修改追踪)
# ---------------------------------------------------------------------------

class ChangeLog(Base):
    """修改记录追踪"""
    __tablename__ = "change_logs"

    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    change_reason: Mapped[str] = mapped_column(Text, nullable=False)
    change_content: Mapped[Optional[dict]] = mapped_column(JSON)
    changed_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    version_before: Mapped[Optional[str]] = mapped_column(String(10))
    version_after: Mapped[Optional[str]] = mapped_column(String(10))

    operator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[changed_by])


# ---------------------------------------------------------------------------
# AI Knowledge Base
# ---------------------------------------------------------------------------

class KnowledgeDocument(Base):
    """AI知识库文档"""
    __tablename__ = "knowledge_documents"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text)
    doc_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_type: Mapped[Optional[str]] = mapped_column(String(50))
    source_id: Mapped[Optional[int]] = mapped_column(Integer)
    file_id: Mapped[Optional[int]] = mapped_column(Integer)
    embedding_status: Mapped[str] = mapped_column(String(20), default="pending")
    tags: Mapped[Optional[dict]] = mapped_column(JSON)
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))

    creator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by])


class KnowledgeChunk(Base):
    """AI知识库文档分块 (embedding存储)"""
    __tablename__ = "knowledge_chunks"

    document_id: Mapped[int] = mapped_column(
        ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[Optional[str]] = mapped_column(Text)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON)

    document: Mapped["KnowledgeDocument"] = relationship(
        "KnowledgeDocument", foreign_keys=[document_id]
    )
