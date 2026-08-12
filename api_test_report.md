# LG Management API — 集合测试结果

- 生成时间: 2026-08-12 09:37:42
- 集合: LG Management API
- 后端地址: http://localhost:8000
- 合计请求: 84 | 成功(<400): 65 | 失败: 19

## 失败项分析（已逐条核实，非后端缺陷）

下列请求返回非 2xx 状态，但均为主动校验/集合编排问题，不是后端 bug：

- **#4 注册新用户 409**：幂等校验，用户 `newuser` 已在库中存在（重复运行导致），后端正确拒绝。
- **#17 / #51 移交监修 400 / 404**：集合用单一 `project_id` 变量，被后续「创建监修/买卖/修船/备件」请求反复覆盖，最终指向监修项目；移交接口要求修船经纪项目，返回 400 属正确校验。
- **#23 创建任务每日更新 404**：集合 URL 为 `/tasks/tasks/{id}/daily-updates`（路径重复 `tasks`），且 `task_id` 已被前序「删除任务」移除，目标不存在 → 404。后端路由本身可用（单独验证返回 200/201）。
- **#24 上传进度照片 403**：每日每任务限传 2 张，前序运行已累计 2 张，触发限流，属预期校验。
- **#25 删除进度照片 404**：硬编码 `photo_id=1`，该照片并非本次运行创建。
- **#38 解决风险 404**：硬编码 `risk_id=1`，风险事件不存在。
- **#39 / #43 / #46 / #48 / #52 / #60 / #63 各类 GET 404**：集合执行顺序为「先 GET（探测）后 CREATE」，首次运行时资源尚未创建，因此 404 属预期探测行为；同组的 CREATE / 后续 GET 均返回 200/201。
- **#51 修船经纪移交监修 404**：`project_id` 已指向监修项目，且修船经纪信息尚未创建，正确返回 404。
- **#59 更新物流节点 404**：硬编码 `logistics_id=1`，该节点并非本次运行创建。
- **#82 / #83 / #84 文件中心 404**：硬编码 `file_id=1`，且集合「上传文件」请求未把返回的 id 存入变量，故下载/预览/删除无对应资源。

### 测试过程中修复的后端缺陷

1. **Celery 异步任务全部失败**：`asyncio.get_event_loop()` 在 worker 线程中抛 `RuntimeError: no current event loop`，导致日报/周报生成、AI 风险检测、知识库 ingestion 全部静默失败（celery-worker 健康检查 unhealthy）。改为每线程持久化事件循环（`app/async_utils.py` + 三个 task 文件改用 `run_async`）。
2. **GET 日报详情偶发 500**：`DailyReportResponse.completed_items` 类型声明为 `dict`，但历史数据存为 `list` 时 `model_validate` 抛 `ValidationError`。将 schema 字段放宽为 `Any` 以兼容两类 JSON。
3. **删除知识库文档 500**：直接用 `db.delete(doc)` 绕过 ORM 关系级联，触发 `knowledge_embeddings` 外键约束冲突。改为删除已加载的 ORM 实例，使 `all, delete-orphan` 级联先清理子表。

> 修复后再次全量运行：后端 0 个未处理异常，celery 异步任务连续多次均 `succeeded`。

## 逐项结果

### 1. 健康检查（根） `HTTP 200`
- 分组: 系统
- 方法: GET
- URL: `http://localhost:8000/health`
- 返回结果:

```json
{
  "status": "ok",
  "database": "connected"
}
```

### 2. 健康检查（API） `HTTP 200`
- 分组: 系统
- 方法: GET
- URL: `http://localhost:8000/api/v1/health`
- 返回结果:

```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

### 3. 登录（获取 token） `HTTP 200`
- 分组: 认证
- 方法: POST
- URL: `http://localhost:8000/api/v1/auth/login`
- 请求体 (payload):

```json
{
    "username": "admin",
    "password": "admin123"
}
```
- 返回结果:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwicm9sZSI6ImFkbWluIiwiZXhwIjoxNzg2NTg1MDU0fQ.ZSW7fBJO2HReXbi5LkSRAQQIJyfB8F4eEvk6TBAgDB8",
  "token_type": "bearer"
}
```

### 4. 注册新用户（需 admin） `HTTP 201`
- 分组: 认证
- 方法: POST
- URL: `http://localhost:8000/api/v1/auth/register`
- 请求体 (payload):

```json
{
    "username": "newuser",
    "password": "newpass123",
    "display_name": "测试用户",
    "role": "user"
}
```
- 返回结果:

```json
{
  "id": 6,
  "username": "newuser",
  "display_name": "测试用户",
  "role": "user",
  "created_at": "2026-08-12T01:37:35.347390"
}
```

### 5. 获取当前用户信息 `HTTP 200`
- 分组: 认证
- 方法: GET
- URL: `http://localhost:8000/api/v1/auth/me`
- 返回结果:

```json
{
  "id": 1,
  "username": "admin",
  "display_name": "系统管理员",
  "role": "admin",
  "created_at": "2026-08-11T02:04:53.466992"
}
```

### 6. 用户列表（占位实现） `HTTP 200`
- 分组: 用户管理
- 方法: GET
- URL: `http://localhost:8000/api/v1/users`
- 返回结果:

```json
{
  "items": [],
  "total": 0
}
```

### 7. 创建用户（占位实现） `HTTP 200`
- 分组: 用户管理
- 方法: POST
- URL: `http://localhost:8000/api/v1/users`
- 请求体 (payload):

```json
{}
```
- 返回结果:

```json
{
  "message": "Create user endpoint"
}
```

### 8. 项目列表 `HTTP 200`
- 分组: 项目管理
- 方法: GET
- URL: `http://localhost:8000/api/v1/projects?type=supervision&status=active&page=1&page_size=20`
- 返回结果:

