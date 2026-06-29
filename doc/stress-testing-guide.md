# 大数据量前端性能压测指南

> 目标：模拟数据库达到千万级数据量时，前端出现的性能瓶颈，并定位优化方向。

---

## 一、架构概览

```
┌────────────────────┐     ┌──────────────────────┐     ┌───────────────┐
│  前端压测工具        │────▶│  API (FastAPI)        │────▶│  PostgreSQL   │
│  __stress.*         │     │  + SlowQueryMiddleware │     │  10M+ rows    │
│  浏览器 DevTools     │     │  + 慢查询模拟            │     │               │
└────────────────────┘     └──────────────────────┘     └───────────────┘
```

三层协作：
1. **数据库层**：用种子脚本灌入百万级真实数据，让 SQL 查询变慢
2. **API 层**：慢查询中间件模拟真实的 IO 延迟（即使没有真实数据也能模拟）
3. **前端层**：压测工具测量 DOM 渲染、滚动帧率、内存泄漏

---

## 二、后端：批量数据种子脚本

### 2.1 位置
`services/api/scripts/seed_bulk.py`

### 2.2 使用方法

```bash
cd services/api

# 前置: 确保数据库已初始化（运行过 alembic upgrade head + seed.py）

# 1. 生成 10,000 条订单（默认，约 40,000+ 总行数）
python -m scripts.seed_bulk

# 2. 生成 100,000 条订单（约 400,000+ 总行数）
python -m scripts.seed_bulk --orders 100000

# 3. 生成 1,000,000 条订单（约 4,000,000+ 总行数，需 10-15 分钟）
python -m scripts.seed_bulk --orders 1000000

# 4. 自定义各表数量
python -m scripts.seed_bulk --orders 50000 --products 5000 --customers 1000

# 5. 清除压测数据（保留前 10 条基础 seed）
python -m scripts.seed_bulk --clean
```

### 2.3 数据比例

以 `--orders N` 为基准，自动生成关联数据：

| 表 | 数量 | 说明 |
|---|---|---|
| customers | N / 50 | 每客户平均 50 单 |
| vessels | customers × 2 | 每客户平均 2 艘船 |
| products | N / 20 | 每 20 单用到同一商品 |
| suppliers | products / 10 | |
| order_line_items | N × 3 | 每单平均 3 个行项目 |
| notifications | min(N, 100000) | |

### 2.4 性能参考

| 数据量 | 耗时 (i7 + SSD + PostgreSQL) |
|---|---|
| 10,000 订单 | ~15s |
| 100,000 订单 | ~2-3 min |
| 1,000,000 订单 | ~15-20 min |

---

## 三、后端：慢查询模拟中间件

### 3.1 位置
`services/api/app/core/middleware.py`

### 3.2 启用方法

```bash
cd services/api

# 方式 1: 环境变量启动
SLOW_QUERY_ENABLED=true uvicorn app.main:app --reload

# 方式 2: 自定义延迟范围
SLOW_QUERY_ENABLED=true \
SLOW_QUERY_MIN_MS=500 \
SLOW_QUERY_MAX_MS=5000 \
SLOW_QUERY_LIST_MULTIPLIER=3.0 \
uvicorn app.main:app --reload

# 方式 3: 只模拟列表查询慢（详情/写入不延迟）
SLOW_QUERY_ENABLED=true \
SLOW_QUERY_LIST_ONLY=true \
uvicorn app.main:app --reload
```

### 3.3 延迟策略

| 请求类型 | 延迟计算 | 模拟场景 |
|---|---|---|
| **列表查询** `GET /api/orders` | `rand(min, max) × 3.0` | COUNT(*) + JOIN + ORDER BY 千万行 |
| 列表 + 大 page size (>50) | 额外 ×1.5 | 大量数据序列化 |
| 列表 + 超大 page size (>100) | 额外 ×2.0 | 内存压力 + 传输 |
| **详情查询** `GET /api/orders/123` | `rand(min×0.5, max×0.3)` | 主键查询 + JOIN |
| **写入** POST/PUT/DELETE | `rand(min×0.2, max×0.2)` | INSERT/UPDATE |

### 3.4 响应头

中间件会在每个响应上添加以下 header，前端压测工具会自动读取：

```
X-Simulated-Delay-Ms: 1500
X-Real-Processing-Ms: 45
```

---

## 四、前端：压测工具

### 4.1 位置
`apps/web-admin/src/utils/stress-test.ts`

### 4.2 使用方法

在浏览器 DevTools Console (F12) 中输入：

```javascript
// === 快捷命令 ===

__stress.mock100()        // 100 行表格渲染
__stress.mock1k()         // 1,000 行表格渲染
__stress.mock5k()         // 5,000 行表格渲染
__stress.mock10k()        // 10,000 行表格渲染（预期卡顿）

// === 详细测试 ===

__stress.mockLargeTable(2000)                    // 自定义行数
__stress.measureApiLatency('/api/orders')         // API 延迟测量
__stress.profileTableScroll()                     // 表格滚动帧率
__stress.domStats()                               // DOM 节点统计
__stress.memoryLeakTest(10)                       // 内存泄漏检测

// === 完整套件 ===

__stress.runFullSuite()    // 运行全部测试
__stress.report()          // 输出汇总报告
__stress.cleanup()         // 清理临时 DOM
```

