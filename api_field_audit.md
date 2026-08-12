# API 返回结果 & 字段完整性审计报告

> 依据：`api_test_report.md`（84 请求全量回放，65 OK / 19 非 2xx）+ 后端 `routers/` `schemas/` 源码核查 + 线上复测。
> 目标：判断"哪些 404 是真 bug、哪些只是集合编排噪音"，并逐个接口核对**返回字段是否完整**。前端重构方案仅作字段需求参考。

---

## 0. 结论速览（TL;DR）

- **19 个非 2xx 中，18 个不是后端 bug**，全是集合编排问题（GET 先于 CREATE、硬编码 ID、单一 `project_id` 变量被覆盖、幂等 409、限流 403）。
- **唯一暴露出来的"真·字段缺陷"是 `/files/upload` 不返回 `id`** —— 这直接导致你看到的大量"文件不存在"：前端上传后拿不到 id，后续 download/preview/delete 全废。
- **影响前端落地、但属于"设计层缺口"（不是 500/404 崩溃）的还有 6 处**：项目列表/详情缺客户与风险聚合、子资源 GET 一律 404（而非返回空）、`/auth/me` 无 phone、知识库文档无下载端点、风险无聚合 summary、任务无 note/photos。
- 上一轮已修复的 3 个崩溃类 bug（Celery 事件循环、日报列表 ValidationError、知识库删除 FK）**保持已修复**。

---

## 1. "文件不存在 / xxx不存在" 究竟是不是 bug？

| # | 接口 | 现象 | 真实原因 | 结论 |
|---|------|------|----------|------|
| 82/83/84 | 文件 download/preview/delete | 404「文件不存在」 | 集合硬编码 `file_id=1`，且**上传响应没返回 id**（见 §3.1），前端无从引用 | **暴露真缺陷** |
| 39/43/46/48/52/60/63 | 调研/商务/合同/修船经纪/备件/HK签收/发票 GET | 404「xxx不存在」 | 集合执行顺序是"先 GET 探测后 CREATE"，首跑资源尚未建；部分是硬编码 ID | 集合噪音，但引出 §3.2 设计问题 |
| 13 | GET 项目详情 | 404「项目不存在」 | **线上复测为瞬时假象**：uvicorn `--reload` 在中途重启，同一 id=36 的 `/stats` 紧接着返回 200，重复 3 次 detail 均 200 | **非 bug** |
| 17/51 | 移交监修 | 400/404 | 单一 `project_id` 变量被 4 次建项目覆盖，最终指向监修项目，接口要求修船经纪 | 集合噪音（后端校验正确） |
| 23 | 创建任务每日更新 | 404 | 集合 URL 写成 `/tasks/tasks/{id}/daily-updates`（路径重复 tasks）；真实路由已单独验证可用 | 集合 bug |
| 25/38/59 | 删照片/解决风险/更新物流节点 | 404 | 硬编码 `photo_id=1` / `risk_id=1` / `logistics_id=1`，非本次运行创建 | 集合噪音 |
| 4 | 注册用户 | 409 | `newuser` 已存在（重复运行），幂等拒绝 | 后端正确 |
| 24 | 上传进度照片 | 403 | 每任务每日限 2 张，前序运行已累计 | 后端正确 |

**小结**：你截图里满屏的"不存在"绝大多数是"GET 跑在 CREATE 前面"或硬编码 ID 造成的，**不代表接口坏掉**。但有两个真实尾巴必须修：①上传不返回 id；②子资源"没数据就 404"的设计会让前端每个 Tab 首屏必红（见 §3.2）。

---

## 2. 实测确认：GET /projects/{id} 详情正常

```
pid=37 → detail HTTP 200（重复 3 次均 200），stats HTTP 200
```
报告里的 #13 404 是测试过程中我改后端触发 `--reload` 的瞬间窗口，**不要据此去改 projects 路由**。

---

## 3. 影响前端可用性的真实字段缺口（按严重度排序）

### 3.1 【严重】`POST /files/upload` 不返回 `id`
- **证据**：上传响应 `{"file_name","file_type","storage_key","file_size","mime_type"}` —— **没有 `id`**。而 `FileResponse`（列表）包含 `id`，`download/preview/delete` 全部以 `file_id`（整型主键）为入参。
- **后果**：前端上传成功却拿不到 id，永远无法 download/preview/delete 自己刚传的文件。这是"文件不存在"连锁反应的真正根因（叠加硬编码 ID）。
- **修复（一行 schema）**：在 `schemas/file.py` 的 `FileUploadResponse` 加 `id: int`（从 `save_file_record` 返回的 `file_record.id` 填入）。同时建议顺手返回 `id` 对应的可直接打开的 `url` 或至少保留 `storage_key` 供前端调试。

