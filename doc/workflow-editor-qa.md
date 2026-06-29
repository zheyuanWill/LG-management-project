# 工作流编辑器 — 技术问答文档

> 基于代码库实际实现的客观回答。已做的标明已做，未做的标明未做。

---

## 一、项目背景类

### 1. 这个工作流编辑器解决什么业务问题？为什么不用现成的开源方案？

**业务问题：** 修船项目管理平台需要一套可视化的流程编排能力，用于定义订单/项目从创建到完成的审批、任务分配、条件路由等流程。核心场景是让管理层 (OWNER) 和项目经理 (PM) 能用拖拽方式定义流程模板，然后将模板实例化到具体订单上，逐节点推进和追踪。

**为什么不用现成方案：** 项目选择了轻量级自建方案而非 bpmn.js / Camunda 等重型工作流引擎，原因推测是：
- 业务复杂度有限，不需要完整的 BPMN 2.0 规范支持
- 需要深度集成船舶维修领域的订单、采购、结算等模型（如条件节点直接读取订单金额、项目类型等字段）
- 前端使用 React，而 bpmn.js 是原生 JS / 与 React 集成成本高
- 后端是 Python FastAPI，没有现成的 Python BPMN 执行引擎能直接用

### 2. 用户是谁？使用频率怎么样？上线后效果如何？

**用户：** RBAC 中仅 `OWNER`（管理层）和 `PM`（项目经理）角色可以访问工作流编排页面。其他角色（采购、财务、仓库）只能在订单详情页通过 `WorkflowTracker` 组件查看和推进已分配给自己的节点。

**使用频率和上线效果：** 代码中没有埋点或使用统计相关的实现，无法从代码层面判断。此外，工作流数据库表的 Alembic 迁移文件缺失（`001_initial.py` 中未包含 workflow 相关表），**说明此功能可能尚未在生产环境完整部署**。

---

## 二、数据结构类

### 3. 工作流的数据结构怎么设计的？节点和边分别怎么表示？

**已做。** 采用经典的图结构（节点 + 边），以 JSON 存储在 `workflow_templates.definition` 字段中（PostgreSQL JSON 列）。

**节点 (Node)：**
```json
{
  "id": "node-1710000000000",
  "type": "task",
  "position": { "x": 250, "y": 100 },
  "data": {
    "label": "采购审批",
    "nodeType": "approval",
    "assignee": "张经理",
    "description": "...",
    "config": {}
  }
}
```

**边 (Edge)：**
```json
{
  "id": "e-1710000000001",
  "source": "node-1",
  "target": "node-2",
  "source_handle": "condition-true",
  "target_handle": null,
  "label": "金额>10000"
}
```

支持的节点类型共 10 种：`start`、`end`、`task`、`approval`、`notification`、`milestone`、`condition`、`parallel_gateway`、`timer`、`subprocess`。

### 4. 怎么保证流程是 DAG（有向无环图），用户画了一个环怎么检测？

**部分做了，但环检测没有做。**

后端 `validate_workflow_definition()` 实现了以下验证：
- 是否有唯一的开始节点和结束节点
- 从开始节点出发的 BFS 可达性检查（不可达的节点会报错）
- 条件节点是否有完整的 true/false 分支

**但没有显式的环检测（cycle detection）。** 如果用户画了一个环（A → B → C → A），只要所有节点从开始节点可达，验证就会通过。执行阶段也没有防护措施——理论上可能导致无限循环推进。

### 5. 条件分支节点的数据结构怎么设计？支持几种条件类型？

**已做。** 条件节点使用 `CustomNode` 组件，有三个出口 Handle：
- `Bottom`（默认）
- `Right` id="true"（绿色，条件为真）
- `Left` id="false"（红色，条件为假）

条件表达式存储在 `node.data.expression` 或 `node.data.config.condition` 中，格式为字符串表达式如 `amount > 10000`。