### 4.3 测试项说明

#### 4.3.1 mockLargeTable — 大表格渲染

测量将 N 行数据渲染为 DOM 表格的耗时：

| 指标 | 含义 | 正常范围 |
|---|---|---|
| 数据生成 | JS 生成 N 个对象的时间 | <10ms (1000行) |
| DOM 构建 | createElement + innerHTML | <100ms (1000行) |
| reflow+paint | 浏览器布局和绘制 | <200ms (1000行) |
| 总 DOM 节点数 | 页面所有元素 | <5000 正常, >10000 危险 |

**什么时候会卡？**
- 1000 行以上：reflow 开始明显
- 5000 行以上：首次渲染可感知卡顿
- 10000 行以上：严重卡顿，需要虚拟滚动

#### 4.3.2 measureApiLatency — API 延迟

- 对同一 endpoint 发送 5 次请求，计算平均和 P95
- 逐步增大 page size (20→50→100→500→1000) 测量延迟增长
- 自动读取 `X-Simulated-Delay-Ms` header（如果启用了慢查询中间件）

#### 4.3.3 profileTableScroll — 滚动帧率

- 在当前页面的 el-table 中自动滚动 3 秒
- 测量帧间隔，计算 FPS 和卡顿帧比例

| FPS | 体感 |
|---|---|
| 60 fps | 丝滑 |
| 30-60 fps | 可接受 |
| <30 fps | 明显卡顿 |
| <15 fps | 不可用 |

#### 4.3.4 memoryLeakTest — 内存泄漏

- 自动在多个路由间来回跳转
- 记录每次跳转后的 JS Heap 大小
- 增长 >50MB 则标记为潜在泄漏

---

## 五、完整压测流程

### 步骤 1: 灌入大量数据

```bash
cd services/api
python -m scripts.seed_bulk --orders 100000
```

### 步骤 2: 启动带慢查询模拟的 API

```bash
SLOW_QUERY_ENABLED=true \
SLOW_QUERY_MIN_MS=200 \
SLOW_QUERY_MAX_MS=2000 \
uvicorn app.main:app --reload
```

### 步骤 3: 启动前端

```bash
cd apps/web-admin
pnpm dev
```

### 步骤 4: 在浏览器中运行压测

1. 打开 http://localhost:3000，登录
2. F12 打开 DevTools Console
3. 执行 `__stress.runFullSuite()`
4. 查看报告

### 步骤 5: Chrome DevTools 深度分析

| 工具 | 操作 | 观察 |
|---|---|---|
| **Performance** | 录制 → 打开订单列表 → 翻页 → 停止 | 长任务(黄色块)、Layout Shift |
| **Network** | Disable cache → 刷新订单列表 | 请求瀑布图、size=1000 的响应时间 |
| **Memory** | Heap Snapshot → 切换 5 个页面 → 再拍一次 → Comparison | 对象增长 delta |
| **Performance Monitor** | 打开实时面板 → 滚动表格 | CPU 使用率、DOM 节点数实时变化 |

### 步骤 6: 模拟 Network Throttling

- DevTools → Network → Throttle → "Slow 3G"
- 观察首屏加载时间（FCP/LCP 会显著恶化）
- 测试骨架屏/loading 状态是否正常展示

### 步骤 7: 模拟 CPU Throttling

- DevTools → Performance → CPU: 4x/6x slowdown
- 打开订单列表 → 翻页 → 观察是否卡顿
- 这模拟了低端手机/旧电脑上的体验

---

## 六、预期发现的性能瓶颈

### 6.1 已确认的瓶颈

| 瓶颈 | 数据量阈值 | 现象 | 解决方案 |
|---|---|---|---|
| el-table DOM 过多 | >200 行/页 | 滚动卡顿, FPS<30 | 虚拟滚动 (`el-table-v2`) |
| 大 page size | size>100 | API 响应慢 + JSON 解析慢 | 限制 max size=100, 分页 |
| COUNT(*) 全表扫描 | >100 万行 | 列表 API 延迟 1-5s | 添加索引, 近似 COUNT |
| 频繁重渲染 | 切换 tab/筛选 | TanStack Query refetch | 增加 staleTime |

### 6.2 高数据量下的优化路径

```
发现问题                    优化手段                      效果
───────────────────────────────────────────────────────────
表格滚动卡顿    ──→    虚拟滚动 (el-table-v2)     ──→   DOM 从 N×7 降到 ~20×7
API 响应慢     ──→    数据库索引 + 分区表           ──→   查询从 2s 降到 50ms
JSON 体积大    ──→    限制字段 (select)            ──→   响应体减小 60%+
翻页闪烁       ──→    骨架屏 + 乐观更新             ──→   感知延迟降为 0
内存泄漏       ──→    组件 unmount 清理             ──→   Heap 稳定不增长
```

---

