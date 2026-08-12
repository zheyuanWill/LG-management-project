from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.celery_app import celery_app
from app.dependencies import get_current_user, get_db
from app.models.project import Project
from app.models.report import RiskEvent
from app.models.user import User
from app.schemas.report import RiskEventCreate, RiskEventResponse

router = APIRouter()


class RiskResolveRequest(BaseModel):
    resolved: bool | None = None
    detail: str | None = None
    risk_level: str | None = None


@router.get(
    "/summary",
    response_model=list[RiskEventResponse],
)
async def risk_summary(
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = (
        select(RiskEvent)
        .where(RiskEvent.resolved.is_(False))
        .order_by(RiskEvent.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    risks = result.scalars().all()
    return [RiskEventResponse.model_validate(r) for r in risks]


@router.get(
    "/projects/{project_id}/risks",
    response_model=list[RiskEventResponse],
)
async def list_risk_events(
    project_id: int,
    resolved: bool | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")

    query = select(RiskEvent).where(RiskEvent.project_id == project_id)
    if resolved is not None:
        query = query.where(RiskEvent.resolved == resolved)

    result = await db.execute(query.order_by(RiskEvent.created_at.desc()))
    risks = result.scalars().all()
    return [RiskEventResponse.model_validate(r) for r in risks]


@router.post(
    "/projects/{project_id}/risks/ai-detect",
)
async def ai_detect_risks(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")

    task = celery_app.send_task(
        "app.tasks.risk_tasks.detect_risks_task",
        args=[project_id],
    )

    return {
        "task_id": task.id,
        "project_id": project_id,
        "status": "pending",
    }


@router.patch(
    "/risks/{risk_id}",
    response_model=RiskEventResponse,
)
async def resolve_risk(
    risk_id: int,
    payload: RiskResolveRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(RiskEvent).where(RiskEvent.id == risk_id)
    )
    risk = result.scalar_one_or_none()
    if risk is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="风险事件不存在")

    if payload.resolved is not None:
        risk.resolved = payload.resolved
    if payload.detail is not None:
        risk.detail = payload.detail
    if payload.risk_level is not None:
        risk.risk_level = payload.risk_level
    risk.updated_at = datetime.utcnow() if hasattr(risk, "updated_at") else datetime.utcnow()

    await db.flush()
    return RiskEventResponse.model_validate(risk)