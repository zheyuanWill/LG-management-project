# 业务逻辑 / 前后端对齐审计报告（基于当前真实代码）

> 范围：只看仓库里**现在的前端 `frontend/src` 和后端 `backend` 代码**，不参考任何重构方案。
> 证据：前端 Explore 静态扫描 + 后端 `routers/`、`services/`、`tasks/` 源码精读 + ai-service 与后端接口**实测**。
> 时间：2026-08-12。ai-service `/v1/embed` 当前**在线**（fastembed，dim 512），与早前"已禁用"的旧记录相反——已更正。

---

## 0. 一句话结论

- **前端和后端严重不对齐**：现有前端大量表单字段名/路径写错，提交会 422/404，或静默丢弃字段；知识库问答、随手存、AI 风险检测三个"智能"功能在前端**要么调错接口、要么整体是 mock**。
- **后端本身可用**，但"AI 风险检测"名不副实——它是**纯规则引擎**，没用知识库、也没读每天的任务备注/图片。
- **知识库问答后端是能正确回答的**（实测返回带引用的答案）；只是前端调了错误端点 `/knowledge/ask` → 永远 404。
- **随手存后端有真 AI（LLM 提取 + OCR + 关键词匹配建议项目）**，但前端是 `setTimeout` 假数据，后端从未被调用。

---

## 1. 前端字段是否和后端字段对齐？有没有"后端有、前端没收集→没存进去"的情况？

**结论：大量不对齐。** 下表是逐个表单核对的结果（前端 `src/` 实际代码 vs 后端 `schemas/`）：

| 表单 | 前端发送的字段 | 后端期望 | 后果 |
|------|----------------|----------|------|
| 任务创建 `TaskList.tsx` | `title, status, priority, due_date, description` | `name, planned_end_date, status, sort_order` | `title`≠`name`(必填缺失→**422**)；`priority/description` 丢失 |
| 任务日报 `DailyUpdateForm.tsx` | `task_id, status, remark, date, photos[]` | `update_date, status, remark, audio_duration` | `date`≠`update_date`(→**422**)；photos 从不被上传 |
| 日报确认 `daily.$date.tsx` | PATCH `…/daily-reports/{date}` `{tomorrow_plan, risk_reminders, confirmed}` | 确认是 `POST …/{id}/confirm`；更新是 `…/{id}` `{tomorrow_plan, risk_alert, completed_items}` | 路径错(date≠id→**404**)；`risk_reminders`≠`risk_alert`(丢失)；`confirmed` 被忽略 |
| 知识库文档上传 `DocUploader.tsx` | FormData `file, category` | 还要求必填 `title` | 缺 `title`→**422** |
| 知识库问答 `QAChat.tsx` | `POST /knowledge/ask` `{question}` | `POST /knowledge/query` `{query, top_k, category}` | 路径+字段全错→**404** |
| 客户 `CustomerForm.tsx` | `name, contact_person, phone, email, notes` | `name, contact_person, phone, survey_conclusion, remarks` | `email` 后端无列→**丢失**；`survey_conclusion` **从不发送**（塞进了 notes） |
| 客户展示 `customers.tsx` | 读 `customer.notes` / `survey_conclusion` | 后端返回 `remarks` / `survey_conclusion`（无 `notes`） | 结论/备注**永不显示** |
| 文件上传 `FileUploader.tsx` | `POST /files` `file, project_id, type` | `POST /files/upload` `file, project_id, file_type` | 路径错→**404**；`type`≠`file_type` |
| 备件 `SparePartForm.tsx` | `name, part_no, quantity, unit, customer_id` | `item_name, model_or_drawing, quantity` | `name`≠`item_name`(→**422**)；`unit/customer_id` 丢失 |
| 备件照片 `SparePhotos.tsx` | `POST /projects/{id}/photos` `type:'logo_package'` | `POST /projects/{id}/spare-photos` `photo_type∈{logo,loading}` | 路径错→**404**；枚举非法 |
| 物流节点 `LogisticsTimeline.tsx` | `type, date, tracking_no, remark` | `node_type, node_date, tracking_no, remark` | `type`≠`node_type`、`date`≠`node_date`→**422**；枚举值与后端不符 |
| HK 签收 `HKSignature.tsx` | FormData `file, sign_date`；PATCH `{sign_date}` | JSON `{signature_file_key, signed_at}` | 格式错；`sign_date`≠`signed_at`；文件 key 永不写入 |
| 发票 `InvoiceForm.tsx` | `title, tax_no, amount, purpose` | `title, tax_number, amount, purpose` | `tax_no`≠`tax_number`→**税号永不保存** |
| 调研 `SurveyForm.tsx` | `{conclusion, details}` | `{conclusion, survey_detail}` | `details`≠`survey_detail`→**详情永不保存**；UI 又读 `details`→**永不显示** |
| 修船移交 `RepairHandover.tsx` | `PATCH /projects/{id}/handover` `{handed_over, handed_over_at}` | `POST /projects/{id}/repair-brokerage/{repair_id}/handover`(无 body) | 路由错→**404** |
| 合同展示 `ContractUpload.tsx` | 读 `contract.name` / `contract.url` | 后端只返回 `id, moa_file_key, created_at` | **名称空白** |