## 七、面试话术

> **Q: 如果数据库到千万级，前端会怎样？你怎么发现和解决的？**
>
> 我在项目中搭建了一套完整的前端性能压测体系：
>
> **模拟层面**：写了一个批量数据种子脚本（SQLAlchemy Core batch INSERT），可以快速灌入百万级测试数据。同时在 API 层加了一个可选的 SlowQueryMiddleware，通过环境变量开关，模拟大数据量下 SQL 查询的真实延迟。
>
> **测量层面**：在前端开发模式下注入了 `__stress` 压测工具集，包括大表格渲染测试（测 DOM reflow）、API 延迟测量（含 P95）、滚动帧率检测、内存泄漏检测。
>
> **发现的问题**：当 el-table 渲染超过 200 行时，滚动帧率从 60fps 降到 20fps 以下；page size 超过 100 后，JSON 序列化和网络传输成为瓶颈；反复切换页面会导致 JS Heap 逐渐增长。
>
> **优化方案**：
> 1. **虚拟滚动**：用 `el-table-v2` 替代大列表的 `el-table`，DOM 节点从 N×7 降到常数级
> 2. **后端索引**：在 orders 表的 status、customer_id、created_at 上加复合索引
> 3. **page size 上限**：前端限制最大 100，后端也做校验
> 4. **TanStack Query staleTime**：从 30s 调到 60s，减少不必要的 refetch

---

## 附录：组件级压测工具

### A. VueFlow 工作流编排压测

**文件**: `apps/web-admin/src/utils/stress-components.ts`

需要先导航到 `/workflow` 页面，然后在 Console 中使用：

```javascript
// 生成 N 个节点的工作流（含合理边连接）
__stress.workflow.generate(50)    // 50 节点 — 应流畅
__stress.workflow.generate(200)   // 200 节点 — 可能开始卡顿
__stress.workflow.generate(500)   // 500 节点 — 预期明显卡顿

// 性能基准测试
__stress.workflow.benchAutoLayout(200)   // 测自动布局（拓扑排序）
__stress.workflow.benchUndoRedo(200, 20) // 200 节点做 20 次 snapshot + undo
__stress.workflow.benchValidation(200)   // 200 节点图验证（BFS + DFS）
__stress.workflow.benchZoomPan()         // 缩放/平移帧率

// 完整套件（依次测试 50/100/200/500 节点）
__stress.workflow.fullSuite()
```

**生成的图结构**：
- 1 个 start + 1 个 end
- 中间节点按层排列（每层 3-5 个），混合 task/approval/condition/gateway/timer 类型
- 条件节点有 true/false 两条分支边
- 并行网关有 2-3 条输出边

**预期瓶颈**：

| 节点数 | 预期表现 | 瓶颈 |
|---|---|---|
| 50 | 流畅 | 无 |
| 100 | 基本流畅 | 自动布局 ~100ms |
| 200 | 开始卡顿 | 拖拽延迟、MiniMap 重绘 |
| 500 | 明显卡顿 | DOM 节点 >10000、snapshot 序列化慢 |
| 1000+ | 不可用 | 需要虚拟化 or 节点分组折叠 |

**面试话术**：
> VueFlow 默认会渲染所有节点的 DOM，200+ 节点时 MiniMap 成为热点（每次拖拽都重绘缩略图）。
> Snapshot (undo/redo) 使用 `JSON.parse(JSON.stringify())` 做深克隆，500 节点的序列化约需 50-100ms。
> 解决方案：1) 关闭 MiniMap；2) snapshot 防抖加长到 500ms；3) 超过 200 节点时折叠子流程为一个节点。

### B. ECharts 大数据量压测

```javascript
// 折线图/散点图大数据量测试（自动创建临时 canvas）
__stress.charts.benchLargeDataset()  // 测试 100 → 50000 数据点

// Gantt 图大量节点
__stress.charts.benchGantt(100)   // 100 节点
__stress.charts.benchGantt(500)   // 500 节点（canvas 高度 18000px+）
```

**预期瓶颈**：

| 数据量 | 折线图 | 散点图 | Gantt |
|---|---|---|---|
| 1,000 | <50ms | <50ms | <100ms |
| 10,000 | ~100ms | ~200ms | 不适用 |
| 50,000 | ~300ms | ~500ms | 不适用 |
| 500 Gantt 节点 | — | — | ~500ms, 高度溢出 |

**优化方向**：ECharts `large: true` + `sampling: 'lttb'` 对大数据量有内建优化。

### C. Kanban 看板压测

```javascript
// 生成 N 张拖拽卡片（4 列均分）
__stress.kanban.generate(200)   // 200 张卡片
__stress.kanban.generate(500)   // 500 张（预期滚动卡顿）
__stress.kanban.generate(1000)  // 1000 张

// 清理
__stress.kanban.cleanup()
```

**预期瓶颈**：
- 500+ 卡片时滚动 FPS < 30
- 每张卡片 ~5 个 DOM 节点，1000 张 = 5000 额外 DOM
- 无虚拟滚动，所有卡片都在 DOM 中