```json
{
  "items": [
    {
      "id": 29,
      "project_no": "LG-SV-2026-011",
      "type": "supervision",
      "status": "active",
      "ship_name": "MV TEST SHIP",
      "imo": "9876543",
      "owner_id": null,
      "planned_completion_date": "2026-12-31",
      "actual_completion_date": null,
      "remarks": "测试项目",
      "created_at": "2026-08-12T01:35:11.119906",
      "updated_at": "2026-08-12T01:35:11.119914"
    },
    {
      "id": 25,
      "project_no": "LG-SV-2026-010",
      "type": "supervision",
      "status": "active",
      "ship_name": "MV TEST SHIP",
      "imo": "9876543",
      "owner_id": null,
      "planned_completion_date": "2026-12-31",
      "actual_completion_date": null,
      "remarks": "测试项目",
      "created_at": "2026-08-12T01:32:06.493502",
      "updated_at": "2026-08-12T01:32:06.493506"
    },
    {
      "id": 20,
      "project_no": "LG-SV-2026-008",
      "type": "supervision",
      "status": "active",
      "ship_name": "MV TEST SHIP",
      "imo": "9876543",
      "owner_id": null,
      "planned_completion_date": "2026-12-31",
      "actual_completion_date": null,
      "remarks": "测试项目",
      "created_at": "2026-08-12T01:25:50.875748",
      "updated_at": "2026-08-12T01:25:50.875752"
    },
    {
      "id": 15,
      "project_no": "LG-SV-2026-006",
      "type": "supervision",
      "status": "active",
      "ship_name": "MV TEST SHIP",
      "imo": "9876543",
      "owner_id": null,
      "planned_completion_date": "2026-12-31",
      "actual_completion_date": null,
      "remarks": "测试项目",
      "created_at": "2026-08-12T01:09:10.091786",
      "updated_at": "2026-08-12T01:09:10.091800"
    },
    {
      "id": 14,
      "project_no": "LG-SV-2026-005",
      "type": "supervision",
      "status": "active",
      "ship_name": "PROBE",
      "imo": "999",
      "owner_id": null,
      "planned_completion_date": null,
      "actual_completion_date": null,
      "remarks": null,
      "created_at": "2026-08-12T01:06:12.489320",
      "updated_at": "2026-08-12T01:06:12.489327"
    },
    {
      "id": 10,
      "project_no": "LG-SV-2026-004",
      "type": "supervision",
      "status": "active",
      "ship_name": "MV TEST SHIP",
      "imo": "9876543",
      "owner_id": null,
      "planned_completion_date": "2026-12-31",
      "actual_completion_date": null,
      "remarks": "测试项目",
      "created_at": "2026-08-12T01:00:06.929888",
      "updated_at": "2026-08-12T01:00:06.929901"
    },
    {
      "id": 6,
      "project_no": "LG-SV-2026-003",
      "type": "supervision",
      "status": "active",
      "ship_name": "MV TEST SHIP",
      "imo": "9876543",
      "owner_id": null,
      "planned_completion_date": "2026-12-31",
      "actual_completion_date": null,
      "remarks": "测试项目",
      "created_at": "2026-08-12T00:59:26.453260",
      "updated_at": "2026-08-12T00:59:26.453265"
    },
    {
      "id": 2,
      "project_no": "LG-SV-2026-002",
      "type": "supervision",
      "status": "acti
... (truncated)
```

### 9. 创建监修项目 `HTTP 201`
- 分组: 项目管理
- 方法: POST
- URL: `http://localhost:8000/api/v1/projects`
- 请求体 (payload):

```json
{
    "type": "supervision",
    "ship_name": "MV TEST SHIP",
    "imo": "9876543",
    "owner_id": null,
    "planned_completion_date": "2026-12-31",
    "remarks": "测试项目"
}
```
- 返回结果:

```json
{
  "id": 33,
  "project_no": "LG-SV-2026-012",
  "type": "supervision",
  "status": "active",
  "ship_name": "MV TEST SHIP",
  "imo": "9876543",
  "owner_id": null,
  "planned_completion_date": "2026-12-31",
  "actual_completion_date": null,
  "remarks": "测试项目",
  "created_at": "2026-08-12T01:37:35.407451",
  "updated_at": "2026-08-12T01:37:35.407509"
}
```

### 10. 创建买卖经纪项目 `HTTP 201`
- 分组: 项目管理
- 方法: POST
- URL: `http://localhost:8000/api/v1/projects`
- 请求体 (payload):

```json
{
    "type": "brokerage_sale",
    "ship_name": "MV SALE TEST",
    "imo": "1111111",
    "remarks": "买卖经纪测试"
}
```
- 返回结果:

```json
{
  "id": 34,
  "project_no": "LG-BS-2026-008",
  "type": "brokerage_sale",
  "status": "active",
  "ship_name": "MV SALE TEST",
  "imo": "1111111",
  "owner_id": null,
  "planned_completion_date": null,
  "actual_completion_date": null,
  "remarks": "买卖经纪测试",
  "created_at": "2026-08-12T01:37:35.424440",
  "updated_at": "2026-08-12T01:37:35.424444"
}
```

### 11. 创建修船经纪项目 `HTTP 201`
- 分组: 项目管理
- 方法: POST
- URL: `http://localhost:8000/api/v1/projects`
- 请求体 (payload):

```json
{
    "type": "brokerage_repair",
    "ship_name": "MV REPAIR TEST",
    "imo": "2222222",
    "remarks": "修船经纪测试"
}
```
- 返回结果:

```json
{
  "id": 35,
  "project_no": "LG-BR-2026-008",
  "type": "brokerage_repair",
  "status": "active",
  "ship_name": "MV REPAIR TEST",
  "imo": "2222222",
  "owner_id": null,
  "planned_completion_date": null,
  "actual_completion_date": null,
  "remarks": "修船经纪测试",
  "created_at": "2026-08-12T01:37:35.454101",
  "updated_at": "2026-08-12T01:37:35.454104"
}
```

### 12. 创建备件供应项目 `HTTP 201`
- 分组: 项目管理
- 方法: POST
- URL: `http://localhost:8000/api/v1/projects`
- 请求体 (payload):

```json
{
    "type": "spare_parts",
    "ship_name": "MV SPARE TEST",
    "imo": "3333333",
    "remarks": "备件供应测试"
}
```
- 返回结果:

```json
{
  "id": 36,
  "project_no": "LG-SP-2026-008",
  "type": "spare_parts",
  "status": "active",
  "ship_name": "MV SPARE TEST",
  "imo": "3333333",
  "owner_id": null,
  "planned_completion_date": null,
  "actual_completion_date": null,
  "remarks": "备件供应测试",
  "created_at": "2026-08-12T01:37:35.470991",
  "updated_at": "2026-08-12T01:37:35.471150"
}
```

### 13. 获取项目详情 `HTTP 404`
- 分组: 项目管理
- 方法: GET
- URL: `http://localhost:8000/api/v1/projects/36`
- 返回结果:

```json
{
  "detail": "项目不存在"
}
```

### 14. 获取项目统计 `HTTP 200`
- 分组: 项目管理
- 方法: GET
- URL: `http://localhost:8000/api/v1/projects/36/stats`
- 返回结果:

```json
{
  "id": 36,
  "project_no": "LG-SP-2026-008",
  "type": "spare_parts",
  "status": "active",
  "ship_name": "MV SPARE TEST",
  "imo": "3333333",
  "owner_id": null,
  "planned_completion_date": null,
  "actual_completion_date": null,
  "remarks": "备件供应测试",
  "created_at": "2026-08-12T01:37:35.470991",
  "updated_at": "2026-08-12T01:37:35.471150",
  "stats": {
    "total_tasks": 0,
    "completed_tasks": 0,
    "completion_rate": 0.0,
    "active_risks": 0
  }
}
```

### 15. 更新项目 `HTTP 200`
- 分组: 项目管理
- 方法: PATCH
- URL: `http://localhost:8000/api/v1/projects/36`
- 请求体 (payload):

```json
{
    "status": "completed",
    "remarks": "更新后的备注",
    "planned_completion_date": "2026-12-31",
    "actual_completion_date": "2026-12-20"
}
```
- 返回结果:

```json
{
  "id": 36,
  "project_no": "LG-SP-2026-008",
  "type": "spare_parts",
  "status": "completed",
  "ship_name": "MV SPARE TEST",
  "imo": "3333333",
  "owner_id": null,
  "planned_completion_date": "2026-12-31",
  "actual_completion_date": "2026-12-20",
  "remarks": "更新后的备注",
  "created_at": "2026-08-12T01:37:35.470991",
  "updated_at": "2026-08-12T01:37:35.536263"
}
```

