# 个人简历 — 前端开发工程师（AI 方向）

## 基本信息

| | |
|---|---|
| **姓名** | [你的名字] |
| **工作年限** | 1 年 |
| **求职意向** | 前端开发工程师（AI 方向） |
| **联系方式** | [手机] · [邮箱] |
| **技术博客/GitHub** | [链接] |

---

## 专业技能

- **前端框架**：精通 React 18/19（Hooks、Context、Suspense），熟练使用 React Native (Expo) 开发跨端应用
- **TypeScript**：精通类型系统设计，具备复杂泛型、Discriminated Union、类型推断实战经验
- **状态管理**：精通 Zustand、Redux Toolkit、TanStack Query v5，具备服务端状态与客户端状态分离架构经验
- **UI 框架**：精通 Ant Design 5/6、MUI v6，参与过自建 Design System（FH 组件库 30+ 组件）
- **工程化**：精通 Vite 5/6 构建优化（manualChunks 分包、预构建）、pnpm Monorepo、ESLint/Prettier 规范
- **可视化**：精通 ECharts（自定义 Gantt 图、Sankey 图、仪表盘）、ReactFlow（工作流编辑器）
- **AI 前端集成**：精通 SSE 流式对话、Tool Call 可视化、多模态输入、AI 结构化解析（text-to-form/filter）
- **跨端开发**：熟练 React Native (Expo Router)，参与过 Transport 抽象层实现 Web/Mobile 代码复用
- **其他**：熟悉 Python/FastAPI、LangChain、Docker；了解 RAG、向量数据库（Chroma）、Prompt Engineering

---

## 工作经历

### 公司 A · 前端开发工程师 | 20XX.XX – 至今

> B2B 跨境物流 SaaS 平台，服务美国本土整车/零担运输，覆盖发货方、承运商、管理后台三端

#### 项目一：Flexhaul.ai 物流平台 Web 前端

**技术栈**：React 18 + TypeScript + Vite 5 + Redux Toolkit + TanStack Query + MUI v6 + Styled Components

**核心职责与亮点**：

1. **AI Chat 全链路落地**：基于 SSE（Server-Sent Events）实现全局 AI 对话组件，支持流式 Token 渲染、Tool Call 状态追踪（运行中/完成）、Markdown 富文本输出。组件按需 Lazy Load，避免 react-markdown 影响首屏加载
2. **AI 结构化解析**：实现 "粘贴文本 → 自动填充表单" 功能，将自然语言通过 AI Parse API 转换为结构化运单数据，覆盖单条创建、批量解析、理赔解析三个场景。通过 Redux `aiFilterSlice` 实现 "自然语言 → 筛选条件" 联动
3. **FH Design System 建设**：主导 30+ 业务组件封装（FHTable、FHModal、FHTextField 等），配合 ESLint 规则强制业务层与 MUI 解耦，保障组件库一致性
4. **多角色路由架构**：设计 Shipper/Carrier/Admin 三端统一 Layout + 基于角色的动态路由方案，80+ 页面通过 `React.lazy` 实现代码分割，配合 Vite `manualChunks` 将 vendor 拆分为 6 个独立 chunk
5. **Stripe 支付集成**：对接 Stripe Elements + Connect + Google Pay + PayPal，实现发货方付费、承运商结算的完整支付闭环

#### 项目二：Flexhaul AI Agent 后端

**技术栈**：Python 3.11 + FastAPI + LangChain 0.3 + OpenAI/Anthropic/Gemini

**核心职责与亮点**：

1. **多 LLM Provider 架构**：设计可切换的 LLM 抽象层，支持 OpenAI GPT-4o-mini、Claude 3.5 Sonnet、Gemini 2.0 Flash 三个模型通过环境变量热切换，无需修改代码
2. **Agent Tool Calling**：基于 LangChain `create_tool_calling_agent` 实现 6 个运输业务工具（实时运费查询、运单追踪、知识库搜索等），Tool 返回 `__action__` JSON 指令驱动前端筛选/导航行为
3. **SSE 流式输出**：通过 LangChain `astream_events` 实现 token 级流式推送，事件类型包括 text_delta、tool_start、tool_end、action、done、error，前端实时渲染
4. **部署**：GCP Cloud Run（Docker），自动扩缩容 1-10 实例，冷启动 <5s，运费查询 <3s

---

### 公司 B · 前端开发工程师 | 20XX.XX – 20XX.XX

> 修船/海事行业项目管理与文档管理系统，覆盖供应链、采购、财务、ERP 对接全流程

