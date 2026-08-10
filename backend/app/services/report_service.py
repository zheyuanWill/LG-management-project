from datetime import date, datetime, timedelta

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.report import DailyReport, WeeklyReport
from app.models.task import Task, TaskDailyUpdate, TaskStatus
from app.services.ai_client import get_ai_client


async def generate_daily_report(
    db: AsyncSession, project_id: int, report_date: date
) -> dict:
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = project_result.scalar_one_or_none()
    if project is None:
        raise ValueError(f"Project not found: {project_id}")

    completed_items = await build_completed_items(db, project_id, report_date)

    updates_result = await db.execute(
        select(TaskDailyUpdate)
        .join(Task, TaskDailyUpdate.task_id == Task.id)
        .where(
            Task.project_id == project_id,
            TaskDailyUpdate.update_date == report_date,
        )
        .order_by(TaskDailyUpdate.id)
    )
    updates = updates_result.scalars().all()

    remarks = []
    for u in updates:
        if u.remark:
            remarks.append(u.remark)

    photos_data = []
    for u in updates:
        for p in u.photos:
            photos_data.append({"update_id": u.id, "storage_key": p.storage_key})

    report_data = {
        "project_id": project_id,
        "report_date": report_date,
        "ship_name": project.ship_name,
        "completed_items": completed_items,
        "remarks": remarks,
        "photos": photos_data,
        "summary": "",
        "tomorrow_plan": "",
        "risk_alert": "",
    }

    ai_client = get_ai_client()
    messages = [
        {
            "role": "system",
            "content": "你是一个专业的船舶工程项目日报生成助手。请根据提供的信息生成简洁、专业的日报摘要。",
        },
        {
            "role": "user",
            "content": f"项目：{project.ship_name}\n日期：{report_date}\n"
            f"已完成事项：{completed_items}\n"
            f"备注：{'; '.join(remarks) if remarks else '无'}\n"
            f"请生成一段不超过200字的日报摘要，包括：今日完成工作、进度状态、存在问题。",
        },
    ]

    try:
        summary = await ai_client.chat(messages, temperature=0.5)
        report_data["summary"] = summary
        logger.info(f"AI-generated daily report summary for project {project_id}")
    except Exception as e:
        logger.warning(f"AI generation failed, using manual summary: {e}")
        completed_names = [item.get("name", "") for item in completed_items]
        report_data["summary"] = f"{report_date} 完成任务：{', '.join(completed_names) if completed_names else '无'}。"

    return report_data


async def generate_weekly_report(
    db: AsyncSession, project_id: int, week_start: date
) -> dict:
    week_end = week_start + timedelta(days=6)

    daily_reports_result = await db.execute(
        select(DailyReport).where(
            DailyReport.project_id == project_id,
            DailyReport.report_date >= week_start,
            DailyReport.report_date <= week_end,
            DailyReport.confirmed == True,
        )
    )
    daily_reports = daily_reports_result.scalars().all()

    if not daily_reports:
        logger.warning(f"No confirmed daily reports for project {project_id} in week {week_start}")
        return {
            "project_id": project_id,
            "week_start_date": week_start,
            "week_end_date": week_end,
            "summary": "",
            "next_week_plan": "",
            "source": "no_data",
        }

    all_completed = []
    all_tomorrow_plans = []
    all_risk_alerts = []
    for dr in daily_reports:
        if dr.completed_items:
            all_completed.extend(dr.completed_items if isinstance(dr.completed_items, list) else [])
        if dr.tomorrow_plan:
            all_tomorrow_plans.append(dr.tomorrow_plan)
        if dr.risk_alert:
            all_risk_alerts.append(dr.risk_alert)

    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = project_result.scalar_one_or_none()

    ai_client = get_ai_client()
    messages = [
        {
            "role": "system",
            "content": "你是一个专业的船舶工程项目周报生成助手。请根据提供的信息生成简洁、专业的周报。",
        },
        {
            "role": "user",
            "content": f"项目：{project.ship_name if project else ''}\n"
            f"周期：{week_start} 至 {week_end}\n"
            f"完成事项汇总：{all_completed}\n"
            f"明日计划汇总：{'; '.join(all_tomorrow_plans) if all_tomorrow_plans else '无'}\n"
            f"风险告警汇总：{'; '.join(all_risk_alerts) if all_risk_alerts else '无'}\n"
            f"请生成周报摘要和下周计划，每部分不超过150字。",
        },
    ]

    summary = ""
    next_week_plan = ""
    try:
        ai_response = await ai_client.chat(messages, temperature=0.5)
        summary = ai_response
        logger.info(f"AI-generated weekly report for project {project_id}")
    except Exception as e:
        logger.warning(f"AI generation failed for weekly report: {e}")
        summary = f"{week_start} 至 {week_end} 共确认 {len(daily_reports)} 份日报。"
        next_week_plan = "; ".join(all_tomorrow_plans[:3]) if all_tomorrow_plans else "待制定"

    return {
        "project_id": project_id,
        "week_start_date": week_start,
        "week_end_date": week_end,
        "summary": summary,
        "next_week_plan": next_week_plan,
        "source": "ai",
    }


async def build_completed_items(
    db: AsyncSession, project_id: int, target_date: date
) -> list[dict]:
    completed_result = await db.execute(
        select(Task).where(
            Task.project_id == project_id,
            Task.status == TaskStatus.COMPLETED.value,
        )
    )
    completed_tasks = completed_result.scalars().all()

    items = []
    for task in completed_tasks:
        update_result = await db.execute(
            select(TaskDailyUpdate).where(
                TaskDailyUpdate.task_id == task.id,
                TaskDailyUpdate.update_date == target_date,
            )
        )
        daily_update = update_result.scalar_one_or_none()
        items.append({
            "task_id": task.id,
            "name": task.name,
            "remark": daily_update.remark if daily_update else None,
            "date": str(target_date),
        })

    logger.info(f"Built completed items for project {project_id} on {target_date}: {len(items)} items")
    return items