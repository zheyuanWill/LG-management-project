"""
ISO 9001 Process Routes

Consolidated router for all ISO 9001 process management:
- Inquiry risk assessments
- Inquiry records (outbound supplier inquiries)
- Supplier comparisons
- Contract reviews
- Project changes
- Quality inspections
- Project acceptances
- Project closures
- Complaints
- Satisfaction surveys
- Supplier admissions
- Supplier evaluations
- Change logs
"""
from datetime import datetime, date
from typing import Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.iso_process import (
    InquiryRiskAssessment, InquiryRecord,
    SupplierComparison, ContractReview,
    ProjectChange, QualityInspection,
    ProjectAcceptance, ProjectClosure,
    Complaint, SatisfactionSurvey,
    SupplierAdmission, SupplierEvaluation,
    ChangeLog, KnowledgeDocument,
    ApprovalStatus, ComplaintStatus, SurveyStatus, ClosureStatus,
)
from app.services.number_service import (
    generate_change_no, generate_acceptance_no,
    generate_closure_no, generate_complaint_no, generate_survey_no,
)

router = APIRouter(tags=["ISO Process"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class RiskAssessmentCreate(BaseModel):
    order_id: int
    customer_credit: Optional[str] = None
    project_feasibility: Optional[str] = None
    payment_risk: Optional[str] = None
    overall_risk: Optional[str] = None
    assessment_notes: Optional[str] = None

class RiskAssessmentApprove(BaseModel):
    approved: bool
    notes: Optional[str] = None

class InquiryRecordCreate(BaseModel):
    order_id: int
    supplier_id: int
    inquiry_method: str = "EMAIL"
    inquiry_time: Optional[str] = None
    deadline: Optional[str] = None
    notes: Optional[str] = None

class InquiryRecordUpdate(BaseModel):
    responded: Optional[bool] = None
    response_time: Optional[str] = None
    notes: Optional[str] = None

class ComparisonCreate(BaseModel):
    order_id: int
    title: Optional[str] = None
    selected_supplier_id: Optional[int] = None
    selection_reason: Optional[str] = None
    comparison_data: Optional[dict] = None

class ContractReviewCreate(BaseModel):
    contract_id: int
    delivery_review: Optional[str] = None
    payment_review: Optional[str] = None
    technical_review: Optional[str] = None
    penalty_review: Optional[str] = None
    warranty_review: Optional[str] = None
    conclusion: str = "PENDING"
    reviewers: Optional[dict] = None
    review_date: Optional[str] = None

class ProjectChangeCreate(BaseModel):
    order_id: int
    change_type: str
    description: str
    impact_analysis: Optional[str] = None

class ProjectChangeConfirm(BaseModel):
    customer_confirmation: bool
    confirmation_date: Optional[str] = None

class InspectionCreate(BaseModel):
    order_id: int
    procurement_id: Optional[int] = None
    inspection_type: str
    inspection_date: Optional[str] = None
    result: Optional[str] = None
    findings: Optional[str] = None
    report_data: Optional[dict] = None

class AcceptanceCreate(BaseModel):
    order_id: int
    acceptance_type: str
    acceptance_date: Optional[str] = None
    notes: Optional[str] = None

class AcceptanceConfirm(BaseModel):
    customer_confirmed: bool
    confirmation_method: Optional[str] = None
    confirmation_date: Optional[str] = None

class ClosureCreate(BaseModel):
    order_id: int
    lessons_learned: Optional[str] = None
    improvement_suggestions: Optional[str] = None

class ClosureUpdate(BaseModel):
    all_payments_settled: Optional[bool] = None
    all_receivables_collected: Optional[bool] = None
    documents_archived: Optional[bool] = None
    archive_location: Optional[str] = None
    lessons_learned: Optional[str] = None
    improvement_suggestions: Optional[str] = None

class ComplaintCreate(BaseModel):
    customer_id: int
    order_id: Optional[int] = None
    source: str = "EMAIL"
    content: str
    period_no_complaint: bool = False

class ComplaintUpdate(BaseModel):
    investigation: Optional[str] = None
    resolution: Optional[str] = None
    customer_feedback: Optional[str] = None
    status: Optional[str] = None

class SurveyCreate(BaseModel):
    customer_id: int
    year: int

class SurveyRespond(BaseModel):
    service_quality: Optional[int] = None
    response_speed: Optional[int] = None
    price_reasonability: Optional[int] = None
    communication: Optional[int] = None
    overall_satisfaction: Optional[int] = None
    comments: Optional[str] = None

class AdmissionCreate(BaseModel):
    supplier_id: int
    business_license_verified: bool = False
    industry_qualification_verified: bool = False
    case_references: Optional[str] = None
    trial_evaluation: Optional[str] = None
    trial_result: Optional[str] = None
    notes: Optional[str] = None

class AdmissionApprove(BaseModel):
    approved: bool
    notes: Optional[str] = None

class EvaluationCreate(BaseModel):
    supplier_id: int
    year: int
    quality_score: Optional[float] = None
    delivery_score: Optional[float] = None
    price_score: Optional[float] = None
    service_score: Optional[float] = None
    notes: Optional[str] = None

class PageResponse(BaseModel):
    items: list
    total: int
    page: int
    size: int


def _page_resp(items, total, page, size):
    return {"items": [i.to_dict() for i in items], "total": total, "page": page, "size": size}


async def _paginate(db, query, page, size):
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0
    result = await db.execute(query.offset((page - 1) * size).limit(size))
    return result.scalars().all(), total


# ========================== Risk Assessment ==========================

@router.get("/risk-assessments")
async def list_risk_assessments(
    order_id: Optional[int] = None,
    page: int = 1, size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(InquiryRiskAssessment).order_by(InquiryRiskAssessment.created_at.desc())
    if order_id:
        q = q.where(InquiryRiskAssessment.order_id == order_id)
    items, total = await _paginate(db, q, page, size)
    return _page_resp(items, total, page, size)

@router.post("/risk-assessments")
async def create_risk_assessment(
    data: RiskAssessmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    obj = InquiryRiskAssessment(
        **data.model_dump(), assessor_id=current_user.id, status=ApprovalStatus.PENDING,
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj.to_dict()

@router.post("/risk-assessments/{id}/approve")
async def approve_risk_assessment(
    id: int,
    data: RiskAssessmentApprove,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.user import UserRole
    obj = (await db.execute(select(InquiryRiskAssessment).where(InquiryRiskAssessment.id == id))).scalar_one()
    if obj.overall_risk and obj.overall_risk.upper() == "HIGH" and current_user.role != UserRole.OWNER:
        from app.core.exceptions import ForbiddenError
        raise ForbiddenError("高风险项目仅总经理可审批")
    obj.status = ApprovalStatus.APPROVED if data.approved else ApprovalStatus.REJECTED
    obj.approved_by = current_user.id
    obj.approved_at = datetime.now()
    await db.commit()
    await db.refresh(obj)
    return obj.to_dict()


# ========================== Inquiry Records ==========================

@router.get("/inquiry-records")
async def list_inquiry_records(
    order_id: Optional[int] = None,
    supplier_id: Optional[int] = None,
    page: int = 1, size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(InquiryRecord).order_by(InquiryRecord.created_at.desc())
    if order_id:
        q = q.where(InquiryRecord.order_id == order_id)
    if supplier_id:
        q = q.where(InquiryRecord.supplier_id == supplier_id)
    items, total = await _paginate(db, q, page, size)
    return _page_resp(items, total, page, size)

@router.post("/inquiry-records")
async def create_inquiry_record(
    data: InquiryRecordCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    obj = InquiryRecord(**data.model_dump())
    if data.inquiry_time:
        obj.inquiry_time = datetime.fromisoformat(data.inquiry_time)
    if data.deadline:
        obj.deadline = datetime.fromisoformat(data.deadline)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)

    # Auto-send inquiry email to supplier if method is email
    if data.inquiry_method and data.inquiry_method.lower() in ('email', '邮件') and data.supplier_id:
        try:
            from app.services.email_service import email_service
            from app.models.product import Supplier
            supplier = (await db.execute(select(Supplier).where(Supplier.id == data.supplier_id))).scalar_one_or_none()
            if supplier and getattr(supplier, 'contact_email', None):
                await email_service.send_inquiry_email(
                    supplier.contact_email, supplier.name, str(data.order_id),
                    data.notes or "请查看询价详情"
                )
        except Exception:
            pass

    return obj.to_dict()

@router.put("/inquiry-records/{id}")
async def update_inquiry_record(
    id: int,
    data: InquiryRecordUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    obj = (await db.execute(select(InquiryRecord).where(InquiryRecord.id == id))).scalar_one()
    if data.responded is not None:
        obj.responded = data.responded
    if data.response_time:
        obj.response_time = datetime.fromisoformat(data.response_time)
    if data.notes is not None:
        obj.notes = data.notes
    await db.commit()
    await db.refresh(obj)
    return obj.to_dict()


# ========================== Supplier Comparison ==========================

@router.get("/supplier-comparisons")
async def list_comparisons(
    order_id: Optional[int] = None,
    page: int = 1, size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(SupplierComparison).order_by(SupplierComparison.created_at.desc())
    if order_id:
        q = q.where(SupplierComparison.order_id == order_id)
    items, total = await _paginate(db, q, page, size)
    return _page_resp(items, total, page, size)

@router.post("/supplier-comparisons")
async def create_comparison(
    data: ComparisonCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    comparison_data = data.comparison_data or {}
    if data.order_id and not comparison_data:
        from app.models.product import SupplierQuote, Supplier
        from sqlalchemy.orm import selectinload
        from app.models.order import Order, OrderLineItem
        order_line_items = (await db.execute(
            select(OrderLineItem).where(OrderLineItem.order_id == data.order_id)
        )).scalars().all()
        product_ids = [li.product_id for li in order_line_items if li.product_id]
        if product_ids:
            sq_result = await db.execute(
                select(SupplierQuote)
                .options(selectinload(SupplierQuote.supplier))
                .where(SupplierQuote.product_id.in_(product_ids))
            )
            supplier_quotes = sq_result.scalars().all()
            quotes_by_supplier = {}
            for sq in supplier_quotes:
                s_name = sq.supplier.name if sq.supplier else str(sq.supplier_id)
                if s_name not in quotes_by_supplier:
                    quotes_by_supplier[s_name] = {"supplier_id": sq.supplier_id, "items": []}
                quotes_by_supplier[s_name]["items"].append({
                    "product_id": sq.product_id,
                    "unit_price": float(sq.unit_price),
                    "lead_time": sq.lead_time,
                })
            comparison_data = quotes_by_supplier

    obj = SupplierComparison(
        order_id=data.order_id,
        title=data.title,
        selected_supplier_id=data.selected_supplier_id,
        selection_reason=data.selection_reason,
        comparison_data=comparison_data,
        created_by=current_user.id,
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj.to_dict()


# ========================== Contract Review ==========================

@router.get("/contract-reviews")
async def list_contract_reviews(
    contract_id: Optional[int] = None,
    page: int = 1, size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(ContractReview).order_by(ContractReview.created_at.desc())
    if contract_id:
        q = q.where(ContractReview.contract_id == contract_id)
    items, total = await _paginate(db, q, page, size)
    return _page_resp(items, total, page, size)

@router.post("/contract-reviews")
async def create_contract_review(
    data: ContractReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    d = data.model_dump()
    if data.review_date:
        d["review_date"] = date.fromisoformat(data.review_date)
    obj = ContractReview(**d)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj.to_dict()


# ========================== Project Changes ==========================

@router.get("/project-changes")
async def list_project_changes(
    order_id: Optional[int] = None,
    page: int = 1, size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(ProjectChange).order_by(ProjectChange.created_at.desc())
    if order_id:
        q = q.where(ProjectChange.order_id == order_id)
    items, total = await _paginate(db, q, page, size)
    return _page_resp(items, total, page, size)

@router.post("/project-changes")
async def create_project_change(
    data: ProjectChangeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    change_no = await generate_change_no(db)
    obj = ProjectChange(
        order_id=data.order_id,
        change_no=change_no,
        change_type=data.change_type,
        description=data.description,
        impact_analysis=data.impact_analysis,
        created_by=current_user.id,
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj.to_dict()

@router.post("/project-changes/{id}/confirm")
async def confirm_project_change(
    id: int,
    data: ProjectChangeConfirm,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    obj = (await db.execute(select(ProjectChange).where(ProjectChange.id == id))).scalar_one()
    obj.customer_confirmation = data.customer_confirmation
    if data.confirmation_date:
        obj.confirmation_date = date.fromisoformat(data.confirmation_date)
    obj.status = ApprovalStatus.APPROVED if data.customer_confirmation else ApprovalStatus.REJECTED
    await db.commit()
    await db.refresh(obj)
    return obj.to_dict()


# ========================== Quality Inspections ==========================

@router.get("/quality-inspections")
async def list_inspections(
    order_id: Optional[int] = None,
    result: Optional[str] = None,
    page: int = 1, size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(QualityInspection).order_by(QualityInspection.created_at.desc())
    if order_id:
        q = q.where(QualityInspection.order_id == order_id)
    if result:
        q = q.where(QualityInspection.result == result)
    items, total = await _paginate(db, q, page, size)
    return _page_resp(items, total, page, size)

@router.post("/quality-inspections")
async def create_inspection(
    data: InspectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    d = data.model_dump()
    if data.inspection_date:
        d["inspection_date"] = date.fromisoformat(data.inspection_date)
    obj = QualityInspection(**d, inspector_id=current_user.id)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj.to_dict()


# ========================== Project Acceptance ==========================

@router.get("/project-acceptances")
async def list_acceptances(
    order_id: Optional[int] = None,
    page: int = 1, size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(ProjectAcceptance).order_by(ProjectAcceptance.created_at.desc())
    if order_id:
        q = q.where(ProjectAcceptance.order_id == order_id)
    items, total = await _paginate(db, q, page, size)
    return _page_resp(items, total, page, size)

@router.post("/project-acceptances")
async def create_acceptance(
    data: AcceptanceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    acceptance_no = await generate_acceptance_no(db)
    d = data.model_dump()
    if data.acceptance_date:
        d["acceptance_date"] = date.fromisoformat(data.acceptance_date)
    obj = ProjectAcceptance(**d, acceptance_no=acceptance_no)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj.to_dict()

@router.post("/project-acceptances/{id}/confirm")
async def confirm_acceptance(
    id: int,
    data: AcceptanceConfirm,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    obj = (await db.execute(select(ProjectAcceptance).where(ProjectAcceptance.id == id))).scalar_one()
    obj.customer_confirmed = data.customer_confirmed
    obj.confirmation_method = data.confirmation_method
    if data.confirmation_date:
        obj.confirmation_date = date.fromisoformat(data.confirmation_date)
    obj.status = "CONFIRMED" if data.customer_confirmed else "PENDING"
    await db.commit()
    await db.refresh(obj)
    return obj.to_dict()


# ========================== Project Closure ==========================

@router.get("/project-closures")
async def list_closures(
    order_id: Optional[int] = None,
    status: Optional[str] = None,
    page: int = 1, size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(ProjectClosure).order_by(ProjectClosure.created_at.desc())
    if order_id:
        q = q.where(ProjectClosure.order_id == order_id)
    if status:
        q = q.where(ProjectClosure.status == status)
    items, total = await _paginate(db, q, page, size)
    return _page_resp(items, total, page, size)

@router.post("/project-closures")
async def create_closure(
    data: ClosureCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    closure_no = await generate_closure_no(db)
    obj = ProjectClosure(
        order_id=data.order_id,
        closure_no=closure_no,
        lessons_learned=data.lessons_learned,
        improvement_suggestions=data.improvement_suggestions,
        closed_by=current_user.id,
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)

    # Auto-add lessons learned to knowledge base
    if data.lessons_learned:
        doc = KnowledgeDocument(
            title=f"项目经验 - {closure_no}",
            content=data.lessons_learned,
            doc_type="project_experience",
            source_type="project_closure",
            source_id=obj.id,
            created_by=current_user.id,
        )
        db.add(doc)
        await db.commit()

    return obj.to_dict()

@router.put("/project-closures/{id}")
async def update_closure(
    id: int,
    data: ClosureUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    obj = (await db.execute(select(ProjectClosure).where(ProjectClosure.id == id))).scalar_one()
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return obj.to_dict()

@router.post("/project-closures/{id}/submit")
async def submit_closure(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    obj = (await db.execute(select(ProjectClosure).where(ProjectClosure.id == id))).scalar_one()
    obj.status = ClosureStatus.PENDING
    await db.commit()
    await db.refresh(obj)
    return obj.to_dict()

@router.post("/project-closures/{id}/approve")
async def approve_closure(
    id: int,
    approved: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    obj = (await db.execute(select(ProjectClosure).where(ProjectClosure.id == id))).scalar_one()
    if approved:
        obj.status = ClosureStatus.CLOSED
        obj.approved_by = current_user.id
        obj.approved_at = datetime.now()
        obj.closed_at = datetime.now()
    else:
        obj.status = ClosureStatus.DRAFT
    await db.commit()
    await db.refresh(obj)
    return obj.to_dict()


# ========================== Complaints ==========================

@router.get("/complaints")
async def list_complaints(
    customer_id: Optional[int] = None,
    status: Optional[str] = None,
    page: int = 1, size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(Complaint).order_by(Complaint.created_at.desc())
    if customer_id:
        q = q.where(Complaint.customer_id == customer_id)
    if status:
        q = q.where(Complaint.status == status)
    items, total = await _paginate(db, q, page, size)
    return _page_resp(items, total, page, size)

@router.post("/complaints")
async def create_complaint(
    data: ComplaintCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from datetime import timedelta
    complaint_no = await generate_complaint_no(db)
    now = datetime.now()
    obj = Complaint(
        complaint_no=complaint_no,
        customer_id=data.customer_id,
        order_id=data.order_id,
        source=data.source,
        content=data.content,
        received_at=now,
        sla_deadline=now + timedelta(hours=24),
        handler_id=current_user.id,
        period_no_complaint=data.period_no_complaint,
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj.to_dict()

@router.put("/complaints/{id}")
async def update_complaint(
    id: int,
    data: ComplaintUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    obj = (await db.execute(select(Complaint).where(Complaint.id == id))).scalar_one()
    if data.investigation is not None:
        obj.investigation = data.investigation
    if data.resolution is not None:
        obj.resolution = data.resolution
        obj.resolved_at = datetime.now()
    if data.customer_feedback is not None:
        obj.customer_feedback = data.customer_feedback
    if data.status:
        obj.status = data.status
        if data.status == ComplaintStatus.RESOLVED.value and not obj.responded_at:
            obj.responded_at = datetime.now()

    # Auto-add resolution to knowledge base
    if data.resolution and data.status == ComplaintStatus.CLOSED.value:
        doc = KnowledgeDocument(
            title=f"投诉处理经验 - {obj.complaint_no}",
            content=f"投诉内容：{obj.content}\n\n处理方案：{data.resolution}",
            doc_type="complaint_resolution",
            source_type="complaint",
            source_id=obj.id,
            created_by=current_user.id,
        )
        db.add(doc)

    await db.commit()
    await db.refresh(obj)
    return obj.to_dict()


# ========================== Satisfaction Surveys ==========================

@router.get("/satisfaction-surveys")
async def list_surveys(
    customer_id: Optional[int] = None,
    year: Optional[int] = None,
    status: Optional[str] = None,
    page: int = 1, size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(SatisfactionSurvey).order_by(SatisfactionSurvey.created_at.desc())
    if customer_id:
        q = q.where(SatisfactionSurvey.customer_id == customer_id)
    if year:
        q = q.where(SatisfactionSurvey.year == year)
    if status:
        q = q.where(SatisfactionSurvey.status == status)
    items, total = await _paginate(db, q, page, size)
    return _page_resp(items, total, page, size)

@router.post("/satisfaction-surveys")
async def create_survey(
    data: SurveyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    survey_no = await generate_survey_no(db)
    obj = SatisfactionSurvey(
        survey_no=survey_no,
        customer_id=data.customer_id,
        year=data.year,
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj.to_dict()

@router.post("/satisfaction-surveys/{id}/send")
async def send_survey(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    obj = (await db.execute(select(SatisfactionSurvey).where(SatisfactionSurvey.id == id))).scalar_one()
    obj.status = SurveyStatus.SENT
    obj.sent_at = datetime.now()
    await db.commit()
    await db.refresh(obj)
    return obj.to_dict()

@router.post("/satisfaction-surveys/{id}/respond")
async def respond_survey(
    id: int,
    data: SurveyRespond,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    obj = (await db.execute(select(SatisfactionSurvey).where(SatisfactionSurvey.id == id))).scalar_one()
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    obj.status = SurveyStatus.RESPONDED
    obj.responded_at = datetime.now()
    await db.commit()
    await db.refresh(obj)
    return obj.to_dict()


# ========================== Supplier Admission ==========================

@router.get("/supplier-admissions")
async def list_admissions(
    supplier_id: Optional[int] = None,
    status: Optional[str] = None,
    page: int = 1, size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(SupplierAdmission).order_by(SupplierAdmission.created_at.desc())
    if supplier_id:
        q = q.where(SupplierAdmission.supplier_id == supplier_id)
    if status:
        q = q.where(SupplierAdmission.approval_status == status)
    items, total = await _paginate(db, q, page, size)
    return _page_resp(items, total, page, size)

@router.post("/supplier-admissions")
async def create_admission(
    data: AdmissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    obj = SupplierAdmission(**data.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj.to_dict()

@router.post("/supplier-admissions/{id}/approve")
async def approve_admission(
    id: int,
    data: AdmissionApprove,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.product import Supplier
    obj = (await db.execute(select(SupplierAdmission).where(SupplierAdmission.id == id))).scalar_one()
    obj.approval_status = ApprovalStatus.APPROVED if data.approved else ApprovalStatus.REJECTED
    obj.approved_by = current_user.id
    obj.approved_at = datetime.now()
    if data.notes:
        obj.notes = data.notes

    if data.approved:
        supplier = (await db.execute(
            select(Supplier).where(Supplier.id == obj.supplier_id)
        )).scalar_one()
        supplier.qualification_status = "QUALIFIED"
        supplier.admission_date = date.today()

    await db.commit()
    await db.refresh(obj)
    return obj.to_dict()


# ========================== Supplier Evaluation ==========================

@router.get("/supplier-evaluations")
async def list_evaluations(
    supplier_id: Optional[int] = None,
    year: Optional[int] = None,
    page: int = 1, size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(SupplierEvaluation).order_by(SupplierEvaluation.created_at.desc())
    if supplier_id:
        q = q.where(SupplierEvaluation.supplier_id == supplier_id)
    if year:
        q = q.where(SupplierEvaluation.year == year)
    items, total = await _paginate(db, q, page, size)
    return _page_resp(items, total, page, size)

@router.post("/supplier-evaluations")
async def create_evaluation(
    data: EvaluationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.product import Supplier
    q_s = Decimal(str(data.quality_score or 0))
    d_s = Decimal(str(data.delivery_score or 0))
    p_s = Decimal(str(data.price_score or 0))
    sv_s = Decimal(str(data.service_score or 0))
    has_scores = any(s is not None for s in [data.quality_score, data.delivery_score, data.price_score, data.service_score])
    total_score = (q_s * Decimal("0.25") + d_s * Decimal("0.25") + p_s * Decimal("0.25") + sv_s * Decimal("0.25")) if has_scores else None

    level = None
    if total_score is not None:
        if total_score >= 90:
            level = "EXCELLENT"
        elif total_score >= 70:
            level = "QUALIFIED"
        elif total_score >= 60:
            level = "OBSERVED"
        else:
            level = "ELIMINATED"

    obj = SupplierEvaluation(
        supplier_id=data.supplier_id,
        year=data.year,
        quality_score=data.quality_score,
        delivery_score=data.delivery_score,
        price_score=data.price_score,
        service_score=data.service_score,
        total_score=total_score,
        level=level,
        evaluator_id=current_user.id,
        evaluation_date=date.today(),
        notes=data.notes,
    )
    db.add(obj)
    await db.flush()

    # Update supplier record
    supplier = (await db.execute(
        select(Supplier).where(Supplier.id == data.supplier_id)
    )).scalar_one()
    supplier.evaluation_score = total_score
    supplier.evaluation_level = level
    supplier.last_evaluation_date = date.today()
    if level == "ELIMINATED":
        supplier.qualification_status = "ELIMINATED"
    elif level == "OBSERVED":
        supplier.qualification_status = "OBSERVED"

    await db.commit()
    await db.refresh(obj)
    return obj.to_dict()


# ========================== Collection Records (催收记录) ==========================

class CollectionRecordCreate(BaseModel):
    payment_plan_id: Optional[int] = None
    contract_id: Optional[int] = None
    order_id: Optional[int] = None
    collection_date: str
    method: str
    content: Optional[str] = None
    next_followup_date: Optional[str] = None


@router.get("/collection-records")
async def list_collection_records(
    contract_id: Optional[int] = None,
    order_id: Optional[int] = None,
    page: int = 1, size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.contract import CollectionRecord, Contract
    q = select(CollectionRecord).order_by(CollectionRecord.created_at.desc())
    if contract_id:
        q = q.where(CollectionRecord.contract_id == contract_id)
    if order_id:
        q = q.join(Contract, CollectionRecord.contract_id == Contract.id).where(Contract.order_id == order_id)
    items, total = await _paginate(db, q, page, size)
    return {"items": [{"id": i.id, "payment_plan_id": i.payment_plan_id, "contract_id": i.contract_id, "collection_date": str(i.collection_date), "method": i.method, "content": i.content, "next_followup_date": str(i.next_followup_date) if i.next_followup_date else None} for i in items], "total": total, "page": page, "size": size}


@router.post("/collection-records")
async def create_collection_record(
    data: CollectionRecordCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.contract import CollectionRecord, Contract

    contract_id = data.contract_id
    if not contract_id and data.order_id:
        c = (await db.execute(select(Contract).where(Contract.order_id == data.order_id).limit(1))).scalar_one_or_none()
        if c:
            contract_id = c.id

    obj = CollectionRecord(
        payment_plan_id=data.payment_plan_id or 0,
        contract_id=contract_id or 0,
        collection_date=date.fromisoformat(data.collection_date),
        method=data.method,
        content=data.content,
        collector_id=current_user.id,
        next_followup_date=date.fromisoformat(data.next_followup_date) if data.next_followup_date else None,
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return {"id": obj.id, "payment_plan_id": obj.payment_plan_id, "contract_id": obj.contract_id, "collection_date": str(obj.collection_date), "method": obj.method}


# ========================== Change Logs ==========================

class ChangeLogCreate(BaseModel):
    entity_type: str
    entity_id: int
    change_reason: str
    change_content: Optional[dict] = None
    version_before: Optional[str] = None
    version_after: Optional[str] = None


@router.get("/change-logs")
async def list_change_logs(
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    page: int = 1, size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(ChangeLog).order_by(ChangeLog.created_at.desc())
    if entity_type:
        q = q.where(ChangeLog.entity_type == entity_type)
    if entity_id:
        q = q.where(ChangeLog.entity_id == entity_id)
    items, total = await _paginate(db, q, page, size)
    return _page_resp(items, total, page, size)


@router.post("/change-logs")
async def create_change_log(
    data: ChangeLogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    obj = ChangeLog(
        entity_type=data.entity_type,
        entity_id=data.entity_id,
        change_reason=data.change_reason,
        change_content=data.change_content,
        version_before=data.version_before,
        version_after=data.version_after,
        changed_by=current_user.id,
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj.to_dict()


# ========================== Knowledge Base ==========================

@router.get("/knowledge")
async def list_knowledge(
    doc_type: Optional[str] = None,
    keyword: Optional[str] = None,
    page: int = 1, size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(KnowledgeDocument).order_by(KnowledgeDocument.created_at.desc())
    if doc_type:
        q = q.where(KnowledgeDocument.doc_type == doc_type)
    if keyword:
        q = q.where(KnowledgeDocument.title.ilike(f"%{keyword}%"))
    items, total = await _paginate(db, q, page, size)
    return _page_resp(items, total, page, size)

@router.post("/knowledge")
async def create_knowledge(
    title: str,
    content: str,
    doc_type: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    obj = KnowledgeDocument(
        title=title,
        content=content,
        doc_type=doc_type,
        source_type="manual",
        created_by=current_user.id,
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj.to_dict()

@router.get("/knowledge/{id}")
async def get_knowledge(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    obj = (await db.execute(select(KnowledgeDocument).where(KnowledgeDocument.id == id))).scalar_one()
    return obj.to_dict()

@router.delete("/knowledge/{id}")
async def delete_knowledge(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    obj = (await db.execute(select(KnowledgeDocument).where(KnowledgeDocument.id == id))).scalar_one()
    await db.delete(obj)
    await db.commit()
    return {"message": "删除成功"}
