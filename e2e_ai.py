"""
LG-Management AI 重构后的 e2e 冒烟测试（真实运行栈，零 mock）。

覆盖 2026-08-19 AI 重构的 5 个功能，全部通过才退出 0：
  - rag-multi-format      : 多格式文档清洗 + 按章节切分 + 向量入库 + 章节化 citation
  - risk-ai-scan          : 规则扫描 + RAG 检索 + LLM 综合判断（同步返回风险列表）
  - quick-save-text       : 随手存文本 → LLM structured output 提取字段
  - daily-report-propose  : 日报草稿（结构化明日计划 + 风险）HITL 入口
  - weekly-report-generate: 周报同步生成（DeepSeek structured output）

依赖：标准库 urllib + requests（multipart 文档上传更顺手）。
用法：python e2e_ai.py

注意：
  - DeepSeek API 真实调用，单次测试整体耗时约 1-3 分钟（取决于网络与 LLM 响应）。
  - 测试结束自动清理创建的文档 / 周报 / 项目，保持 dev 库干净。
"""
import json
import sys
import time
import urllib.request
import urllib.error
import urllib.parse

try:
    import requests
except ImportError:
    print("FATAL: 请先 pip install requests")
    sys.exit(2)

BASE = "http://localhost:8000/api/v1"
TIMEOUT = 90  # DeepSeek 调用可能较慢，统一 90s


def rest(method, path, token=None, body=None, timeout=TIMEOUT):
    url = BASE + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode()
            return resp.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw
    except urllib.error.URLError as e:
        return -1, f"URLError: {e}"


def assert_eq(name, cond, extra=""):
    if cond:
        print(f"  [PASS] {name}")
    else:
        print(f"  [FAIL] {name} {extra}")
        raise SystemExit(1)


def login():
    s, d = rest("POST", "/auth/login", body={"username": "admin", "password": "admin123"})
    assert_eq("login", s == 200 and d and "access_token" in d, f"{s} {d}")
    return d["access_token"]


# ── multipart 上传文档 ─────────────────────────────────────────────
def upload_doc(token, title, content_bytes, ext, category=None):
    """构造 multipart/form-data 上传文档。返回 (status, json)。"""
    url = BASE + "/knowledge/documents"
    boundary = "----e2e_boundary_" + str(int(time.time()))
    parts = []
    # title field
    parts.append(f"--{boundary}\r\n".encode())
    parts.append(b'Content-Disposition: form-data; name="title"\r\n\r\n')
    parts.append(title.encode() + b"\r\n")
    if category:
        parts.append(f"--{boundary}\r\n".encode())
        parts.append(b'Content-Disposition: form-data; name="category"\r\n\r\n')
        parts.append(category.encode() + b"\r\n")
    # file field
    filename = f"doc.{ext}"
    parts.append(f"--{boundary}\r\n".encode())
    parts.append(
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode()
    )
    parts.append(b"Content-Type: application/octet-stream\r\n\r\n")
    parts.append(content_bytes + b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    body = b"".join(parts)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    }
    r = requests.post(url, data=body, headers=headers, timeout=TIMEOUT)
    try:
        return r.status_code, r.json()
    except Exception:
        return r.status_code, r.text