**支持的变量（6 种）：**
| 变量名 | 含义 | 类型 |
|--------|------|------|
| `amount` | 订单金额 | number |
| `project_type` | 项目类型 | string |
| `status` | 订单状态 | string |
| `customer_name` | 客户名称 | string |
| `currency` | 币种 | string |
| `days_elapsed` | 已用天数 | number |

**支持的运算符（6 种比较 + 3 种逻辑）：** `>`、`<`、`>=`、`<=`、`==`、`!=`、`and`、`or`、`not`

后端使用 **AST 安全解析器**（`_safe_eval`），不使用 Python 的 `eval()`，防止代码注入。

### 6. 并行节点（会签/或签）怎么表示？

**部分做了。** 使用 `parallel_gateway` 节点类型表示并行网关，支持两种模式（通过 `config.mode` 区分）：

- **fork（分叉）：** 网关完成后，所有下游节点同时激活为 RUNNING
- **join（汇聚）：** 等待所有上游前驱节点完成/跳过后才激活

**会签（全部通过）语义通过 join 实现**：所有前驱节点必须完成。

**或签（任一通过）没有做。** 当前 join 逻辑硬编码为 `all_preds_done`，没有 `any` 模式的实现。

### 7. 流程数据最终存成什么格式？JSON 结构大概长什么样？

**模板定义（`workflow_templates.definition` JSON 列）：**

```json
{
  "nodes": [
    { "id": "node-1", "type": "start", "position": { "x": 250, "y": 0 }, "data": { "label": "开始", "nodeType": "start" } },
    { "id": "node-2", "type": "approval", "position": { "x": 250, "y": 120 }, "data": { "label": "经理审批", "nodeType": "approval", "assignee": "项目经理" } },
    { "id": "node-3", "type": "condition", "position": { "x": 250, "y": 240 }, "data": { "label": "金额判断", "nodeType": "condition", "config": { "condition": "amount > 50000" } } },
    { "id": "node-4", "type": "end", "position": { "x": 250, "y": 360 }, "data": { "label": "结束", "nodeType": "end" } }
  ],
  "edges": [
    { "id": "e-1", "source": "node-1", "target": "node-2" },
    { "id": "e-2", "source": "node-2", "target": "node-3" },
    { "id": "e-3", "source": "node-3", "target": "node-4", "source_handle": "condition-true" }
  ]
}
```

**实例运行状态（`workflow_instances.node_states` JSON 列）：**

```json
{
  "node-1": { "status": "COMPLETED", "label": "开始", "nodeType": "start", "completedAt": "2026-03-10T..." },
  "node-2": { "status": "RUNNING", "label": "经理审批", "nodeType": "approval", "startedAt": "2026-03-10T...", "assignee": "项目经理" },
  "node-3": { "status": "PENDING", "label": "金额判断", "nodeType": "condition" },
  "node-4": { "status": "PENDING", "label": "结束", "nodeType": "end" }
}
```

---

## 三、前端渲染类

### 8. 画布用什么技术实现的？Canvas 还是 SVG？用了什么库？为什么选它？

**已做。** 使用 **@xyflow/react (React Flow)** 库，版本 `^12.4.0`。

**底层是 SVG**（连线）+ **HTML DOM**（节点），不是 Canvas。React Flow 的渲染架构是：
- 节点是普通的 React 组件（HTML div），通过 CSS transform 定位
- 连线使用 SVG path 绘制
- 画布层使用 CSS transform 实现平移缩放

**选择原因推测：**
- React Flow 是 React 生态中最成熟的流程图库
- 原生支持自定义节点组件（直接用 Ant Design 组件）
- TypeScript 支持好
- 内置了缩放、小地图、背景网格等功能

### 9. 节点怎么渲染的？连线怎么画的？用的直线还是贝塞尔曲线？

**节点：** 自定义 `CustomNode` 组件（`memo` 优化），每种节点类型有对应的 Ant Design 图标和颜色。节点包含：
- 顶部 `Handle`（入口，`Position.Top`）
- 底部 `Handle`（出口，`Position.Bottom`）
- 条件节点额外有左侧（false，红色）和右侧（true，绿色）Handle

