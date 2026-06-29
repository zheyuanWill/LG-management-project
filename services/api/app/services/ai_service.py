
"""
AI Service - LLM Integration
"""
import json
import logging
from typing import Optional, Any, Dict, List
from datetime import datetime, date
from pydantic import BaseModel
from enum import Enum

from app.core.config import settings
from app.core.exceptions import BusinessError

logger = logging.getLogger(__name__)


class AIProvider(str, Enum):
    """AI Provider"""
    OPENAI = "OPENAI"
    AZURE_OPENAI = "AZURE_OPENAI"
    ANTHROPIC = "ANTHROPIC"
    DEEPSEEK = "DEEPSEEK"
    QWEN = "QWEN"


class AIService:
    """AI Service"""
    
    def __init__(self):
        self.provider = AIProvider(settings.AI_PROVIDER) if settings.AI_PROVIDER else None
        self.api_key = settings.AI_API_KEY
        self.base_url = settings.AI_BASE_URL
        self.model = settings.AI_MODEL or "gpt-4"
    
    async def is_available(self) -> bool:
        """检查AI服务是否可用"""
        return self.provider is not None and self.api_key is not None
    
    async def _call_llm(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        """调用LLM"""
        if not await self.is_available():
            raise BusinessError(
                code="AI_NOT_CONFIGURED",
                message="AI服务未配置",
                status_code=500
            )
        
        try:
            # 根据provider选择实现
            if self.provider == AIProvider.DEEPSEEK:
                return await self._call_deepseek(system_prompt, user_prompt, **kwargs)
            elif self.provider == AIProvider.OPENAI:
                return await self._call_openai(system_prompt, user_prompt, **kwargs)
            else:
                # 默认模拟
                logger.warning(f"AI Provider {self.provider} not fully implemented, using mock")
                return await self._call_mock(system_prompt, user_prompt, **kwargs)
        except Exception as e:
            logger.error(f"AI call failed: {e}")
            raise BusinessError(
                code="AI_CALL_FAILED",
                message=f"AI调用失败: {str(e)}",
                status_code=500
            )
    
    async def _call_deepseek(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        """调用DeepSeek"""
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise BusinessError(
                code="AI_DEPENDENCY_MISSING",
                message="需要安装openai库",
                status_code=500
            )
        
        client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url or "https://api.deepseek.com"
        )
        
        response = await client.chat.completions.create(
            model=self.model or "deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 4000)
        )
        
        return response.choices[0].message.content
    
    async def _call_openai(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        """调用OpenAI"""
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise BusinessError(
                code="AI_DEPENDENCY_MISSING",
                message="需要安装openai库",
                status_code=500
            )
        
        client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        response = await client.chat.completions.create(
            model=self.model or "gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 4000)
        )
        
        return response.choices[0].message.content
    
    async def _call_mock(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        """模拟AI响应（用于开发测试）"""
        import time
        time.sleep(0.5)
        
        # 根据不同的请求返回不同的mock数据
        if "拆解" in user_prompt or "disassemble" in user_prompt.lower():
            return json.dumps({
                "tasks": [
                    {
                        "task_name": "船体除锈",
                        "sub_tasks": ["表面清洁", "喷砂除锈", "质量检查"],
                        "category": "HULL",
                        "estimated_days": 3,
                        "start_condition": "进坞完成",
                        "critical_path": True,
                        "risk_level": "MEDIUM",
                        "remarks": "注意天气影响"
                    }
                ],
                "summary": "AI已完成计划拆解，共生成1个主任务，含3个子任务"
            }, ensure_ascii=False)
        elif "对比" in user_prompt or "compare" in user_prompt.lower():
            return json.dumps({
                "added_tasks": [],
                "removed_tasks": [],
                "modified_tasks": [],
                "changes_summary": "版本对比完成，无重大变化",
                "schedule_impact": 0
            }, ensure_ascii=False)
        elif "日报" in user_prompt or "daily" in user_prompt.lower():
            return json.dumps({
                "missing_fields": [],
                "risk_assessment": "LOW",
                "followup_questions": [],
                "needs_manager_attention": False,
                "suggestions": ["日报信息完整"]
            }, ensure_ascii=False)
        else:
            return json.dumps({
                "today_status": "正常",
                "key_risks": [],
                "suggestions": ["项目进展顺利"]
            }, ensure_ascii=False)
    
    async def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """解析JSON响应"""
        # 尝试提取JSON
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {response}")
            raise BusinessError(
                code="AI_RESPONSE_INVALID",
                message=f"AI返回格式错误: {str(e)}",
                status_code=500
            )
    
    async def disassemble_repair_plan(
        self,
        plan_text: str,
        project_info: Optional[Dict[str, Any]] = None,
        plan_duration: Optional[int] = None
    ) -> Dict[str, Any]:
        """AI拆解修船计划"""
        system_prompt = """你是一个专业的修船项目计划拆解专家。请将修船计划拆解为结构化的任务列表。

输出必须是严格的JSON格式，不要包含任何其他说明文字。

JSON结构要求：
{
    "tasks": [
        {
            "task_name": "任务名称",
            "sub_tasks": ["子任务1", "子任务2"],
            "category": "任务分类：HULL/ENGINE/ELECTRICAL/PAINTING/SPARE_PARTS/CLASS_SOCIETY/OTHER",
            "estimated_days": 预计工期天数,
            "planned_start_date": "YYYY-MM-DD或null",
            "planned_end_date": "YYYY-MM-DD或null",
            "start_condition": "前置条件",
            "dependencies": [依赖任务ID数组，留空],
            "can_parallel": true/false,
            "critical_path": true/false是否在关键路径,
            "related_spare_parts": ["相关备件1", "相关备件2"],
            "responsible_party": "责任方：SHIPYARD/SUPERVISOR/SUPPLIER/INTERNAL",
            "risk_level": "风险等级：LOW/MEDIUM/HIGH/URGENT",
            "required_photo_evidence": ["需要的照片类型"],
            "daily_check_points": ["每日检查要点"],
            "delay_impact": "延期影响说明",
            "remarks": "备注"
        }
    ],
    "summary": "拆解摘要"
}
"""
        
        user_prompt = f"""请拆解以下修船计划：

计划内容：
{plan_text}

项目信息：
{json.dumps(project_info or {}, ensure_ascii=False)}

计划工期：{plan_duration or '未指定'}天
"""
        
        response = await self._call_llm(system_prompt, user_prompt, temperature=0.3)
        return await self._parse_json_response(response)
    
    async def compare_plan_versions(
        self,
        old_plan: str,
        new_plan: str
    ) -> Dict[str, Any]:
        """对比计划版本"""
        system_prompt = """你是一个专业的修船计划对比专家。请对比两个版本的修船计划。

输出必须是严格的JSON格式。

JSON结构：
{
    "added_tasks": ["新增任务1", "新增任务2"],
    "removed_tasks": ["删除任务1"],
    "modified_tasks": [{"task_name": "任务名", "changes": "变更内容"}],
    "schedule_changes": "工期变化说明",
    "date_changes": "日期变化说明",
    "critical_path_changes": "关键路径变化说明",
    "spare_part_changes": "备件需求变化",
    "risk_changes": "风险变化说明",
    "changes_summary": "变更摘要",
    "schedule_impact": 对总工期影响天数,
    "recommended_actions": ["建议措施"]
}
"""
        
        user_prompt = f"""旧计划：
{old_plan}

新计划：
{new_plan}
"""
        
        response = await self._call_llm(system_prompt, user_prompt, temperature=0.3)
        return await self._parse_json_response(response)
    
    async def check_daily_report_gaps(
        self,
        report_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """检查日报信息缺口"""
        system_prompt = """你是一个专业的修船项目日报审核专家。请检查日报是否有信息缺失。

输出必须是严格的JSON格式。

JSON结构：
{
    "missing_fields": ["缺失字段1", "缺失字段2"],
    "risk_assessment": "风险等级：LOW/MEDIUM/HIGH",
    "followup_questions": ["需要追问的问题1"],
    "needs_manager_attention": true/false,
    "suggestions": ["建议补充内容"]
}
"""
        
        user_prompt = f"日报数据：\n{json.dumps(report_data, ensure_ascii=False)}"
        
        response = await self._call_llm(system_prompt, user_prompt, temperature=0.3)
        return await self._parse_json_response(response)
    
    async def generate_boss_summary(
        self,
        project_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成老板项目摘要"""
        system_prompt = """你是一个专业的修船项目管理专家。请为总经理生成项目摘要。

输出必须是严格的JSON格式。

JSON结构：
{
    "today_status": "今日项目状态",
    "today_progress": "今日主要进展",
    "key_risks": ["主要风险1"],
    "delay_reasons": "延期原因",
    "critical_path_risks": ["关键路径风险"],
    "spare_part_risks": ["缺备件风险"],
    "manager_decisions_needed": ["需总经理决策事项"],
    "shipowner_communication_suggestions": "对船东沟通建议",
    "information_gaps": "信息缺口",
    "next_steps": ["下一步建议"]
}
"""
        
        user_prompt = f"项目数据：\n{json.dumps(project_data, ensure_ascii=False)}"
        
        response = await self._call_llm(system_prompt, user_prompt, temperature=0.5)
        return await self._parse_json_response(response)
    
    async def generate_shipowner_communication(
        self,
        status_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成船东沟通建议"""
        system_prompt = """你是一个专业的修船项目沟通专家。请生成对船东的沟通建议。

输出必须是严格的JSON格式。

JSON结构：
{
    "brief_version": "简洁版沟通话术",
    "formal_version": "正式版沟通话术",
    "conservative_version": "风险保守表达版本",
    "avoid_commitments": ["需要避免承诺的内容"],
    "key_points": ["沟通要点"]
}
"""
        
        user_prompt = f"状态数据：\n{json.dumps(status_data, ensure_ascii=False)}"
        
        response = await self._call_llm(system_prompt, user_prompt, temperature=0.5)
        return await self._parse_json_response(response)


# Singleton instance
ai_service = AIService()

