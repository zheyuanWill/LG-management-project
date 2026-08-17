"""
LG-Management 全功能 e2e 冒烟测试（真实运行栈，零 mock）。

覆盖 4 个此前 not_started 的功能，全部通过才退出 0：
  - supervision-refresh : 子 Tab 写操作后详情页所读的端点返回最新数据（前端 invalidation 已接；此处验证数据层一致）
  - brokerage-404-ux    : 经纪/修船 6 个子资源未创建时返回 200 + null（而非 404）
  - knowledge-chat-persist: QA 聊天记录后端持久化，跨请求可回溯
  - realtime-websocket  : 提交每日更新后，项目房间的 WS 连接实时收到广播事件

依赖：标准库 urllib + pip 安装的 websockets。
用法：python e2e_all.py
"""
import json
import sys
import time
import urllib.request
import urllib.error
import asyncio

try:
    import websockets
except ImportError:
    print("FATAL: 请先 pip install websockets")
    sys.exit(2)

BASE = "http://localhost:8000/api/v1"
WS_BASE = "ws://localhost:8000/ws/projects"


def rest(method, path, token=None, body=None):
    url = BASE + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode()
            return resp.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw


def login():
    status, data = rest("POST", "/auth/login", body={"username": "admin", "password": "admin123"})
    assert status == 200 and "access_token" in data, f"login failed: {status} {data}"
    return data["access_token"]


def assert_eq(name, cond, extra=""):
    if cond:
        print(f"  [PASS] {name}")
    else:
        print(f"  [FAIL] {name} {extra}")
        raise SystemExit(1)


async def ws_collect(project_id, token, timeout=15):
    """连接项目房间，等待并返回第一条业务事件。"""
    url = f"{WS_BASE}/{project_id}?token={token}"
    async with websockets.connect(url, open_timeout=10, close_timeout=5) as ws:
        msg = await asyncio.wait_for(ws.recv(), timeout=timeout)
        return json.loads(msg)


def main():
    token = login()
    print("login OK")

    # ── 建一个 supervision 项目（无经纪子资源）──────────────
    status, proj = rest("POST", "/projects", token=token, body={
        "project_no": "LG-SV-E2E-0001",
        "ship_name": "E2E Supervision Ship",
        "type": "supervision",
        "status": "active",
    })
    # 项目编号唯一约束可能冲突，若 400 则换号重试
    if status != 200:
        proj = None
    if proj is None:
        for i in range(2, 20):
            status, proj = rest("POST", "/projects", token=token, body={
                "project_no": f"LG-SV-E2E-{i:04d}",
                "ship_name": "E2E Supervision Ship",
                "type": "supervision",
                "status": "active",
            })
            if status == 200:
                break
    assert_eq("创建 supervision 项目", status in (200, 201) and proj, f"{status} {proj}")
    pid = proj["id"]
    print(f"project id={pid}")

    # ── Feature 2: brokerage-404-ux（200 + null）────────────
    print("\n== brokerage-404-ux ==")
    null_paths = [
        f"/brokerage/projects/{pid}/surveys",
        f"/brokerage/projects/{pid}/commercials",
        f"/brokerage/projects/{pid}/contracts",
        f"/brokerage/projects/{pid}/repair-brokerage",
        f"/spare-parts/projects/{pid}/hk-signatures",
        f"/spare-parts/projects/{pid}/invoices",
    ]
    for p in null_paths:
        s, d = rest("GET", p, token=token)
        assert_eq(f"GET {p} -> 200+null", s == 200 and d is None, f"got {s} {d}")

    # ── Feature 1: supervision-refresh（数据层一致）──────────
    print("\n== supervision-refresh (data-layer) ==")
    s, task = rest("POST", f"/tasks/projects/{pid}/tasks", token=token, body={
        "name": "E2E 任务",
        "planned_end_date": "2026-09-30",
        "status": "not_started",
    })
    assert_eq("创建任务(planned_end_date)", s in (200, 201) and task.get("planned_end_date") == "2026-09-30", f"{s} {task}")
    tid = task["id"]
    s, tasks = rest("GET", f"/tasks/projects/{pid}/tasks", token=token)
    assert_eq("GET 任务列表含新建任务", s == 200 and any(t["id"] == tid for t in tasks), f"{s}")
    s, proj_detail = rest("GET", f"/projects/{pid}", token=token)
    assert_eq("GET 项目详情 200", s == 200 and proj_detail["id"] == pid, f"{s}")

    # ── Feature 4: realtime-websocket ───────────────────────
    print("\n== realtime-websocket ==")
    # 后台等待 WS 事件，同时在主流程提交每日更新
    async def run_ws():
        return await ws_collect(pid, token, timeout=20)

    async def trigger_and_wait():
        # 先连 WS（在独立任务中），再提交每日更新触发广播
        task_ws = asyncio.create_task(run_ws())
        await asyncio.sleep(1.0)  # 等 WS 连接建立
        s, du = rest("POST", f"/tasks/{tid}/daily-updates", token=token, body={
            "update_date": "2026-08-17",
            "status": "in_progress",
            "remark": "e2e ws trigger",
        })
        assert_eq("创建每日更新触发广播", s in (200, 201) and du.get("id"), f"{s} {du}")
        event = await task_ws
        return du, event

    du, event = asyncio.run(trigger_and_wait())
    assert_eq("WS 收到 daily_update_created 事件",
              event.get("type") == "daily_update_created" and event.get("task_id") == tid,
              f"event={event}")

    # ── Feature 3: knowledge-chat-persist ───────────────────
    print("\n== knowledge-chat-persist ==")
    s, _ = rest("POST", "/knowledge/chat-messages", token=token, body={
        "role": "user", "content": "如何判断船东资质?",
    })
    assert_eq("保存 user 消息", s == 201, f"{s}")
    s, _ = rest("POST", "/knowledge/chat-messages", token=token, body={
        "role": "assistant", "content": "可通过企查查等核验工商信息。",
        "citations": [{"document_id": 1, "document_title": "船东尽调", "chunk_index": 0, "chunk_text": "..."}],
    })
    assert_eq("保存 assistant 消息(带引用)", s == 201, f"{s}")
    s, hist = rest("GET", "/knowledge/chat-messages", token=token)
    items = (hist or {}).get("items", [])
    roles = [m["role"] for m in items]
    assert_eq("GET 历史含 user+assistant", s == 200 and "user" in roles and "assistant" in roles,
              f"{s} roles={roles}")
    # 模拟「跨设备」：用全新请求再拉一次，数据仍在
    s2, hist2 = rest("GET", "/knowledge/chat-messages", token=token)
    assert_eq("跨请求可回溯(后端持久化)", s2 == 200 and len((hist2 or {}).get("items", [])) >= 2, f"{s2}")
    s, _ = rest("DELETE", "/knowledge/chat-messages", token=token)
    assert_eq("清理聊天历史", s == 204, f"{s}")

    # ── 清理测试项目（级联删除任务/每日更新）────────────────
    print("\n== cleanup ==")
    s, _ = rest("DELETE", f"/projects/{pid}", token=token)
    assert_eq("删除测试项目", s in (200, 204), f"{s}")

    print("\nALL E2E CHECKS PASSED ✅")


if __name__ == "__main__":
    main()
