#!/usr/bin/env bash
set -e
BASE=http://localhost:8000
PY="C:/Users/zheyu/.workbuddy/binaries/python/versions/3.13.12/python.exe"

echo "=== 1. login (admin/admin123) ==="
TOKEN=$(curl -s -X POST "$BASE/api/v1/auth/login" -H "Content-Type: application/json" -d '{"username":"admin","password":"admin123"}' | "$PY" -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
echo "token: ${TOKEN:0:16}... (len ${#TOKEN})"

echo "=== 2. create project (supervision) ==="
PROJ_JSON=$(curl -s -X POST "$BASE/api/v1/projects" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"type":"supervision","ship_name":"E2E Test Vessel"}')
PROJECT_ID=$(echo "$PROJ_JSON" | "$PY" -c "import sys,json;print(json.load(sys.stdin)['id'])")
echo "project_id=$PROJECT_ID"

echo "=== 3. create task WITH planned_end_date (verifies Fix 1) ==="
TASK_JSON=$(curl -s -X POST "$BASE/api/v1/tasks/projects/$PROJECT_ID/tasks" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"name":"E2E task","planned_end_date":"2026-09-01"}')
TASK_ID=$(echo "$TASK_JSON" | "$PY" -c "import sys,json;print(json.load(sys.stdin)['id'])")
PED=$(echo "$TASK_JSON" | "$PY" -c "import sys,json;print(json.load(sys.stdin).get('planned_end_date'))")
echo "task_id=$TASK_ID planned_end_date=$PED"
if [ "$PED" != "2026-09-01" ]; then echo "FAIL Fix1: planned_end_date NOT persisted (got '$PED')"; exit 1; fi
echo "PASS Fix1: planned_end_date persisted"

echo "=== 4. create daily update ==="
DU_JSON=$(curl -s -X POST "$BASE/api/v1/tasks/$TASK_ID/daily-updates" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"update_date":"2026-08-17","status":"in_progress","remark":"e2e smoke"}')
UPDATE_ID=$(echo "$DU_JSON" | "$PY" -c "import sys,json;print(json.load(sys.stdin)['id'])")
echo "update_id=$UPDATE_ID"

echo "=== 5. upload a real photo to daily update (verifies Fix 2 upload path) ==="
"$PY" -c "open('/tmp/test_photo.png','wb').write(bytes([137,80,78,71,13,10,26,10,0,0,0,13,73,72,68,82,0,0,0,1,0,0,0,1,8,6,0,0,0,31,21,196,137,0,0,0,13,73,68,65,84,120,156,99,0,1,0,0,5,0,1,13,10,45,180,0,0,0,0,73,69,78,68,174,66,96,130]))"
UP=$(curl -s -X POST "$BASE/api/v1/tasks/daily-updates/$UPDATE_ID/photos" -H "Authorization: Bearer $TOKEN" -F "file=@/tmp/test_photo.png;type=image/png")
PHOTO_ID=$(echo "$UP" | "$PY" -c "import sys,json;print(json.load(sys.stdin)['id'])")
echo "photo_id=$PHOTO_ID storage_key=$(echo "$UP" | "$PY" -c "import sys,json;print(json.load(sys.stdin).get('storage_key'))")"

echo "=== 6. GET daily-updates -> verify photo round-trips in photos[] (Fix 2) ==="
LIST=$(curl -s "$BASE/api/v1/tasks/$TASK_ID/daily-updates" -H "Authorization: Bearer $TOKEN")
HAS_PHOTO=$(echo "$LIST" | "$PY" -c "import sys,json;d=json.load(sys.stdin);print(any(p['id']==$PHOTO_ID for u in d for p in (u.get('photos') or [])))")
echo "photo present in daily-updates list: $HAS_PHOTO"
if [ "$HAS_PHOTO" != "True" ]; then echo "FAIL Fix2: photo not returned in daily-updates list"; exit 1; fi
echo "PASS Fix2: photo persisted + round-tripped in response"

echo "=== 7. GET task-photos/{id}/url (preview endpoint Fix 2) ==="
URL_RESP=$(curl -s "$BASE/api/v1/tasks/task-photos/$PHOTO_ID/url" -H "Authorization: Bearer $TOKEN")
URL=$(echo "$URL_RESP" | "$PY" -c "import sys,json;print(json.load(sys.stdin).get('url',''))")
echo "preview url length=${#URL}"
if [ -z "$URL" ]; then echo "FAIL: preview url empty"; exit 1; fi
echo "PASS: preview url returned (presigned MinIO URL)"

echo
echo "===== ALL E2E CHECKS PASSED ====="
