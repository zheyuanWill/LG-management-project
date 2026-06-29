# LG Management - 修船项目管理 & 供应链系统

> 以销定采的一体化项目管理 & 供应链系统，支持 PC Web 管理端 + 移动 App（H5/小程序/App）

## 🚀 快速开始

### 一键启动（Docker Compose）

```bash
# 1. 克隆项目
git clone <repo-url>
cd LG-management

# 2. 启动所有服务
cd infra
docker-compose up -d

# 3. 等待服务启动完成（约2-3分钟）
docker-compose logs -f api
```

启动完成后访问：
- **Web 管理端**: http://localhost
- **移动端 H5**: http://localhost:8080
- **API 文档**: http://localhost:8000/docs
- **MinIO 控制台**: http://localhost:9001 (minioadmin/minioadmin123)

### 分开启动（开发模式）

#### 1. 启动基础设施
```bash
cd infra
docker-compose up -d postgres redis minio minio-init
```

#### 2. 启动后端 API
```bash
cd services/api
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
pip install -r requirements.txt

# 创建数据库表
alembic upgrade head

# 初始化种子数据
python -m app.db.seed

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 3. 启动前端 Web Admin
```bash
# 安装依赖（项目根目录）
pnpm install

# 启动开发服务器
pnpm --filter web-admin dev
```

#### 4. 启动移动端（H5）
```bash
cd c:\dev\LG-management; pnpm --filter web-admin dev
pnpm --filter mobile-app dev:h5# 安装依赖
pnpm install

# 构建共享包
pnpm build:packages

# 运行 web-admin (localhost:5173)
pnpm dev:web

# 运行 mobile-app H5 (localhost:5174)  
pnpm dev:app
```

## 👥 测试账号

| 角色 | 用户名 | 密码 | 权限说明 |
|------|--------|------|----------|
| 老板 | owner | 123456 | 全部权限，可审批结项 |
| 项目经理 | pm | 123456 | 订单管理、报价、合同、跟单 |
| 采购员 | proc | 123456 | 采购单创建、供应商管理 |
| 财务 | fin | 123456 | 回款/付款录入、成本核算 |
| 仓库 | ops | 123456 | 收货、发货、库存管理 |

## 📁 项目结构

```
LG-management/
├── apps/
│   ├── web-admin/          # PC Web 管理端 (Vue3 + Element Plus)
│   └── mobile-app/         # 移动端 (uni-app)
├── packages/
│   ├── core/               # 共享核心库 (类型、枚举、工具)
│   └── api-client/         # API 客户端 SDK
├── services/
│   └── api/                # 后端 API (FastAPI + SQLAlchemy)
└── infra/                  # Docker 配置
```

## 🔧 核心功能

### Phase 1: 订单 + 报价 ✅
- 订单 CRUD，支持多明细行
- 报价版本管理，状态流转
- 客户/船舶管理

### Phase 2: 合同 + 采购 + 库存 ✅
- 合同管理，回款计划
- 采购单审批流程
- 库存批次管理，预留/出库

### Phase 3: 跟单模板 + 节点推进 ✅
- 按项目类型配置节点模板
- 一键从模板初始化跟单节点
- 节点状态推进，附件上传

### Phase 4: 回款/付款 + 结项 + 成本核算 ✅
- 回款/付款记录管理
- 结项申请与审批
- 订单成本利润核算

### Phase 5: 移动端离线上传 ✅
- 拍照/选择图片
- 离线缓存队列
- 网络恢复自动同步

## 🔐 RBAC 权限

后端强校验，前端 UI 差异化显示：

| 功能 | OWNER | PM | PROC | FIN | OPS |
|------|-------|-----|------|-----|-----|
| 订单管理 | ✅ | ✅ | ❌ | 👁️ | 👁️ |
| 报价管理 | ✅ | ✅ | ❌ | ❌ | ❌ |
| 合同管理 | ✅ | ✅ | ❌ | 👁️ | ❌ |
| 采购管理 | ✅ | 审批 | ✅ | ❌ | 👁️ |
| 库存管理 | ✅ | 👁️ | 👁️ | ❌ | ✅ |
| 回款录入 | ✅ | ❌ | ❌ | ✅ | ❌ |
| 结项审批 | ✅ | ❌ | ❌ | ✅ | ❌ |

## 💰 多币种支持

- 支持币种：CNY、USD、EUR、JPY、HKD
- 汇率管理：每日维护汇率表
- 自动折算：外币金额自动折算人民币

## 📎 附件系统

- 存储：MinIO 对象存储
- 上传：预签名 URL 直传
- 支持类型：合同、采购单、跟单节点、发票等

## 📱 移动端特性

- 离线拍照：照片本地缓存
- 同步队列：网络恢复自动上传
- 进度显示：实时上传进度
- 重试机制：失败自动重试

## 🔄 API 测试

使用 `services/api/requests.http` 或导入 Postman：

```http
### 登录
POST http://localhost:8000/api/auth/login
Content-Type: application/json