**连线：** 使用 React Flow **默认的贝塞尔曲线（Bezier Curve）**。代码中没有自定义 `edgeTypes`，也没有设置 `type: 'straight'` 或 `type: 'step'`，所以走的是 React Flow 默认行为——`default` 类型即贝塞尔曲线。

### 10. 画布缩放和平移怎么实现的？

**已做，但是 React Flow 内置功能，非自行实现。** 使用了 React Flow 提供的：
- `<Controls />` — 左下角的缩放按钮（+、-、fit view）
- `<MiniMap />` — 右下角的缩略图导航
- `<Background />` — 背景网格
- `fitView` 属性 — 初始加载时自动适配视口

缩放和平移是 React Flow 的核心能力，底层通过 CSS `transform: translate(x, y) scale(zoom)` 实现，鼠标滚轮缩放、拖拽平移都是内置行为。

### 11. 节点拖拽的实现原理是什么？拖拽过程中连线怎么跟着动？

**React Flow 内置能力，非自行实现。** 原理：
- 节点拖拽：React Flow 监听 `mousedown/mousemove/mouseup` 事件，实时更新节点的 `position` 属性
- 连线跟随：SVG path 的端点坐标绑定到节点 Handle 的位置，节点位置更新时连线自动重新计算路径

项目中通过 `onNodesChange` 回调接收 React Flow 的节点状态变更（包括拖拽位置变更）。

### 12. 大量节点的情况下有没有性能问题？怎么优化的？

**没有专门做性能优化。** 当前实现：
- `CustomNode` 使用了 `React.memo()` 包裹（避免无关节点重渲染）
- 使用了 `manualChunks` 将 `@xyflow/react` 单独打包

**没有做的优化：**
- 没有虚拟化渲染（React Flow 内置了视口裁剪，但没有额外配置）
- 没有节点懒加载
- 没有 Web Worker 辅助计算
- 实际场景中船舶维修流程节点数量通常在 10–30 个，不太会遇到性能瓶颈

### 13. 节点的对齐和吸附怎么做的？

**没有做。** 代码中没有使用 React Flow 的 `snapToGrid` 属性，也没有自定义对齐线或磁吸逻辑。节点可以自由放置在画布任意位置。

### 14. 撤销/重做功能有没有？怎么实现的？

**已做。** 在 `useWorkflowEditor` hook 中实现：

- **数据结构：** 使用 `useRef` 维护一个历史栈（`HistoryEntry[]`），最大深度 50 条
- **快照时机：** 每次 `addNode`、`removeSelected`、`updateNodeData`、`onConnect` 操作后调用 `pushHistory()`，用 `structuredClone()` 深拷贝当前 nodes 和 edges
- **撤销 (undo)：** `historyIndex - 1`，恢复该时刻的 nodes/edges 快照
- **重做 (redo)：** `historyIndex + 1`，恢复该时刻的快照
- **快捷键：** `Ctrl+Z` 撤销，`Ctrl+Shift+Z` 重做（在 `types.ts` 的 `KEYBOARD_SHORTCUTS` 中定义，但**快捷键绑定在 UI 层没有找到实际的 `useEffect` 监听**，工具栏上有撤销/重做按钮）

**局限：**
- 拖拽节点位置变更不会触发 `pushHistory()`，因此移动节点无法撤销
- 没有保存操作描述（history entry 只有 nodes/edges 快照）

---

## 四、交互设计类

### 15. 用户创建一个完整流程的操作流程是什么？

