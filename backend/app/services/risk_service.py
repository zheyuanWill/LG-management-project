from datetime import datetime
import json

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.report import RiskEvent
from app.models.task import Task, TaskStatus
from app.services.ai_client import get_ai_client
from app.services.rag_service import retrieve


RISK_LEVELS = ["info", "warning", "critical"]


async def detect_risks(db: AsyncSession, project_id: int) -> list[dict]:
    """规则扫描：逾期 / 未启动多 / 完成率低。确定性判断，AI 不如规则。"""
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

    risks: list[dict] = []

    not_started = [t for t in tasks if t.status == TaskStatus.NOT_STARTED.value]
    if not_started and len(not_started) > len(tasks) * 0.5:
        risks.append({
            "title": "大量任务未启动",
            "detail": f"{len(not_started)}/{len(tasks)} 个任务尚未开始，可能影响项目进度",
            "risk_level": "warning",
            "source": "rule",
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
            "source": "rule",
        })

    completed = [t for t in tasks if t.status == TaskStatus.COMPLETED.value]
    if tasks:
        completion_rate = len(completed) / len(tasks)
        if completion_rate < 0.3 and project.status == "active":
            risks.append({
                "title": "项目完成率偏低",
                "detail": f"当前完成率 {completion_rate:.1%}，建议关注进度推进",
                "risk_level": "info",
                "source": "rule",
            })

    return risks


async def detect_risks_with_ai(db: AsyncSession, project_id: int) -> list[dict]:
    """规则扫描 + RAG 检索 + LLM 综合判断。

    LLM 真正擅长：多信息源综合软推理。
    输入：项目任务列表 + 规则扫描结果 + RAG 检索知识库要点
    输出：结构化风险事件 `[{title, detail, risk_level}]`

    返回合并去重后的列表（规则扫出的 + AI 综合判断的），落库由调用方负责。
    """
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = project_result.scalar_one_or_none()
    if project is None:
        raise ValueError(f"Project not found: {project_id}")

    tasks_result = await db.execute(
        select(Task).where(Task.project_id == project_id).order_by(Task.sort_order)
    )
    tasks = tasks_result.scalars().all()

    # 1. 规则扫描
    rule_risks = await detect_risks(db, project_id)

    # 2. 准备上下文：任务列表 + 规则风险
    task_lines = []
    today = datetime.now().date()
    for t in tasks:
        overdue_mark = " [已逾期]" if (
            t.status == TaskStatus.IN_PROGRESS.value
            and t.planned_end_date
            and t.planned_end_date < today
        ) else ""
        task_lines.append(
            f"- {t.name}（状态：{t.status}{overdue_mark}）"
        )
    task_summary = "\n".join(task_lines) if task_lines else "（无任务）"

    rule_risk_text = "（规则未扫出风险）"
    if rule_risks:
        rule_risk_text = "\n".join(
            f"- [{r['risk_level']}] {r['title']}: {r.get('detail', '')}"
            for r in rule_risks
        )

    # 3. RAG 检索知识库要点
    knowledge_q = (
        f"项目：{project.ship_name}（{project.type}）。\n"
        f"任务列表：\n{task_summary}\n"
        "请检索与该项目修船管理、进度管控、质量与安全风险相关的知识要点。"
    )
    try:
        knowledge_ctx = await retrieve(db, knowledge_q, top_k=5)
    except Exception as e:
        logger.warning(f"风险检测 RAG 检索失败：{e}")
        knowledge_ctx = []
    knowledge_text = (
        "\n".join(f"- {c}" for c in knowledge_ctx)
        if knowledge_ctx
        else "（知识库暂无相关内容）"
    )

    # 4. LLM 综合判断
    ai_client = get_ai_client()
    messages = [
        {
            "role": "system",
            "content": (
                "你是资深的修船/船舶工程项目风险管理助手。"
                "基于项目任务数据、规则扫描结果、知识库要点，"
                "做规则之外的隐性风险综合判断。\n"
                "严格输出 JSON 对象，不要任何额外说明或代码块标记。\n"
                "字段定义：\n"
                "- risks: 风险事件数组，每个元素 {title, detail, risk_level}\n"
                "  - title: 简洁风险标题（≤30 字）\n"
                "  - detail: 风险描述与建议应对（≤200 字）\n"
                "  - risk_level: 'critical' | 'warning' | 'info'\n"
                "原则：\n"
                "1. 只输出规则没扫出的隐性风险，不要重复规则已扫出的；\n"
                "2. 若整体风险可控，返回空数组 {\"risks\": []}；\n"
                "3. 风险必须基于给定信息推理，不要凭空臆测。"
            ),
        },
        {
            "role": "user",
            "content": (
                f"项目：{project.ship_name}（类型：{project.type}）\n\n"
                f"### 任务列表\n{task_summary}\n\n"
                f"### 规则扫描结果\n{rule_risk_text}\n\n"
                f"### 知识库要点\n{knowledge_text}\n\n"
                "请做综合风险判断。"
            ),
        },
    ]

    ai_risks: list[dict] = []
    try:
        data = await ai_client.chat_json(messages, temperature=0.4)
        raw_risks = data.get("risks") if isinstance(data, dict) else data
        if isinstance(raw_risks, list):
            for r in raw_risks:
                if not isinstance(r, dict):
                    continue
                title = str(r.get("title") or "").strip()
                if not title:
                    continue
                ai_risks.append({
                    "title": title[:256],
                    "detail": str(r.get("detail") or "").strip(),
                    "risk_level": (r.get("risk_level") or "info").lower(),
                    "source": "ai",
                })
        logger.info(
            f"AI 综合风险判断完成：project={project_id}, ai_risks={len(ai_risks)}"
        )
    except Exception as e:
        logger.warning(f"AI 综合风险判断失败：{e}")
        # AI 失败时只返回规则扫出的
        return rule_risks

    # 5. 合并去重（按 title）
    merged: list[dict] = []
    seen_titles: set[str] = set()
    for r in rule_risks + ai_risks:
        key = r["title"]
        if key in seen_titles:
            continue
        seen_titles.add(key)
        merged.append(r)

    return merged


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