{
  "username": "owner",
  "password": "123456"
}

### 获取订单列表
GET http://localhost:8000/api/orders
Authorization: Bearer {{token}}
```

## 📦 数据初始化 (Seed)

> 以下命令在 Docker 服务启动后执行。如果是分开启动（开发模式），在后端 venv 中直接运行即可。

### Step 1: 数据库迁移 + 基础种子数据

```bash
# Docker 模式
docker exec lgm-api alembic upgrade head
docker exec lgm-api python -m app.db.seed

# 开发模式
cd services/api
alembic upgrade head
python -m app.db.seed
```

基础 seed 创建：5 个角色账号（owner/pm/proc/fin/ops，密码均为 123456）、示例客户、船舶、商品、供应商、跟单模板。

### Step 2: 生成历史项目数据（AI 功能依赖）

```bash
# Docker 模式
docker exec lgm-api python -m scripts.seed_historical

# 开发模式
cd services/api
python -m scripts.seed_historical
```

生成 30+ 条历史订单，关联报价单、合同、付款计划、跟单节点，覆盖备件采购/技术服务/物资供应等项目类型。AI Agent 的搜索订单、成本计算、报告生成等工具依赖这些数据。

### Step 3: 批量压测数据（可选）

```bash
# 生成 10,000 条订单（含关联数据）— 用于前端性能压测
docker exec lgm-api python -m scripts.seed_bulk --orders 10000

# 清除压测数据（保留基础 seed）
docker exec lgm-api python -m scripts.seed_bulk --clean
```

### AI 功能环境变量

在 `infra/.env` 中配置（或 Docker Compose environment 中直接设置）：

| 变量 | 说明 | 示例 |
|------|------|------|
| `DEEPSEEK_API_KEY` | DeepSeek API Key | `sk-xxx` |
| `DEEPSEEK_BASE_URL` | API 地址（可选） | `https://api.deepseek.com/v1` |
| `DEEPSEEK_MODEL` | 模型名称（可选） | `deepseek-chat` |
| `DASHSCOPE_API_KEY` | 阿里云 DashScope Key（可选，用于 Embedding） | `sk-xxx` |

## 🤖 AI 功能

- **AI Agent**：LangChain 0.3 + 4 个工具（搜索订单、项目详情、成本计算、报告生成），自然语言驱动多步操作
- **成本估算**：基于历史同类项目数据 + DeepSeek 智能分析报价
- **AI Chat Panel**：全局浮动按钮，SSE 流式输出 + Tool Calling 可视化 + 多模态输入

## 📝 开发说明

### 添加新的数据库模型
```bash
cd services/api
# 创建迁移
alembic revision --autogenerate -m "add xxx table"
# 执行迁移
alembic upgrade head
```

### 构建生产镜像
```bash
cd infra
docker-compose build
```

## 🐛 常见问题

**Q: 数据库连接失败**
A: 确保 PostgreSQL 已启动，检查 DATABASE_URL 配置

**Q: MinIO 上传失败**
A: 确保 MinIO 服务已启动，bucket 已创建

**Q: 移动端无法访问 API**
A: 检查 manifest.json 中的 API 地址配置
cd d:\LG-management
docker-compose -f infra/docker-compose.yml --env-file infra/.env up -d

cd d:\LG-management
pnpm dev:web
KINGDEE_ENABLED=true
KINGDEE_CLIENT_ID=你的应用ID（如 336930）
KINGDEE_CLIENT_SECRET=你的应用密钥
KINGDEE_APP_KEY=应用集成的 AppKey
KINGDEE_APP_SECRET=应用集成的 AppSecret
KINGDEE_INSTANCE_ID=实例ID（outerInstanceId）
KINGDEE_SID=账套ID
KINGDEE_DB_ID=数据库ID（通常和 SID 相同）
MIT
