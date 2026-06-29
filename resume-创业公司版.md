# 个人简历 — 全栈前端 + AI 应用开发

## 基本信息

| | |
|---|---|
| **姓名** | [你的名字] |
| **工作经验** | 1 年（前端 + AI 全栈） |
| **求职意向** | 前端开发 / AI 应用开发 / 全栈工程师 |
| **联系方式** | [手机] · [邮箱] |
| **GitHub** | [链接] |

---

## 一句话

1 年经验，独立交付过 4 个从 0 到 1 的产品（2 个 Web + 2 个 Mobile），能写 React 也能搭 AI Agent，擅长把 LLM 能力快速落地到产品中。

---

## 技术能力

**我最擅长的**：React 全家桶（React 18/19 + TypeScript + Vite）、AI 前端集成（SSE 流式对话、Tool Calling、结构化输出）、跨端开发（React Native / Expo）

**我也能做的**：Python 后端（FastAPI）、LLM 应用开发（LangChain、OpenAI/DeepSeek/Claude API）、RAG（向量数据库 + Embedding）、Docker 部署、数据库设计

**用过的技术栈**：
- 前端：React、React Native (Expo)、TypeScript、Vite、Zustand、Redux、TanStack Query、Ant Design、MUI、ECharts、ReactFlow、TipTap、Konva
- AI：LangChain、OpenAI API、DeepSeek、Claude、Gemini、Qwen-VL、ChromaDB、SSE Streaming
- 后端：Python、FastAPI、PostgreSQL、Redis、MinIO、Celery
- 工具：Git、Docker、pnpm Monorepo、GCP Cloud Run、GitHub Actions

---

## 项目经历

### 1. Flexhaul.ai — B2B 物流 SaaS 平台

> 美国本土货运平台，覆盖发货方、承运商、后台管理三个角色

**我做了什么**：

- **从 0 搭建 AI 对话系统** — 前端 React 组件（SSE 流式渲染 + Tool Call 状态卡片 + Markdown）+ 后端 Python Agent（LangChain + 多 LLM 切换）。用户在平台内随时对话查运费、追踪包裹、筛选订单
- **AI "一键填单"** — 用户粘贴一段文字或 CSV，AI 自动解析成结构化运单。单条、批量、理赔三种场景都做了
- **文本转筛选器** — 用户输入 "显示上周 FedEx 的订单"，AI 自动设置筛选条件，前端 Redux 联动更新列表
- **造了一套组件库**（FH Design System）— 30 多个组件，写了 ESLint 规则让团队只能用组件库不能直接用 MUI
- **80+ 页面代码分割** — React.lazy + Vite 手动分包，首屏加载控制在 2s 内
- **对接 Stripe 支付** — Elements + Google Pay + PayPal，从付费到结算全链路

**AI Agent 后端部分**：

- **三个 LLM 随时切** — GPT-4o、Claude 3.5、Gemini 2.0，改个环境变量就行
- **6 个业务工具** — 实时运费查询、包裹追踪、知识库搜索等，Agent 自动决策调用
- **部署在 GCP Cloud Run** — Docker 容器，自动扩缩容，运费查询延迟 <3 秒

---

### 2. LG-Management — 修船项目管理系统

> 以销定采的一体化项目管理 + 供应链系统

**我做了什么**：

- **Monorepo 一套代码三端跑** — 设计了 Transport 抽象层，Web 用 fetch、Mobile 用 Expo、小程序用 uni.request，共享 80% 的 API Client 和业务逻辑
- **拖拽式工作流编辑器** — ReactFlow 实现，10 种节点类型，支持 50 步撤销/重做，能直接导出定义提交后端
- **ECharts 全家桶** — 自定义甘特图（Custom Series renderItem）、桑基图（供应链流向）、仪表盘、漏斗图
- **金蝶 ERP 集成** — 连接状态监控、同步日志、失败重试、AI 智能诊断，做了完整的集成管理页面
- **AI 对话助手** — SSE 流式 + 工具调用（搜订单、算成本、生成报告），Web 端有全屏页面和浮动 chatbox

---

### 3. LG-Doc — 海事文档管理系统

> 船员在弱网/离线环境下填写检查文档，上线后同步生成 Word/PDF

**我做了什么**：

- **四种 AI 能力全落地** — 智能填表（DeepSeek）、文档审查（AI 打分 + 逐字段建议）、照片缺陷检测（Qwen-VL 视觉模型）、AI 对话（自己实现了 Tool Calling，没用 LangChain）
- **离线优先** — WatermelonDB 本地持久化，船员断网也能填表拍照，联网后增量同步
- **文档编辑器** — TipTap 富文本 + Konva Canvas 照片标注（画笔/箭头/矩形/文字），三种表单类型
- **冲突解决** — 乐观锁 + ConflictModal（保留本地 / 使用服务端），800ms 防抖减少冲突
- **RAG 知识库** — Chroma + DashScope Embedding，AI 填表和对话时自动检索历史文档作为参考

---

## 我能带来什么

1. **AI 产品感** — 不只是接 API，而是思考 AI 在产品中怎么用才自然。做过对话、填表、解析、审查、图像分析 5 种形态
2. **全链路交付** — 从 React 前端到 Python AI 后端到 Docker 部署，一个人能串起来
3. **跨端能力** — Web + Mobile + 小程序，一套架构覆盖
4. **快速出活** — 4 个项目 1 年内交付，习惯创业公司节奏

---

## 教育背景

| | |
|---|---|
| **学校** | [学校名称] |
| **学历/专业** | [本科/硕士] · [专业] |
| **毕业时间** | 20XX 年 |