1. 进入 `/workflow` 页面，默认显示「流程编辑器」Tab
2. 左侧 `NodePanel` 显示可添加的节点类型（9 种），点击即可添加到画布中心
3. 在画布上拖拽节点调整位置
4. 从节点底部 Handle 拖拽到另一个节点的顶部 Handle 创建连线
5. 双击节点打开 `NodeEditDialog`，编辑节点名称、负责人、条件表达式等
6. 点击工具栏「验证」按钮，后端返回验证结果显示在 `ValidationPanel`
7. 点击工具栏「保存」按钮，弹出 Modal 填写模板名称和描述，保存到数据库
8. 在「模板列表」Tab 可以查看已保存的模板，点击「编辑」加载回画布
9. 在订单详情页可以创建流程实例，通过 `WorkflowTracker` 逐节点推进

### 16. 节点的配置面板怎么做的？不同类型节点配置项不同怎么处理？

**已做，但比较简单。** `NodeEditDialog` 是一个 Ant Design Modal，根据 `nodeType` 条件渲染不同表单项：

| 节点类型 | 可配置字段 |
|---------|-----------|
| 所有类型 | `label`（节点名称）、`notes`（备注） |
| `task` / `approval` | 额外显示 `assignee`（负责人，纯文本输入） |
| `condition` | 额外显示 `expression`（条件表达式，文本域） |

**没有做的：**
- `notification` 节点没有通知模板配置
- `timer` 节点没有延时时间配置 UI
- `subprocess` 节点没有子流程模板选择
- `parallel_gateway` 没有 fork/join 模式切换
- `milestone` 没有里程碑特定配置
- 负责人是纯文本输入，没有从用户列表下拉选择

### 17. 连线的校验规则有哪些？比如开始节点不能有入边，结束节点不能有出边？

**前端没有做连线校验。** React Flow 的 `onConnect` 回调直接调用 `addEdge`，没有任何前置校验：
- 开始节点可以有入边（不限制）
- 结束节点可以有出边（不限制）
- 同一对节点可以重复连线
- 自连接也不限制

**后端验证** 在 `validate_workflow_definition()` 中做了部分检查：
- 开始节点必须唯一
- 结束节点必须唯一
- 条件节点检查 true/false 分支完整性
- 可达性检查（从开始节点 BFS）

但**没有检查**：开始节点不应有入边、结束节点不应有出边、不允许自环等。

### 18. 流程保存前做了哪些校验？

**前端保存前不强制校验。** 保存按钮直接调用 `PUT /api/workflows/templates/{id}`，不会自动先调验证接口。

验证是**手动触发**的——用户需要主动点击工具栏的「验证」按钮，后端返回结果展示在 `ValidationPanel` 中。验证不通过时用户仍然可以保存。

**后端验证检查项（手动触发 `POST /api/workflows/validate`）：**
1. 定义不为空
2. 有且仅有一个开始节点
3. 有且仅有一个结束节点
4. 所有节点从开始节点可达（BFS）
5. 条件节点有 true/false 分支（作为 warning）

---

## 五、RBAC 权限类

### 19. RBAC 的权限模型怎么设计的？角色、权限、用户之间的关系？

**已做，是一套完整的 RBAC 系统。** 架构分三层：

**角色（5 种固定角色，非动态）：**
| 角色 | 标签 |
|------|------|
| OWNER | 老板/管理层 |
| PM | 项目经理 |
| PROC | 采购员 |
| FIN | 财务 |
| OPS | 仓库/运营 |

**权限模型：** `Resource × Action` 矩阵

- **Resource（13 种）：** order, quote, contract, procurement, supplier, product, inventory, tracking, settlement, cost, report, user, file
- **Action（8 种）：** create, read, update, delete, approve, export, view_cost, view_profit

**前后端一致：**
- 后端 `services/api/app/core/rbac.py` — `PERMISSIONS` 字典定义权限矩阵，`require_permission()` 作为 FastAPI 依赖注入
- 前端 `packages/core/src/rbac/index.ts` — 镜像同一份权限矩阵，`hasPermission()` / `getVisibility()` 函数

**用户-角色关系：** 一对一，用户表的 `role` 字段直接存储角色枚举值（不是多对多关联表）。

### 20. 工作流节点怎么跟角色绑定？一个审批节点怎么知道该谁来审？