#### 项目三：LG-Management 修船项目管理系统

**技术栈**：React 19 + Vite 6 + TanStack Router + Zustand + TanStack Query + ECharts + ReactFlow · React Native (Expo) · pnpm Monorepo

**核心职责与亮点**：

1. **Monorepo 跨端架构**：设计 `@lg/core`（领域模型 + RBAC）、`@lg/api-client`（Transport 抽象 HTTP 客户端）、`@lg/react-hooks`（React Query 封装 + Auth Store）三层共享包，Web 和 Mobile 共享 80%+ 业务逻辑
2. **Transport 抽象层**：实现可插拔的 `HttpTransport` 接口，Web 端使用 `fetch`，uni-app 使用 `uni.request`，Expo 使用 `AsyncStorage`，一套 API Client 适配三端
3. **可视化工作流编辑器**：基于 ReactFlow 实现拖拽式工作流编排，支持 10 种节点类型（审批/条件/并行/定时器/子流程等），集成 50 步 Undo/Redo 和后端校验
4. **ECharts 复杂图表**：自定义 `renderItem` 实现甘特图（Gantt Chart），状态着色 + 时间轴缩放 + Tooltip；Dashboard 集成 Sankey 供应链流向图、漏斗图、仪表盘
5. **金蝶 ERP 集成监控**：实现集成管理全功能页面，包括连接状态监测、同步日志表格（筛选/分页/重试）、ECharts 趋势图、AI 智能诊断失败原因

#### 项目四：LG-Doc 海事文档管理系统

**技术栈**：React 19 + Ant Design 6 + TipTap 3 + Konva · React Native (Expo 54) + WatermelonDB

**核心职责与亮点**：

1. **AI 四合一集成**：落地智能填表（DeepSeek 结构化输出）、文档审查（AI 评分 + 字段级建议）、照片缺陷检测（Qwen-VL 视觉模型）、AI 对话（SSE 流式 + 自实现 Tool Calling），覆盖文档全生命周期
2. **离线优先架构（Mobile）**：基于 WatermelonDB + LokiJS 实现本地持久化，支持弱网环境下表单填写和照片标注，上线后通过 Pull/Push 增量同步
3. **文档编辑器**：集成 TipTap 富文本（6 个扩展）+ Konva Canvas 照片标注（画笔/箭头/矩形/文字），支持三种 Group 类型（表格/数据网格/照片组）
4. **乐观锁冲突解决**：通过 `version_int` 实现乐观锁，409 冲突时弹出 ConflictModal 让用户选择 "保留本地" 或 "使用服务端"，配合 800ms 防抖减少冲突概率
5. **RAG 语义搜索**：后端基于 Chroma + DashScope text-embedding-v3 实现文档向量化，AI 填表和对话时自动检索历史相似文档作为上下文

---

## 技术亮点总结

| 亮点 | 难度 | 描述 |
|------|------|------|
| SSE 流式 AI 对话 + Tool Call 可视化 | ⭐⭐⭐⭐ | 两个项目均实现，覆盖 Web + Mobile 双端，含多模态输入和 Markdown 渲染 |
| 多 LLM Provider 热切换 | ⭐⭐⭐⭐ | OpenAI/Anthropic/Gemini 统一抽象，环境变量切换，兼容不同模型 Tool Calling 差异 |
| Monorepo 跨端 Transport 抽象 | ⭐⭐⭐⭐ | 一套 API Client 适配 Web (fetch) / Mobile (Expo) / uni-app 三端 |
| ReactFlow 可视化工作流 | ⭐⭐⭐⭐ | 10 种节点、50 步历史记录、拖拽创建、后端校验 |
| 离线优先 + 乐观锁冲突解决 | ⭐⭐⭐⭐⭐ | WatermelonDB 本地持久化 + Pull/Push 增量同步 + 版本冲突 UI |
| ECharts 自定义 Gantt | ⭐⭐⭐ | Custom Series renderItem，动态高度，时间轴缩放 |
| AI 结构化解析 (Text→Form) | ⭐⭐⭐ | 自然语言转结构化数据，覆盖物流运单、海事文档、保险理赔 |
| Design System 建设 | ⭐⭐⭐ | 30+ 组件 + ESLint 规则强制解耦 |

---

## 教育背景

| | |
|---|---|
| **学校** | [学校名称] |
| **学历/专业** | [本科/硕士] · [专业] |
| **毕业时间** | 20XX 年 |
