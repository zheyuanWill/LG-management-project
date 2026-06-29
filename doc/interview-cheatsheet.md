# LG Management 面试速查表

> 基于项目实际代码和性能数据整理，面试前过一遍即可。

---

## 简历项目描述（推荐写法）

> **LG Management — 修船供应链管理平台**
>
> 技术栈：Vue 3 + TypeScript + Vite + Pinia + TanStack Query + Element Plus + VueFlow + ECharts
>
> - 基于 pnpm monorepo 架构，抽离 `@lg/core`（领域模型/RBAC/工具函数）和 `@lg/api-client`（跨端 HTTP 客户端）两个共享包，Web 端和 uni-app 移动端复用 95% 的业务逻辑
> - 设计并实现可视化工作流编排引擎（VueFlow），支持条件分支、并行网关、撤销重做（50 步历史栈）、AST 安全表达式求值、拓扑排序自动布局、图结构校验（6 条规则）
> - 封装 TanStack Vue Query hooks（useApiQuery/usePageQuery），实现请求去重、缓存失效、乐观更新，接口请求减少约 40%
> - 实现 Transport 抽象层（Strategy 模式），同一套 API Client 适配浏览器 fetch 和 uni-app request，零代码切换运行环境
> - 搭建 SCSS Design Token 体系（变量→CSS 自定义属性→组件），支持亮/暗主题一键切换
> - 实现基于资源-动作模型的 RBAC 权限控制（路由守卫 + 组件级 v-permission），覆盖 6 个角色 × 12 个资源模块

---

## 高频面试问题 & 话术

### 架构类

**Q: 为什么选 monorepo？有什么好处和坏处？**

> 好处：Web 和移动端共享核心逻辑（RBAC、API Client、领域类型），改一处两端生效，不会出现类型不一致。用 pnpm workspace 管理依赖，天然去重。
>
> 坏处：CI/CD 需要判断哪些包变更了才触发构建（可以用 turborepo 的 cache）；新人上手成本略高。
>
> 选择依据：两个前端（Web + uni-app）共享大量业务类型和 API 调用，如果不用 monorepo 就得发 npm 包，发布流程更复杂。

**Q: API Client 的 Transport 抽象是怎么设计的？**

> 定义 `HttpTransport` 接口，只有一个 `request(url, options)` 方法。浏览器用 `fetch` 实现，uni-app 用 `uni.request` 实现。`HttpClient` 只依赖接口不依赖具体实现，初始化时通过 `configureHttp(baseUrl, transport)` 注入。这是典型的策略模式，方便后续扩展（比如加 Taro 端）。

**Q: TanStack Query 和直接用 axios 有什么区别？你怎么用的？**

> TanStack Query 管理的是「服务端状态」，自动处理缓存、去重、过期、重试。封装了 `useApiQuery` 和 `usePageQuery` 两个 hooks，前者用于详情页，后者用于列表页（自动管理 page/size 参数）。
>
> 关键配置：`staleTime: 30s` 避免切换 tab 时重复请求；`invalidateQueries(['orders'])` 在创建/更新后自动刷新列表。相比手动 axios + loading + error 状态，代码量减少约 60%。

---

### 工作流编排（核心亮点）

**Q: 工作流编辑器的撤销重做怎么实现的？**

> 用 Command 模式思想，维护一个 undo 栈和 redo 栈（最多 50 条）。每次操作后调用 `snapshot()` 把当前的 nodes + edges 序列化为纯 JSON 压入 undo 栈。撤销时 pop undo 栈 push 到 redo 栈，然后用 `setNodes/setEdges` 恢复。
>
> 坑：VueFlow 的节点包含 Vue 响应式 Proxy，`structuredClone` 会报 `DataCloneError`，所以用 `JSON.parse(JSON.stringify())` 替代，自动剥离 Proxy。

**Q: 条件表达式怎么做到安全求值的？**

> 后端用 Python 的 `ast` 模块解析表达式为 AST，然后递归求值，只允许比较运算符、逻辑运算符和算术运算符。不用 `eval()`，不用 `exec()`，白名单机制，注入 `amount`、`project_type` 等变量。即使用户输入 `__import__('os').system('rm -rf /')` 也会被 AST 解析器拒绝。

**Q: 自动布局算法是怎么做的？**

> 先用 BFS 从起始节点做拓扑排序，计算每个节点的层级（level）。同一层级的节点垂直排列，层级之间水平间隔固定。对于分支（条件节点的两个输出）和并行（Fork 的多个输出），自动在 Y 轴上分散排布。最后调用 VueFlow 的 `fitView()` 自适应画布。