**没有做角色绑定。** 当前实现中：

- 审批/任务节点的 `assignee` 字段是**纯文本**（如 "张经理"），在 `NodeEditDialog` 中手动输入
- 没有关联 RBAC 角色系统
- 没有用户选择器（不是从用户列表中选择）
- 没有根据 assignee 过滤"我的待办"
- 推进节点时不检查当前操作人是否是 assignee

**实际行为：** 任何有 `Resource.TRACKING + Action.UPDATE` 权限的用户都可以推进任意节点（OWNER、PM、PROC 都可以）。

### 21. 前端怎么根据权限控制按钮和页面的显示隐藏？

**部分做了。**

1. **菜单级控制（已做）：** `MainLayout.tsx` 中每个菜单项有 `roles` 数组，根据 `user.role` 过滤显示。工作流编排页仅对 OWNER 和 PM 可见。

2. **路由级控制（没有做）：** `_authenticated` 路由组只检查是否登录（有 token），不检查角色。用户直接访问 `/workflow` URL 不会被拦截。

3. **按钮级控制（没有做）：** 虽然 `packages/react-hooks` 中有 `usePermission` hook（提供 `can(resource, action)` 方法），但 **web-admin 中没有任何组件使用它**。没有 `PermissionButton` 等权限组件。

### 22. 权限数据是每次请求都拉还是登录时缓存？怎么处理权限变更？

**前端：** 权限矩阵是**硬编码在前端代码中的**（`packages/core/src/rbac/index.ts`），不需要从服务端拉取。登录后获取用户信息（含 `role` 字段），存入 Zustand store（`useAuthStore`），权限判断直接用本地 `hasPermission(role, resource, action)` 计算。

**后端：** 每次请求都从 JWT 中解析用户 → 查数据库获取当前角色 → 用 `check_permission()` 校验。

**权限变更处理：** 如果管理员修改了某用户的角色，该用户当前会话不会感知到变化（JWT 和前端缓存中仍是旧角色），需要**重新登录**才能生效。没有实时推送权限变更的机制。

---

## 六、后端执行类

### 23. 后端怎么解析前端保存的流程 JSON？用什么引擎执行？

**已做，自建轻量引擎。** 没有使用第三方工作流引擎（如 Camunda、Temporal、Airflow）。

`WorkflowService`（`services/api/app/services/workflow_service.py`）是一个单例服务，执行逻辑：

1. **创建实例时：** 读取模板的 `definition` JSON，初始化所有节点状态为 PENDING，开始节点自动标记为 COMPLETED，激活开始节点的下游节点
2. **推进节点时（`advance_node`）：** 更新目标节点状态 → 查找下游节点 → 根据节点类型自动处理：
   - `end` 节点：自动标记 COMPLETED
   - `condition` 节点：用 AST 解析器求值表达式，路由到 true/false 分支
   - `parallel_gateway` 节点：fork 模式直接通过，join 模式等待所有前驱完成
   - `timer` / `subprocess`：标记为 RUNNING（实际定时和子流程逻辑未实现）
   - 普通节点：标记为 RUNNING
3. **完成检查：** 所有节点都是 COMPLETED 或 SKIPPED 时，实例自动标记为 COMPLETED

**图遍历用邻接表 + BFS/递归**，状态持久化在 `workflow_instances.node_states` JSON 列中。

### 24. 流程执行到某个节点，怎么通知对应的审批人？

**没有做。** 当前实现中：
- 没有节点状态变更时的通知推送
- 没有邮件/站内信/WebSocket 通知
- `notification.py` 路由中没有工作流相关的通知逻辑
- `WorkflowTracker` 是**被动的**——用户需要打开订单详情页才能看到当前流程状态

### 25. 审批超时怎么处理？有没有超时自动流转？

