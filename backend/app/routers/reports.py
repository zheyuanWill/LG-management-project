from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.celery_app import celery_app
from app.dependencies import get_current_user, get_db
from app.models.project import Project
from app.models.report import DailyReport, WeeklyReport
from app.models.user import User
from app.schemas.report import (
    DailyReportConfirmRequest,
    DailyReportCreate,
    DailyReportResponse,
    WeeklyReportCreate,
    WeeklyReportResponse,
)

router = APIRouter()


@router.get(
    "/projects/{project_id}/daily-reports",
    response_model=list[DailyReportResponse],
)
async def list_daily_reports(
    project_id: int,
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")

    query = select(DailyReport).where(DailyReport.project_id == project_id)
    if start_date:
        query = query.where(DailyReport.report_date >= start_date)
    if end_date:
        query = query.where(DailyReport.report_date <= end_date)

    result = await db.execute(query.order_by(DailyReport.report_date.desc()))
    reports = result.scalars().all()
    return [DailyReportResponse.model_validate(r) for r in reports]


@router.get(
    "/projects/{project_id}/daily-reports/latest",
    response_model=DailyReportResponse | None,
)
async def latest_daily_report(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Most recent daily report for a project (or null). Lets the frontend poll
    async generation without loading the full history."""
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")

    result = await db.execute(
        select(DailyReport)
        .where(DailyReport.project_id == project_id)
        .order_by(DailyReport.report_date.desc())
        .limit(1)
    )
    report = result.scalar_one_or_none()
    return DailyReportResponse.model_validate(report) if report else None


@router.get(
    "/daily-reports/{report_id}",
    response_model=DailyReportResponse,
)
async def get_daily_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(DailyReport).where(DailyReport.id == report_id)
    )
    report = result.scalar_one_or_none()
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="日报不存在")
    return DailyReportResponse.model_validate(report)


@router.post(
    "/projects/{project_id}/daily-reports/generate",
)
async def generate_daily_report(
    project_id: int,
    report_date: date | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")

    target_date = report_date or date.today()

    task = celery_app.send_task(
        "app.tasks.report_tasks.generate_daily_report_task",
        args=[project_id, str(target_date)],
    )

    return {
        "task_id": task.id,
        "project_id": project_id,
        "report_date": str(target_date),
        "status": "pending",
    }


@router.patch(
    "/daily-reports/{report_id}",
    response_model=DailyReportResponse,
)
async def update_daily_report(
    report_id: int,
    payload: DailyReportCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(DailyReport).where(DailyReport.id == report_id)
    )
    report = result.scalar_one_or_none()
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="日报不存在")

    if payload.tomorrow_plan is not None:
        report.tomorrow_plan = payload.tomorrow_plan
    if payload.risk_alert is not None:
        report.risk_alert = payload.risk_alert
    if payload.completed_items is not None:
        report.completed_items = payload.completed_items

    await db.flush()
    return DailyReportResponse.model_validate(report)


@router.post(
    "/daily-reports/{report_id}/confirm",
    response_model=DailyReportResponse,
)
async def confirm_daily_report(
    report_id: int,
    payload: DailyReportConfirmRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(DailyReport).where(DailyReport.id == report_id)
    )
    report = result.scalar_one_or_none()
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="日报不存在")

    report.confirmed = payload.confirmed
    await db.flush()
    return DailyReportResponse.model_validate(report)


@router.get(
    "/projects/{project_id}/weekly-reports",
    response_model=list[WeeklyReportResponse],
)
async def list_weekly_reports(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")

    result = await db.execute(
        select(WeeklyReport)
        .where(WeeklyReport.project_id == project_id)
        .order_by(WeeklyReport.week_start_date.desc())
    )
    reports = result.scalars().all()
    return [WeeklyReportResponse.model_validate(r) for r in reports]


@router.get(
    "/projects/{project_id}/weekly-reports/latest",
    response_model=WeeklyReportResponse | None,
)
async def latest_weekly_report(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Most recent weekly report for a project (or null)."""
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")

    result = await db.execute(
        select(WeeklyReport)
        .where(WeeklyReport.project_id == project_id)
        .order_by(WeeklyReport.week_start_date.desc())
        .limit(1)
    )
    report = result.scalar_one_or_none()
    return WeeklyReportResponse.model_validate(report) if report else None


@router.post(
    "/projects/{project_id}/weekly-reports/generate",
)
async def generate_weekly_report(
    project_id: int,
    week_start_date: date | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")

    if week_start_date is None:
        today = date.today()
        from datetime import timedelta
        monday = today - timedelta(days=today.weekday())
        week_start_date = monday

    task = celery_app.send_task(
        "app.tasks.report_tasks.generate_weekly_report_task",
        args=[project_id, str(week_start_date)],
    )

    return {
        "task_id": task.id,
        "project_id": project_id,
        "week_start_date": str(week_start_date),
        "status": "pending",
    }


@router.patch(
    "/weekly-reports/{report_id}",
    response_model=WeeklyReportResponse,
)
async def update_weekly_report(
    report_id: int,
    payload: WeeklyReportCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(WeeklyReport).where(WeeklyReport.id == report_id)
    )
    report = result.scalar_one_or_none()
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="周报不存在")

    if payload.summary is not None:
        report.summary = payload.summary
    if payload.next_week_plan is not None:
        report.next_week_plan = payload.next_week_plan

    await db.flush()
    return WeeklyReportResponse.model_validate(report)


@router.post(
    "/weekly-reports/{report_id}/confirm",
    response_model=WeeklyReportResponse,
)
async def confirm_weekly_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(WeeklyReport).where(WeeklyReport.id == report_id)
    )
    report = result.scalar_one_or_none()
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="周报不存在")

    report.confirmed = True
    report.confirmed_by = current_user.id
    await db.flush()
    return WeeklyReportResponse.model_validate(report)