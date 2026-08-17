# quality-document.md — 代码库质量快照

> 给每个产品领域与架构层打分，跟踪代码库随时间是变强还是变弱。
> 与 `evaluator-rubric.md` 不同：rubric 评「单轮 agent 输出」，本文评「代码库本身」。
> 更新时机：每轮重要会话后、做基准对比前、做清理/简化后、换 agent/模型时。

## 评级刻度

- 验证状态：`verified` / `partial` / `unverified`
- 可读性（Agent 友好度）：`good` / `fair` / `poor`
- 测试稳定性：`stable` / `fragile` / `none`
- 关键缺口：自由描述

## 产品领域快照（2026-08-17）

| 领域 | 验证状态 | Agent 可读性 | 测试稳定性 | 关键缺口 |
|---|---|---|---|---|
| 监修主表/详情 | verified | good | none | 子 Tab 刷新接缝 |
| 任务管理 | verified | good | none | 每日更新照片未持久化 |
| 日报（HITL） | verified | good | none | — |
| 周报 | verified | good | none | — |
| 风险（规则引擎） | verified | good | none | 标签已纠正，勿加 LLM |
| 知识库 RAG | verified | good | none | 聊天仅 localStorage |
| 随手存 | verified | fair | none | OCR 默认关闭 |
| 用户管理 | verified | good | none | — |
| 备件/物流 | verified | good | none | 死代码已删 |
| 经纪/修船 | partial | fair | none | 子资源 404 UX 缺口 |
| 实时推送 | unverified | poor | none | 后端无 WS 服务，死代码 |

## 架构层快照（2026-08-17）

| 层 | 边界执行 | Agent 可读性 | 备注 |
|---|---|---|---|
| backend（FastAPI routers/services） | good | good | 卷挂载热更新 |
| ai-service（chat/embed/ocr） | good | good | mock provider 默认，可接 ollama/cloud |
| frontend（Vite/React） | fair | fair | 历史类型错误多，不影响构建 |
| infra（docker-compose/Caddy/MinIO） | good | good | 镜像源已配国内镜像 |
| Celery（worker/beat） | good | fair | 任务出错返回 failed，需轮询 |

## 趋势判断

- **变强**：2026-08-14 修通一批数据接线回归；2026-08-17 补齐 harness 工程化（可观测/可交接）。
- **待加强**：测试稳定性全为 none（无自动化测试，仅靠手动 curl/构建）；前端历史类型债务；实时能力缺失。

## 与 harness 简化的关系

每个 harness 组件编码一个假设——「模型做不到这件事」。模型变强后假设可能过时。验证某组件是否多余：拍快照 → 移除组件 → 跑基准 → 再拍快照 → 对比（评级未降则多余，降则恢复）。
当前 harness 组件（9 个文档）体量轻、零运行时成本，暂无裁剪必要。
