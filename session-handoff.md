# session-handoff.md — 会话交接摘要

> 一轮会话结束时写，下一轮开始时读。让接手的人（或 agent）快速了解现状。
> 短会话可不写；会话长或项目有多并行区域时关键。

## 当前已验证（2026-08-17）

- 工程已完成 **harness 工程化**：根目录新增 `AGENTS.md` / `CLAUDE.md` / `init.sh` / `PROGRESS.md` / `feature_list.json` / `session-handoff.md` / `clean-state-checklist.md` / `evaluator-rubric.md` / `quality-document.md`。
- 技术栈与启动方式已固化进 `AGENTS.md`：Docker Compose 9 服务；前端构建后由 Caddy 静态托管。
- 监修模块数据接线在 2026-08-14 已修一批（quick-save、周报 UI、users、风险标签、删死代码）。

## 本轮改动

- 新增 9 个 harness 文档（本轮仅文档工程，未改业务代码）。
- 新增 `监修模块国内Notion替代分析.md`（判断监修功能能否用国内类 Notion 产品直接实现）。

## 仍损坏或未验证

- `daily-update-photo-persist`：日报每日更新照片后端未持久化（blocked）。
- 前端 `tsc --noEmit` 大量历史类型错误（不影响 `vite build`）。
- 经纪子资源 404 UX 缺口、知识库聊天仅 localStorage、WebSocket 未实现。

## 下一步最佳动作

1. 修 `daily-update-photo-persist`（最高优先级）。
2. 统一子 Tab 刷新（`invalidateQueries`）。
3. （可选）经纪子资源 200+null。

## 命令（快速参考）

- 启动（Win）：`start-dev.bat` ｜（Linux/Mac）：`bash init.sh`
- 起指定服务：`docker compose up -d postgres redis minio backend frontend ai-service`
- 后端健康：`curl -s localhost:8000/docs | head`
- 前端构建：`cd frontend && npm run build`
- 重启后端：`docker compose restart backend`
- 全量重建：`docker compose up -d --build`
