"""Ship Repair Module V2 Router"""
import os, uuid
from typing import Optional, Any
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, Query, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.deps import get_db, get_current_user
from app.core.exceptions import NotFoundError
from app.schemas.common import PageResponse
from app.models.user import User
from app.models.order import Order
from app.models.customer import Customer
from app.models.ship_repair import (
    Project, Task, DailyLog, DailyLogAttachment, Issue,
    ProjectStatus, TaskStatus, IssueStatus,
)
from app.schemas.ship_repair import (
    ProjectCreate, ProjectUpdate, ProjectResponse, ProjectDetailResponse,
    TaskCreate, TaskUpdate, TaskResponse,
    DailyLogCreate, DailyLogUpdate, DailyLogResponse, DailyLogAttachmentResponse,
    IssueCreate, IssueUpdate, IssueResponse,
    AITaskGenerationResponse, AIProcessLogResponse, AIReportResponse,
)
from app.services.ai_tools import ShipRepairAITools

router = APIRouter(prefix="/ship-repair", tags=["ship-repair"])
UPLOAD_DIR = "/app/uploads/ship-repair"


class DashboardStats(BaseModel):
    projects_total: int = 0
    projects_active: int = 0
    tasks_total: int = 0
    tasks_completed: int = 0
    tasks_in_progress: int = 0
    tasks_pending: int = 0
    issues_open: int = 0
    issues_high_risk: int = 0


@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stats = DashboardStats()
    
    projects = (await db.execute(select(Project))).scalars().all()
    stats.projects_total = len(projects)
    stats.projects_active = len([p for p in projects if p.status == ProjectStatus.IN_PROGRESS])
    
    tasks = (await db.execute(select(Task))).scalars().all()
    stats.tasks_total = len(tasks)
    stats.tasks_completed = len([t for t in tasks if t.status == TaskStatus.COMPLETED])
    stats.tasks_in_progress = len([t for t in tasks if t.status == TaskStatus.IN_PROGRESS])
    stats.tasks_pending = len([t for t in tasks if t.status == TaskStatus.PENDING])
    
    issues = (await db.execute(select(Issue))).scalars().all()
    stats.issues_open = len([i for i in issues if i.status in [IssueStatus.OPEN, IssueStatus.IN_PROGRESS]])
    stats.issues_high_risk = len([i for i in issues if i.status in [IssueStatus.OPEN, IssueStatus.IN_PROGRESS] and i.severity in ["HIGH", "CRITICAL"]])
    
    return stats


@router.get("/projects", response_model=PageResponse[ProjectResponse])
async def list_projects(
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Project).order_by(Project.created_at.desc())
    if status:
        query = query.where(Project.status == status)
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0
    items = (await db.execute(query.offset((page - 1) * size).limit(size))).scalars().all()
    order_ids = {p.order_id for p in items if getattr(p, "order_id", None)}
    order_map: dict[int, tuple[str, str]] = {}
    if order_ids:
        rows = (await db.execute(
            select(Order.id, Order.order_no, Customer.name)
            .join(Customer, Customer.id == Order.customer_id)
            .where(Order.id.in_(order_ids))
        )).all()
        order_map = {r.id: (r.order_no, r.name) for r in rows}

    enriched: list[ProjectResponse] = []
    for p in items:
        resp = ProjectResponse.model_validate(p)
        if p.order_id and p.order_id in order_map:
            resp.order_no = order_map[p.order_id][0]
            resp.customer_name = order_map[p.order_id][1]
        enriched.append(resp)

    return PageResponse.create(items=enriched, total=total, page=page, size=size)


