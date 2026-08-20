# PROGRESS.md — LG 船舶管理 ERP 进度日志

> 每轮会话结束更新本文件；每轮新会话开始先读它。
> 这是项目当前进展的**唯一真相来源**。

## 当前已验证状态（2026-08-19）

- **仓库根目录**：`C:\dev\LG-management-project`（Git 仓库；`.workbuddy/` 为项目数据，勿删）
- **标准启动路径**：
  - Windows：`start-dev.bat`
  - Linux/Mac：`bash init.sh`
  - 指定服务：`docker compose up -d postgres redis minio backend frontend ai-service`
- **标准验证路径**：
  - 后端健康：`curl -s localhost:8000/docs | head`（实际用 `curl.exe` 避免 PS alias）
  - 前端构建：`cd frontend && npm run build`（`node build.js` → `vite build`）
  - 前端类型检查：`cd frontend && npm run typecheck`（仅检查，不阻断构建）
- **当前最高优先级未完成功能**：无（全部 14 项功能 `passing`；2026-08-19 AI 重构后新增 `e2e_ai.py` 覆盖 5 个 AI 功能，全 PASS）。
- **当前 blocker**：无硬性 blocker；前端 `tsc --noEmit` 存在大量**历史**类型错误（number→string、`asChild` 等），但 `build.js` 仅跑 `vite build`（esbuild 不去类型），dist 生成即视为成功，不影响构建。

## 已知全局约束（来自过往复盘，2026-08-19 更新）

- 后端 `GET/POST /users` 已是真实接口（admin 建用户）；用户管理唯一入口 `POST /auth/register`（仅 admin）。
- **风险检测已升级为「规则 + RAG + LLM 综合判断」**（2026-08-19）：`POST /risks/projects/{id}/risks/scan` 同步返回风险列表；旧 `/ai-detect` 保留为 deprecated 别名。前端标签可改为「风险扫描」。
- 知识库 QA 聊天记录已**后端持久化**（2026-08-17 起 `KnowledgeChatMessage` + `/knowledge/chat-messages`），localStorage 仅作离线兜底。
- `lib/websocket.ts` 已接通原生 WebSocket（2026-08-17 起，非死代码）。
- 文件下载依赖 `get_minio_public_client` 公开地址签名（已 pin `region='us-east-1'`）。
- 经纪 / 修船 8 子资源未创建返 200+null（2026-08-17 已修，非 404）。
- **AI 调用走 DeepSeek API**（`ai_client.py`），`chat_json` 支持 structured output；RAG embedding 走 ai-service 的 fastembed（`BAAI/bge-small-zh-v1.5` 512 维）。
- **Celery worker 容器不在部署里**：日报/周报/RAG ingest/风险扫描均已改为同步调用（API 调用即返回），不要写 `celery_app.send_task` 进新代码。
- **ai-service 容器无源码卷挂载**（仅 `ai-cache:/cache`）：改 ai-service 代码后必须 `docker compose build ai-service`，重启无效。

## 会话记录

### 2026-08-19 · AI 重构 + 全功能 e2e 验证（本轮）

- **本轮目标**：用户要求「不为 AI 而 AI」重构项目 AI 部分，只在 LLM 擅长场景（自然语言生成、结构化提取、上下文问答）使用 AI；并跑全部 e2e 验证所有指标达标。
- **已完成的 5 个 AI 功能重构**：
  1. **RAG 多格式清洗 + 按章节切分**（`services/document_processor.py` 新建）：支持 PDF/DOCX/Markdown/TXT，扫描版 PDF/不支持的格式拒绝入库；按章节标题切分，chunk 前缀带 `【《书名》/ 第N章 / 第N节】` 元数据；`rag_service.ingest_document` 改同步调用（砍 Celery 壳）；`CitationItem` 扩展 `book_title/chapter/section/source` 字段，`/knowledge/query` 返回结构化 citation。
  2. **风险检测「规则 + RAG + LLM 综合判断」**（`services/risk_service.detect_risks_with_ai`）：规则扫描打底 + RAG 检索知识库要点 + LLM 综合任务列表与知识上下文输出结构化风险事件 `[{title, detail, risk_level}]`；`POST /risks/projects/{id}/risks/scan` 同步返回，旧 `/ai-detect` 保留为 deprecated 别名。
  3. **随手存文本 structured output**（`services/quick_save_service.recognize_content`）：砍掉图片识别 AI（图片直接存图由用户手选项目）；文本用 `ai_client.chat_json` 提取结构化字段供 `suggest_projects` 匹配活跃项目。
  4. **日报 propose + finalize HITL**（`services/report_service.propose_daily_report`）：今日工作确定性生成 + AI 明日计划候选（`chat_json` 出 list）+ AI 项目级风险；砍掉素材压缩步骤（多花一次 API 调用，64k 上下文够用）；`/propose` 返回草稿，`/finalize` 落库 confirmed 日报。
  5. **周报同步 generate + structured output**（`services/report_service.generate_weekly_report` + `routers/reports.py`）：砍掉 Celery 异步任务壳，API 调用即返回；DeepSeek `chat_json` 一次出 `{summary, next_week_plan}`；只统计 `confirmed=True` 的日报，无数据降级 `source=no_data`。
  6. **ai_client 加 `chat_json`**：system prompt 强制 JSON 输出 + 调用方解析，支持 structured output 场景统一。
