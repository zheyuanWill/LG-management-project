from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.project import Project
from app.models.report import RiskEvent
from app.models.user import User
from app.schemas.report import RiskEventCreate, RiskEventResponse
from app.services.risk_service import detect_risks_with_ai

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
    "/projects/{project_id}/risks/scan",
    response_model=list[RiskEventResponse],
)
async def scan_risks(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """同步扫描：规则扫描 + RAG 检索 + LLM 综合判断，落库后返回风险列表。

    命名诚实：从旧的 /ai-detect（实际只跑规则）改为 /scan。
    Celery 异步任务壳已砍掉，API 调用即返回。
    """
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")

    try:
        risks_data = await detect_risks_with_ai(db, project_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    # 落库：按 title 去重，已存在的同 title 跳过
    existing_result = await db.execute(
        select(RiskEvent).where(
            RiskEvent.project_id == project_id,
            RiskEvent.resolved.is_(False),
        )
    )
    existing_titles = {
        r.title for r in existing_result.scalars().all()
    }

    new_risks: list[RiskEvent] = []
    for risk in risks_data:
        if risk["title"] in existing_titles:
            continue
        event = RiskEvent(
            project_id=project_id,
            title=risk["title"],
            detail=risk.get("detail"),
            risk_level=risk.get("risk_level", "info"),
            resolved=False,
        )
        db.add(event)
        new_risks.append(event)

    await db.flush()
    return [RiskEventResponse.model_validate(r) for r in new_risks]


# 兼容旧路径别名：保留 /ai-detect 但实现为 /scan 的转发
@router.post(
    "/projects/{project_id}/risks/ai-detect",
    response_model=list[RiskEventResponse],
    deprecated=True,
)
async def ai_detect_risks_legacy(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """已废弃：保留只为兼容旧前端调用。新代码请用 /scan。"""
    return await scan_risks(project_id=project_id, db=db, _=user)


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


@router.delete(
    "/risks/{risk_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_risk(
    risk_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(RiskEvent).where(RiskEvent.id == risk_id)
    )
    risk = result.scalar_one_or_none()
    if risk is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="风险事件不存在")
    await db.delete(risk)