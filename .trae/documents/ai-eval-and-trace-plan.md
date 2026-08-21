# AI 应用可观测性 + LLM 输出质量 eval

## Context

项目将作为 AI 应用岗面试素材。当前缺两个工程基本盘：

1. **可观测性**：DeepSeek 是付费 API，日报 / 周报 / 风险扫描 / RAG / 随手存都是高频 LLM 调用。当前 `backend/app/services/ai_client.py` 只 log `"AI chat request completed"`，没有 token cost / latency / 失败降级 trace，生产出问题没法定位是 prompt、模型还是网络。
2. **LLM 输出质量 eval**：`e2e_ai.py` 只测接口能通 + 字段存在，不测"输出语义对不对"。改一次 prompt 就有回归风险，没有 eval set 锁定输出质量。

预期产出：
- backend stdout 出结构化 trace JSON（feature + latency + token + success + fallback）
- `eval_ai.py` 8 条用例 + PASS/FAIL 汇总报告
- 不动 DB schema、不动前端、ai-service 改动控制在加一个 usage 字段

用户已确认：
- Trace 形式：loguru stdout 结构化日志（最小改动方案）
- Eval 范围：8 条核心用例

## 改动清单

### 1. ai-service 层（需 `docker compose build ai-service`）

DeepSeek 在 `_cloud_chat` 收到的 `response.json()` 里就含 `usage`（标准 OpenAI 格式：prompt_tokens / completion_tokens / total_tokens），当前代码没读。改 4 个文件：