- **运行过的验证**：
  - `e2e_all.py`（2026-08-17 旧 4 功能回归）：supervision-refresh / brokerage-404-ux / knowledge-chat-persist / realtime-websocket 全 PASS ✅，确认 AI 重构未破坏现有功能。
  - `e2e_ai.py`（本轮新建，5 AI 功能，DeepSeek 真实调用零 mock）：rag-multi-format（上传 Markdown→ingest→查询命中→章节化 citation→AI answer）/ risk-ai-scan（扫出 3 条风险）/ quick-save-text（AI 提取字段）/ daily-report-propose+finalize（结构化明日计划+风险，落库 confirmed）/ weekly-report-generate（source=ai，summary 非空）全 PASS ✅。
  - 前端 `npm run build`（`node build.js`）：1855 模块，28.69s，构建成功 ✅。
  - 后端健康 `curl.exe localhost:8000/docs` HTTP 200；ai-service `localhost:8001/health` HTTP 200；frontend `localhost:3000` HTTP 200。
- **e2e 暴露并修复的接线问题**：
  1. 日报/周报端点路径漏 `/reports` 前缀（reports router 挂在 `/api/v1/reports`，不是直接挂在 `/api/v1`）——e2e 脚本修正后通过。
  2. 日报 propose 返回字段名是 `tomorrow_candidates`（不是 `tomorrow_items`，后者是 finalize 的入参）——e2e 断言修正后通过。
  3. 周报 generate 只统计 `confirmed=True` 日报，需先 finalize 一份 confirmed 日报才能走 AI 路径——e2e 补 finalize 步骤后 source=ai 通过。
- **已知风险或未解决问题**：
  - `e2e_ai.py` 的 RAG ingest 用 Markdown 测试，PDF/DOCX 路径未实跑（需准备真实样本文件，且扫描版 PDF 拒绝路径未覆盖）。建议后续补 PDF 端到端样本。
  - 风险扫描依赖 DeepSeek API，若 key 失效或限流，LLM 综合判断会降级（`detect_risks_with_ai` 内部 try/except 兜底，仅返回规则扫描结果）。e2e 当前在 key 可用前提下通过。
  - 日报 propose 的 `today_work` 在无 TaskDailyUpdate 时返回「今日暂无任务更新记录」（非空但无实质内容）；建议前端建任务后引导用户先提交每日更新再生成日报。
- **下一步最佳动作**：
  1. （可选）补 PDF/DOCX 真实样本进 `e2e_ai.py`，覆盖扫描版 PDF 拒绝路径。
  2. （可选）前端「自动进度检查」按钮文案改为「风险扫描」对齐新 `/risks/scan` 路径。
  3. 长期：清理前端 `tsc --noEmit` 历史类型错误（不阻断构建，但污染日志）。

---

### 2026-08-17 · 修理接线缺陷（本轮）

- **本轮目标**：修掉此前审计中仍真实存在的接线缺陷。
- **已确认并完成**：
  1. `TaskList.tsx` 创建任务：原发 `due_date`（后端忽略）→ 已发 `planned_end_date`（后端字段名），计划结束日期不再静默丢失。（上一轮已落盘，本轮复核确认仍在。）
  2. **每日更新照片持久化（原 blocked 项）**：
     - 前端 `DailyUpdateForm.tsx`：保留真实 `File` 引用，创建每日更新后逐个 `POST /tasks/daily-updates/{id}/photos`（multipart）上传到 MinIO；上传失败不阻断主流程。
     - 后端 `schemas/task.py`：`TaskDailyUpdateResponse` 增加 `photos: list[TaskPhotoUploadResponse]`。
     - 后端 `routers/tasks.py`：`create_daily_update` / `list_daily_updates` 用 `joinedload` 预载 photos；新增 `GET /tasks/task-photos/{photo_id}/url` 返回 presigned URL。
     - 前端 `DailyUpdateHistory.tsx`：新增 `TaskPhotoThumb`，历史记录渲染已持久化照片。