@router.post("/projects", response_model=ProjectResponse)
async def create_project(
    data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if getattr(data, "order_id", None):
        order = (await db.execute(select(Order).where(Order.id == data.order_id))).scalar_one_or_none()
        if not order:
            raise NotFoundError("订单", data.order_id)
    project = Project(**data.model_dump(), created_by=current_user.id)
    db.add(project)
    await db.commit()
    await db.refresh(project)
    resp = ProjectResponse.model_validate(project)
    if project.order_id:
        row = (await db.execute(
            select(Order.order_no, Customer.name)
            .join(Customer, Customer.id == Order.customer_id)
            .where(Order.id == project.order_id)
        )).one_or_none()
        if row:
            resp.order_no = row[0]
            resp.customer_name = row[1]
    return resp


@router.get("/projects/{pid}", response_model=ProjectDetailResponse)
async def get_project(
    pid: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = (await db.execute(select(Project).where(Project.id == pid))).scalar_one_or_none()
    if not project:
        raise NotFoundError("Project", pid)
    t = (await db.execute(
        select(func.count(Task.id), func.count(Task.id).filter(Task.status == TaskStatus.COMPLETED), func.count(Task.id).filter(Task.status == TaskStatus.IN_PROGRESS)).where(Task.project_id == pid)
    )).one()
    i = (await db.execute(
        select(func.count(Issue.id).filter(Issue.status.in_(["OPEN", "IN_PROGRESS"])), func.count(Issue.id).filter(Issue.status.in_(["OPEN", "IN_PROGRESS"]), Issue.severity.in_(["HIGH", "CRITICAL"]))).where(Issue.project_id == pid)
    )).one()
    resp = ProjectDetailResponse.model_validate(project)
    resp.task_count, resp.task_completed, resp.task_in_progress = t[0], t[1], t[2]
    resp.open_issues, resp.high_severity_issues = i[0], i[1]
    if project.order_id:
        row = (await db.execute(
            select(Order.order_no, Customer.name)
            .join(Customer, Customer.id == Order.customer_id)
            .where(Order.id == project.order_id)
        )).one_or_none()
        if row:
            resp.order_no = row[0]
            resp.customer_name = row[1]
    return resp


@router.put("/projects/{pid}", response_model=ProjectResponse)
async def update_project(pid: int, data: ProjectUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = (await db.execute(select(Project).where(Project.id == pid))).scalar_one_or_none()
    if not project:
        raise NotFoundError("Project", pid)
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(project, k, v)
    await db.commit()
    await db.refresh(project)
    return project


@router.post("/projects/{pid}/ai-generate-tasks", response_model=AITaskGenerationResponse)
async def ai_generate_tasks(pid: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = (await db.execute(select(Project).where(Project.id == pid))).scalar_one_or_none()
    if not project:
        raise NotFoundError("Project", pid)
    ai_result = await ShipRepairAITools.generate_tasks_from_spec(project.project_name, project.vessel_name, project.repair_specification or "")
    created = []
    for idx, td in enumerate(ai_result.get("tasks", [])):
        task = Task(project_id=pid, task_name=td.get("task_name", f"Task {idx+1}"), description=td.get("description"), category=td.get("category", "OTHER"), ai_generated=True, sort_order=idx)
        db.add(task)
        created.append(task)
    if project.status == ProjectStatus.NOT_STARTED:
        project.status = ProjectStatus.IN_PROGRESS
    await db.commit()
    for t in created:
        await db.refresh(t)
    return AITaskGenerationResponse(tasks_created=len(created), tasks=[TaskResponse.model_validate(t) for t in created])


@router.get("/projects/{pid}/tasks", response_model=list[TaskResponse])
async def list_tasks(pid: int, status: Optional[str] = None, category: Optional[str] = None, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = select(Task).where(Task.project_id == pid).order_by(Task.sort_order, Task.id)
    if status:
        query = query.where(Task.status == status)
    if category:
        query = query.where(Task.category == category)
    return (await db.execute(query)).scalars().all()


@router.post("/projects/{pid}/tasks", response_model=TaskResponse)
async def create_task(pid: int, data: TaskCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not (await db.execute(select(Project).where(Project.id == pid))).scalar_one_or_none():
        raise NotFoundError("Project", pid)
    task = Task(project_id=pid, **data.model_dump(), ai_generated=False)
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@router.put("/tasks/{tid}", response_model=TaskResponse)
async def update_task(tid: int, data: TaskUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = (await db.execute(select(Task).where(Task.id == tid))).scalar_one_or_none()
    if not task:
        raise NotFoundError("Task", tid)
    updates = data.model_dump(exclude_unset=True)
    if updates.get("status") == "IN_PROGRESS" and not task.actual_start:
        task.actual_start = date.today()
    elif updates.get("status") == "COMPLETED" and not task.actual_end:
        task.actual_end = date.today()
    for k, v in updates.items():
        setattr(task, k, v)
    await db.commit()
    await db.refresh(task)
    return task


@router.delete("/tasks/{tid}")
async def delete_task(tid: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = (await db.execute(select(Task).where(Task.id == tid))).scalar_one_or_none()
    if not task:
        raise NotFoundError("Task", tid)
    await db.delete(task)
    await db.commit()
    return {"ok": True}


@router.get("/projects/{pid}/daily-logs", response_model=PageResponse[DailyLogResponse])
async def list_daily_logs(pid: int, page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100), db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = select(DailyLog).options(selectinload(DailyLog.attachments)).where(DailyLog.project_id == pid).order_by(DailyLog.log_date.desc())
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0
    items = (await db.execute(query.offset((page - 1) * size).limit(size))).scalars().all()
    return PageResponse.create(items=[DailyLogResponse.model_validate(x) for x in items], total=total, page=page, size=size)


@router.post("/projects/{pid}/generate-daily-report", response_model=AIReportResponse)
async def generate_daily_report(
    pid: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = (await db.execute(select(Project).where(Project.id == pid))).scalar_one_or_none()
    if not project:
        raise NotFoundError("Project", pid)
    
    today = date.today().isoformat()
    daily_logs = (
        await db.execute(
            select(DailyLog).options(selectinload(DailyLog.attachments))
            .where(DailyLog.project_id == pid, DailyLog.log_date == date.today())
        )
    ).scalars().all()
    
    tasks = (await db.execute(select(Task).where(Task.project_id == pid))).scalars().all()
    open_issues = (
        await db.execute(
            select(Issue).where(
                Issue.project_id == pid,
                Issue.status.in_([IssueStatus.OPEN, IssueStatus.IN_PROGRESS])
            )
        )
    ).scalars().all()
    
    result = await ShipRepairAITools.generate_daily_report(
        project.project_name,
        project.vessel_name,
        today,
        [
            {
                "id": log.id,
                "log_date": log.log_date.isoformat(),
                "work_done": log.work_done,
                "discoveries": log.discoveries,
                "tomorrow_plan": log.tomorrow_plan
            }
            for log in daily_logs
        ],
        [
            {
                "id": task.id,
                "task_name": task.task_name,
                "status": task.status,
                "category": task.category
            }
            for task in tasks
        ],
        [
            {
                "id": issue.id,
                "title": issue.title,
                "severity": issue.severity,
                "status": issue.status
            }
            for issue in open_issues
        ]
    )
    
    return AIReportResponse(
        report_date=today,
        content=result.get("content", ""),
        sections=result.get("sections")
    )


@router.post("/projects/{pid}/generate-weekly-report", response_model=AIReportResponse)
async def generate_weekly_report(
    pid: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = (await db.execute(select(Project).where(Project.id == pid))).scalar_one_or_none()
    if not project:
        raise NotFoundError("Project", pid)
    
    today = date.today()
    start_date = today - timedelta(days=today.weekday())
    end_date = start_date + timedelta(days=6)
    
    daily_logs = (
        await db.execute(
            select(DailyLog).options(selectinload(DailyLog.attachments))
            .where(
                DailyLog.project_id == pid,
                DailyLog.log_date >= start_date,
                DailyLog.log_date <= end_date
            )
        )
    ).scalars().all()
    
    tasks = (await db.execute(select(Task).where(Task.project_id == pid))).scalars().all()
    issues = (await db.execute(select(Issue).where(Issue.project_id == pid))).scalars().all()
    
    result = await ShipRepairAITools.generate_weekly_report(
        project.project_name,
        project.vessel_name,
        start_date.isoformat(),
        end_date.isoformat(),
        [
            {
                "id": log.id,
                "log_date": log.log_date.isoformat(),
                "work_done": log.work_done,
                "discoveries": log.discoveries
            }
            for log in daily_logs
        ],
        [
            {
                "id": task.id,
                "task_name": task.task_name,
                "status": task.status
            }
            for task in tasks
        ],
        [
            {
                "id": issue.id,
                "title": issue.title,
                "severity": issue.severity,
                "status": issue.status
            }
            for issue in issues
        ]
    )
    
    return AIReportResponse(
        report_date=today.isoformat(),
        content=result.get("content", ""),
        sections=result.get("sections")
    )


@router.post("/projects/{pid}/generate-summary", response_model=AIReportResponse)
async def generate_project_summary(
    pid: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = (await db.execute(select(Project).where(Project.id == pid))).scalar_one_or_none()
    if not project:
        raise NotFoundError("Project", pid)
    
    tasks = (await db.execute(select(Task).where(Task.project_id == pid))).scalars().all()
    issues = (await db.execute(select(Issue).where(Issue.project_id == pid))).scalars().all()
    total_logs = (await db.execute(select(func.count(DailyLog.id)).where(DailyLog.project_id == pid))).scalar() or 0
    
    result = await ShipRepairAITools.generate_project_summary(
        project.project_name,
        project.vessel_name,
        project.shipyard,
        project.dock_in_date.isoformat() if project.dock_in_date else None,
        project.dock_out_date.isoformat() if project.dock_out_date else None,
        [
            {
                "id": task.id,
                "task_name": task.task_name,
                "status": task.status
            }
            for task in tasks
        ],
        [
            {
                "id": issue.id,
                "title": issue.title,
                "status": issue.status
            }
            for issue in issues
        ],
        total_logs
    )
    
    return AIReportResponse(
        report_date=date.today().isoformat(),
        content=result.get("content", ""),
        sections=result.get("sections")
    )


@router.post("/projects/{pid}/daily-logs", response_model=DailyLogResponse)
async def create_daily_log(pid: int, data: DailyLogCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not (await db.execute(select(Project).where(Project.id == pid))).scalar_one_or_none():
        raise NotFoundError("Project", pid)
    log = DailyLog(project_id=pid, reporter_id=current_user.id, **data.model_dump())
    db.add(log)
    await db.commit()
    await db.refresh(log, attribute_names=["attachments"])
    return log


@router.get("/daily-logs/{lid}", response_model=DailyLogResponse)
async def get_daily_log(lid: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    log = (await db.execute(select(DailyLog).options(selectinload(DailyLog.attachments)).where(DailyLog.id == lid))).scalar_one_or_none()
    if not log:
        raise NotFoundError("DailyLog", lid)
    return log


@router.put("/daily-logs/{lid}", response_model=DailyLogResponse)
async def update_daily_log(lid: int, data: DailyLogUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    log = (await db.execute(select(DailyLog).options(selectinload(DailyLog.attachments)).where(DailyLog.id == lid))).scalar_one_or_none()
    if not log:
        raise NotFoundError("DailyLog", lid)
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(log, k, v)
    await db.commit()
    await db.refresh(log, attribute_names=["attachments"])
    return log


@router.post("/daily-logs/{lid}/attachments", response_model=DailyLogAttachmentResponse)
async def upload_attachment(lid: int, file: UploadFile = File(...), description: Optional[str] = Form(None), db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not (await db.execute(select(DailyLog).where(DailyLog.id == lid))).scalar_one_or_none():
        raise NotFoundError("DailyLog", lid)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename or "file")[1]
    saved = f"{uuid.uuid4().hex}{ext}"
    content = await file.read()
    with open(os.path.join(UPLOAD_DIR, saved), "wb") as f:
        f.write(content)
    att = DailyLogAttachment(daily_log_id=lid, file_path=f"/uploads/ship-repair/{saved}", file_name=file.filename or saved, file_size=len(content), mime_type=file.content_type, description=description)
    db.add(att)
    await db.commit()
    await db.refresh(att)
    return att


@router.post("/daily-logs/{lid}/ai-process", response_model=AIProcessLogResponse)
async def ai_process_daily_log(
    lid: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    log = (
        await db.execute(
            select(DailyLog).options(selectinload(DailyLog.attachments)).where(DailyLog.id == lid)
        )
    ).scalar_one_or_none()
    if not log:
        raise NotFoundError("DailyLog", lid)
    tasks = (
        await db.execute(select(Task).where(Task.project_id == log.project_id).order_by(Task.sort_order))
    ).scalars().all()
    ai = await ShipRepairAITools.process_daily_log(
        log.work_done or "",
        log.discoveries or "",
        log.tomorrow_plan or "",
        [{"id": t.id, "task_name": t.task_name, "status": t.status} for t in tasks],
    )
    updated = []
    for u in ai.get("task_updates", []):
        task = next((t for t in tasks if t.id == u.get("task_id")), None)
        if task and task.status != u.get("new_status"):
            task.status = u["new_status"]
            if u["new_status"] == "IN_PROGRESS" and not task.actual_start:
                task.actual_start = log.log_date
            elif u["new_status"] == "COMPLETED" and not task.actual_end:
                task.actual_end = log.log_date
            updated.append({"task_id": task.id, "task_name": task.task_name, "new_status": u["new_status"]})
    created = []
    for idata in ai.get("issues", []):
        issue = Issue(
            project_id=log.project_id,
            daily_log_id=log.id,
            task_id=idata.get("task_id"),
            issue_type=idata.get("issue_type", "OTHER"),
            title=idata.get("title", "AI识别问题"),
            description=idata.get("description"),
            severity=idata.get("severity", "MEDIUM"),
            ai_generated=True,
        )
        db.add(issue)
        created.append({"title": issue.title, "issue_type": issue.issue_type, "severity": issue.severity})
    log.ai_processed = True
    log.ai_processed_at = datetime.utcnow()
    log.ai_summary = ai.get("summary", "")
    await db.commit()
    return AIProcessLogResponse(tasks_updated=updated, issues_created=created, summary=ai.get("summary", "AI处理完成"))


@router.get("/projects/{pid}/issues", response_model=list[IssueResponse])
async def list_issues(
    pid: int,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Issue).where(Issue.project_id == pid).order_by(Issue.created_at.desc())
    if status:
        query = query.where(Issue.status == status)
    if severity:
        query = query.where(Issue.severity == severity)
    return (await db.execute(query)).scalars().all()


@router.post("/projects/{pid}/issues", response_model=IssueResponse)
async def create_issue(
    pid: int,
    data: IssueCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not (await db.execute(select(Project).where(Project.id == pid))).scalar_one_or_none():
        raise NotFoundError("Project", pid)
    issue = Issue(project_id=pid, **data.model_dump(), ai_generated=False)
    db.add(issue)
    await db.commit()
    await db.refresh(issue)
    return issue


@router.put("/issues/{iid}", response_model=IssueResponse)
async def update_issue(
    iid: int,
    data: IssueUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    issue = (await db.execute(select(Issue).where(Issue.id == iid))).scalar_one_or_none()
    if not issue:
        raise NotFoundError("Issue", iid)
    updates = data.model_dump(exclude_unset=True)
    if updates.get("status") in ("RESOLVED", "CLOSED") and not issue.resolved_at:
        issue.resolved_at = datetime.utcnow()
        issue.resolved_by = current_user.id
    for k, v in updates.items():
        setattr(issue, k, v)
    await db.commit()
    await db.refresh(issue)
    return issue


@router.post("/issues/{iid}/resolve", response_model=IssueResponse)
async def resolve_issue(
    iid: int,
    data: IssueUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    issue = (await db.execute(select(Issue).where(Issue.id == iid))).scalar_one_or_none()
    if not issue:
        raise NotFoundError("Issue", iid)
    issue.status = IssueStatus.RESOLVED
    issue.resolved_at = datetime.utcnow()
    issue.resolved_by = current_user.id
    if data.resolution_notes:
        issue.resolution_notes = data.resolution_notes
    await db.commit()
    await db.refresh(issue)
    return issue