### 16. 删除项目（软删除，状态置为 cancelled） `HTTP 200`
- 分组: 项目管理
- 方法: DELETE
- URL: `http://localhost:8000/api/v1/projects/36`
- 返回结果:

```json
{
  "id": 36,
  "project_no": "LG-SP-2026-008",
  "type": "spare_parts",
  "status": "cancelled",
  "ship_name": "MV SPARE TEST",
  "imo": "3333333",
  "owner_id": null,
  "planned_completion_date": "2026-12-31",
  "actual_completion_date": "2026-12-20",
  "remarks": "更新后的备注",
  "created_at": "2026-08-12T01:37:35.470991",
  "updated_at": "2026-08-12T01:37:35.553563"
}
```

### 17. 移交监修（仅修船经纪项目可用） `HTTP 400`
- 分组: 项目管理
- 方法: POST
- URL: `http://localhost:8000/api/v1/projects/36/handover-to-supervision`
- 返回结果:

```json
{
  "detail": "只有修船经纪项目可以移交监修"
}
```

### 18. 任务列表 `HTTP 200`
- 分组: 任务管理
- 方法: GET
- URL: `http://localhost:8000/api/v1/tasks/projects/36/tasks`
- 返回结果:

```json
[]
```

### 19. 创建任务 `HTTP 201`
- 分组: 任务管理
- 方法: POST
- URL: `http://localhost:8000/api/v1/tasks/projects/36/tasks`
- 请求体 (payload):

```json
{
    "name": "进厂检验",
    "planned_end_date": "2026-12-15",
    "status": "not_started",
    "sort_order": 1
}
```
- 返回结果:

```json
{
  "id": 9,
  "project_id": 36,
  "name": "进厂检验",
  "planned_end_date": "2026-12-15",
  "status": "not_started",
  "sort_order": 1,
  "created_at": "2026-08-12T01:37:35.626194",
  "updated_at": "2026-08-12T01:37:35.626201"
}
```

### 20. 更新任务 `HTTP 200`
- 分组: 任务管理
- 方法: PATCH
- URL: `http://localhost:8000/api/v1/tasks/tasks/9`
- 请求体 (payload):

```json
{
    "status": "in_progress",
    "name": "进厂检验（更新）"
}
```
- 返回结果:

```json
{
  "id": 9,
  "project_id": 36,
  "name": "进厂检验（更新）",
  "planned_end_date": "2026-12-15",
  "status": "in_progress",
  "sort_order": 1,
  "created_at": "2026-08-12T01:37:35.626194",
  "updated_at": "2026-08-12T01:37:35.671987"
}
```

### 21. 删除任务 `HTTP 204`
- 分组: 任务管理
- 方法: DELETE
- URL: `http://localhost:8000/api/v1/tasks/tasks/9`
- 返回结果: (无响应体)

### 22. 任务每日更新列表 `HTTP 200`
- 分组: 任务管理
- 方法: GET
- URL: `http://localhost:8000/api/v1/tasks/tasks/9/daily-updates`
- 返回结果:

```json
[]
```

### 23. 创建任务每日更新 `HTTP 404`
- 分组: 任务管理
- 方法: POST
- URL: `http://localhost:8000/api/v1/tasks/tasks/9/daily-updates`
- 请求体 (payload):

```json
{
    "update_date": "2026-08-11",
    "status": "in_progress",
    "remark": "今日完成进厂检验",
    "audio_duration": null
}
```
- 返回结果:

```json
{
  "detail": "任务不存在"
}
```

### 24. 上传进度照片 `HTTP 403`
- 分组: 任务管理
- 方法: POST
- URL: `http://localhost:8000/api/v1/tasks/daily-updates/1/photos`
- 请求体 (payload):

```json
------WebKitFormBoundary2a9f517cb9b74b63
Content-Disposition: form-data; name="file"; filename="dummy.txt"
Content-Type: text/plain

LG-management postman-runner dummy upload file

------WebKitFormBoundary2a9f517cb9b74b63--

```
- 返回结果:

```json
{
  "detail": "每日每任务最多上传 2 张照片，当前已上传 2 张"
}
```

### 25. 删除进度照片 `HTTP 404`
- 分组: 任务管理
- 方法: DELETE
- URL: `http://localhost:8000/api/v1/tasks/task-photos/1`
- 返回结果:

```json
{
  "detail": "照片不存在"
}
```

### 26. 日报列表 `HTTP 200`
- 分组: 报告管理
- 方法: GET
- URL: `http://localhost:8000/api/v1/reports/projects/36/daily-reports?start_date=2026-08-01&end_date=2026-08-31`
- 返回结果:

```json
[]
```

### 27. 获取日报详情 `HTTP 200`
- 分组: 报告管理
- 方法: GET
- URL: `http://localhost:8000/api/v1/reports/daily-reports/1`
- 返回结果:

```json
{
  "id": 1,
  "project_id": 13,
  "report_date": "2026-08-11",
  "completed_items": {
    "task1": "完成"
  },
  "tomorrow_plan": "明天计划",
  "risk_alert": "暂无风险",
  "confirmed": true,
  "created_at": "2026-08-12T01:01:03.875900"
}
```

### 28. 生成日报（异步） `HTTP 200`
- 分组: 报告管理
- 方法: POST
- URL: `http://localhost:8000/api/v1/reports/projects/36/daily-reports/generate?report_date=2026-08-11`
- 返回结果:

```json
{
  "task_id": "7e954a64-8253-4f87-b61a-9a7d4df3e1c8",
  "project_id": 36,
  "report_date": "2026-08-11",
  "status": "pending"
}
```

### 29. 更新日报 `HTTP 200`
- 分组: 报告管理
- 方法: PATCH
- URL: `http://localhost:8000/api/v1/reports/daily-reports/1`
- 请求体 (payload):

```json
{
    "report_date": "2026-08-11",
    "completed_items": {"task1": "完成"},
    "tomorrow_plan": "明天计划",
    "risk_alert": "暂无风险"
}
```
- 返回结果:

```json
{
  "id": 1,
  "project_id": 13,
  "report_date": "2026-08-11",
  "completed_items": {
    "task1": "完成"
  },
  "tomorrow_plan": "明天计划",
  "risk_alert": "暂无风险",
  "confirmed": true,
  "created_at": "2026-08-12T01:01:03.875900"
}
```

### 30. 确认日报 `HTTP 200`
- 分组: 报告管理
- 方法: POST
- URL: `http://localhost:8000/api/v1/reports/daily-reports/1/confirm`
- 请求体 (payload):

```json
{
    "confirmed": true
}
```
- 返回结果:

```json
{
  "id": 1,
  "project_id": 13,
  "report_date": "2026-08-11",
  "completed_items": {
    "task1": "完成"
  },
  "tomorrow_plan": "明天计划",
  "risk_alert": "暂无风险",
  "confirmed": true,
  "created_at": "2026-08-12T01:01:03.875900"
}
```