### 3.2 【设计】8 个子资源 GET 一律 404（而非 200/空）
调研信息、商务信息、合同(MOA)、修船经纪信息、备件详情、物流节点、HK 签收单、发票 —— 每个都是独立子表 + 独立 GET，未创建时返回 404「不存在」。
- **问题**：① RESTful 上"404 = 资源不存在"没错，但前端**无法区分"该项目的这类信息还没填"和"接口炸了"**；②项目详情页每个 Tab 首屏必 404，体验差且易误报。
- **建议（二选一）**：A. 这些 GET 改为"未找到返回 200 + `null`"；B. 按前端方案做**统一 `/projects/:id/info` GET/PUT**，内部按 type 映射到各子表，前端只用一套端点。方案 B 同时解决 §3.3/§3.4。

### 3.3 【重要】`GET /projects`（列表）缺前端卡片必需字段
当前返回 `ProjectResponse` 原样字段：`id, project_no, type, status, ship_name, imo, owner_id, planned_completion_date, actual_completion_date, remarks, created_at, updated_at`。
- **缺**：`customerName`（船东名，`owner_id` 只是数字，无 join）、`customerPhone`、`riskSummary`（"等料1项·延期2天"）、`hasUnconfirmedReport`（卡片右上小红点）、任何聚合计数。
- **后果**：项目列表卡片按方案要做"船东 + 风险摘要 + 红点"，现在**一个都拿不到**，要么 N+1 调客户接口，要么拿不到。这是方案里"统一项目列表接口"要解决的头等大事。

### 3.4 【重要】`GET /projects/{id}` 详情缺聚合
详情顶部要"项目 + 客户 + 船东电话 + 风险摘要/详情"，当前只返回裸 `ProjectResponse`，同样没有客户信息与风险聚合。建议与 §3.3 一并做聚合视图。

### 3.5 【次要】`GET /auth/me` 无 `phone`
返回 `id, username, display_name, role, created_at`。方案需要 `phone` 来做**总经理权限判断**和**点击拨号**。核查 `models/user.py`：**User 模型根本没有 phone 字段**。要么加字段，要么总经理判断改用 role（已有）+ 单独通讯录。

### 3.6 【次要】知识库文档不走 files 表，且无下载端点
`KnowledgeDocument` 直接存 `file_key`（MinIO key），`routers/knowledge.py` 只有 upload/list/get/delete/qa，**没有 `/download`/`/preview`**。方案里知识库预览想用 `/files/:id/download`，但该文档**不是 files 表的行**，调不通。需补知识库专用下载端点，或把文档也归入 files 表统一管理。

### 3.7 【次要】风险无聚合 `summary` 字段
`/risks`、`/projects/{id}/risks` 返回 `RiskEventResponse[]`（原始事件：`id, project_id, title, detail, risk_level, resolved, created_at`）。没有"等料1项·延期2天"这种**一行聚合字符串**供卡片红点/摘要。要么前端聚合，要么新增 `/projects/{id}/risk-summary` 返回 `{summary, detail}`。

### 3.8 【次要】日报"今日完成事项"不自动派生
`DailyReportResponse` 的 `completed_items` 是自由 dict/list，`tomorrow_plan`/`risk_alert` 由前端直接写。方案卡片要的"今日完成 = 遍历 tasks 中 status=COMPLETED 且 actual_end=today"**没有专门 GET 派生**（对应方案第二梯队的 `/reports/today`）。当前日报接口字段齐全，缺的是这个聚合入口。

### 3.9 【次要】任务缺 `note` / `photos` 字段
`TaskResponse` 返回 `id, name, planned_end_date, project_id, sort_order, status, created_at, updated_at` —— **无 `note`、无 `photos`**。方案里 `/tasks/:id` PATCH 要传 `{status, note, photos:[fileId]}`，备注和照片**无法落库**。需给 Task 模型加 `note` 和 `photos`（关联 file id 数组）字段。

---

## 4. 逐接口字段完整性核查表

图例：✅ 字段完整可用 ｜ ⚠️ 字段可用但缺前端需要的聚合/关联 ｜ ❌ 缺关键字段 ｜ 🔧 占位未实现 ｜ (编排) 非 2xx 属集合噪音

