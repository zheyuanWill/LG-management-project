# Project Memory — LG-management-project

## Network / build constraints (KEY — learned 2026-08-11)
This dev environment (CN network) blocks/throttles many package sources. Docker builds fail unless mirrors are configured.

**Working mirrors (bake into Dockerfiles / compose):**
- PyPI: `https://mirrors.aliyun.com/pypi/simple` — FULL mirror, serves wheels itself. PREFERRED.
  - Do NOT use Tuna PyPI (`pypi.tuna.tsinghua.edu.cn`): it is *lazy* and 302-redirects uncached packages to the blocked `files.pythonhosted.org` → ReadTimeout. (Tuna Debian apt mirror IS fine.)
- Debian apt: `https://mirrors.tuna.tsinghua.edu.cn/debian` works.
- npm: `https://registry.npmmirror.com` works.
- PyTorch CPU wheels: `https://download.pytorch.org/whl/cpu` is reachable directly (4+ MB/s).

**Broken / blocked:**
- `hf-mirror.com` (HuggingFace mirror) — SSL EOF / read timeouts. Do NOT rely on it.
- Docker Hub base image pull needs a registry mirror or the daemon must reach `auth.docker.io` (set Docker Desktop → Settings → Docker Engine → registry-mirrors, e.g. `https://docker.m.daocloud.io`).
- Host has a proxy at `127.0.0.1:7890` but it does NOT forward PyPI/Docker Hub; and containers can't reach the host loopback anyway.

## ai-service embedding model
- **UPDATED 2026-08-12 (verified live):** ai-service `/v1/embed` is NOW WORKING — uses `fastembed` (BAAI/bge-small, dim 512), model downloaded + cached to `/cache/models`. `/v1/embed` returns 200 with real vectors; `/v1/chat` works (deepseek-chat); OCR depends on `settings.OCR_ENABLED`.
- Earlier note (2026-08-11) that embeddings were disabled/503 is STALE — the image was rebuilt with fastembed and now embeddings function. `rag_service.query()` (knowledge Q&A) therefore works end-to-end IF docs were ingested with embeddings (KnowledgeEmbedding rows exist). Existing docs ingested while embedding was disabled have empty embeddings → re-upload to populate.
- `ai_client.embed()` returns `[]` on any HTTP error → rag_service returns "AI服务暂时不可用" fallback; `ai_client.chat/ocr` return error strings on failure (degrade gracefully, no crash).

## Build notes
- Base image pinned to `python:3.12-slim-bookworm` (the `python:3.12-slim` tag now tracks trixie, whose apt index 404s).
- ai-service image is now LIGHT (no torch) → fast, reliable build. Embeddings are opt-in.

## Start stack
- Only the `lg-management-project` compose project should run. Another project `lg-management-backend` (containers `lgm-*`) existed and was removed.
- Run: `docker compose up -d postgres redis minio backend frontend ai-service` (skip celery unless needed).
- Endpoints: frontend :3000, backend :8000, ai-service :8001.

