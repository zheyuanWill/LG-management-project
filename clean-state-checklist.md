# clean-state-checklist.md — 收尾检查清单

> 每次会话结束前逐项检查，确保仓库处于「下一轮可直接开工」的状态。
> agent 的收尾流程也应包含这些检查。

## 关掉会话前逐项检查

- [ ] **标准启动路径还能用**：`docker compose up -d`（或 `start-dev.bat`）能拉起 9 个服务，无报错。
- [ ] **标准验证还能跑**：后端 `curl -s localhost:8000/docs` 可达；前端 `cd frontend && npm run build` 成功。
- [ ] **进度日志已更新**：`PROGRESS.md` 的「当前已验证状态」与本轮「会话记录」已填写。
- [ ] **功能清单真实**：`feature_list.json` 中 `passing` 与未验证边界一致，**没有假 passing**；`in_progress` 至多一个。
- [ ] **没有半成品处于未记录状态**：任何未完成的改动都在 `feature_list.json` 的 `notes` / `evidence` 或 `PROGRESS.md` 中说明。
- [ ] **下一轮不需人工修复即可继续**：新会话仅凭仓库内文件（`AGENTS.md` + `PROGRESS.md` + `feature_list.json` + 业务文档）即可推进。
- [ ] **没有误提交**：未 `git add` 临时文件 / 密钥；`.env`、`.workbuddy/` 未被误纳入。

## 额外提醒（本项目）

- 前端改完务必 `docker compose up -d --build frontend`，否则 Caddy 仍服务旧 dist。
- backend / ai-service 是卷挂载 + `--reload`，改完无需重建，但确认 `--reload` 已热更新（看容器日志）。
- 若本轮动了 MinIO 签名逻辑，确认 `get_minio_public_client` 与下载/预览端点一致。
