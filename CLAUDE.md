# CLAUDE.md — LG 船舶管理 ERP

> Claude Code 根指令文件（与 `AGENTS.md` 内容一致，按 Claude 指令风格编排）。
> **每次会话开始**：先读 `PROGRESS.md` 与 `feature_list.json`，再动手。完成定义段落不可删改。

## 这是什么项目

LG 船舶管理 ERP —— 围绕「船舶修理」的全栈业务系统。
- 后端：`FastAPI` + `SQLAlchemy(async)` + `PostgreSQL(pgvector)` + `Redis` + `Celery` + `MinIO` + 独立 `AI 推理服务`。
- 前端：`Vite` + `React` + `TanStack Router/Query`，Caddy 静态托管。
- 四条业务线：**监修 / 买卖经纪 / 修船经纪 / 备件供应**；通用：客户 / 文件 / 知识库 / 随手存 / 风险 / 报表。
- 仓库根有业务文档：`功能与流程总览.md`、`监修模块组件流程.md`、`api_field_audit.md`、`business_logic_audit.md`、`recommendation.md`。

## 开工步骤（按顺序）

1. 读 `PROGRESS.md` → 取「下一轮最佳动作」。
2. 读 `feature_list.json` → 定位唯一 `in_progress` 功能；若空缺，按 `priority` 从 `not_started` 选一个。
3. 读对应业务文档，确认字段 / 流程 / 既有约束。
4. 确认环境：`docker compose ps`（Windows：`start-dev.bat`）显示 9 个服务 healthy/up。
5. 只做那一个功能，做完更新两份文件。

## 行为规则

- **一次只做一个功能**：`feature_list.json` 同时刻仅一个 `in_progress`。
- **先读后改**：避免复现已修回归（任务创建路径、日报照片持久化缺口等）。
- **范围纪律**：跨模块通用能力（MinIO / `ai_client` / JWT / pgvector）非必要不动。
- **前端改动要重建镜像**：`docker compose up -d --build frontend`；backend / ai-service 卷挂载热更新。
- **证据优先**：标记完成前必须留真实运行证据。

## ✅ 完成定义（Definition of Done）— 不可删改

功能从 `in_progress` → `passing` 必须**同时满足**：

1. 改动完成且仅落在预定范围。
2. 后端端点 `curl` / Postman 实测 2xx，响应字段对齐前端需求（`api_field_audit.md`）。
3. 前端改动经 `docker compose up -d --build frontend` 后浏览器实测可用（或 `npm run build` 通过）。
4. 基础验证通过：后端 `curl -s localhost:8000/docs` 可达；前端 `npm run build` 成功。
5. 已知接缝 / 缺口已在 `feature_list.json` 的 `notes` / `evidence` 如实记录（**不许假 passing**）。
6. 已更新 `PROGRESS.md` 与 `feature_list.json`。
7. 仓库处于「干净收尾」状态（`clean-state-checklist.md`）。

## 标准命令

- 启动（Win）：`start-dev.bat` ｜（Linux/Mac）：`bash init.sh`
- 起指定服务：`docker compose up -d postgres redis minio backend frontend ai-service`
- 后端健康：`curl -s localhost:8000/docs | head`
- 前端构建：`cd frontend && npm run build` ｜ 类型检查：`cd frontend && npm run typecheck`
- 重启后端：`docker compose restart backend` ｜ 全量重建：`docker compose up -d --build`

## 关键约束（勿重蹈）

- `GET/POST /users` 已是真实接口；用户管理唯一入口 `POST /auth/register`（仅 admin）。
- 风险「AI 自动检测」= 规则引擎，前端标签已改「自动进度检查」，勿加 LLM 进 `detect_risks`。
- 知识库 QA 聊天记录仅 `localStorage`，勿谎称后端同步。
- `lib/websocket.ts` 死代码（无 Socket.IO 服务端），勿依赖。
- 文件下载依赖 `get_minio_public_client` 公开签名，改 MinIO 需同步。
- 经纪 / 修船 8 子资源未创建返 404 是设计性 UX 缺口，非 Bug。

## 验证失败

环境未就绪时**先修基础状态再叠加新功能**，把 blocker 写入 `PROGRESS.md`。