def main():
    token = login()
    print("login OK")

    # ── 建一个 supervision 项目 + 任务，作为后续 AI 端点的载体 ──────
    print("\n== setup: 创建 supervision 项目 + 任务 ==")
    proj_no = f"LG-SV-AI-E2E-{int(time.time()) % 100000:05d}"
    s, proj = rest("POST", "/projects", token=token, body={
        "project_no": proj_no,
        "ship_name": "E2E AI Test Ship",
        "type": "supervision",
        "status": "active",
    })
    assert_eq("创建 supervision 项目", s in (200, 201) and proj, f"{s} {proj}")
    pid = proj["id"]
    print(f"project id={pid}")

    s, task = rest("POST", f"/tasks/projects/{pid}/tasks", token=token, body={
        "name": "主机大修",
        "planned_end_date": "2026-09-30",
        "status": "in_progress",
        "progress": 60,
    })
    assert_eq("创建任务(planned_end_date+progress)", s in (200, 201) and task, f"{s} {task}")
    tid = task["id"]

    # ──────────────────────────────────────────────────────────────
    # Feature 1: RAG 多格式 ingest + 章节化 citation
    # ──────────────────────────────────────────────────────────────
    print("\n== rag-multi-format ==")

    # 1a. 上传一个 Markdown 文档（含清晰的章节标题，方便测试章节切分）
    md_content = """# 船舶修理质量验收手册

## 第一章 船体部分

### 第一节 船壳板
船壳板厚度应符合规范要求，不得有明显凹陷、裂纹。测厚点应均匀分布。

### 第二节 舱口盖
舱口盖密封条应完整无老化，水密试验保压 15 分钟无渗漏。

## 第二章 轮机部分

### 第一节 主机
主机大修后应进行系泊试验，连续运转 4 小时无异常振动。
曲轴臂距差应小于 0.15mm/m。

### 第二节 副机
副机负载切换试验，主副机并车稳定运行 30 分钟。
"""
    s, doc_md = upload_doc(token, "船舶修理质量验收手册", md_content.encode("utf-8"), "md")
    assert_eq("上传 Markdown 文档", s == 201 and doc_md.get("id"), f"{s} {doc_md}")
    md_id = doc_md["id"]
    # original_text 应非空（清洗后全文），且不含 [INGEST REJECTED]
    assert_eq(
        "Markdown ingest 后 original_text 已清洗填充",
        doc_md.get("original_text") and "[INGEST REJECTED]" not in (doc_md.get("original_text") or ""),
        f"original_text={doc_md.get('original_text')[:200] if doc_md.get('original_text') else None}"
    )

    # 1b. 不支持的文件类型应返回 400
    s, rej = upload_doc(token, "bad.jpg", b"\xff\xd8\xff\xe0", "jpg")
    assert_eq("不支持的文件类型被拒绝(400)", s == 400, f"got {s} {rej}")

    # 1c. 查询：验证 citations 含 chunk_text + score，章节化字段（book_title/chapter/section）
    # Markdown 的 chapter heading 会触发章节切分，citation 应携带 chapter/section
    s, q = rest("POST", "/knowledge/query", token=token, body={
        "query": "主机大修后要做什么试验？",
        "top_k": 5,
    })
    assert_eq("RAG 查询返回 200", s == 200 and q is not None, f"{s} {q}")
    citations = (q or {}).get("citations", []) or []
    assert_eq(
        "RAG 查询返回 citations 列表(>=1)",
        len(citations) >= 1 and citations[0].get("chunk_text"),
        f"citations={citations}"
    )
    # 至少一条 citation 命中我们刚上传的手册（document_id == md_id）
    hit = [c for c in citations if c.get("document_id") == md_id]
    assert_eq("查询命中刚上传的手册", len(hit) >= 1, f"hits={hit}")
    # chunk_text 应包含上下文片段（如"主机"或"系泊试验"或"曲轴"）
    hit_text = hit[0].get("chunk_text", "")
    assert_eq(
        "命中 chunk 内容与查询相关",
        any(kw in hit_text for kw in ["主机", "系泊", "曲轴", "试验"]),
        f"chunk_text={hit_text[:200]}"
    )
    # 章节化字段：至少有 chapter 或 section 之一被填充（Markdown 章节标题触发的）
    has_chapter = any(c.get("chapter") or c.get("section") for c in citations)
    assert_eq("citation 含章节元数据(chapter/section)", has_chapter, f"citations={citations}")

    # 1d. answer 非空（DeepSeek 综合回答）
    assert_eq("RAG answer 非空", bool((q or {}).get("answer")), f"answer={(q or {}).get('answer')[:200] if q else None}")

    # ──────────────────────────────────────────────────────────────
    # Feature 2: 风险检测 AI 综合（规则 + RAG + LLM）
    # ──────────────────────────────────────────────────────────────
    print("\n== risk-ai-scan ==")
    s, risks = rest("POST", f"/risks/projects/{pid}/risks/scan", token=token)
    assert_eq("风险扫描返回 200", s == 200, f"{s} {risks}")
    assert_eq("风险扫描返回 list", isinstance(risks, list), f"risks={risks}")
    # 规则扫描至少能扫到风险（progress=60 不会触发未开始>50%；但 LLM 综合判断通常会给）
    # 这里放宽：list 可以为空（LLM 判断无风险也是合法），只要调用链路通
    print(f"    扫描出 {len(risks)} 条风险")
    for r in (risks or [])[:3]:
        assert_eq(
            f"风险字段完整(title={r.get('title', '')[:20]})",
            r.get("title") and r.get("risk_level"),
            f"risk={r}"
        )

    # ──────────────────────────────────────────────────────────────
    # Feature 3: 随手存文本 → LLM structured output 提取
    # ──────────────────────────────────────────────────────────────
    print("\n== quick-save-text ==")
    text_input = "NACC Procida IMO 9018345 今天抵达大连港，主机曲轴臂距差超差，需要安排大修"
    # text 是 query param，URL 编码
    s, qs = rest("POST", f"/quick-saves/text?{urllib.parse.urlencode({'text': text_input})}", token=token)
    assert_eq("随手存文本创建 201", s == 201 and qs, f"{s} {qs}")
    save_id = qs["save"]["id"]
    # recognized_text 应非空（AI 提取的结构化结果或原文）
    assert_eq(
        "随手存 recognized_text 非空(AI 提取)",
        bool(qs["save"].get("recognized_text")),
        f"save={qs['save']}"
    )
    # suggestions 是 list（可能为空，如果没有匹配项目）
    assert_eq("随手存返回 suggestions list", isinstance(qs.get("suggestions"), list), f"suggestions={qs.get('suggestions')}")
    # 清理：标记 deleted
    s, _ = rest("PATCH", f"/quick-saves/{save_id}", token=token, body={"status": "deleted"})
    assert_eq("清理随手存记录", s == 200, f"{s}")

    # ──────────────────────────────────────────────────────────────
    # Feature 4: 日报 propose + finalize（结构化明日计划 + 风险，HITL 入口）
    # ──────────────────────────────────────────────────────────────
    print("\n== daily-report-propose ==")
    from datetime import date as _date
    today_iso = _date.today().isoformat()
    s, dr = rest("POST", f"/reports/projects/{pid}/daily-reports/propose", token=token)
    assert_eq("日报 propose 返回 200", s == 200 and dr is not None, f"{s} {dr}")
    # 结构化字段：today_work / tomorrow_candidates / risk_alert
    for field in ("today_work", "tomorrow_candidates", "risk_alert"):
        assert_eq(f"日报草稿含字段 {field}", field in dr, f"keys={list(dr.keys()) if isinstance(dr, dict) else dr}")
    # tomorrow_candidates 应是 list
    assert_eq("tomorrow_candidates 是 list", isinstance(dr.get("tomorrow_candidates"), list), f"tomorrow_candidates={dr.get('tomorrow_candidates')}")
    # today_work 应非空（有任务+每日更新时）
    assert_eq("today_work 非空", bool(dr.get("today_work")), f"today_work={dr.get('today_work')}")

    # finalize：把 propose 的 candidates 落库为 confirmed 日报，供周报 AI 路径使用
    s, fr = rest("POST", f"/reports/projects/{pid}/daily-reports/finalize", token=token, body={
        "report_date": today_iso,
        "today_work": dr.get("today_work"),
        "tomorrow_items": dr.get("tomorrow_candidates", []),
        "risk_alert": dr.get("risk_alert"),
        "confirmed": True,
    })
    assert_eq("日报 finalize 落库 200", s == 200 and fr.get("id"), f"{s} {fr}")
    assert_eq("日报 confirmed=True", fr.get("confirmed") is True, f"confirmed={fr.get('confirmed')}")

    # ──────────────────────────────────────────────────────────────
    # Feature 5: 周报 generate（DeepSeek structured output 一次出 {summary, next_week_plan}）
    # ──────────────────────────────────────────────────────────────
    print("\n== weekly-report-generate ==")
    s, wr = rest("POST", f"/reports/projects/{pid}/weekly-reports/generate", token=token)
    assert_eq("周报 generate 返回 200", s == 200 and wr is not None, f"{s} {wr}")
    # 结构化字段：summary / next_week_plan / source
    for field in ("summary", "next_week_plan", "source"):
        assert_eq(f"周报含字段 {field}", field in wr, f"keys={list(wr.keys()) if isinstance(wr, dict) else wr}")
    # 有 confirmed 日报，source 应为 'ai'
    assert_eq("周报 source=ai(有 confirmed 日报)", wr.get("source") == "ai", f"source={wr.get('source')}")
    assert_eq("周报 summary 非空(AI 生成)", bool(wr.get("summary")), f"summary={wr.get('summary')}")
    assert_eq("周报 next_week_plan 非空", bool(wr.get("next_week_plan")), f"next_week_plan={wr.get('next_week_plan')}")
    # 清理：删掉落库的周报（如果有 report_id）
    if wr.get("report_id"):
        s, _ = rest("DELETE", f"/reports/weekly-reports/{wr['report_id']}", token=token)
        assert_eq("清理周报", s == 204, f"{s}")

    # ── 清理测试数据 ──────────────────────────────────────────────
    print("\n== cleanup ==")
    # 删知识库文档（级联删 embeddings）
    s, _ = rest("DELETE", f"/knowledge/documents/{md_id}", token=token)
    assert_eq("删除测试知识文档", s == 204, f"{s}")
    # 删项目（级联删任务/每日更新/风险/报表）
    s, _ = rest("DELETE", f"/projects/{pid}", token=token)
    assert_eq("删除测试项目", s in (200, 204), f"{s}")

    print("\nALL AI E2E CHECKS PASSED ✅")


if __name__ == "__main__":
    main()