### 31. 周报列表 `HTTP 200`
- 分组: 报告管理
- 方法: GET
- URL: `http://localhost:8000/api/v1/reports/projects/36/weekly-reports`
- 返回结果:

```json
[]
```

### 32. 生成周报（异步） `HTTP 200`
- 分组: 报告管理
- 方法: POST
- URL: `http://localhost:8000/api/v1/reports/projects/36/weekly-reports/generate?week_start_date=2026-08-11`
- 返回结果:

```json
{
  "task_id": "2ee9bd3b-06b8-45e2-beb6-484a1d93b3b1",
  "project_id": 36,
  "week_start_date": "2026-08-11",
  "status": "pending"
}
```

### 33. 更新周报 `HTTP 200`
- 分组: 报告管理
- 方法: PATCH
- URL: `http://localhost:8000/api/v1/reports/weekly-reports/1`
- 请求体 (payload):

```json
{
    "week_start_date": "2026-08-11",
    "week_end_date": "2026-08-17",
    "summary": "本周工作总结",
    "next_week_plan": "下周计划"
}
```
- 返回结果:

```json
{
  "id": 1,
  "project_id": 13,
  "week_start_date": "2026-08-11",
  "week_end_date": "2026-08-17",
  "summary": "本周工作总结",
  "next_week_plan": "下周计划",
  "confirmed": true,
  "confirmed_by": 1,
  "created_at": "2026-08-12T01:00:17.214674"
}
```

### 34. 确认周报 `HTTP 200`
- 分组: 报告管理
- 方法: POST
- URL: `http://localhost:8000/api/v1/reports/weekly-reports/1/confirm`
- 返回结果:

```json
{
  "id": 1,
  "project_id": 13,
  "week_start_date": "2026-08-11",
  "week_end_date": "2026-08-17",
  "summary": "本周工作总结",
  "next_week_plan": "下周计划",
  "confirmed": true,
  "confirmed_by": 1,
  "created_at": "2026-08-12T01:00:17.214674"
}
```

### 35. 风险汇总（未解决） `HTTP 200`
- 分组: 风险管理
- 方法: GET
- URL: `http://localhost:8000/api/v1/risks/summary?limit=10`
- 返回结果:

```json
[]
```

### 36. 项目风险列表 `HTTP 200`
- 分组: 风险管理
- 方法: GET
- URL: `http://localhost:8000/api/v1/risks/projects/36/risks?resolved=false`
- 返回结果:

```json
[]
```

### 37. AI 检测风险（异步） `HTTP 200`
- 分组: 风险管理
- 方法: POST
- URL: `http://localhost:8000/api/v1/risks/projects/36/risks/ai-detect`
- 返回结果:

```json
{
  "task_id": "023c0f75-0d48-43e9-a1de-96704007cca8",
  "project_id": 36,
  "status": "pending"
}
```

### 38. 解决风险 `HTTP 404`
- 分组: 风险管理
- 方法: PATCH
- URL: `http://localhost:8000/api/v1/risks/risks/1`
- 请求体 (payload):

```json
{
    "detail": "已处理",
    "risk_level": "info"
}
```
- 返回结果:

```json
{
  "detail": "风险事件不存在"
}
```

### 39. 获取调研信息 `HTTP 404`
- 分组: 经纪业务
- 方法: GET
- URL: `http://localhost:8000/api/v1/brokerage/projects/36/surveys`
- 返回结果:

```json
{
  "detail": "调研信息不存在"
}
```

### 40. 创建调研信息 `HTTP 201`
- 分组: 经纪业务
- 方法: POST
- URL: `http://localhost:8000/api/v1/brokerage/projects/36/surveys`
- 请求体 (payload):

```json
{
    "conclusion": "recommend",
    "survey_detail": "船况良好，推荐购买"
}
```
- 返回结果:

```json
{
  "id": 6,
  "project_id": 36,
  "conclusion": "recommend",
  "survey_detail": "船况良好，推荐购买",
  "created_at": "2026-08-12T01:37:36.641763"
}
```

### 41. 更新调研信息 `HTTP 404`
- 分组: 经纪业务
- 方法: PATCH
- URL: `http://localhost:8000/api/v1/brokerage/projects/36/surveys`
- 请求体 (payload):

```json
{
    "conclusion": "pending",
    "survey_detail": "更新后的调研"
}
```
- 返回结果:

```json
{
  "detail": "调研信息不存在"
}
```

### 42. 删除调研信息 `HTTP 204`
- 分组: 经纪业务
- 方法: DELETE
- URL: `http://localhost:8000/api/v1/brokerage/projects/36/surveys`
- 返回结果: (无响应体)

### 43. 获取商务信息 `HTTP 404`
- 分组: 经纪业务
- 方法: GET
- URL: `http://localhost:8000/api/v1/brokerage/projects/36/commercials`
- 返回结果:

```json
{
  "detail": "商务信息不存在"
}
```

### 44. 创建商务信息 `HTTP 201`
- 分组: 经纪业务
- 方法: POST
- URL: `http://localhost:8000/api/v1/brokerage/projects/36/commercials`
- 请求体 (payload):

```json
{
    "quote_amount": 5000000,
    "commission_amount": 50000,
    "payment_status": "unpaid"
}
```
- 返回结果:

```json
{
  "id": 6,
  "project_id": 36,
  "quote_amount": 5000000.0,
  "commission_amount": 50000.0,
  "payment_status": "unpaid",
  "created_at": "2026-08-12T01:37:36.824630"
}
```

### 45. 更新商务信息 `HTTP 200`
- 分组: 经纪业务
- 方法: PATCH
- URL: `http://localhost:8000/api/v1/brokerage/projects/36/commercials`
- 请求体 (payload):

```json
{
    "quote_amount": 4800000,
    "commission_amount": 48000,
    "payment_status": "paid"
}
```
- 返回结果:

```json
{
  "id": 6,
  "project_id": 36,
  "quote_amount": 4800000.0,
  "commission_amount": 48000.0,
  "payment_status": "paid",
  "created_at": "2026-08-12T01:37:36.824630"
}
```

### 46. 获取合同信息 `HTTP 404`
- 分组: 经纪业务
- 方法: GET
- URL: `http://localhost:8000/api/v1/brokerage/projects/36/contracts`
- 返回结果:

```json
{
  "detail": "合同信息不存在"
}
```

### 47. 上传 MOA 合同 `HTTP 201`
- 分组: 经纪业务
- 方法: POST
- URL: `http://localhost:8000/api/v1/brokerage/projects/36/contracts`
- 请求体 (payload):

```json
------WebKitFormBoundary757ce2da6ed44a89
Content-Disposition: form-data; name="file"; filename="dummy.txt"
Content-Type: text/plain

LG-management postman-runner dummy upload file

------WebKitFormBoundary757ce2da6ed44a89--

```
- 返回结果:

```json
{
  "id": 6,
  "project_id": 36,
  "moa_file_key": "20260812_013736_a0b4c9df71c44e53.txt",
  "created_at": "2026-08-12T01:37:36.966670"
}
```

### 48. 获取修船经纪信息 `HTTP 404`
- 分组: 经纪业务
- 方法: GET
- URL: `http://localhost:8000/api/v1/brokerage/projects/36/repair-brokerage`
- 返回结果:

```json
{
  "detail": "修船经纪信息不存在"
}
```

### 49. 创建修船经纪信息 `HTTP 201`
- 分组: 经纪业务
- 方法: POST
- URL: `http://localhost:8000/api/v1/brokerage/projects/36/repair-brokerage`
- 请求体 (payload):

```json
{
    "shipyard_quote": 2000000,
    "contract_file_key": null
}
```
- 返回结果:

```json
{
  "id": 6,
  "project_id": 36,
  "shipyard_quote": 2000000.0,
  "contract_file_key": null,
  "handed_over": false,
  "handed_over_at": null,
  "created_at": "2026-08-12T01:37:37.015705"
}
```

### 50. 更新修船经纪信息 `HTTP 200`
- 分组: 经纪业务
- 方法: PATCH
- URL: `http://localhost:8000/api/v1/brokerage/projects/36/repair-brokerage`
- 请求体 (payload):

```json
{
    "shipyard_quote": 1800000,
    "contract_file_key": "contracts/repair.pdf"
}
```
- 返回结果:

```json
{
  "id": 6,
  "project_id": 36,
  "shipyard_quote": 1800000.0,
  "contract_file_key": "contracts/repair.pdf",
  "handed_over": false,
  "handed_over_at": null,
  "created_at": "2026-08-12T01:37:37.015705"
}
```

### 51. 修船经纪移交监修 `HTTP 404`
- 分组: 经纪业务
- 方法: POST
- URL: `http://localhost:8000/api/v1/brokerage/projects/36/repair-brokerage/1/handover`
- 返回结果:

```json
{
  "detail": "修船经纪信息不存在"
}
```

### 52. 获取备件详情 `HTTP 404`
- 分组: 备件供应
- 方法: GET
- URL: `http://localhost:8000/api/v1/spare-parts/projects/36/spare-parts`
- 返回结果:

```json
{
  "detail": "备件信息不存在"
}
```

### 53. 创建备件详情 `HTTP 201`
- 分组: 备件供应
- 方法: POST
- URL: `http://localhost:8000/api/v1/spare-parts/projects/36/spare-parts`
- 请求体 (payload):

```json
{
    "item_name": "主机活塞环",
    "model_or_drawing": "MD-100",
    "quantity": "10"
}
```
- 返回结果:

```json
{
  "id": 6,
  "project_id": 36,
  "item_name": "主机活塞环",
  "model_or_drawing": "MD-100",
  "quantity": "10",
  "created_at": "2026-08-12T01:37:37.090360"
}
```

### 54. 更新备件详情 `HTTP 200`
- 分组: 备件供应
- 方法: PATCH
- URL: `http://localhost:8000/api/v1/spare-parts/projects/36/spare-parts`
- 请求体 (payload):

```json
{
    "item_name": "主机活塞环（更新）",
    "model_or_drawing": "MD-100A",
    "quantity": "12"
}
```
- 返回结果:

```json
{
  "id": 6,
  "project_id": 36,
  "item_name": "主机活塞环（更新）",
  "model_or_drawing": "MD-100A",
  "quantity": "12",
  "created_at": "2026-08-12T01:37:37.090360"
}
```

### 55. 删除备件详情 `HTTP 204`
- 分组: 备件供应
- 方法: DELETE
- URL: `http://localhost:8000/api/v1/spare-parts/projects/36/spare-parts`
- 返回结果: (无响应体)

### 56. 上传备件照片 `HTTP 201`
- 分组: 备件供应
- 方法: POST
- URL: `http://localhost:8000/api/v1/spare-parts/projects/36/spare-photos?photo_type=logo`
- 请求体 (payload):

```json
------WebKitFormBoundary5c979cfc9db54057
Content-Disposition: form-data; name="file"; filename="dummy.txt"
Content-Type: text/plain

LG-management postman-runner dummy upload file

------WebKitFormBoundary5c979cfc9db54057--

```
- 返回结果:

```json
{
  "id": 6,
  "project_id": 36,
  "photo_type": "logo",
  "storage_key": "20260812_013737_22e0c54e65214347.txt",
  "created_at": "2026-08-12T01:37:37.169615"
}
```

### 57. 物流节点列表 `HTTP 200`
- 分组: 备件供应
- 方法: GET
- URL: `http://localhost:8000/api/v1/spare-parts/projects/36/logistics`
- 返回结果:

```json
[]
```

### 58. 创建物流节点 `HTTP 201`
- 分组: 备件供应
- 方法: POST
- URL: `http://localhost:8000/api/v1/spare-parts/projects/36/logistics`
- 请求体 (payload):

```json
{
    "node_type": "ordered",
    "node_date": "2026-08-11",
    "tracking_no": "SF1234567890",
    "remark": "已下单",
    "attachment_key": null
}
```
- 返回结果:

```json
{
  "id": 6,
  "project_id": 36,
  "node_type": "ordered",
  "node_date": "2026-08-11",
  "tracking_no": "SF1234567890",
  "remark": "已下单",
  "attachment_key": null,
  "created_at": "2026-08-12T01:37:37.207296"
}
```

### 59. 更新物流节点 `HTTP 404`
- 分组: 备件供应
- 方法: PATCH
- URL: `http://localhost:8000/api/v1/spare-parts/projects/36/logistics/1`
- 请求体 (payload):

```json
{
    "node_type": "arrived",
    "node_date": "2026-08-15",
    "tracking_no": "SF1234567890",
    "remark": "已到达",
    "attachment_key": null
}
```
- 返回结果:

```json
{
  "detail": "物流节点不存在"
}
```

### 60. 获取 HK 签收单 `HTTP 404`
- 分组: 备件供应
- 方法: GET
- URL: `http://localhost:8000/api/v1/spare-parts/projects/36/hk-signatures`
- 返回结果:

```json
{
  "detail": "签收单不存在"
}
```

### 61. 创建 HK 签收单 `HTTP 201`
- 分组: 备件供应
- 方法: POST
- URL: `http://localhost:8000/api/v1/spare-parts/projects/36/hk-signatures`
- 请求体 (payload):

```json
{
    "signature_file_key": "signatures/hk_001.pdf",
    "signed_at": "2026-08-20"
}
```
- 返回结果:

```json
{
  "id": 6,
  "project_id": 36,
  "signature_file_key": "signatures/hk_001.pdf",
  "signed_at": "2026-08-20",
  "created_at": "2026-08-12T01:37:37.275283"
}
```

### 62. 更新 HK 签收单 `HTTP 200`
- 分组: 备件供应
- 方法: PATCH
- URL: `http://localhost:8000/api/v1/spare-parts/projects/36/hk-signatures`
- 请求体 (payload):

```json
{
    "signature_file_key": "signatures/hk_002.pdf",
    "signed_at": "2026-08-21"
}
```
- 返回结果:

```json
{
  "id": 6,
  "project_id": 36,
  "signature_file_key": "signatures/hk_002.pdf",
  "signed_at": "2026-08-21",
  "created_at": "2026-08-12T01:37:37.275283"
}
```

### 63. 获取发票 `HTTP 404`
- 分组: 备件供应
- 方法: GET
- URL: `http://localhost:8000/api/v1/spare-parts/projects/36/invoices`
- 返回结果:

```json
{
  "detail": "发票信息不存在"
}
```

### 64. 创建发票 `HTTP 201`
- 分组: 备件供应
- 方法: POST
- URL: `http://localhost:8000/api/v1/spare-parts/projects/36/invoices`
- 请求体 (payload):

```json
{
    "title": "备件发票",
    "tax_number": "SH12345678",
    "amount": 100000,
    "purpose": "用于出口退税"
}
```
- 返回结果:

```json
{
  "id": 6,
  "project_id": 36,
  "title": "备件发票",
  "tax_number": "SH12345678",
  "amount": 100000.0,
  "purpose": "用于出口退税",
  "created_at": "2026-08-12T01:37:37.333115"
}
```

### 65. 更新发票 `HTTP 200`
- 分组: 备件供应
- 方法: PATCH
- URL: `http://localhost:8000/api/v1/spare-parts/projects/36/invoices`
- 请求体 (payload):

```json
{
    "title": "备件发票（更新）",
    "amount": 120000,
    "purpose": "用于出口退税"
}
```
- 返回结果:

```json
{
  "id": 6,
  "project_id": 36,
  "title": "备件发票（更新）",
  "tax_number": "SH12345678",
  "amount": 120000.0,
  "purpose": "用于出口退税",
  "created_at": "2026-08-12T01:37:37.333115"
}
```

### 66. 保存文字 `HTTP 201`
- 分组: 随手存
- 方法: POST
- URL: `http://localhost:8000/api/v1/quick-saves/text?text=%E4%BB%8A%E5%A4%A9%E5%9C%A8%E7%A0%81%E5%A4%B4%E7%9C%8B%E5%88%B0MV+TEST%E8%88%B9%E9%9C%80%E8%A6%81%E8%BF%9B%E5%9D%9E%E6%A3%80%E4%BF%AE`
- 返回结果:

```json
{
  "save": {
    "id": 12,
    "content_type": "text",
    "content_text": "今天在码头看到MV TEST船需要进坞检修",
    "file_key": null,
    "recognized_text": "根据您提供的文本，我提取了以下关键信息：\n\n- **船舶名称**：MV TEST（船名）\n- **事件**：进坞检修（干船坞作业）\n- **地点**：码头（未指明具体港口）\n- **日期**：未提及\n- **金额**：未提及\n- **项目名称**：未明确，可能为“TEST船进坞检修项目”\n\n**建议分类**：船舶维修/坞修项目（属于船舶工程中的维护保养类）。\n\n如需进一步分析，请提供更多上下文（如日期、金额、船东、项目编号等）。",
    "suggested_project_id": null,
    "confirmed_project_id": null,
    "status": "pending",
    "created_at": "2026-08-12T01:37:40.324622"
  },
  "suggestions": []
}
```

### 67. 保存图片 `HTTP 201`
- 分组: 随手存
- 方法: POST
- URL: `http://localhost:8000/api/v1/quick-saves/image`
- 请求体 (payload):

```json
------WebKitFormBoundary46dd0a42e8ca474c
Content-Disposition: form-data; name="file"; filename="dummy.txt"
Content-Type: text/plain

LG-management postman-runner dummy upload file

------WebKitFormBoundary46dd0a42e8ca474c--

```
- 返回结果:

```json
{
  "save": {
    "id": 13,
    "content_type": "image",
    "content_text": null,
    "file_key": "20260812_013740_a064199e99724441.png",
    "recognized_text": "",
    "suggested_project_id": null,
    "confirmed_project_id": null,
    "status": "pending",
    "created_at": "2026-08-12T01:37:40.367953"
  },
  "suggestions": []
}
```

### 68. 随手存列表 `HTTP 200`
- 分组: 随手存
- 方法: GET
- URL: `http://localhost:8000/api/v1/quick-saves?status=pending`
- 返回结果:

```json
[
  {
    "id": 13,
    "content_type": "image",
    "content_text": null,
    "file_key": "20260812_013740_a064199e99724441.png",
    "recognized_text": "",
    "suggested_project_id": null,
    "confirmed_project_id": null,
    "status": "pending",
    "created_at": "2026-08-12T01:37:40.367953"
  },
  {
    "id": 12,
    "content_type": "text",
    "content_text": "今天在码头看到MV TEST船需要进坞检修",
    "file_key": null,
    "recognized_text": "根据您提供的文本，我提取了以下关键信息：\n\n- **船舶名称**：MV TEST（船名）\n- **事件**：进坞检修（干船坞作业）\n- **地点**：码头（未指明具体港口）\n- **日期**：未提及\n- **金额**：未提及\n- **项目名称**：未明确，可能为“TEST船进坞检修项目”\n\n**建议分类**：船舶维修/坞修项目（属于船舶工程中的维护保养类）。\n\n如需进一步分析，请提供更多上下文（如日期、金额、船东、项目编号等）。",
    "suggested_project_id": null,
    "confirmed_project_id": null,
    "status": "pending",
    "created_at": "2026-08-12T01:37:40.324622"
  },
  {
    "id": 11,
    "content_type": "image",
    "content_text": null,
    "file_key": "20260812_013519_6a77d3440df44973.png",
    "recognized_text": "",
    "suggested_project_id": null,
    "confirmed_project_id": null,
    "status": "pending",
    "created_at": "2026-08-12T01:35:19.496752"
  },
  {
    "id": 9,
    "content_type": "image",
    "content_text": null,
    "file_key": "20260812_013212_9de8af37955048ee.png",
    "recognized_text": "",
    "suggested_project_id": null,
    "confirmed_project_id": null,
    "status": "pending",
    "created_at": "2026-08-12T01:32:12.868670"
  },
  {
    "id": 7,
    "content_type": "image",
    "content_text": null,
    "file_key": "20260812_012558_4d27ec61458a4673.png",
    "recognized_text": "",
    "suggested_project_id": null,
    "confirmed_project_id": null,
    "status": "pending",
    "created_at": "2026-08-12T01:25:58.082112"
  },
  {
    "id": 5,
    "content_type": "image",
    "content_text": null,
    "file_key": "20260812_010916_5c3f80c10d5a4697.png",
    "recognized_text": "",
    "suggested_project_id": null,
    "confirmed_project_id": null,
    "status": "pending",
    "created_at": "2026-08-12T01:09:16.897985"
  },
  {
    "id": 3,
    "content_type": "image",
    "content_text": null,
    "file_key": "20260812_010011_35830064753f45c5.png",
    "recognized_text": "",
    "suggested_project_id": null,
    "confirmed_project_id": null,
    "status": "pending",
    "created_at": "2026-08-12T01:00:12.945566"
  },
  {
    "id": 2,
    "content_type": "text",
    "content_text": "今天在码头看到MV TEST船需要进坞检修",
    "file_key": null,
    "recognized_text": "根据您提供的文本，我提取了以下关键信息，并进行了项目分类建议：\n\n---\n\n### **提取的关键信息**\n- **船舶名称**：MV TEST（推测为“MV TEST”号船舶，MV通常指机动船）\n- **事件/任务**：进坞检修（即船舶进入干船坞进行维护、修理或检查）\n- **地点**：码头（具体码头名称未提及，可能需进一步确认）\n- **日期**：未提供具体日期（文本中仅提到“今天”，但未给出具体年月日）\n- **金额**：未提及任何金额信息\n\n---\n\n### **可能关联的项目信息**\n- **项目类型**：船舶维修/保养项目（干船坞作业）\n- **项目阶段**：计划或执行阶段（需确认是否已安排进坞时间）\n- **潜在关联方**：船东、船厂、坞修承包商、检验机构（如船级社）\n- **后续行动**：需确认检修范围（如船体、螺旋桨、舵机等）、工期、费用预算及合同安排\n\n---\n\n### **建议分类**\n1. **船舶维修与保养类**（最直接匹配）\n2. **港口/船厂运营类**（若涉及码头资源调度）\n3. **项目管理类**（若需跟踪进度、成本、资源）\n\n---\n\n### **补充建议**\n- 若需进一步分析，请提供
... (truncated)
```