**没有做。** 代码中的处理：
- `timer` 节点类型存在于数据模型中，`advance_node` 会将 timer 节点标记为 RUNNING 并设置 `timer_fires_at`
- 但实际的定时触发**没有实现**。代码注释写道 `"in production, schedule a Celery task"`
- Celery 任务模块中没有工作流相关的任务
- 没有超时检测的定时任务
- 没有超时自动流转或超时提醒

### 26. 流程执行中如果有人改了流程定义，正在跑的实例怎么办？

**没有做版本隔离。** 当前行为：
- 实例通过 `template_id` 关联模板
- 实例创建时会将模板的节点信息初始化到 `node_states` 中
- 模板更新时 `version` 字段会 +1，但**不会影响已有实例**（因为实例的 `node_states` 已经是创建时的快照）
- **但是**：实例推进时（`advance_node`）会重新读取模板的 `edges`（用于查找下游节点），所以如果模板定义被修改，**已有实例的自动推进逻辑可能会出错**（比如删除了某条边）

这是一个**潜在的 bug**——应该在实例中保存创建时的完整 definition 快照。

---

## 七、状态管理类

### 27. 编辑器的状态管理用的什么方案？为什么？

**使用 React Flow 内置状态 + 本地 React 状态，没有使用全局状态管理。**

| 状态 | 管理方式 |
|------|---------|
| 节点列表 (nodes) | `useNodesState`（React Flow 内置 hook） |
| 边列表 (edges) | `useEdgesState`（React Flow 内置 hook） |
| 选中节点 | `useState<Node \| null>` |
| 撤销/重做历史 | `useRef<HistoryEntry[]>` |
| 模板列表/实例列表 | React Query (`usePageQuery`) |
| Tab 切换、对话框开关 | 页面组件内 `useState` |

没有使用 Zustand 做工作流状态（项目中 Zustand 只用于 theme 和 auth）。

**原因推测：** 编辑器状态完全由画布页面持有，不需要跨组件/跨页面共享，所以 React Flow 的内置状态已经足够。

### 28. 画布状态（缩放、位置）、节点状态、选中状态是怎么组织的？

- **画布缩放和位置：** 完全由 React Flow 内部管理（`<ReactFlow>` 组件的 viewport state），未暴露到应用层
- **节点状态（位置、数据）：** `useNodesState` 管理，通过 `onNodesChange` 回调接收拖拽等变更
- **边状态：** `useEdgesState` 管理，通过 `onEdgesChange` 和 `onConnect` 更新
- **选中状态：** React Flow 内部管理 `node.selected` / `edge.selected`，同时 `useWorkflowEditor` 维护一个 `selectedNode` 用于编辑弹窗

### 29. 多个状态之间有联动怎么处理？

联动较少，主要有：
- **选中节点 → 编辑弹窗：** `onNodeDoubleClick` 设置 `selectedNode`，触发 `NodeEditDialog` 打开
- **删除节点 → 清理相关边：** React Flow 内置处理，删除节点时自动删除关联边
- **推进操作 → 审计日志刷新：** `WorkflowTracker` 中 `advanceNode` 成功后重新拉取审计日志

没有复杂的状态联动或状态机。

---

## 八、与项目其他部分的关系

### 30. 工作流编辑器怎么跟船舶维修管理平台集成的？

集成点有两个：

1. **订单详情页内嵌 `WorkflowTracker`：** 在 `routes/_authenticated/orders/$id.tsx` 中，当订单状态非 DRAFT 时，显示「工作流追踪」Card，渲染 `WorkflowTracker orderId={order.id}`

2. **条件节点读取订单上下文：** 后端 `_build_order_context()` 从订单提取 `amount`、`project_type`、`status`、`currency`、`customer_name`、`days_elapsed` 六个变量，供条件表达式求值

### 31. 维修工单的状态流转跟工作流引擎是怎么打通的？

**没有打通。** 当前实现中：
- 订单状态（DRAFT → IN_PROGRESS → COMPLETED 等）和工作流实例状态是**两套独立的系统**
- 推进工作流节点不会自动变更订单状态
- 变更订单状态不会自动推进工作流节点
- 没有 event/hook 机制将两者关联

