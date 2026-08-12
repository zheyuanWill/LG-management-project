from datetime import datetime

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.quick_save import QuickSave
from app.services.ai_client import get_ai_client


async def recognize_content(content_type: str, content: str) -> dict:
    ai_client = get_ai_client()

    if content_type == "text":
        messages = [
            {
                "role": "system",
                "content": "你是一个船舶工程项目管理助手。请分析用户粘贴的文本，提取关键信息（项目名称、船舶名称、日期、金额等），并给出建议的分类。",
            },
            {
                "role": "user",
                "content": f"请分析以下文本，提取关键词和可能关联的项目信息：\n\n{content}",
            },
        ]
        recognized = await ai_client.chat(messages, temperature=0.3)
        return {
            "recognized_text": recognized,
            "keywords": _extract_keywords(recognized),
        }

    elif content_type == "image":
        # OCR 已移除（依赖较重，按需再启用）。图片暂不提取文字，
        # 后端直接返回空识别结果，前端会提示「图片暂不支持 AI 文字识别，已保存原图」。
        return {"recognized_text": "", "keywords": [], "ocr_text": ""}

    return {"recognized_text": "", "keywords": []}


def _extract_keywords(text: str) -> list[str]:
    keywords = []
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("-") or line.startswith("•"):
            kw = line.lstrip("-• ").strip()
            if kw and len(kw) > 1:
                keywords.append(kw)
    return keywords[:10]


async def suggest_projects(db: AsyncSession, recognized_text: str) -> list[dict]:
    if not recognized_text:
        return []

    keywords = _extract_keywords(recognized_text)
    if not keywords:
        return []

    project_result = await db.execute(select(Project).where(Project.status == "active"))
    projects = project_result.scalars().all()

    scored_projects = []
    for project in projects:
        score = 0
        project_text = f"{project.ship_name} {project.project_no} {project.remarks or ''}"
        for kw in keywords:
            if kw.lower() in project_text.lower():
                score += 1

        if score > 0:
            scored_projects.append({
                "id": project.id,
                "project_no": project.project_no,
                "ship_name": project.ship_name,
                "type": project.type,
                "match_score": score,
            })

    scored_projects.sort(key=lambda x: x["match_score"], reverse=True)
    return scored_projects[:5]


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