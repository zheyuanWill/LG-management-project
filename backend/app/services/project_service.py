from datetime import datetime

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.task import Task


TYPE_CODE_MAP = {
    "supervision": "SV",
    "brokerage_sale": "BS",
    "brokerage_repair": "BR",
    "spare_parts": "SP",
}


async def generate_project_number(db: AsyncSession, project_type: str) -> str:
    year = datetime.now().year
    type_code = TYPE_CODE_MAP.get(project_type, "UN")

    result = await db.execute(
        select(func.count(Project.id)).where(
            Project.type == project_type,
            func.extract("year", Project.created_at) == year,
        )
    )
    seq = result.scalar() or 0
    seq += 1

    project_no = f"LG-{type_code}-{year}-{seq:03d}"
    logger.info(f"Generated project number: {project_no}")
    return project_no


async def get_project_stats(db: AsyncSession, project_id: int) -> dict:
    task_count_result = await db.execute(
        select(func.count(Task.id)).where(Task.project_id == project_id)
    )
    total_tasks = task_count_result.scalar() or 0

    completed_result = await db.execute(
        select(func.count(Task.id)).where(
            Task.project_id == project_id,
            Task.status == "completed",
        )
    )
    completed_tasks = completed_result.scalar() or 0

    completion_rate = round((completed_tasks / total_tasks) * 100, 1) if total_tasks > 0 else 0.0

    from app.models.report import RiskEvent

    risk_result = await db.execute(
        select(func.count(RiskEvent.id)).where(
            RiskEvent.project_id == project_id,
            RiskEvent.resolved == False,
        )
    )
    active_risks = risk_result.scalar() or 0

    return {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "completion_rate": completion_rate,
        "active_risks": active_risks,
    }