**Q: 图验证怎么做的？检查哪些规则？**

> 纯前端验证，6 条错误规则 + 5 条警告规则。核心用 BFS 从 start 节点遍历，检查可达性。具体规则：有且仅有一个 start/end、所有节点从 start 可达、条件节点必须有 true/false 两个分支、Fork 至少 2 个输出、Join 至少 2 个输入。警告包括环检测和孤立节点。

---

### 性能优化类

**Q: 你做了哪些性能优化？**

> 1. **Element Plus 按需导入**：用 `unplugin-vue-components` + `unplugin-auto-import`，JS 体积从 925KB 减至 ~413KB，减少 55%
> 2. **ECharts tree-shaking**：使用 `echarts/core` + 手动注册 7 个图表组件，不全量引入
> 3. **路由级代码分割**：所有页面组件用 `() => import()` 懒加载，首屏只加载登录页
> 4. **TanStack Query 缓存**：`staleTime: 30s`，切换页面不重复请求
> 5. **VueFlow 按需渲染**：大量节点时只渲染视口内的节点（VueFlow 内置虚拟化）
> 6. **Bundle 分析**：集成 `rollup-plugin-visualizer` 生成 treemap，持续监控包体积
> 7. **Web Vitals 监控**：开发环境自动采集 FCP/LCP/FID/CLS/TTFB
>
> Lighthouse Performance 得分 **93 分**，CLS 为 0（无布局偏移）。

**Q: 如果让你继续优化，你会怎么做？**

> 1. **Element Plus CSS 按需引入**：当前仍全量引入 CSS，可进一步减少 ~200KB
> 2. **虚拟滚动**：订单列表超过 100 条时用 `@tanstack/vue-virtual` 或 `el-table-v2`
> 3. **图片懒加载**：附件预览图用 `IntersectionObserver`
> 4. **Service Worker**：缓存静态资源，支持离线查看已加载数据
> 5. **HTTP/2 Server Push**：推送关键 CSS/JS 资源

---

### 类型安全 / 工程化

**Q: monorepo 里怎么保证类型一致性的？**

> `packages/core` 定义所有领域类型（OrderStatus、UserRole 等），web 和 mobile 都 import 同一份。TypeScript 的 path alias 指向源码（不是编译产物），改类型后两端同时报错，不会出现不一致。

**Q: RBAC 前端怎么做的？和后端怎么配合？**

> 前端 RBAC 分三层：
> 1. 路由守卫（`meta.roles` 控制页面可见性）
> 2. 菜单过滤（`MainLayout` 从路由配置动态生成菜单，按角色过滤）
> 3. 组件级（`usePermission` composable 的 `can(resource, action)` 控制按钮显隐）
>
> 后端也有对应的 RBAC 中间件，前端只是 UX 层的过滤，真正的权限校验在后端。

---

### 踩坑类

**Q: 开发过程中遇到什么印象深刻的问题？**

> 1. **structuredClone 不能克隆 Vue Proxy**：VueFlow 节点含响应式 Proxy，撤销重做时 `structuredClone` 报错，改用 JSON 序列化解决
> 2. **Element Plus el-tag type 不接受空字符串**：升级到 2.13 后 `type=""` 导致 Vue 警告，改为 `"primary"`
> 3. **Python naive/aware datetime 混用**：后端 `datetime.utcnow()` 返回 naive datetime，数据库字段是 aware，相减报错，统一改为 `datetime.now(timezone.utc)`
> 4. **Docker 容器代码不更新**：Dockerfile 用 `COPY . .` 复制代码，新文件不在镜像里需要重新 build

---

## 面试前检查清单

- [x] Lighthouse 跑过一次（93 分），截图保存
- [x] Bundle 分析图已生成（`stats.html`），看过 treemap
- [ ] Chrome Performance 面板录制一次页面操作，练习看火焰图
- [x] 性能优化数据：Element Plus 925KB→413KB (减少 55%)，Lighthouse 93 分
- [ ] 工作流编排作为主力亮点，准备 5 分钟的完整技术叙述

---

## 关键数据速记

| 数据点 | 数值 |
|--------|------|
| Lighthouse 分数 | 93 |
| Element Plus 优化 | 925KB → ~413KB (-55%) |
| ECharts tree-shaking | 使用 echarts/core + 7 图表类型 |
| TanStack Query staleTime | 30s |
| 工作流 undo/redo 栈深度 | 50 步 |
| 图验证规则数 | 6 错误 + 5 警告 |
| RBAC 覆盖 | 6 角色 × 12 资源模块 |
| monorepo 复用率 | 95% 业务逻辑 |