- **运行过的验证**：`python -m py_compile` 后端改动文件 → OK；`npx tsc --noEmit` 前端 → 无新增错误（仅历史 number→string 噪音，Vite 构建忽略）。
- **复核排除的误报**：审计曾称 `customer.email`「静默丢失」，但通读 `models/customer.py`、`schemas/customer.py`、`CustomerForm.tsx` 确认 email 字段根本未实现（非接线错配），无需修。
- **已知风险或未解决问题**：
  - ✅ **live e2e 已于 2026-08-17 跑通**（见下「e2e 真机验证」会话）。照片持久化由静态验证升级为端到端验证。
  - 前端历史类型错误（ProjectTabs/TaskItem/PhotoUploader taskId:number→string 等）仍为噪音，不影响构建。
- **下一步最佳动作**：
  1. ✅ 已完成：启动栈跑 live e2e（建项目→建任务→每日更新带图→历史可见图→预览 URL）。
  2. `supervision-refresh`：子 Tab 写操作后改用 `invalidateQueries` 统一刷新。
  3. `brokerage-404-ux`：8 子资源未创建返 200+null。

---

### 2026-08-17 · e2e 真机验证（本轮）

- **目标**：用户确认 Docker Desktop 已开，跑真实端到端测试，闭合 `daily-update-photo-persist` 与 `planned_end_date` 两项修复。
- **环境**：`docker compose up -d postgres redis minio backend frontend ai-service`；后端镜像需重建（`docker compose build backend`，代码烘焙进镜像非 bind-mount）；默认管理员 `admin/admin123` 由 `seed_admin_user` 注入。
- **回归测试脚本**：仓库根 `e2e_smoke.sh`（login→建 supervision 项目→建任务带 `planned_end_date`→建每日更新→传真实 PNG→列表 round-trip→取 presigned URL），全程零 mock。
- **结果**：ALL E2E CHECKS PASSED。
  1. ✅ Fix1 `planned_end_date`：POST 任务返回 `planned_end_date=2026-09-01`，确认不再静默丢失。
  2. ✅ Fix2 照片持久化全链路：上传返回 `storage_key`；GET 列表 `photos[]` 命中；GET `/task-photos/{id}/url` 返回 322 字符 presigned URL。
- **e2e 暴露并修复的 2 个后端缺陷**（均为本轮回填验证时发现，已重建镜像）：
  1. `routers/tasks.py` `create_daily_update` / `list_daily_updates`：`joinedload(TaskDailyUpdate.photos)` 后 `.scalar_one()` 与 `.scalars().all()` 未加 `.unique()` → SQLAlchemy `The unique() method must be invoked...` 500。改为 `await db.refresh(update, ["photos"])` 与 `result.unique().scalars().all()`。
  2. `dependencies.py` `get_minio_public_client`：未 pin region，`presigned_get_object` 在容器内解析 bucket region 时连接 `localhost:9000`（容器内不可达 MinIO）→ 500。已加 `region="us-east-1"`（MinIO 默认，与 `make_bucket` 一致），签名变为纯本地、URL host 仍保留 `MINIO_PUBLIC_ENDPOINT` 供浏览器访问。
- **善后**：e2e 创建的测试项目(3-7)/任务(1-5)/照片(1-3)已通过 DELETE 接口清理，dev 库无残留。

---

### 2026-08-17 · 修复剩余 4 个 not_started 功能 + 全量 e2e（本轮）

