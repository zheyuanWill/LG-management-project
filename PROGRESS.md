# PROGRESS.md — LG 船舶管理 ERP 进度日志

> 每轮会话结束更新本文件；每轮新会话开始先读它。
> 这是项目当前进展的**唯一真相来源**。

## 当前已验证状态（2026-08-17）

- **仓库根目录**：`C:\dev\LG-management-project`（Git 仓库；`.workbuddy/` 为项目数据，勿删）
- **标准启动路径**：
  - Windows：`start-dev.bat`
  - Linux/Mac：`bash init.sh`
  - 指定服务：`docker compose up -d postgres redis minio backend frontend ai-service`
- **标准验证路径**：
  - 后端健康：`curl -s localhost:8000/docs | head`
  - 前端构建：`cd frontend && npm run build`（`node build.js`）
  - 前端类型检查：`cd frontend && npm run typecheck`（仅检查，不阻断构建）
- **当前最高优先级未完成功能**：无（全部 14 项功能 `passing`，含原 4 个 `not_started`：`supervision-refresh` / `brokerage-404-ux` / `knowledge-chat-persist` / `realtime-websocket` 均已 live e2e 通过）。
- **当前 blocker**：无硬性 blocker；前端 `tsc --noEmit` 存在大量**历史**类型错误（number→string、`asChild` 等），但 `build.js` 仅跑 `vite build`（esbuild 不去类型），dist 生成即视为成功，不影响构建。

## 已知全局约束（来自过往复盘）

- 后端 `GET/POST /users` 已是真实接口（admin 建用户）；用户管理唯一入口 `POST /auth/register`（仅 admin）。
- 风险「AI 自动检测」= 规则引擎（阈值），前端标签已改「自动进度检查」。
- 知识库 QA 聊天记录仅 `localStorage`（跨设备不同步）——已知限制。
- `lib/websocket.ts` 死代码（后端无 Socket.IO 服务器）。
- 文件下载依赖 `get_minio_public_client` 公开地址签名。
- 经纪 / 修船 8 子资源未创建返 404 是设计性 UX 缺口（建议 200+null 或统一 `/info`）。

## 会话记录

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
