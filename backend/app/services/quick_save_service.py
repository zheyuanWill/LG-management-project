from datetime import datetime

from loguru import logger
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.quick_save import QuickSave
from app.services.ai_client import get_ai_client


async def recognize_content(content_type: str, content: str) -> dict:
    """随手存内容识别。

    设计原则：图片是佐证不是内容，不做图转字识别（监修人员本来就要写日报文字，
    让 AI 替他描述图片反而降低日报质量）。只有文本走 AI 提取结构化字段。
    """
    if content_type == "text":
        ai_client = get_ai_client()
        messages = [
            {
                "role": "system",
                "content": (
                    "你是船舶工程项目管理助手。从用户粘贴的文本中提取结构化信息，"
                    "严格输出 JSON 对象，不要任何额外说明或代码块标记。\n"
                    "字段定义：\n"
                    "- ship_name: 提及的船名（string 或 null）\n"
                    "- imo: 提及的 IMO 号（string 或 null）\n"
                    "- date: 提及的日期 YYYY-MM-DD（string 或 null）\n"
                    "- amount: 提及的金额数字（number 或 null）\n"
                    "- keywords: 关键工作要点数组（string[]，每条 ≤15 字）\n"
                    "- summary: 一句话摘要（string）"
                ),
            },
            {
                "role": "user",
                "content": f"请提取以下文本的结构化信息：\n\n{content}",
            },
        ]
        try:
            data = await ai_client.chat_json(messages, temperature=0.2)
            recognized_text = data.get("summary") or content
            return {"recognized_text": recognized_text, "structured": data}
        except Exception as e:
            logger.warning(f"随手存文本 AI 提取失败：{e}")
            return {"recognized_text": content, "structured": {}}

    # 图片不识别：图片是佐证不是内容，前端引导用户手选项目
    return {"recognized_text": "", "structured": {}}


async def suggest_projects(db: AsyncSession, structured: dict | None, recognized_text: str = "") -> list[dict]:
    """根据 structured 字段推荐项目。

    优先用 ship_name 做 DB LIKE 匹配；其次用 keywords 做 OR 模糊匹配；
    都没有则返回 []。彻底替代旧的字符串 contains 方案。
    """
    if not structured:
        return []

    ship_name = (structured.get("ship_name") or "").strip()
    keywords = structured.get("keywords") or []
    if isinstance(keywords, str):
        keywords = [keywords]

    conditions = []
    if ship_name:
        conditions.append(Project.ship_name.ilike(f"%{ship_name}%"))
    for kw in keywords:
        if kw and len(kw) > 1:
            conditions.append(Project.ship_name.ilike(f"%{kw}%"))
            conditions.append((Project.remarks or "").ilike(f"%{kw}%"))

    if not conditions:
        return []

    query = select(Project).where(
        Project.status == "active",
        or_(*conditions),
    )
    result = await db.execute(query)
    projects = result.scalars().all()

    scored = []
    for project in projects:
        score = 0
        project_text = f"{project.ship_name} {project.project_no} {project.remarks or ''}".lower()
        if ship_name and ship_name.lower() in project.ship_name.lower():
            score += 5
        for kw in keywords:
            if kw and kw.lower() in project_text:
                score += 1
        scored.append({
            "id": project.id,
            "project_no": project.project_no,
            "ship_name": project.ship_name,
            "type": project.type,
            "match_score": score,
        })

    scored.sort(key=lambda x: x["match_score"], reverse=True)
    return scored[:5]


async def confirm_save(db: AsyncSession, save_id: int, project_id: int) -> QuickSave:
    result = await db.execute(
        select(QuickSave).where(QuickSave.id == save_id)
    )
    save = result.scalar_one_or_none()
    if save is None:
        raise ValueError(f"QuickSave not found: {save_id}")

    save.confirmed_project_id = project_id
    save.status = "confirmed"
    await db.flush()

    logger.info(f"QuickSave {save_id} confirmed with project {project_id}")
    return save
