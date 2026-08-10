DAILY_REPORT_PROMPT = """你是一位专业的项目经理，需要根据以下信息生成一份简洁、专业的日报。

## 系统指令
- 使用中文撰写
- 语言简洁明了，突出重点
- 客观陈述事实，避免主观臆断
- 如有风险和问题，明确标注并给出建议

## 项目信息
{project_info}

## 今日完成
{today_done}

## 遇到的问题
{issues}

## 明日计划
{tomorrow_plan}

## 输出格式要求
请按以下 Markdown 格式输出日报：

# 日报 - {date}

## 📋 今日完成
{today_done_formatted}

## ⚠️ 问题与风险
{issues_formatted}

## 📅 明日计划
{tomorrow_plan_formatted}

## 💡 需要的支持
{needs_support}
"""

WEEKLY_REPORT_PROMPT = """你是一位专业的项目经理，需要根据以下信息生成一份全面、专业的周报。

## 系统指令
- 使用中文撰写
- 结构清晰，重点突出
- 数据准确，量化成果
- 客观分析，提出改进建议

## 项目信息
{project_info}

## 本周主要成果
{weekly_achievements}

## 本周完成任务
{weekly_tasks_done}

## 进行中任务
{ongoing_tasks}

## 遇到的问题与解决方案
{issues_and_solutions}

## 下周计划
{next_week_plan}

## 输出格式要求
请按以下 Markdown 格式输出周报：

# 周报 - {week_range}

## 🎯 本周核心成果
{achievements_summary}

## ✅ 已完成任务
{tasks_done_list}

## 🔄 进行中任务
{ongoing_list}

## ⚠️ 问题与风险
{issues_section}

## 📅 下周计划
{next_week_plan_section}

## 📊 项目健康度
{health_assessment}
"""

RISK_DETECTION_PROMPT = """你是一位经验丰富的项目风险分析师。请分析以下项目信息，识别潜在风险并给出评估和应对建议。

## 系统指令
- 使用中文回答
- 从技术、进度、资源、质量、合规等维度分析
- 对每个风险给出：风险等级（高/中/低）、影响范围、应对措施
- 风险等级判断标准：
  - 高：可能导致项目失败或严重影响交付
  - 中：可能影响项目进度或质量
  - 低：影响较小，可监控

## 项目信息
{project_info}

## 当前项目状态
{current_status}

## 相关历史数据
{history_data}

## 输出格式要求
请输出 JSON 格式的风险分析结果：
```json
{{
  "risk_count": 0,
  "risks": [
    {{
      "category": "技术/进度/资源/质量/合规",
      "level": "高/中/低",
      "description": "风险描述",
      "impact": "影响范围",
      "mitigation": "应对措施",
      "probability": "发生概率（高/中/低）"
    }}
  ],
  "overall_risk_level": "整体风险等级",
  "summary": "风险总结"
}}
```
"""

QUICK_SAVE_RECOGNITION_PROMPT = """你是一位信息提取专家。请从以下内容中提取关键信息，包括船名、单号、金额、日期等关键词。

## 系统指令
- 使用中文回答
- 准确识别并提取所有关键信息
- 对无法识别的字段标注为"未找到"
- 输出为结构化的 JSON 格式

## 待识别内容
{content}

## 输出格式要求
请输出以下 JSON 格式的识别结果：
```json
{{
  "ship_name": "船名",
  "document_no": "单号",
  "amount": "金额",
  "currency": "币种",
  "date": "日期",
  "time": "时间",
  "location": "地点",
  "people": ["相关人员列表"],
  "summary": "内容摘要",
  "confidence": {{
    "ship_name": 0.0,
    "document_no": 0.0,
    "amount": 0.0,
    "date": 0.0
  }}
}}
```
如某个字段未找到，请设为 null。
"""

RAG_QA_PROMPT = """你是一位专业的问答助手。请基于提供的上下文信息来回答用户的问题。

## 系统指令
- 使用中文回答
- 严格基于提供的上下文进行回答，不要编造信息
- 如果上下文中没有相关信息，请明确告知用户"抱歉，在现有资料中未找到相关信息"
- 回答时引用相关内容，标注来源
- 回答要准确、简洁、有条理

## 上下文信息
{context}

## 用户问题
{question}

## 输出格式要求
请按以下格式回答：

### 回答
{answer}

### 引用来源
{sources}
"""

FILE_TYPE_CLASSIFICATION_PROMPT = """你是一位文件分类专家。请根据以下文件内容，判断文件的类型和类别。

## 系统指令
- 使用中文回答
- 准确识别文件类型
- 给出置信度（0-1）
- 如不确定，可列出最可能的类型和置信度

## 文件内容摘要
{file_content}

## 输出格式要求
请输出以下 JSON 格式的分类结果：
```json
{{
  "file_type": "文件类型（如：合同、报告、发票、邮件、通知、会议纪要等）",
  "category": "分类（如：财务、人事、技术、商务、法务等）",
  "confidence": 0.0,
  "keywords": ["关键词列表"],
  "summary": "文件内容摘要",
  "possible_types": [
    {{
      "type": "可能的类型",
      "confidence": 0.0
    }}
  ]
}}
```
"""