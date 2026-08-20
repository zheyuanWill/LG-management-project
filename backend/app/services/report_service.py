import asyncio
import json
import re
from datetime import date, datetime, timedelta

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.project import Project
from app.models.report import DailyReport, WeeklyReport
from app.models.task import Task, TaskDailyUpdate
from app.services.ai_client import get_ai_client
from app.services.rag_service import retrieve


# ── 今日工作 / 项目摘要 ────────────────────────────────────────────────

async def _build_today_work(
    db: AsyncSession, project_id: int, report_date: date
) -> tuple[list[dict], str]:
    """从当天的 TaskDailyUpdate 取「任务名称 + 备注」，生成结构化数据 + Markdown 富文本。"""
    updates_result = await db.execute(
        select(TaskDailyUpdate)
        .join(Task, TaskDailyUpdate.task_id == Task.id)
        .where(
            Task.project_id == project_id,
            TaskDailyUpdate.update_date == report_date,
        )
        .options(
            selectinload(TaskDailyUpdate.photos),
            selectinload(TaskDailyUpdate.task),
        )
        .order_by(TaskDailyUpdate.id)
    )
    updates = updates_result.scalars().all()

    completed_items: list[dict] = []
    for u in updates:
        photos = [p.storage_key for p in u.photos]
        completed_items.append({
            "task_id": u.task_id,
            "name": u.task.name if u.task else "未知任务",
            "status": u.status,
            "remark": u.remark,
            "photos": photos,
        })

    if not completed_items:
        today_work = f"## 今日工作（{report_date}）\n\n今日暂无任务更新记录。"
    else:
        lines = [f"## 今日工作（{report_date}）\n"]
        for item in completed_items:
            remark = item["remark"] if item["remark"] else "（无备注）"
            photo_note = f"  📎照片×{len(item['photos'])}" if item["photos"] else ""
            lines.append(f"- **{item['name']}**：{remark}{photo_note}")
        today_work = "\n".join(lines)

    return completed_items, today_work


async def _build_project_summary(db: AsyncSession, project_id: int) -> str:
    """汇总任务列表 + 近期日报，作为 RAG 检索与 AI 生成的基础摘要。

    设计原则：DeepSeek 上下文 64k，3000 字远不到上限，无需预先压缩。
    之前的压缩多花一次 API 调用、多花一倍延迟和成本，已砍掉。
    """
    tasks_result = await db.execute(
        select(Task).where(Task.project_id == project_id).order_by(Task.sort_order)
    )
    tasks = tasks_result.scalars().all()
    task_lines = [f"- {t.name}（状态：{t.status}）" for t in tasks]

    reports_result = await db.execute(
        select(DailyReport)
        .where(DailyReport.project_id == project_id)
        .order_by(DailyReport.report_date.desc())
        .limit(14)
    )
    reports = reports_result.scalars().all()
    report_lines = []
    for r in reports:
        parts = [f"【{r.report_date}】"]
        if r.today_work:
            parts.append(f"今日：{r.today_work}")
        if r.tomorrow_plan:
            parts.append(f"明日：{r.tomorrow_plan}")
        if r.risk_alert:
            parts.append(f"风险：{r.risk_alert}")
        report_lines.append("\n".join(parts))

    return (
        "### 任务列表\n"
        + ("\n".join(task_lines) if task_lines else "（无）")
        + "\n\n### 近期日报\n"
        + ("\n\n".join(report_lines) if report_lines else "（无）")
    )


def _parse_candidate_list(raw: str) -> list[str]:
    """已废弃：保留只为兼容旧调用。新代码使用 ai_client.chat_json 直接拿结构化数组。"""
    if not raw:
        return []
    try:
        text = raw.strip()
        text = re.sub(r"^```(?:json)?", "", text, flags=re.IGNORECASE).strip()
        text = re.sub(r"```$", "", text).strip()
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end != -1 and end > start:
            data = json.loads(text[start : end + 1])
            if isinstance(data, list):
                return [str(x).strip() for x in data if str(x).strip()]
    except Exception:
        pass
    return []


# ── 日报：提议（human-in-the-loop 前置） ──────────────────────────────

