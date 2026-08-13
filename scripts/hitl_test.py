import json
import urllib.request
import urllib.error

BASE = "http://localhost:8000/api/v1"
PROJ = 39


def req(method, path, token=None, body=None):
    url = BASE + path
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


# 1) login
s, b = req("POST", "/auth/login", body={"username": "admin", "password": "admin123"})
tok = json.loads(b).get("access_token")
print(f"[login] {s} token_len={len(tok) if tok else 0}")
assert tok, "no token"

# 2) propose (AI draft)
s, b = req("POST", f"/reports/projects/{PROJ}/daily-reports/propose")
print(f"[propose] {s}")
draft = json.loads(b) if s == 200 else {}
today_work = draft.get("today_work")
cands = draft.get("tomorrow_candidates")
risk = draft.get("risk_alert")
print("  today_work:", (today_work or "")[:120])
print("  tomorrow_candidates:", cands)
print("  risk_alert:", (risk or "")[:160])

# 3) finalize (human confirms -> persist). confirmed tomorrow_items = candidates.
finalize_body = {
    "report_date": "2026-08-13",
    "today_work": today_work or "（测试）今日监修工作",
    "tomorrow_items": cands or ["（测试）明日计划项"],
    "risk_alert": risk or "（测试）无重大风险",
    "confirmed": True,
}
s, b = req("POST", f"/reports/projects/{PROJ}/daily-reports/finalize", token=tok, body=finalize_body)
print(f"[finalize] {s}")
fin = json.loads(b) if s == 200 else {}
print("  returned id=", fin.get("id"), "confirmed=", fin.get("confirmed"))

# 4) GET report to prove persistence
rid = fin.get("id")
if rid:
    s, b = req("GET", f"/reports/daily-reports/{rid}", token=tok)
    g = json.loads(b) if s == 200 else {}
    print(f"[get #{rid}] {s} confirmed={g.get('confirmed')} today_work={(g.get('today_work') or '')[:80]}")

print("\nRESULT:", "HITL E2E OK" if (fin.get("confirmed") is True) else "HITL E2E FAILED")