- **目标**：用户要求修复全部 4 个剩余 `not_started` 功能，且每个都必须 live e2e 通过才停。
- **已完成（4/4 全部 passing + e2e 通过）**：
  1. `supervision-refresh`：前端 `routes/supervision/$id.tsx` 移除无效 `setDataVersion` 状态变量，`handleDataChange` 改为对详情页真实 queryKey（`/projects/{id}`、`/tasks/projects/{id}/tasks`、`/reports/...`、`/risks/...`、`/projects`）统一 `invalidateQueries`。子 Tab 写操作后详情页（头部/统计卡/风险滚动条）立即重取。
  2. `brokerage-404-ux`：`brokerage.py` 4 个 GET（survey/commercial/contract/repair-brokerage）与 `spare_parts.py` 的 hk-signatures/invoices GET 改为 `response_model=Optional[...]` + `return None` → 未创建返回 200+null（非 404）。覆盖 6 个子资源（logistics/spare-parts 列表本就返回空数组，无需改）。
  3. `knowledge-chat-persist`：新增 `KnowledgeChatMessage` 模型 + `/knowledge/chat-messages`（GET/POST/DELETE）端点；`QAChat.tsx` 挂载从后端恢复历史、每条消息落库，localStorage 仅离线兜底。跨设备同步达成。
  4. `realtime-websocket`：新增 `app/ws.py`（FastAPI 原生 WebSocket，按 `project_id` 分房间，token 鉴权）；`main.py` 挂载 `/ws/projects/{project_id}`；`tasks.create_daily_update` 触发 `manager.broadcast`；`Dockerfile` 改单 worker（进程内广播）；`lib/websocket.ts` 改为原生 WS（原 socket.io 死代码）；`$id.tsx` 订阅房间 → 收到 `daily_update_created` 即刷新+提示。
- **顺带修复的潜在缺陷（e2e 暴露）**：`project_service.generate_project_number` 原用 `COUNT+1` 生成唯一项目号，遇软删除/残留行会撞唯一约束 500；改为 `MAX(已有序号)+1`，始终大于历史最大值。
- **验证**：`e2e_all.py`（零 mock，驱动真实栈）：brokerage 6 子资源全 200+null；supervision 建任务后端点返回最新数据；WS 连接后提交每日更新收到广播事件；chat POST→GET 跨请求可回溯→DELETE 清理。**ALL E2E CHECKS PASSED ✅**。`tsc` 改动文件 0 新增错误；`vite build` 通过（1855 模块）。
- **已知环境限制**：`npm run build` 在本沙箱因 safe-delete 对 `dist` 的 trash 步骤失败（非代码问题），改跑 `npx vite build` 验证通过。
- **善后**：e2e 创建的测试项目均已 DELETE 清理（含失败轮次残留的 20 个 E2E 项目）。

---

### 2026-08-17 · harness 工程化（本轮）

- **本轮目标**：按 WalkingLabs《Learn Harness Engineering》中文模板，给整个工程补齐 harness 文档（AGENTS.md / CLAUDE.md / init.sh / PROGRESS.md / feature_list.json / session-handoff.md / clean-state-checklist.md / evaluator-rubric.md / quality-document.md）；并就「监修模块是否能用国内类 Notion 产品直接实现」给出判断。
- **已完成**：
  - 创建全部 9 个 harness 文件（见上）。
  - 通读 `功能与流程总览.md`、`监修模块组件流程.md`、`docker-compose.yml`、`start-dev.bat`、`frontend/package.json`，将真实技术栈 / 启动命令 / 已知缺口写入 harness 文档。
  - 撰写 `监修模块国内Notion替代分析.md`（功能逐一映射：哪些可用飞书多维表格 / 我来 / 语雀 / 腾讯文档等直接实现，哪些不能）。
- **运行过的验证**：目录与文件确认（Write 成功）；技术栈核对来自既有文档，未重新跑测试（本轮为文档工程，未改动业务代码）。
- **已记录证据**：9 个新文件落盘；分析文档含逐功能映射表与结论。
- **提交记录**：（待用户确认后提交）
- **已知风险或未解决问题**：
  - `feature_list.json` 中部分功能状态基于 2026-08-14 复盘文档推断，未逐条重新跑端点验证；下次会话若要做某个功能，先按 `api_field_audit.md` 复核。
  - 前端历史类型错误未清理，长期建议专项治理（不影响构建）。
- **下一步最佳动作**：
  1. 优先修 `daily-update-photo-persist`：后端 `create_daily_update` 消费 `photos` 字段并调用 `/daily-updates/{update_id}/photos` 上传 MinIO（当前照片仅前端本地预览，不持久化）。
  2. 统一子 Tab 写操作后刷新：详情页改用 `queryClient.invalidateQueries` 替代仅 bump `dataVersion`。
  3. （可选）经纪 / 修船子资源 404 → 200+null 的 UX 改善。

---

### 2026-08-14 · 数据接线修复（历史，摘要）

- **已完成**：修通 `quick-save` 前端（原整页 mock）；补周报 `generate` UI（`WeeklyReportList`）；`/users` 改为真实接口；风险标签改「自动进度检查」；删 `HKSignature/InvoiceForm/SparePhotos` 死代码。
- **证据**：`功能与流程总览.md` 第五节「复核结果」逐条记录。
- **保留缺口**：经纪子资源 404、知识库聊天仅 localStorage、WebSocket 未实现。