async def propose_daily_report(
    db: AsyncSession, project_id: int, report_date: date
) -> dict:
    """生成日报草稿：今日工作（确定性）+ AI 明日计划候选 + AI 项目级风险。

    返回给前端后，由前端逐条确认明日计划候选、允许用户自增，再调用 finalize 落库。
    """
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = project_result.scalar_one_or_none()
    if project is None:
        raise ValueError(f"Project not found: {project_id}")

    completed_items, today_work = await _build_today_work(db, project_id, report_date)
    summary = await _build_project_summary(db, project_id)

    # 检索修船知识库相关要点（明日计划 & 风险共用一份检索上下文）
    knowledge_q = (
        f"项目：{project.ship_name}（{project.type}）。\n"
        f"当前任务与进度摘要：\n{summary}\n"
        "请检索与该项目修船管理、进度管控、质量与安全风险相关的知识要点。"
    )
    knowledge_ctx = await retrieve(db, knowledge_q, top_k=5)
    knowledge_text = (
        "\n\n".join(f"- {c}" for c in knowledge_ctx)
        if knowledge_ctx
        else "（知识库暂无相关内容）"
    )

    ai_client = get_ai_client()

    async def gen_tomorrow() -> list[str]:
        messages = [
            {
                "role": "system",
                "content": "你是资深的修船/船舶工程项目管理助手，善于制定可执行的明日工作计划。",
            },
            {
                "role": "user",
                "content": (
                    f"项目：{project.ship_name}（类型：{project.type}）\n\n"
                    f"今日工作：\n{today_work}\n\n"
                    f"项目摘要（任务列表 + 历史日报）：\n{summary}\n\n"
                    f"修船知识库相关要点：\n{knowledge_text}\n\n"
                    "请基于以上信息，为该项目制定明天的重点工作计刬。\n"
                    "要求：\n"
                    "1. 输出 JSON 数组，每个元素是一句简洁、可执行的明日计划条目（≤30 汉字）；\n"
                    "2. 聚焦项目整体推进，3-6 条为宜；\n"
                    "3. 只输出 JSON 数组本身，不要任何额外说明或代码块标记。"
                ),
            },
        ]
        try:
            data = await ai_client.chat_json(messages, temperature=0.6)
            if isinstance(data, list):
                items = [str(x).strip() for x in data if str(x).strip()]
                return items[:8]
            if isinstance(data, dict) and "items" in data:
                items = [str(x).strip() for x in data["items"] if str(x).strip()]
                return items[:8]
            logger.warning(f"明日计划返回非数组：{type(data).__name__}")
            return []
        except Exception as e:
            logger.warning(f"明日计划生成失败：{e}")
            return []

    async def gen_risk() -> str:
        messages = [
            {
                "role": "system",
                "content": "你是资深的修船/船舶工程项目管理助手，善于从整体项目角度识别风险。",
            },
            {
                "role": "user",
                "content": (
                    f"项目：{project.ship_name}（类型：{project.type}）\n\n"
                    f"项目摘要（任务列表 + 历史日报）：\n{summary}\n\n"
                    f"修船知识库相关要点：\n{knowledge_text}\n\n"
                    "请从「整个项目」的角度（不是单条任务）总结当前主要风险与注意事项。\n"
                    "用 Markdown 分点列出，简洁专业。若整体风险可控，请直接说明「当前项目整体风险可控」。"
                ),
            },
        ]
        try:
            return await ai_client.chat(messages, temperature=0.4)
        except Exception as e:
            logger.warning(f"风险提示生成失败：{e}")
            return "当前项目整体风险可控（AI 生成失败）。"

    tomorrow_candidates, risk_alert = await asyncio.gather(gen_tomorrow(), gen_risk())

    existing_result = await db.execute(
        select(DailyReport).where(
            DailyReport.project_id == project_id,
            DailyReport.report_date == report_date,
        )
    )
    existing = existing_result.scalar_one_or_none()

    return {
        "project_id": project_id,
        "report_date": report_date,
        "ship_name": project.ship_name,
        "today_work": today_work,
        "completed_items": completed_items,
        "tomorrow_candidates": tomorrow_candidates,
        "risk_alert": risk_alert,
        "existing_report_id": existing.id if existing else None,
    }


# ── 日报：定稿（human-in-the-loop 后置） ──────────────────────────────