**后端有、前端从不收集/显示的字段（数据丢失或界面空白）：**
- `Customer.survey_conclusion`、`remarks`（前端根本不渲染）
- `RiskEvent.title/detail/risk_level`（前端读 `message/level/category` → 全是空/默认）
- 周报 `progress_total` / `key_events`（前端展示但后端无这两字段 → 永远空）
- 合同文档 `name` / `url`（后端无 → 前端空白）
- 任务 `note` / `photos`（后端 `TaskResponse` 根本没有这两个字段，方案想存的备注+照片落不了库）

> 这些"前端漏字段"在**当前前端**是真实 bug；如果按你的方案从零重写前端，则这些问题随重写消失，只需保证新前端严格按 `schemas/` 契约写。

---

## 2. 前端问知识库，能否正确回答？

**后端能正确回答，前端调错接口。** 实测：

```
POST /api/v1/knowledge/query  {"query":"修船规范有哪些要求","top_k":3}
→ 200，返回带引用的真实答案（引用自《船舶修理SOP标准流程》chunk 0/1，score 0.71/0.65）
```

后端链路（`routers/knowledge.py → rag_service.query`）：
1. `ai_client.embed(question)` 拿向量（**直播可用**，fastembed dim 512）；
2. 在 `knowledge_embeddings` 里做余弦相似度取 top_k；
3. 把命中的 chunk 拼进 system+user prompt，调 `ai_client.chat`（deepseek）生成答案；
4. 返回 `{answer, citations[{document_id, document_title, chunk_text, score}]}`。

**但前端 `QAChat.tsx` 调的是 `POST /knowledge/ask` 且 body 是 `{question}`** —— 后端根本没有这个路由 → **永远 404**。所以用户在界面上"问不出东西"，不是知识库不行，是前端接错线。

⚠️ 前提：文档必须**带着 embedding 入库**才能被检索。早期 embedding 被禁用时入库的文档 `knowledge_embeddings` 是空的，会返回"未找到相关内容"——重新上传一次即可（现在 embedding 在线）。

---

## 3. 怎么证明"AI 是根据知识库 + 理解每天任务的备注/图片来生成风险"？

**结论：当前代码做不到，也不能证明——因为这个能力根本没实现。**

后端的"AI 风险检测"链路：`POST /projects/{id}/risks/ai-detect` → Celery `detect_risks_task` → `risk_service.detect_risks(db, project_id)`。

精读 `risk_service.py` 的 `detect_risks`，它做的事**只有这几条硬编码规则**：
- 未启动任务占比 > 50% → "大量任务未启动"(warning)
- 进行中任务 `planned_end_date` 早于今天 → "X 个任务已逾期"(critical)
- 完成率 < 30% 且项目 active → "项目完成率偏低"(info)

**它：**
- ❌ **没有调用任何 LLM / 大模型**（整段无 `ai_client.chat/embed`）；
- ❌ **没有检索知识库**（不碰 `knowledge_*` 表）；
- ❌ **没有读取每天的任务备注/图片**（`TaskDailyUpdate` 的 remark/photos 完全没被读，只读了 `Task.status` 和 `planned_end_date`）；
- 纯粹是"按任务状态+日期数数"的确定性规则，却命名为"AI 检测风险"。

所以：**无法证明**它用了知识库或理解了日报备注/图片，因为代码里就没有这一步。如果你要的是方案里描述的"结合知识库规范 + 读懂每日任务备注和现场照片来生成风险"，那是**尚未开发的功能**，需要新写（检索知识库相关条款 + 把日报备注/图片 OCR 文本作为上下文喂给 LLM + 结构化输出风险）。当前的"AI 风险"建议改名为"自动进度检查"，避免误导。

