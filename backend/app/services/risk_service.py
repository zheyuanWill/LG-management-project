from datetime import datetime

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.report import RiskEvent
from app.models.task import Task, TaskStatus
from app.services.ai_client import get_ai_client


RISK_LEVELS = ["info", "warning", "critical"]


async def detect_risks(db: AsyncSession, project_id: int) -> list[dict]:
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = project_result.scalar_one_or_none()
    if project is None:
        raise ValueError(f"Project not found: {project_id}")

    tasks_result = await db.execute(
        select(Task).where(Task.project_id == project_id)
    )
    tasks = tasks_result.scalars().all()

    risks = []

    not_started = [t for t in tasks if t.status == TaskStatus.NOT_STARTED.value]
    if not_started and len(not_started) > len(tasks) * 0.5:
        risks.append({
            "title": "大量任务未启动",
            "detail": f"{len(not_started)}/{len(tasks)} 个任务尚未开始，可能影响项目进度",
            "risk_level": "warning",
        })

    in_progress = [t for t in tasks if t.status == TaskStatus.IN_PROGRESS.value]
    overdue_tasks = []
    today = datetime.now().date()
    for t in in_progress:
        if t.planned_end_date and t.planned_end_date < today:
            overdue_tasks.append(t)

    if overdue_tasks:
        risks.append({
            "title": f"{len(overdue_tasks)} 个任务已逾期",
            "detail": "、".join([t.name for t in overdue_tasks[:5]]),
            "risk_level": "critical",
        })

    completed = [t for t in tasks if t.status == TaskStatus.COMPLETED.value]
    if tasks:
        completion_rate = len(completed) / len(tasks)
        if completion_rate < 0.3 and project.status == "active":
            risks.append({
                "title": "项目完成率偏低",
                "detail": f"当前完成率 {completion_rate:.1%}，建议关注进度推进",
                "risk_level": "info",
            })

    existing_risks_result = await db.execute(
        select(RiskEvent).where(
            RiskEvent.project_id == project_id,
            RiskEvent.resolved == False,
        )
    )
    existing_risks = existing_risks_result.scalars().all()
    existing_titles = {r.title for r in existing_risks}

    new_risks = []
    for risk in risks:
        if risk["title"] not in existing_titles:
            new_risks.append(risk)

    if new_risks:
        logger.info(f"Detected {len(new_risks)} new risks for project {project_id}")
    else:
        logger.info(f"No new risks detected for project {project_id}")

    return new_risks


def build_risk_summary(risks: list[dict]) -> str:
    if not risks:
        return "当前无风险"

    critical = [r for r in risks if r.get("risk_level") == "critical"]
    warning = [r for r in risks if r.get("risk_level") == "warning"]
    info = [r for r in risks if r.get("risk_level") == "info"]

    parts = []
    if critical:
        parts.append(f"{len(critical)} 项紧急")
    if warning:
        parts.append(f"{len(warning)} 项警告")
    if info:
        parts.append(f"{len(info)} 项提示")

    summary = "、".join(parts) + "："
    summary += "；".join([r.get("title", "") for r in risks[:3]])
    return summary