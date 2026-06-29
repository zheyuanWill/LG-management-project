"""
AI Agent Router — Project management chatbot with tool calling and SSE streaming.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user
from app.core.config import settings
from app.models.user import User

router = APIRouter(prefix="/ai-agent", tags=["AI Agent"])


class ChatRequest(BaseModel):
    message: str
    chat_history: Optional[list] = None


class ChatResponse(BaseModel):
    output: str
    steps: list


class CostEstimateRequest(BaseModel):
    vessel_name: Optional[str] = None
    equipment_type: Optional[str] = None
    work_description: str
    project_type: Optional[str] = None


class CostEstimateResponse(BaseModel):
    cost_range: dict
    duration_range: dict
    similar_projects: list
    risks: list
    summary: str


@router.post("/chat", response_model=ChatResponse)
async def agent_chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Chat with the project management AI agent (non-streaming)."""
    from app.services.agent import run_agent
    result = await run_agent(request.message, request.chat_history)
    return ChatResponse(**result)


@router.post("/chat/stream")
async def agent_chat_stream(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Chat with SSE streaming — real-time tool calls and text generation."""
    from app.services.agent import run_agent_stream

    async def event_generator():
        async for event in run_agent_stream(request.message, request.chat_history):
            yield event

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/estimate-cost", response_model=CostEstimateResponse)
async def estimate_cost(
    request: CostEstimateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """AI-powered cost estimation based on historical similar projects."""
    import json
    from app.services.agent.tools import search_orders

    search_query = f"{request.vessel_name or ''} {request.equipment_type or ''} {request.work_description}"
    similar_raw = search_orders(search_query.strip(), limit=5)
    similar_data = json.loads(similar_raw)

    similar_projects = similar_data.get("orders", [])
    amounts = [p["total_amount"] for p in similar_projects if p["total_amount"] > 0]

    if not amounts:
        return CostEstimateResponse(
            cost_range={"min": 0, "max": 0, "avg": 0, "currency": "CNY"},
            duration_range={"min_days": 15, "max_days": 90},
            similar_projects=[],
            risks=["没有找到类似项目，无法准确估算"],
            summary="未找到历史类似项目，建议人工评估。",
        )

    avg_amount = sum(amounts) / len(amounts)
    min_amount = min(amounts) * 0.8
    max_amount = max(amounts) * 1.2

    prompt = f"""基于以下历史类似项目数据，为新项目生成成本预估:

新项目: {request.work_description}
船名: {request.vessel_name or '未指定'}
设备: {request.equipment_type or '未指定'}
类型: {request.project_type or '未指定'}

历史数据:
{json.dumps(similar_projects[:3], ensure_ascii=False, indent=2)}

请输出 JSON（不含 ```json 标记）:
{{
  "cost_range": {{"min": 最低估算, "max": 最高估算, "avg": 平均估算, "currency": "CNY"}},
  "duration_range": {{"min_days": 最短工期天数, "max_days": 最长工期天数}},
  "risks": ["风险点1", "风险点2"],
  "summary": "简要评估说明"
}}"""

    config_key = settings.DEEPSEEK_API_KEY
    if config_key:
        try:
            import httpx
            headers = {
                "Authorization": f"Bearer {config_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": settings.DEEPSEEK_MODEL,
                "messages": [
                    {"role": "system", "content": "你是一个船修项目成本估算专家。"},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
                "max_tokens": 1000,
            }
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"{settings.DEEPSEEK_BASE_URL}/chat/completions",
                    headers=headers, json=payload,
                )
                resp.raise_for_status()
                content = resp.json()["choices"][0]["message"]["content"]

                cleaned = content.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("\n", 1)[1]
                if cleaned.endswith("```"):
                    cleaned = cleaned.rsplit("```", 1)[0]

                ai_result = json.loads(cleaned.strip())
                return CostEstimateResponse(
                    cost_range=ai_result.get("cost_range", {"min": min_amount, "max": max_amount, "avg": avg_amount, "currency": "CNY"}),
                    duration_range=ai_result.get("duration_range", {"min_days": 15, "max_days": 60}),
                    similar_projects=[
                        {"order_no": p["order_no"], "amount": p["total_amount"], "vessel": p.get("vessel", "")}
                        for p in similar_projects[:3]
                    ],
                    risks=ai_result.get("risks", []),
                    summary=ai_result.get("summary", ""),
                )
        except Exception:
            pass

    return CostEstimateResponse(
        cost_range={"min": round(min_amount, 2), "max": round(max_amount, 2), "avg": round(avg_amount, 2), "currency": "CNY"},
        duration_range={"min_days": 15, "max_days": 60},
        similar_projects=[
            {"order_no": p["order_no"], "amount": p["total_amount"], "vessel": p.get("vessel", "")}
            for p in similar_projects[:3]
        ],
        risks=["基于历史数据的简单统计，仅供参考"],
        summary=f"基于 {len(amounts)} 个类似项目，预估成本范围 {min_amount:,.0f} ~ {max_amount:,.0f} 元。",
    )


@router.get("/status")
async def agent_status():
    """Check AI agent configuration status."""
    return {
        "configured": bool(settings.DEEPSEEK_API_KEY),
        "model": settings.DEEPSEEK_MODEL,
        "tools": [t["name"] for t in __import__("app.services.agent.tools", fromlist=["TOOL_DEFINITIONS"]).TOOL_DEFINITIONS],
    }