async def finalize_daily_report(
    db: AsyncSession,
    project_id: int,
    report_date: date,
    today_work: str | None = None,
    tomorrow_items: list[str] | None = None,
    risk_alert: str | None = None,
    confirmed: bool = True,
) -> DailyReport:
    """把用户确认后的日报落库（今日工作 + 确认/自增的明日计划 + 项目级风险）。"""
    result = await db.execute(
        select(DailyReport).where(
            DailyReport.project_id == project_id,
            DailyReport.report_date == report_date,
        )
    )
    report = result.scalar_one_or_none()
    if report is None:
        report = DailyReport(project_id=project_id, report_date=report_date)
        db.add(report)

    # 今日工作：优先用前端回传；缺失则回退到确定性重建
    if today_work is None:
        _, today_work = await _build_today_work(db, project_id, report_date)
    report.today_work = today_work

    if tomorrow_items is not None:
        items = list(tomorrow_items) if isinstance(tomorrow_items, (list, tuple)) else []
        report.tomorrow_plan = "\n".join(f"- {it}" for it in items) if items else ""
        report.tomorrow_candidates = items

    if risk_alert is not None:
        report.risk_alert = risk_alert

    report.confirmed = confirmed
    await db.commit()
    await db.refresh(report)
    logger.info(f"日报已定稿：project={project_id}, date={report_date}, confirmed={confirmed}")
    return report


# ── 兼容：celery 一键生成（自动确认全部候选，无 HITL） ──────────────────

async def generate_daily_report(
    db: AsyncSession, project_id: int, report_date: date
) -> dict:
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = project_result.scalar_one_or_none()
    if project is None:
        raise ValueError(f"Project not found: {project_id}")

    proposal = await propose_daily_report(db, project_id, report_date)
    candidates = proposal["tomorrow_candidates"]
    tomorrow_plan = "\n".join(f"- {c}" for c in candidates) if candidates else ""

    return {
        "project_id": project_id,
        "report_date": report_date,
        "ship_name": project.ship_name,
        "completed_items": proposal["completed_items"],
        "today_work": proposal["today_work"],
        "tomorrow_plan": tomorrow_plan,
        "tomorrow_candidates": candidates,
        "risk_alert": proposal["risk_alert"],
    }


# ── 周报：AI 汇总一周日报 ─────────────────────────────────────────────

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

    context_parts = []
    for dr in daily_reports:
        block = f"【{dr.report_date}】"
        if dr.today_work:
            block += f"\n今日工作：{dr.today_work}"
        if dr.tomorrow_plan:
            block += f"\n明日计划：{dr.tomorrow_plan}"
        if dr.risk_alert:
            block += f"\n风险：{dr.risk_alert}"
        context_parts.append(block)
    context = "\n\n".join(context_parts)

    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = project_result.scalar_one_or_none()

    ai_client = get_ai_client()
    messages = [
        {
            "role": "system",
            "content": (
                "你是专业的船舶工程项目周报生成助手。"
                "请严格输出 JSON 对象，不要任何额外说明或代码块标记。\n"
                "字段定义：\n"
                "- summary: 本周工作摘要（string，Markdown 分点，≤200 字）\n"
                "- next_week_plan: 下周计划（string，Markdown 分点，≤200 字）"
            ),
        },
        {
            "role": "user",
            "content": (
                f"项目：{project.ship_name if project else ''}\n"
                f"周期：{week_start} 至 {week_end}\n\n"
                f"本周日报汇总：\n{context}\n\n"
                "请生成本周工作摘要与下周计划。"
            ),
        },
    ]

    summary = ""
    next_week_plan = ""
    try:
        data = await ai_client.chat_json(messages, temperature=0.5)
        summary = str(data.get("summary") or "").strip()
        next_week_plan = str(data.get("next_week_plan") or "").strip()
        if not summary:
            summary = f"{week_start} 至 {week_end} 共确认 {len(daily_reports)} 份日报。"
        if not next_week_plan:
            next_week_plan = "待制定"
        logger.info(f"AI-generated weekly report for project {project_id}")
    except Exception as e:
        logger.warning(f"AI generation failed for weekly report: {e}")
        summary = f"{week_start} 至 {week_end} 共确认 {len(daily_reports)} 份日报。"
        next_week_plan = "待制定"

    return {
        "project_id": project_id,
        "week_start_date": week_start,
        "week_end_date": week_end,
        "summary": summary,
        "next_week_plan": next_week_plan,
        "source": "ai",
    }