| # | 接口 | 状态 | 返回关键字段 | 完整性 |
|---|------|------|--------------|--------|
| 1/2 | health | 200 | status, database/version | ✅ |
| 3 | 登录 | 200 | access_token, token_type | ✅ |
| 4 | 注册 | 201 | id, username, display_name, role, created_at | ✅ |
| 5 | auth/me | 200 | id, username, display_name, role, created_at | ⚠️ 缺 phone（§3.5） |
| 6 | 用户列表 | 200 | items[], total（恒空） | 🔧 占位 |
| 7 | 创建用户 | 200 | message | 🔧 占位 |
| 8 | 项目列表 | 200 | items[ProjectResponse], total | ⚠️ 缺 customer/risk/红点（§3.3） |
| 9–12 | 创建项目×4 | 201 | ProjectResponse | ✅ |
| 13 | 项目详情 | 404(报告)/200(实测) | ProjectResponse | ⚠️ 缺聚合（§3.4），404 系 reload 假象 |
| 14 | 项目统计 | 200 | ProjectResponse + stats | ⚠️ stats 内部结构未核实 |
| 15/16 | 更新/删除项目 | 200/204 | ProjectResponse | ✅ |
| 17 | 移交监修 | 400 | — | (编排) |
| 18 | 任务列表 | 200 | TaskResponse[] | ⚠️ 缺 note/photos（§3.9） |
| 19/20 | 创建/更新任务 | 201/200 | TaskResponse | ⚠️ 缺 note/photos |
| 21 | 删除任务 | 204 | — | ✅ |
| 22 | 任务每日更新列表 | 200 | [] | ✅（路由可用） |
| 23 | 创建每日更新 | 404 | — | (编排：URL 双 tasks) |
| 24 | 上传进度照片 | 403 | — | (限流，正确) |
| 25 | 删除照片 | 404 | — | (硬编码 id) |
| 26 | 日报列表 | 200 | DailyReportResponse[] | ⚠️ 无今日完成自动派生（§3.8） |
| 27–30 | 日报详情/更新/确认 | 200 | completed_items, tomorrow_plan, risk_alert, confirmed… | ⚠️ 同上 |
| 31–34 | 周报列表/生成/更新/确认 | 200 | WeeklyReportResponse | ✅ |
| 35/36 | 风险汇总/项目风险 | 200 | RiskEventResponse[] | ⚠️ 缺聚合 summary（§3.7） |
| 37 | AI 检测风险 | 200 | project_id, status, task_id | ✅（异步） |
| 38 | 解决风险 | 404 | — | (硬编码 id) |
| 39–65 | 调研/商务/合同/修船经纪/备件/物流/签收/发票 CRUD | 混合 | 各子表 Response（字段本身齐） | ⚠️ GET 未建即 404（§3.2） |
| 66/67 | 保存文字/图片（随手存） | 201 | save, suggestions | ⚠️ suggestions 形状需核实是否含 suggested_project_id |
| 68/69 | 随手存列表/更新 | 200 | QuickSaveResponse | ✅ |
| 70 | 上传文档 | 201 | id, category, title, file_key, original_text, uploaded_by | ✅ 有 id |
| 71/72 | 文档列表/详情 | 200 | 同上 | ✅ |
| 73 | 删除文档 | 204 | — | ✅（已修 FK） |
| 74 | 知识库问答 | 200 | answer, citations | ⚠️ 命名/形状 vs sources[{doc,ref}]；且无下载端点（§3.6） |
| 75–79 | 客户 列表/创建/详情/更新/删除 | 200/201/204 | CustomerResponse（含 phone✅） | ✅ 字段最齐的一组 |
| 80 | 上传文件 | 201 | file_name, file_type, storage_key, file_size, mime_type | ❌ **缺 id（§3.1）** |
| 81 | 文件列表 | 200 | FileResponse[]（含 id） | ✅ |
| 82–84 | 文件 download/preview/delete | 404 | — | ❌ 根因在 §3.1 + 硬编码 id |

---

## 5. 修复优先级

- **P0（一行改动，立刻解"文件不存在"）**：`FileUploadResponse` 加 `id`（§3.1）。
- **P1（决定前端能否少写一堆胶水）**：
  - 统一项目列表/详情聚合：join 客户 + 风险摘要 + `hasUnconfirmedReport` 红点（§3.3/§3.4）。
  - 子资源 GET 改"200 + null"或统一 `/projects/:id/info`（§3.2）。
- **P2（功能闭环）**：`/auth/me` 补 phone（先给 User 模型加字段，§3.5）；知识库补下载端点（§3.6）；风险聚合 summary（§3.7）；日报 `/reports/today` 派生（§3.8）；Task 加 note/photos（§3.9）。

---

## 6. 可直接落地的补丁（P0）

`backend/app/schemas/file.py`：
```python
class FileUploadResponse(BaseModel):
    id: int                      # ← 新增：上传后返回主键，供 download/preview/delete 引用
    file_name: str
    file_type: str
    storage_key: str
    file_size: int
    mime_type: str
```
`backend/app/routers/files.py` 的 `upload_file` 返回处补 `id=file_record.id`。改完 uvicorn `--reload` 自动生效，无需重启容器。

---

> 说明：以上"缺字段"判断基于后端 `schemas/` 实际定义 + 回放返回的 JSON，**不是**照抄前端方案（方案为 draft）。凡标注 ⚠️ 的，接口本身不崩溃、字段在"存在时"完整，缺的是**前端卡片/Tab 直接要的关联与聚合数据**——这正是重构时要不要做"统一聚合接口"的核心论据。