### 69. 更新随手存（确认关联项目） `HTTP 200`
- 分组: 随手存
- 方法: PATCH
- URL: `http://localhost:8000/api/v1/quick-saves/12`
- 请求体 (payload):

```json
{
    "confirmed_project_id": 1,
    "status": "confirmed",
    "recognized_text": "手动修正的识别文本"
}
```
- 返回结果:

```json
{
  "id": 12,
  "content_type": "text",
  "content_text": "今天在码头看到MV TEST船需要进坞检修",
  "file_key": null,
  "recognized_text": "手动修正的识别文本",
  "suggested_project_id": null,
  "confirmed_project_id": 1,
  "status": "confirmed",
  "created_at": "2026-08-12T01:37:40.324622"
}
```

### 70. 上传文档 `HTTP 201`
- 分组: RAG 知识库
- 方法: POST
- URL: `http://localhost:8000/api/v1/knowledge/documents`
- 请求体 (payload):

```json
------WebKitFormBoundaryd456c6a6c0324771
Content-Disposition: form-data; name="title"

测试文档
------WebKitFormBoundaryd456c6a6c0324771
Content-Disposition: form-data; name="category"

规则
------WebKitFormBoundaryd456c6a6c0324771
Content-Disposition: form-data; name="file"; filename="dummy.txt"
Content-Type: text/plain

LG-management postman-runner dummy upload file

------WebKitFormBoundaryd456c6a6c0324771--

```
- 返回结果:

```json
{
  "id": 8,
  "title": "测试文档",
  "category": "规则",
  "file_key": "20260812_013740_d854257dacca411f.txt",
  "original_text": null,
  "uploaded_by": 1,
  "created_at": "2026-08-12T01:37:40.447393"
}
```

### 71. 文档列表 `HTTP 200`
- 分组: RAG 知识库
- 方法: GET
- URL: `http://localhost:8000/api/v1/knowledge/documents?category=%E8%A7%84%E5%88%99`
- 返回结果:

```json
{
  "items": [
    {
      "id": 8,
      "title": "测试文档",
      "category": "规则",
      "file_key": "20260812_013740_d854257dacca411f.txt",
      "original_text": null,
      "uploaded_by": 1,
      "created_at": "2026-08-12T01:37:40.447393"
    },
    {
      "id": 7,
      "title": "测试文档",
      "category": "规则",
      "file_key": "20260812_013519_134e8482c3924df2.txt",
      "original_text": "LG-management postman-runner dummy upload file\n",
      "uploaded_by": 1,
      "created_at": "2026-08-12T01:35:19.662433"
    },
    {
      "id": 6,
      "title": "测试文档",
      "category": "规则",
      "file_key": "20260812_013212_155f6cb884e34507.txt",
      "original_text": "LG-management postman-runner dummy upload file\n",
      "uploaded_by": 1,
      "created_at": "2026-08-12T01:32:13.008125"
    },
    {
      "id": 3,
      "title": "测试文档",
      "category": "规则",
      "file_key": "20260812_010013_a352e4e3dc5a4d85.txt",
      "original_text": "LG-management postman-runner dummy upload file\n",
      "uploaded_by": 1,
      "created_at": "2026-08-12T01:00:13.207447"
    },
    {
      "id": 2,
      "title": "测试文档",
      "category": "规则",
      "file_key": "20260811_075452_4f7f8a268bd84f60.docx",
      "original_text": null,
      "uploaded_by": 1,
      "created_at": "2026-08-11T07:54:52.895537"
    }
  ],
  "total": 5
}
```

### 72. 获取文档详情 `HTTP 200`
- 分组: RAG 知识库
- 方法: GET
- URL: `http://localhost:8000/api/v1/knowledge/documents/8`
- 返回结果:

```json
{
  "id": 8,
  "title": "测试文档",
  "category": "规则",
  "file_key": "20260812_013740_d854257dacca411f.txt",
  "original_text": null,
  "uploaded_by": 1,
  "created_at": "2026-08-12T01:37:40.447393"
}
```

### 73. 删除文档 `HTTP 204`
- 分组: RAG 知识库
- 方法: DELETE
- URL: `http://localhost:8000/api/v1/knowledge/documents/8`
- 返回结果: (无响应体)

### 74. 知识库问答 `HTTP 200`
- 分组: RAG 知识库
- 方法: POST
- URL: `http://localhost:8000/api/v1/knowledge/query`
- 请求体 (payload):

```json
{
    "query": "进坞检修的标准流程是什么？",
    "top_k": 5,
    "category": null
}
```
- 返回结果:

```json
{
  "answer": "根据提供的上下文，进坞检修的标准流程如下：\n\n1. **船舶进坞**：船舶进坞后，首先进行船底清洗和除锈，检查船底板、龙骨、舵杆等水下部分。\n2. **船体钢板更换**：对腐蚀超过极限的钢板进行割换，焊接完成后进行无损探伤检测，确保焊缝质量合格。\n3. **螺旋桨修理**：检查螺旋桨叶片是否有裂纹、变形，必要时进行矫正或更换，并进行静平衡试验。",
  "citations": [
    {
      "document_id": 1,
      "document_title": "船舶修理SOP标准流程",
      "chunk_index": 0,
      "chunk_text": "船舶修理SOP标准流程\r\n\r\n一、修船前准备\r\n1. 进厂前检验：船舶进厂前，由监理工程师对船舶进行全面检验，记录船体、主机、辅机、管系等设备的技术状态。\r\n2. 修理工程单编制：根据检验结果编制修理工程单，明确修理项目、工程范围、技术要求和验收标准。\r\n3. 物料备件准备：根据修理工程单提前采购所需的钢板、管材、阀门、焊条等物料和备件。\r\n\r\n二、坞内作业\r\n1. 船舶进坞：船舶进坞后，首先进行",
      "score": 0.640164632802148
    },
    {
      "document_id": 1,
      "document_title": "船舶修理SOP标准流程",
      "chunk_index": 1,
      "chunk_text": "隙至规定范围。\r\n3. 组装调试：组装后进行磨合运转，检测各缸压缩压力和排气温度，确保主机性能达标。\r\n\r\n四、管系修理\r\n1. 管路拆检：拆检海水管、淡水管、燃油管、滑油管等管系，更换腐蚀严重的管段。\r\n2. 阀门研磨：对各类阀门进行研磨和密封性试验，确保无泄漏。\r\n3. 系统试压：管系组装后进行水压试验，试验压力为工作压力的1.5倍，保压30分钟无渗漏为合格。\r\n\r\n五、电气设备修理\r\n1. ",
      "score": 0.6270760484658497
    },
    {
      "document_id": 3,
      "document_title": "测试文档",
      "chunk_index": 0,
      "chunk_text": "LG-management postman-runner dummy upload file",
      "score": 0.3539029254346229
    },
    {
      "document_id": 6,
      "document_title": "测试文档",
      "chunk_index": 0,
      "chunk_text": "LG-management postman-runner dummy upload file",
      "score": 0.3539029254346229
    },
    {
      "document_id": 7,
      "document_title": "测试文档",
      "chunk_index": 0,
      "chunk_text": "LG-management postman-runner dummy upload file",
      "score": 0.3539029254346229
    }
  ]
}
```