- [backend/ai_service/llm.py](file:///c:/dev/LG-management-project/backend/ai_service/llm.py)
  - `chat()` 返回值从 `str` 改为 `tuple[str, dict]`（content, usage_dict）
  - `_cloud_chat` (L138-L157)：读 `data.get("usage", {})` 返回 `(content, usage)`
  - `_ollama_chat` / `_mock_chat`：返回 `(content, {})`（拿不到 token 就空 dict）
  - `chat_stream`：保持返回增量字符串，不记 usage（流式拿 token 复杂，留给后续）

- [backend/ai_service/schemas.py](file:///c:/dev/LG-management-project/backend/ai_service/schemas.py)
  - `ChatResponse` 加 `usage: dict | None = None` 字段

- [backend/ai_service/main.py](file:///c:/dev/LG-management-project/backend/ai_service/main.py) (L84-L102)
  - `/v1/chat` 端点：`content, usage = llm_client.chat(...)`，传 usage 给 `ChatResponse`
  - `/v1/qa` 端点：同样解包（qa 内部调 chat，usage 也可顺带返回；可选）

### 2. backend 层 trace

- [backend/app/services/ai_client.py](file:///c:/dev/LG-management-project/backend/app/services/ai_client.py)
  - `chat / chat_json / embed / qa` 加 `feature: str = "unknown"` 参数
  - 每个方法记 `t0 = time.perf_counter()`，结束/失败时 loguru 输出一行结构化 JSON：
    ```
    {"event":"ai_call","feature":"daily_report_propose","method":"chat_json","latency_ms":1234,"success":true,"prompt_tokens":1500,"completion_tokens":300,"total_tokens":1800,"error":null}
    ```
  - `chat` 读 ai-service 返回的 usage 字段一并 log（chat_json 内部调 chat，复用同一 trace）
  - 失败时记 `success=false` + error_msg + 是否降级（fallback 走"AI服务暂时不可用"返回值时记 `fallback=true`）

业务调用点显式传 feature 参数：
- [backend/app/services/report_service.py](file:///c:/dev/LG-management-project/backend/app/services/report_service.py) ~L152-L187：`propose_daily_report` 传 `"daily_report_propose"`；`generate_weekly_report` 传 `"weekly_report_generate"`
- [backend/app/services/risk_service.py](file:///c:/dev/LG-management-project/backend/app/services/risk_service.py) `detect_risks_with_ai`：传 `"risk_scan"`
- [backend/app/services/quick_save_service.py](file:///c:/dev/LG-management-project/backend/app/services/quick_save_service.py) `recognize_content`：传 `"quick_save_text"`
- [backend/app/services/rag_service.py](file:///c:/dev/LG-management-project/backend/app/services/rag_service.py) `query`：embed 传 `"rag_query_embed"`，chat 传 `"rag_query_answer"`

### 3. eval set（新建）

`eval_ai.py`（项目根，与 [e2e_ai.py](file:///c:/dev/LG-management-project/e2e_ai.py) 同风格：纯 Python + urllib + 自写 assert_eq，复用 e2e_ai 的 `rest / upload_doc / login / cleanup` 模式）。

8 条用例，每条固定输入 + 语义/结构断言：

| # | 用例 | 输入 | 断言 |
|---|---|---|---|
| 1 | rag-hit-keyword | 上传固定 Markdown 手册 + 查询"主机大修后要做什么试验？" | answer 含"系泊"/"曲轴"/"4 小时"任一 |
| 2 | rag-miss-refusal | 查询"什么是量子力学？"（手册外问题） | answer 含拒绝语义（"无法"/"未在"/"不在知识库"任一） |
| 3 | risk-scan-fields | 建 progress=20 + planned_end_date=今天-1 天项目 | 扫描返回 list + 至少 1 条 + 每条含 title + risk_level |
| 4 | risk-scan-fallback | 检测 ai-service `/health` 的 provider，若是 mock 则 SKIP，若是 cloud 走正常扫描 | 即使 LLM 降级仍返回 list（规则兜底） |
| 5 | quick-save-extract | 固定文本"NACC Procida IMO 9018345 今天抵达大连港，主机曲轴臂距差超差" | recognized_text 含 NACC / IMO / 9018345 / 大连 任一 |
| 6 | daily-report-propose-structure | 建任务 + 每日更新 → propose | today_work 非空 + tomorrow_candidates 是 list + ≥1 条 |
| 7 | weekly-report-generate-structure | 先 finalize 一份 confirmed 日报 → weekly generate | summary 非空 + next_week_plan 非空 + source=ai |
| 8 | chat-json-stability | 连续 3 次调 propose | 每次返回 200 + tomorrow_candidates 是 list（不抛 RuntimeError） |

输出：每条用例 `[PASS]/[FAIL]/[SKIP]`，最后汇总 `X/8 PASS, Y FAIL, Z SKIP`。失败也跑完全部用例再汇总 exit 1。DeepSeek 真实调用，跑一次约 3-5 分钟。结束时清理测试项目 + 知识文档（复用 e2e_ai.py 模式）。

### 4. 文档更新

- [PROGRESS.md](file:///c:/dev/LG-management-project/PROGRESS.md)：新增 `### 2026-08-21 · AI eval + trace 工程化` 会话记录
- [feature_list.json](file:///c:/dev/LG-management-project/feature_list.json)：新增 feature `ai-observability-eval`，priority=85，status=passing，evidence 记录 eval 8 条结果 + trace 日志样例
- [ai-engineering-highlights.md](file:///c:/dev/LG-management-project/ai-engineering-highlights.md)：追加「AI 选型判断」一节，写"为什么做 eval/trace，为什么不做 Agent/微调/rerank"——面试讲故事用

## 验证

按顺序执行：

1. `docker compose build ai-service`（ai-service 无源码卷挂载，改代码必重建）
2. `docker compose up -d ai-service backend`（重启两个受影响服务）
3. ai-service health：`curl.exe localhost:8001/health` → 200 + provider=cloud
4. backend health：`curl.exe localhost:8000/docs | Select-Object -First 1` → 200
5. 跑 eval：`python eval_ai.py` → 8 条全 PASS（允许 risk-scan-fallback SKIP，不允许多于 1 个 SKIP）
6. 看 trace 日志：`docker compose logs backend 2>&1 | Select-String "ai_call" | Select-Object -Last 5` → 应该看到结构化 JSON 行，含 feature + latency_ms + token 数
7. 回归：`python e2e_ai.py` → 5 条全 PASS（确认改动没破坏现有功能）

## 不在范围内（已与用户确认）

- 不加 DB 表（不增 AiCallTrace 模型）
- 不加前端 dashboard
- 不加 Agent / function calling / 微调 / rerank（业务场景不需要，违背"不为 AI 而 AI"原则）
- 不做 ai-service JSONL 持久化（loguru stdout 够用，`docker compose logs` 可查）

## 关键文件路径汇总

- 改：[backend/ai_service/llm.py](file:///c:/dev/LG-management-project/backend/ai_service/llm.py)、[backend/ai_service/schemas.py](file:///c:/dev/LG-management-project/backend/ai_service/schemas.py)、[backend/ai_service/main.py](file:///c:/dev/LG-management-project/backend/ai_service/main.py)
- 改：[backend/app/services/ai_client.py](file:///c:/dev/LG-management-project/backend/app/services/ai_client.py)
- 改：[backend/app/services/report_service.py](file:///c:/dev/LG-management-project/backend/app/services/report_service.py)、[risk_service.py](file:///c:/dev/LG-management-project/backend/app/services/risk_service.py)、[quick_save_service.py](file:///c:/dev/LG-management-project/backend/app/services/quick_save_service.py)、[rag_service.py](file:///c:/dev/LG-management-project/backend/app/services/rag_service.py)
- 新建：[eval_ai.py](file:///c:/dev/LG-management-project/eval_ai.py)
- 改：[PROGRESS.md](file:///c:/dev/LG-management-project/PROGRESS.md)、[feature_list.json](file:///c:/dev/LG-management-project/feature_list.json)、[ai-engineering-highlights.md](file:///c:/dev/LG-management-project/ai-engineering-highlights.md)