## Backend test insights (added 2026-08-12)
- Postman collection `LG-Management-API.postman_collection.json` has 84 requests. A stdlib-only runner `postman_runner.py` replays it in order, emulates the collection's `test` scripts (variable capture: token/project_id/task_id/customer_id/save_id/doc_id), and writes `api_test_report.md` + `api_test_report.json` with every request payload + response.
- **Backend bugs fixed during collection testing:**
  1. Celery async tasks failed (`no current event loop`) — added `app/async_utils.py` `run_async()` using a **persistent per-thread event loop** (NOT `asyncio.run`, which closes the loop and breaks SQLAlchemy's connection pool). Used by `tasks/{report_tasks,risk_tasks,knowledge_tasks}.py`.
  2. `GET /daily-reports/{id}` 500 (ValidationError: completed_items dict vs list) — relaxed `DailyReportResponse.completed_items` to `Any`.
  3. DELETE knowledge document 500 (FK violation on `knowledge_embeddings`) — delete the loaded ORM instance so the `all, delete-orphan` cascade fires first.
- Note: ~17-19 collection requests return non-2xx purely from collection wiring (single `project_id` var overwritten by 4 create-project calls; hardcoded IDs like `report_id=1`/`file_id=1`; GET-before-CREATE probe ordering) — NOT backend defects. Reruns also create leftover `newuser` (409) and leftover daily-update photos (403 limit=2).

## API field-completeness audit (added 2026-08-12)
- Deliverable: `api_field_audit.md` — per-endpoint verdict on whether returned fields are complete for a CRUD/mobile frontend.
- **REAL defect (P0):** `POST /files/upload` (`FileUploadResponse` in `schemas/file.py`) does NOT return `id`, yet `/files/{id}/download|preview|delete` key off the integer PK. So after upload the frontend cannot reference the file → root cause of many "文件不存在". Fix: add `id: int` to `FileUploadResponse` (one-liner).
- **Design gaps (P1/P2), interfaces don't crash but lack front-end-needed data:**
  - `GET /projects` (list) & `GET /projects/{id}` (detail) return bare `ProjectResponse` — NO joined `customerName`/`customerPhone`, NO `riskSummary`, NO `hasUnconfirmedReport` red-dot flag. Frontend card needs all three.
  - 8 sub-resources (调研/商务/合同/修船经纪/备件/物流/HK签收/发票) GET returns 404 "不存在" when not yet created (correct REST, bad UX) — recommend 200+null or a unified `/projects/:id/info` GET/PUT.
  - `GET /auth/me` (`UserResponse`) has NO `phone` AND `models/user.py` User has no phone field at all — blocks GM-role判断 + click-to-call.
  - Knowledge docs (`KnowledgeDocument`) store `file_key` directly, bypass the `files` table, and `routers/knowledge.py` has NO download/preview endpoint — scheme's `/files/:id/download` won't serve them.
  - Risks return raw `RiskEventResponse[]` with no aggregated `summary` string for the card red-dot.
  - `TaskResponse` has NO `note` / `photos` fields, but the plan's `/tasks/:id` PATCH needs `{status, note, photos}` — can't persist note/photos.
- Confirmed NON-bug: `#13 GET /projects/{id}` 404 in the report was a transient uvicorn `--reload` artifact (live repeat = 200). Don't touch the projects router for that.

## Frontend direction decision (2026-08-12)
- User LIKES the current UI style/layout/components — **do NOT rewrite the frontend from scratch**. Keep the visual shell.
- Root problems are in the **data-wiring layer**, not the UI: many forms send wrong endpoint paths or wrong field names (→ 422/404 / silently dropped data), plus mocked/hardcoded behaviors. Decision = **repair the wiring**, not rebuild.
- Verified frontend↔backend mismatches (mechanical fixes, P0): task-create `title`→`name`; daily-report confirm path + `risk_reminders`→`risk_alert`; knowledge QA `/knowledge/ask`→`/knowledge/query` + `question`→`query` (backend works, frontend 404s); customer `survey_conclusion` never sent + `email` has no backend column; invoice `tax_no`→`tax_number`; survey `details`→`survey_detail`; repair-handover route wrong; logistics node `type/date`→`node_type/node_date` + enum mismatch; spare-part customer dropdown hardcoded string ids (backend ints); `RiskDetail` uses bare `fetch` instead of unified client.
- Mocked/hardcoded to remove: quick-save (`setTimeout` + fake "远洋一号" data + `alert`) is fully mocked — backend AI (`ai_client.chat`/`ocr`) is real but never called.
- **Recommendation defaults (pending user confirm):** (1) fix-not-rewrite frontend; (2) keep risk rule-engine but RELABEL "自动进度检查" (it's NOT AI — `risk_service.detect_risks` is threshold rules, no LLM/knowledge-base/daily-notes); (3) keep quick-save AI recognition and actually wire it (genuine differentiator), degrade OCR failures gracefully.
- Containers: frontend is Vite (hot-reload, no rebuild needed for frontend fixes); only backend changes need `docker compose up -d backend` / `docker restart lg-backend`.
- Deliverables this session: `api_test_report.md/.json`, `postman_runner.py`, `api_field_audit.md`, `business_logic_audit.md`, `recommendation.md`.