工作流目前是一个**独立的追踪视图**，而非驱动业务状态流转的引擎。

---

## 九、技术选型对比类

### 32. 调研过哪些工作流相关的库或方案？React Flow、X6、bpmn.js 有没有对比过？

从代码和依赖来看，**直接选择了 @xyflow/react (React Flow)**，没有看到其他库的痕迹。

主流方案对比（供参考）：

| 方案 | 类型 | 优势 | 劣势 |
|------|------|------|------|
| **@xyflow/react (React Flow)** ✅ 已选 | React 流程图库 | React 原生、TypeScript、社区活跃、自定义节点灵活 | 不包含工作流执行引擎 |
| AntV X6 | 图编辑框架 | 蚂蚁金服出品、功能全面、中文文档好 | 较重、非 React 原生 |
| bpmn.js | BPMN 建模器 | BPMN 2.0 标准、可对接 Camunda | 非 React、样式定制困难 |
| Camunda | 完整工作流引擎 | 企业级、BPMN 执行、历史/监控 | Java 后端、重量级 |
| Temporal | 编程式工作流 | 可靠性强、支持长流程 | 需要 Go/Java SDK，学习曲线高 |

### 33. 如果重新做这个项目，有什么会改进的地方？

基于代码分析，以下是明确的改进点：

**数据层面：**
- [ ] 添加环检测（拓扑排序或 DFS 检测回边）
- [ ] 实例创建时保存完整的 definition 快照，避免模板修改影响运行中的实例
- [ ] 添加 Alembic 迁移文件创建 workflow 相关表

**前端层面：**
- [ ] 连线校验规则（限制开始节点入边、结束节点出边、自环）
- [ ] 保存前强制验证
- [ ] 节点对齐/吸附 (`snapToGrid`)
- [ ] 拖拽位置变更也纳入撤销历史
- [ ] Ctrl+Z / Ctrl+S 快捷键实际绑定
- [ ] 负责人从用户列表选择（而非纯文本）
- [ ] timer / subprocess / parallel_gateway 节点的配置 UI
- [ ] 使用 `usePermission` 做按钮级权限控制

**后端层面：**
- [ ] 节点推进时校验当前用户是否是 assignee
- [ ] 实现或签（any）模式的并行汇聚
- [ ] 实现 timer 节点的 Celery 定时任务
- [ ] 实现 subprocess 的子流程实例化
- [ ] 工作流节点推进时发送通知
- [ ] 工作流状态与订单状态联动
- [ ] 审批超时自动提醒/流转

---

## 附录：文件清单

| 文件 | 作用 |
|------|------|
| `apps/web-admin/src/components/workflow/types.ts` | 前端类型定义、节点常量 |
| `apps/web-admin/src/components/workflow/CustomNode.tsx` | 自定义画布节点组件 |
| `apps/web-admin/src/components/workflow/NodePanel.tsx` | 左侧节点面板 |
| `apps/web-admin/src/components/workflow/NodeEditDialog.tsx` | 节点编辑弹窗 |
| `apps/web-admin/src/components/workflow/ValidationPanel.tsx` | 验证结果面板 |
| `apps/web-admin/src/components/workflow/useWorkflowEditor.ts` | 编辑器核心 hook |
| `apps/web-admin/src/components/workflow/WorkflowTracker.tsx` | 实例追踪组件 |
| `apps/web-admin/src/routes/_authenticated/workflow.tsx` | 工作流编辑器页面 |
| `services/api/app/routers/workflow.py` | API 路由 |
| `services/api/app/services/workflow_service.py` | 业务逻辑（含执行引擎） |
| `services/api/app/models/workflow.py` | 数据库模型 |
| `services/api/app/schemas/workflow.py` | 请求/响应 Schema |
| `packages/core/src/rbac/index.ts` | 前端 RBAC 权限矩阵 |
| `services/api/app/core/rbac.py` | 后端 RBAC 权限矩阵 |