---

## 4. 项目里有没有硬编码行为？

**有，集中在前端，且部分是"假功能"：**

- **随手存整体 mock**（`routes/quick-save.tsx`）：`setTimeout(...,1000)` 模拟识别，`projects:[{id:'1',name:'远洋一号',confidence:0.92},…]` 写死三条假数据；"确认关联"只是 `alert(...)` 然后清状态，**完全不调后端**。
- **备件客户下拉写死**（`SparePartForm.tsx`）：`customer_1..customer_4`（中远海运/马士基…）且是**字符串 id**，后端 `owner_id` 是**整数** → 即便传上去也对不上。
- **物流节点类型写死且错误**（`LogisticsTimeline.tsx`）：`order_placed/arrived_port/shipped_to_owner/settlement_done`，后端枚举是 `ordered/arrived/sent_to_owner/settled` → 直接 422。
- **`RiskDetail.tsx` 用裸 `fetch('/api/v1/risks/.../analyze')`** 绕过统一 `apiClient`（且端点不存在，404）。
- 后端侧：风险阈值（0.5 / 0.3）、`project_no` 生成规则属于业务逻辑常量，不算"坏硬编码"；未发现后端有 localhost/端口/写死 ID 之类的问题。

---

## 5. 随手存的"AI 识别"是怎么做的？能不能不要？

**后端实现（`routers/quick_saves.py` + `services/quick_save_service.py`）：**
1. 文字：`recognize_content("text", text)` → 把粘贴文本发给 LLM（deepseek-chat），system prompt 要求抽取"项目名称/船名/日期/金额"等 → 返回 `recognized_text`。
2. 图片：`recognize_content("image", bytes)` → 先调 ai-service `/v1/ocr` 做 OCR 出文字，再交给同一个 LLM 抽取结构化信息（返回 `recognized_text` + `ocr_text`）。
3. `suggest_projects(db, recognized_text)`：把抽取出的关键词和**活跃项目**的 `ship_name/project_no/remarks` 做子串匹配打分，返回 top5 候选项目。

**这个功能的价值**：让用户（尤其老板手机端）随手拍一张微信截图/合同/订单，或粘贴一段文字，**自动抽出关键信息并推荐归属哪个项目**，少打字、少选。AI 部分是"加速器"。

**能不能不要？可以，但要分清层级：**
- **OCR + LLM 抽取**：图片场景没有它就得手抄，价值最高；文字场景可省（直接粘贴也算"随手存"）。
- **项目自动推荐**：纯便利，可保留可去掉（去掉就改成手动选项目）。
- **最省事方案**：保留"上传图片/文字 → 存库 → 手动选归属项目"，砍掉 AI 抽取与推荐——功能仍在，只是没那么"智能"。

> 注意：图片 OCR 依赖 `settings.OCR_ENABLED` 与对应模型；若该开关没开，`ocr()` 返回空串，图片识别会静默失效（只存原图，不抽文字）。

---

## 6. 其他值得说的点（前端有、后端无 / 反之）

- **周报无编辑器**：`WeeklyReportCard.tsx` 只展示，后端 `generate` 返回异步 task，前端**不轮询**结果 → 周报永远看不到生成内容；且展示的 `progress_total`/`key_events` 后端根本没有。
- **日报 AI 生成不轮询**：`generate` 返回 `{task_id, status:"pending"}`（Celery 异步），前端拿到后什么都不填，也没有轮询 → "AI 生成中"之后没下文。
- **WebSocket 类导出但从未使用**（`lib/websocket.ts`）——死代码。
- **`/projects/{id}/stats` 前端已定义但从未调用**。

---

## 7. 需要你拍板的不确定点（见随附提问）

1. **当前前端是"要修"还是"要扔掉重写"？** 如果是按你的方案从零重写，那么第 1 节那些"字段不对齐"会随重写消失，我只需保证后端契约清晰 + 新前端严格对齐；如果是要修当前前端，我可以把这些 422/404 逐个改对。
2. **风险"AI"要不要做成真 AI？** 目前是规则引擎。你要的是"结合知识库+日报备注/图片"的真 AI，还是先把名不副实的"AI"改名、后续再说？
3. **随手存的 AI 识别保留 / 简化 / 砍掉？**
4. **知识库问答前端接错线**——修前端接线，还是等重写时一并处理？

---