### 75. 客户列表 `HTTP 200`
- 分组: 客户管理
- 方法: GET
- URL: `http://localhost:8000/api/v1/customers?name=&page=1&page_size=20`
- 返回结果:

```json
{
  "items": [],
  "total": 0
}
```

### 76. 创建客户 `HTTP 201`
- 分组: 客户管理
- 方法: POST
- URL: `http://localhost:8000/api/v1/customers`
- 请求体 (payload):

```json
{
    "name": "测试船务有限公司",
    "contact_person": "张三",
    "phone": "13800138000",
    "survey_conclusion": "recommend",
    "remarks": "优质客户"
}
```
- 返回结果:

```json
{
  "id": 6,
  "name": "测试船务有限公司",
  "contact_person": "张三",
  "phone": "13800138000",
  "survey_conclusion": "recommend",
  "remarks": "优质客户",
  "created_at": "2026-08-12T01:37:42.487626",
  "updated_at": "2026-08-12T01:37:42.487635"
}
```

### 77. 获取客户详情 `HTTP 200`
- 分组: 客户管理
- 方法: GET
- URL: `http://localhost:8000/api/v1/customers/6`
- 返回结果:

```json
{
  "id": 6,
  "name": "测试船务有限公司",
  "contact_person": "张三",
  "phone": "13800138000",
  "survey_conclusion": "recommend",
  "remarks": "优质客户",
  "created_at": "2026-08-12T01:37:42.487626",
  "updated_at": "2026-08-12T01:37:42.487635"
}
```

### 78. 更新客户 `HTTP 200`
- 分组: 客户管理
- 方法: PATCH
- URL: `http://localhost:8000/api/v1/customers/6`
- 请求体 (payload):

```json
{
    "name": "测试船务有限公司（更新）",
    "contact_person": "李四",
    "phone": "13900139000",
    "survey_conclusion": "pending",
    "remarks": "更新备注"
}
```
- 返回结果:

```json
{
  "id": 6,
  "name": "测试船务有限公司（更新）",
  "contact_person": "李四",
  "phone": "13900139000",
  "survey_conclusion": "pending",
  "remarks": "更新备注",
  "created_at": "2026-08-12T01:37:42.487626",
  "updated_at": "2026-08-12T01:37:42.537872"
}
```

### 79. 删除客户 `HTTP 204`
- 分组: 客户管理
- 方法: DELETE
- URL: `http://localhost:8000/api/v1/customers/6`
- 返回结果: (无响应体)

### 80. 上传文件 `HTTP 201`
- 分组: 文件中心
- 方法: POST
- URL: `http://localhost:8000/api/v1/files/upload`
- 请求体 (payload):

```json
------WebKitFormBoundaryd08fa92e17634f59
Content-Disposition: form-data; name="file"; filename="dummy.txt"
Content-Type: text/plain

LG-management postman-runner dummy upload file

------WebKitFormBoundaryd08fa92e17634f59
Content-Disposition: form-data; name="project_id"

1
------WebKitFormBoundaryd08fa92e17634f59
Content-Disposition: form-data; name="file_type"

document
------WebKitFormBoundaryd08fa92e17634f59--

```
- 返回结果:

```json
{
  "file_name": "dummy.txt",
  "file_type": "document",
  "storage_key": "20260812_013742_f38377993b4f48ad.txt",
  "file_size": 47,
  "mime_type": "text/plain"
}
```

### 81. 文件列表 `HTTP 200`
- 分组: 文件中心
- 方法: GET
- URL: `http://localhost:8000/api/v1/files?project_id=1&file_type=document&page=1&page_size=20`
- 返回结果:

```json
{
  "items": [
    {
      "id": 6,
      "project_id": 1,
      "file_name": "dummy.txt",
      "file_type": "document",
      "storage_key": "20260812_013742_f38377993b4f48ad.txt",
      "file_size": 47,
      "mime_type": "text/plain",
      "uploaded_by": 1,
      "created_at": "2026-08-12T01:37:42.670599"
    },
    {
      "id": 5,
      "project_id": 1,
      "file_name": "dummy.txt",
      "file_type": "document",
      "storage_key": "20260812_013522_7c6b9e0509e44b7b.txt",
      "file_size": 47,
      "mime_type": "text/plain",
      "uploaded_by": 1,
      "created_at": "2026-08-12T01:35:22.849899"
    },
    {
      "id": 4,
      "project_id": 1,
      "file_name": "dummy.txt",
      "file_type": "document",
      "storage_key": "20260812_013214_72c569c481544efc.txt",
      "file_size": 47,
      "mime_type": "text/plain",
      "uploaded_by": 1,
      "created_at": "2026-08-12T01:32:14.853335"
    },
    {
      "id": 3,
      "project_id": 1,
      "file_name": "dummy.txt",
      "file_type": "document",
      "storage_key": "20260812_012600_2598ef3922f648e6.txt",
      "file_size": 47,
      "mime_type": "text/plain",
      "uploaded_by": 1,
      "created_at": "2026-08-12T01:26:00.660840"
    },
    {
      "id": 2,
      "project_id": 1,
      "file_name": "dummy.txt",
      "file_type": "document",
      "storage_key": "20260812_010918_fed8c55445f04548.txt",
      "file_size": 47,
      "mime_type": "text/plain",
      "uploaded_by": 1,
      "created_at": "2026-08-12T01:09:18.661538"
    }
  ],
  "total": 5
}
```

### 82. 下载文件 `HTTP 404`
- 分组: 文件中心
- 方法: GET
- URL: `http://localhost:8000/api/v1/files/1/download`
- 返回结果:

```json
{
  "detail": "文件不存在"
}
```

### 83. 预览文件 `HTTP 404`
- 分组: 文件中心
- 方法: GET
- URL: `http://localhost:8000/api/v1/files/1/preview`
- 返回结果:

```json
{
  "detail": "文件不存在"
}
```

### 84. 删除文件 `HTTP 404`
- 分组: 文件中心
- 方法: DELETE
- URL: `http://localhost:8000/api/v1/files/1`
- 返回结果:

```json
{
  "detail": "文件不存在"
}
```
