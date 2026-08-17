# AGENTS.md — LG 船舶管理 ERP

> **根指令文件。** Agent 每次开工前**先读此文件**，再按顺序读 `PROGRESS.md` 与 `feature_list.json`。
> 本文件定义工作规则、开工流程与「完成定义」。**完成定义段落不可删改**——它是整个 harness 最关键的部分。

## 项目一句话

LG 船舶管理 ERP：围绕「船舶修理」业务的全栈管理系统。
技术栈：`FastAPI` + `SQLAlchemy(async)` + `PostgreSQL(pgvector)` + `Redis` + `Celery` + `MinIO` + `AI 推理服务`；前端 `Vite` + `React` + `TanStack Router/Query`（Caddy 静态托管）。
四条核心业务线：**监修（supervision）**、**买卖经纪**、**修船经纪**、**备件供应**；通用能力：客户 / 文件 / 知识库 / 随手存 / 风险 / 报表。

## 开工流程（每次会话必须按顺序）

1. 读 `PROGRESS.md` → 确认「当前已验证状态」与「下一轮最佳动作」。
2. 读 `feature_list.json` → 找到唯一 `in_progress` 的功能；若没有，从 `not_started` 按 `priority` 选一个置为 `in_progress`。
3. 读相关业务文档（仓库根）：`功能与流程总览.md`、`监修模块组件流程.md`、`api_field_audit.md`、`business_logic_audit.md`、`recommendation.md`。
4. 确认环境已起：`docker compose ps` 应显示 9 个服务 healthy/up（Windows 用 `start-dev.bat`）。
5. **只处理那一个 `in_progress` 功能**。完成后更新 `feature_list.json` 与 `PROGRESS.md`。

## 工作规则

- **一次只做一个功能**：任何时刻 `feature_list.json` 只能有一个 `in_progress`。
- **先读规则再动手**：改动任何端点 / 组件前，先确认它在 `功能与流程总览.md` / `监修模块组件流程.md` 中的字段与流程，避免引入早已修过的回归（例如 `POST /tasks/projects/{id}/tasks` 路径、日报每日更新照片持久化缺口）。
- **改动范围纪律**：只在选定功能范围内改；跨模块通用能力（`MinIO`、`ai_client`、`JWT`、pgvector）非必要不动。
- **前端改动必须重建前端镜像**：`frontend` 是构建后由 Caddy 静态托管，源码改动需 `docker compose up -d --build frontend` 才生效；`backend` / `ai-service` 是卷挂载 + `--reload`，热更新无需重建。
- **证据优先**：不允许「看起来能跑就标记完成」。必须留下真实运行证据（curl 响应、测试输出、页面截图 / 录屏、构建日志）。

## 完成定义（Definition of Done）— 不可删改

一个功能只能在**同时满足以下全部条件**时从 `in_progress` 改为 `passing`：

1. 代码改动完成，且只落在预定功能范围。
2. 后端改动：相关端点经 `curl` / Postman 实测返回 2xx，且响应字段与前端需求一致（参考 `api_field_audit.md`）。
3. 前端改动：`docker compose up -d --build frontend` 后，目标页面 / 交互在浏览器实测可用（或至少 `npm run build` 通过）。
4. 已跑基础验证：后端健康检查 `curl -s localhost:8000/docs` 可达；前端 `npm run build`（`node build.js`）成功。
5. 已知接缝 / 缺口已在 `feature_list.json` 该功能的 `notes` 或 `evidence` 中如实记录（**不许假 `passing`**）。
6. 已更新 `PROGRESS.md`（会话记录 + 下一步）与 `feature_list.json`（status=passing + evidence）。
7. 仓库处于「干净收尾」状态（见 `clean-state-checklist.md`）。

## 标准命令

| 用途 | 命令 |
|---|---|
| 启动全部（Windows） | `start-dev.bat` |
| 启动全部（Linux/Mac）｜`init.sh` | `bash init.sh` |
| 启动指定服务 | `docker compose up -d postgres redis minio backend frontend ai-service` |
| 后端健康 | `curl -s localhost:8000/docs \| head` |
| 前端构建 | `cd frontend && npm run build` |
| 前端类型检查 | `cd frontend && npm run typecheck`（仅检查，不阻断构建） |
| 重启后端（热更新） | `docker compose restart backend` |
| 全量重建 | `docker compose up -d --build` |

## 关键约束（来自过往复盘，勿重蹈）

- 后端 `GET/POST /users` 已是真实接口（admin 建用户）；唯一用户管理入口是 `POST /auth/register`（仅 admin）。
- 风险的「AI 自动检测」实为**规则引擎**，前端标签已改为「自动进度检查」。不要再写 LLM 调用进 `detect_risks`。
- 知识库 QA 聊天记录仅存 `localStorage`（跨设备不同步）——已知限制，勿谎称已实现后端同步。
- `lib/websocket.ts` 是死代码（后端无 Socket.IO 服务器），勿依赖。
- 文件下载修复依赖 `get_minio_public_client` 公开地址签名；改 MinIO 配置需同步此签名逻辑。
- 经纪 / 修船 8 个子资源「未创建返回 404」是设计性 UX 缺口（建议改 200+null 或统一 `/info`），非 Bug。

## 验证失败时的行为

若 `init.sh` / `start-dev.bat` 验证失败（容器未就绪 / 端口不通），**停下来先修基础状态**，不要在坏基础上叠新功能。把 blocker 记录到 `PROGRESS.md` 的「当前 blocker」。
