"""
Integration Management Router

Provides endpoints for:
- Kingdee connection status / test
- Kingdee webhook (消息订阅 callback)
- Sync log listing / detail / AI diagnosis
- Manual sync triggers (master data, retry failed)
- Daily trend statistics
"""
import logging
from typing import Optional, Any, Union
from datetime import datetime, date, timedelta

from fastapi import APIRouter, Depends, Query, Path, Request
from pydantic import BaseModel
from sqlalchemy import select, func, desc, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_db, get_current_user, require_owner
from app.models.user import User, UserRole
from app.models.sync_log import SyncLog, SyncStatus
from app.schemas.common import PageResponse

logger = logging.getLogger("integration")
router = APIRouter(prefix="/integration", tags=["集成管理"])


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class ConnectionStatus(BaseModel):
    enabled: bool
    configured: bool
    connected: bool = False
    message: str = ""
    token_preview: Optional[str] = None


class SyncLogResponse(BaseModel):
    id: int
    entity_type: str
    entity_id: int
    kingdee_doc_type: str
    kingdee_doc_no: Optional[str] = None
    direction: str
    status: str
    error_message: Optional[str] = None
    retry_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SyncStats(BaseModel):
    total: int
    success: int
    failed: int
    pending: int
    skipped: int


class ManualSyncRequest(BaseModel):
    entity_type: str
    entity_id: Optional[int] = None


class ManualSyncResponse(BaseModel):
    message: str
    task_ids: list[str] = []


class DailyStatsItem(BaseModel):
    date: str
    success: int
    failed: int
    total: int


# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

@router.get("/kingdee/status", response_model=ConnectionStatus)
async def kingdee_status(
    current_user: User = Depends(require_owner),
):
    """查看精斗云连接状态"""
    from app.integrations.kingdee.client import get_kingdee_client

    client = get_kingdee_client()
    result = ConnectionStatus(
        enabled=settings.KINGDEE_ENABLED,
        configured=client.is_configured,
    )

    if result.enabled and result.configured:
        test = await client.test_connection()
        result.connected = test["connected"]
        result.message = test["message"]
        result.token_preview = test.get("token_preview")
    elif not result.enabled:
        result.message = "精斗云集成未启用 (KINGDEE_ENABLED=false)"
    else:
        result.message = "精斗云凭证未配置 (缺少 APP_ID / APP_SECRET / INSTANCE_ID)"

    return result


@router.post("/kingdee/test")
async def kingdee_test_connection(
    current_user: User = Depends(require_owner),
):
    """测试精斗云连接"""
    from app.integrations.kingdee.client import get_kingdee_client

    client = get_kingdee_client()
    if not client.is_configured:
        return {"connected": False, "message": "精斗云凭证未配置"}

    return await client.test_connection()


@router.get("/kingdee/debug-call")
async def kingdee_debug_call(
    current_user: User = Depends(require_owner),
):
    """Debug: 尝试调用精斗云业务 API 并返回完整响应"""
    from app.integrations.kingdee.client import get_kingdee_client, KingdeeAPIError

    client = get_kingdee_client()
    results = {}

    # Step 1: Call push_app_authorize to see full response (includes domain, serviceId, accountId)
    try:
        http = await client._get_http()
        auth_path = "/jdyconnector/app_management/push_app_authorize"
        auth_params = {"outerInstanceId": client.instance_id}
        auth_headers = client._sign_headers("POST", auth_path, auth_params)
        auth_resp = await http.post(auth_path, params=auth_params, headers=auth_headers)
        results["authorize_response"] = auth_resp.json()
    except Exception as exc:
        results["authorize_error"] = str(exc)

    # Step 2: Get token
    try:
        token = await client._ensure_token()
        results["access_token"] = token[:20] + "..." if token else None
        results["token_is_jwt"] = token.startswith("eyJ") if token else False
    except Exception as exc:
        results["token_error"] = str(exc)

    # Extract domain from authorize response
    auth_data = results.get("authorize_response", {}).get("data", [])
    if isinstance(auth_data, list) and auth_data:
        real_domain = auth_data[0].get("domain", "")
        results["detected_domain"] = real_domain
        if real_domain and not client.domain:
            client.domain = real_domain

    # Token diagnostics
    results["token_type"] = "JWT" if (results.get("access_token", "") or "").startswith("eyJ") else "access_token (非JWT)"
    results["client_domain"] = client.domain or "(未设置)"
    results["sid"] = client.sid
    results["db_id"] = client.db_id

    # Step 3: Test ALL jdyaccouting APIs with raw responses
    test_apis: list[tuple] = [
        ("POST", "/jdyaccouting/voucherlist", {
            "fromPeriod": 202501, "toPeriod": 202512, "page": 1, "pageSize": 5,
        }),
        ("GET", "/jdyaccouting/voucher?action=getVchTotalQuery&fromDate=202501&toDate=202512", None),
        ("GET", "/jdyaccouting/account/balance", None),
        ("GET", "/jdyaccouting/report/genledger?fromPeriod=202501&toPeriod=202512", None),
        ("GET", "/jdyaccouting/querydetail?accountNum=1001&fromPeriod=202501&toPeriod=202512", None),
        ("GET", "/jdyaccouting/report?reportType=2&startPeriod=202501&endPeriod=202503", None),
        ("GET", "/jdyaccouting/cashier/journal/list?fromPeriod=202501&toPeriod=202512", None),
        ("GET", "/jdyaccouting/cashieraccount/list", None),
    ]
    for method, path, body in test_apis:
        try:
            if method == "POST":
                raw = await client.post(path, json=body)
            else:
                raw = await client.get(path)
            results[path] = {"ok": True, "raw_response": raw}
        except KingdeeAPIError as exc:
            results[path] = {"ok": False, "code": exc.code, "msg": exc.message, "raw_response": exc.response}
        except Exception as exc:
            results[path] = {"ok": False, "error": str(exc)}

    return results


# ---------------------------------------------------------------------------
# Kingdee Cloud Accounting data queries (based on Postman collection)
# ---------------------------------------------------------------------------

KINGDEE_EMPTY_CODES = {46002, 48001}


def _safe_kingdee_code(code: str) -> int:
    try:
        return int(code)
    except (ValueError, TypeError):
        return -1


def _extract_total(d: dict) -> Optional[int]:
    """Try common field names Kingdee uses for total record count.

    'records' must come before 'totalsize' because voucherlist uses
    'records' for the real total while 'totalsize' is per-page count.
    """
    for key in ("records", "totalsize", "totalSize", "total", "totalCount", "recordCount", "count"):
        v = d.get(key)
        if v is not None and isinstance(v, (int, float)):
            return int(v)
    return None


def _kingdee_result(data: dict) -> dict:
    """Normalise Kingdee responses into {code, msg, list, count} for the frontend."""
    if not isinstance(data, dict):
        return {"code": -1, "msg": "非预期响应", "list": [], "count": 0}

    resp_code = data.get("code", data.get("status", 0))
    if resp_code in KINGDEE_EMPTY_CODES:
        return {"code": 0, "msg": data.get("msg", "暂无数据"), "list": [], "count": 0}

    # Pagination metadata from Kingdee (voucherlist etc.)
    pagination = {}
    if isinstance(data.get("page"), (int, float)):
        pagination["page"] = int(data["page"])
    if isinstance(data.get("totalPages"), (int, float)):
        pagination["totalPages"] = int(data["totalPages"])

    # data.items / data.reportValues / data.list / data.rows
    inner = data.get("data")
    if isinstance(inner, dict):
        items = inner.get("items") or inner.get("reportValues") or inner.get("list") or inner.get("rows") or []
        if isinstance(items, list) and items:
            total = _extract_total(inner) or _extract_total(data) or len(items)
            return {"code": 0, "msg": data.get("msg", ""), "list": items, "count": total, **pagination}

    # Top-level "items" (e.g. voucherlist, account/balance)
    if "items" in data and isinstance(data["items"], list) and data["items"]:
        total = _extract_total(data) or len(data["items"])
        return {"code": 0, "msg": data.get("msg", ""), "list": data["items"], "count": total, **pagination}

    # Top-level "list"
    if "list" in data and isinstance(data["list"], list):
        if "count" not in data:
            data["count"] = _extract_total(data) or len(data["list"])
        data.update(pagination)
        return data

    if resp_code == 0 or resp_code == 200 or resp_code == 250:
        return {"code": 0, "msg": data.get("msg", "暂无数据"), "list": [], "count": 0, "raw": data}

    return data


# ── 凭证 ──────────────────────────────────────────────────────────────

@router.get("/kingdee/vouchers")
async def list_kingdee_vouchers(
    from_period: int = Query(202501, description="起始期间 YYYYMM"),
    to_period: int = Query(202512, description="截止期间 YYYYMM"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_owner),
):
    """POST /jdyaccouting/voucherlist — 凭证查询"""
    from app.integrations.kingdee.client import get_kingdee_client, KingdeeAPIError

    client = get_kingdee_client()
    try:
        data = await client.post("/jdyaccouting/voucherlist", json={
            "fromPeriod": from_period,
            "toPeriod": to_period,
            "onlyMech": 2,
            "page": page,
            "pageSize": page_size,
        })
        logger.info("voucherlist raw: records=%s totalsize=%s totalPages=%s page=%s",
                     data.get("records") if isinstance(data, dict) else "?",
                     data.get("totalsize") if isinstance(data, dict) else "?",
                     data.get("totalPages") if isinstance(data, dict) else "?",
                     data.get("page") if isinstance(data, dict) else "?")
        return _kingdee_result(data)
    except KingdeeAPIError as exc:
        return {"code": _safe_kingdee_code(exc.code), "msg": exc.message, "list": [], "count": 0}
    except Exception as exc:
        return {"code": -1, "msg": str(exc), "list": [], "count": 0}


@router.get("/kingdee/voucher-summary")
async def kingdee_voucher_summary(
    from_period: int = Query(202501, description="起始期间 YYYYMM"),
    to_period: int = Query(202512, description="截止期间 YYYYMM"),
    current_user: User = Depends(require_owner),
):
    """GET /jdyaccouting/voucher?action=getVchTotalQuery — 凭证汇总表"""
    from app.integrations.kingdee.client import get_kingdee_client, KingdeeAPIError

    client = get_kingdee_client()
    try:
        data = await client.get("/jdyaccouting/voucher", params={
            "action": "getVchTotalQuery",
            "fromPeriod": from_period,
            "toPeriod": to_period,
        })
        return _kingdee_result(data)
    except KingdeeAPIError as exc:
        return {"code": _safe_kingdee_code(exc.code), "msg": exc.message, "list": []}
    except Exception as exc:
        return {"code": -1, "msg": str(exc), "list": []}


# ── 账簿 ──────────────────────────────────────────────────────────────

@router.get("/kingdee/account-balance")
async def kingdee_account_balance(
    from_period: int = Query(202501, description="起始期间 YYYYMM"),
    to_period: int = Query(202512, description="截止期间 YYYYMM"),
    current_user: User = Depends(require_owner),
):
    """GET /jdyaccouting/account/balance — 科目余额表"""
    from app.integrations.kingdee.client import get_kingdee_client, KingdeeAPIError

    client = get_kingdee_client()
    try:
        data = await client.get("/jdyaccouting/account/balance", params={
            "fromPeriod": from_period,
            "toPeriod": to_period,
        })
        return _kingdee_result(data)
    except KingdeeAPIError as exc:
        return {"code": _safe_kingdee_code(exc.code), "msg": exc.message, "list": []}
    except Exception as exc:
        return {"code": -1, "msg": str(exc), "list": []}


@router.get("/kingdee/general-ledger")
async def kingdee_general_ledger(
    from_period: int = Query(202501, description="起始期间 YYYYMM"),
    to_period: int = Query(202512, description="截止期间 YYYYMM"),
    current_user: User = Depends(require_owner),
):
    """GET /jdyaccouting/report/genledger — 总账"""
    from app.integrations.kingdee.client import get_kingdee_client, KingdeeAPIError

    client = get_kingdee_client()
    try:
        data = await client.get("/jdyaccouting/report/genledger", params={
            "fromPeriod": from_period,
            "toPeriod": to_period,
        })
        return _kingdee_result(data)
    except KingdeeAPIError as exc:
        return {"code": _safe_kingdee_code(exc.code), "msg": exc.message, "list": []}
    except Exception as exc:
        return {"code": -1, "msg": str(exc), "list": []}


@router.get("/kingdee/detail-ledger")
async def kingdee_detail_ledger(
    account_num: str = Query("", description="科目编码，如 1001"),
    from_period: int = Query(202501, description="起始期间 YYYYMM"),
    to_period: int = Query(202512, description="截止期间 YYYYMM"),
    current_user: User = Depends(require_owner),
):
    """GET /jdyaccouting/querydetail — 明细账"""
    from app.integrations.kingdee.client import get_kingdee_client, KingdeeAPIError

    if not account_num:
        return {"code": -1, "msg": "请输入科目编码（如 1001）", "list": []}

    client = get_kingdee_client()
    try:
        data = await client.get("/jdyaccouting/querydetail", params={
            "accountNum": account_num,
            "fromPeriod": from_period,
            "toPeriod": to_period,
        })
        return _kingdee_result(data)
    except KingdeeAPIError as exc:
        return {"code": _safe_kingdee_code(exc.code), "msg": exc.message, "list": []}
    except Exception as exc:
        return {"code": -1, "msg": str(exc), "list": []}


# ── 报表 ──────────────────────────────────────────────────────────────

@router.get("/kingdee/report")
async def kingdee_report(
    report_type: int = Query(2, description="1=资产负债表, 2=利润表, 3=现金流量表"),
    start_period: int = Query(202501, description="起始期间 YYYYMM"),
    end_period: int = Query(202512, description="截止期间 YYYYMM"),
    current_user: User = Depends(require_owner),
):
    """GET /jdyaccouting/report — 利润表/资产负债表/现金流量表"""
    from app.integrations.kingdee.client import get_kingdee_client, KingdeeAPIError

    client = get_kingdee_client()
    try:
        data = await client.get("/jdyaccouting/report", params={
            "reportType": report_type,
            "startPeriod": start_period,
            "endPeriod": end_period,
        })
        return _kingdee_result(data)
    except KingdeeAPIError as exc:
        return {"code": _safe_kingdee_code(exc.code), "msg": exc.message, "list": []}
    except Exception as exc:
        return {"code": -1, "msg": str(exc), "list": []}


# ── 出纳 ──────────────────────────────────────────────────────────────

@router.get("/kingdee/cashier-journal")
async def kingdee_cashier_journal(
    account_number: str = Query("", description="出纳账户编号（先查询出纳账户获取）"),
    period: int = Query(202503, description="会计期间 YYYYMM（单月）"),
    current_user: User = Depends(require_owner),
):
    """GET /jdyaccouting/cashier/journal/list — 日记账查询（单月）"""
    from app.integrations.kingdee.client import get_kingdee_client, KingdeeAPIError

    if not account_number:
        return {"code": -1, "msg": "请先查询出纳账户列表，获取账户编号后填入", "list": []}

    client = get_kingdee_client()
    try:
        data = await client.get("/jdyaccouting/cashier/journal/list", params={
            "cashierAccountNumber": account_number,
            "period": period,
        })
        return _kingdee_result(data)
    except KingdeeAPIError as exc:
        return {"code": _safe_kingdee_code(exc.code), "msg": exc.message, "list": []}
    except Exception as exc:
        return {"code": -1, "msg": str(exc), "list": []}


@router.get("/kingdee/cashier-accounts")
async def kingdee_cashier_accounts(
    current_user: User = Depends(require_owner),
):
    """GET /jdyaccouting/cashieraccount/list — 出纳账户查询"""
    from app.integrations.kingdee.client import get_kingdee_client, KingdeeAPIError

    client = get_kingdee_client()
    try:
        data = await client.get("/jdyaccouting/cashieraccount/list")
        return _kingdee_result(data)
    except KingdeeAPIError as exc:
        return {"code": _safe_kingdee_code(exc.code), "msg": exc.message, "list": []}
    except Exception as exc:
        return {"code": -1, "msg": str(exc), "list": []}


# ── 凭证操作 ──────────────────────────────────────────────────────────

class VoucherSaveRequest(BaseModel):
    date: str
    group_name: str = "记"
    year_period: Optional[int] = None
    explanation: str = ""
    attachments: int = 0
    entries: list[dict]
    link_id: Optional[str] = None


class VoucherIdRequest(BaseModel):
    vch_id: Union[str, int]


class VoucherBatchDeleteRequest(BaseModel):
    vch_ids: list[Union[str, int]]


@router.post("/kingdee/voucher/save")
async def kingdee_voucher_save(
    req: VoucherSaveRequest,
    current_user: User = Depends(require_owner),
):
    """POST /jdyaccouting/voucher — 凭证保存（金蝶 body 要求数组格式）"""
    from app.integrations.kingdee.client import get_kingdee_client, KingdeeAPIError

    client = get_kingdee_client()

    year_period = req.year_period
    if not year_period:
        year_period = int(req.date[:4] + req.date[5:7])

    voucher = {
        "groupName": req.group_name,
        "vchNumber": 0,
        "date": req.date,
        "yearPeriod": year_period,
        "entries": req.entries,
    }
    if req.link_id:
        voucher["linkId"] = req.link_id

    try:
        data = await client.post("/jdyaccouting/voucher", json=[voucher])
        # Kingdee returns {code, list: [{code, msg, vchId, ...}]} — check inner item
        resp_code = data.get("code") if isinstance(data, dict) else -1
        items = data.get("list", []) if isinstance(data, dict) else []
        first = items[0] if items else {}
        item_code = first.get("code", -1)

        if resp_code == 0 and item_code == 0:
            return {"code": 0, "msg": "凭证保存成功", "data": data}
        item_msg = first.get("msg", data.get("msg", "保存失败")) if isinstance(data, dict) else "保存失败"
        return {"code": item_code if item_code != 0 else (resp_code or -2), "msg": item_msg, "data": data}
    except KingdeeAPIError as exc:
        return {"code": _safe_kingdee_code(exc.code), "msg": exc.message, "data": exc.response}
    except Exception as exc:
        return {"code": -1, "msg": str(exc)}


@router.post("/kingdee/voucher/reverse")
async def kingdee_voucher_reverse(
    req: VoucherIdRequest,
    current_user: User = Depends(require_owner),
):
    """POST /jdyaccouting/voucher/reverse — 凭证冲销"""
    from app.integrations.kingdee.client import get_kingdee_client, KingdeeAPIError

    client = get_kingdee_client()
    try:
        data = await client.post("/jdyaccouting/voucher/reverse", params={"vchId": req.vch_id})
        resp_code = data.get("code") if isinstance(data, dict) else -1
        items = data.get("list", data.get("items", [])) if isinstance(data, dict) else []
        first = items[0] if items else {}
        item_code = first.get("code", resp_code)

        if resp_code == 0 and (item_code == 0 or item_code is None or not items):
            return {"code": 0, "msg": "凭证冲销成功", "data": data}
        item_msg = first.get("msg", data.get("msg", "冲销失败")) if isinstance(data, dict) else "冲销失败"
        return {"code": item_code if item_code and item_code != 0 else (resp_code or -2), "msg": item_msg, "data": data}
    except KingdeeAPIError as exc:
        return {"code": _safe_kingdee_code(exc.code), "msg": exc.message, "data": exc.response}
    except Exception as exc:
        return {"code": -1, "msg": str(exc)}


@router.post("/kingdee/voucher/delete")
async def kingdee_voucher_delete(
    req: VoucherIdRequest,
    current_user: User = Depends(require_owner),
):
    """DELETE /jdyaccouting/voucher — 凭证删除（金蝶用 DELETE + idSet）"""
    from app.integrations.kingdee.client import get_kingdee_client, KingdeeAPIError

    client = get_kingdee_client()
    vch_id = int(req.vch_id) if isinstance(req.vch_id, str) else req.vch_id
    try:
        data = await client.request("DELETE", "/jdyaccouting/voucher", json={"idSet": [vch_id]})
        items = data.get("items", []) if isinstance(data, dict) else []
        if items and items[0].get("code") == 0:
            return {"code": 0, "msg": "凭证删除成功", "data": data}
        msg = items[0].get("msg", "删除失败") if items else data.get("msg", "删除失败")
        return {"code": data.get("code", -2), "msg": msg, "data": data}
    except KingdeeAPIError as exc:
        return {"code": _safe_kingdee_code(exc.code), "msg": exc.message, "data": exc.response}
    except Exception as exc:
        return {"code": -1, "msg": str(exc)}


@router.post("/kingdee/voucher/batch-delete")
async def kingdee_voucher_batch_delete(
    req: VoucherBatchDeleteRequest,
    current_user: User = Depends(require_owner),
):
    """DELETE /jdyaccouting/voucher — 批量凭证删除"""
    from app.integrations.kingdee.client import get_kingdee_client, KingdeeAPIError

    if not req.vch_ids:
        return {"code": -1, "msg": "请选择要删除的凭证", "results": []}

    client = get_kingdee_client()
    results = []
    success_count = 0
    fail_count = 0

    for vch_id in req.vch_ids:
        vid = int(vch_id) if isinstance(vch_id, str) else vch_id
        try:
            data = await client.request("DELETE", "/jdyaccouting/voucher", json={"idSet": [vid]})
            items = data.get("items", []) if isinstance(data, dict) else []
            if items and items[0].get("code") == 0:
                success_count += 1
                results.append({"vch_id": vid, "success": True, "msg": "删除成功"})
            else:
                fail_count += 1
                msg = items[0].get("msg", "删除失败") if items else data.get("msg", "删除失败")
                results.append({"vch_id": vid, "success": False, "msg": msg})
        except KingdeeAPIError as exc:
            fail_count += 1
            results.append({"vch_id": vid, "success": False, "msg": exc.message})
        except Exception as exc:
            fail_count += 1
            results.append({"vch_id": vid, "success": False, "msg": str(exc)})

    return {
        "code": 0 if fail_count == 0 else -1,
        "msg": f"删除完成：成功 {success_count} 条，失败 {fail_count} 条",
        "results": results,
        "success_count": success_count,
        "fail_count": fail_count,
    }


# ── 原始凭证 ──────────────────────────────────────────────────────────

class EvidenceUploadRequest(BaseModel):
    file_name: str
    file_size: int
    period: int
    file_data: str  # base64 encoded
    content_type: str = "application/octet-stream"


class EvidenceAttachRequest(BaseModel):
    voucher_id: str
    evid_ids: str  # comma-separated evidIds


class EvidenceUnattachRequest(BaseModel):
    evid_id: str
    file_id: str


@router.post("/kingdee/evidence/upload")
async def kingdee_evidence_upload(
    req: EvidenceUploadRequest,
    current_user: User = Depends(require_owner),
):
    """POST /jdyaccouting/evidence/upload — 原始凭证上传 (multipart/form-data)"""
    from app.integrations.kingdee.client import get_kingdee_client, KingdeeAPIError
    import base64

    client = get_kingdee_client()
    try:
        await client._ensure_token()
        http_client = await client._get_http()

        query_params = {
            "access_token": client._app_token,
            "sId": client.sid,
            "dbId": client.db_id,
            "fileName": req.file_name,
            "fileSize": req.file_size,
            "period": req.period,
        }

        path = "/jdyaccouting/evidence/upload"
        headers = client._sign_headers("POST", path, query_params, skip_app_token=True)
        headers["Authorization"] = f"Bearer {client._app_token}"
        if client.domain:
            headers["X-GW-Router-Addr"] = client.domain
        headers.pop("Content-Type", None)

        file_bytes = base64.b64decode(req.file_data)
        files = {"file1": (req.file_name, file_bytes, req.content_type)}

        resp = await http_client.post(path, params=query_params, headers=headers, files=files)
        body = resp.json()
        return {"code": 0, "msg": "原始凭证上传成功", "data": body}
    except KingdeeAPIError as exc:
        return {"code": _safe_kingdee_code(exc.code), "msg": exc.message, "data": exc.response}
    except Exception as exc:
        return {"code": -1, "msg": str(exc)}


@router.post("/kingdee/evidence/attach")
async def kingdee_evidence_attach(
    req: EvidenceAttachRequest,
    current_user: User = Depends(require_owner),
):
    """POST /jdyaccouting/evidence/attach — 原始凭证绑定到凭证"""
    from app.integrations.kingdee.client import get_kingdee_client, KingdeeAPIError

    client = get_kingdee_client()
    try:
        data = await client.post(
            "/jdyaccouting/evidence/attach",
            params={"voucherId": req.voucher_id, "evidIds": req.evid_ids},
        )
        return {"code": 0, "msg": "原始凭证绑定成功", "data": data}
    except KingdeeAPIError as exc:
        return {"code": _safe_kingdee_code(exc.code), "msg": exc.message, "data": exc.response}
    except Exception as exc:
        return {"code": -1, "msg": str(exc)}


@router.post("/kingdee/evidence/unattach")
async def kingdee_evidence_unattach(
    req: EvidenceUnattachRequest,
    current_user: User = Depends(require_owner),
):
    """POST /jdyaccouting/evidence/unattach — 原始凭证解绑"""
    from app.integrations.kingdee.client import get_kingdee_client, KingdeeAPIError

    client = get_kingdee_client()
    try:
        data = await client.post(
            "/jdyaccouting/evidence/unattach",
            params={"evidId": req.evid_id, "fileId": req.file_id},
        )
        return {"code": 0, "msg": "原始凭证解绑成功", "data": data}
    except KingdeeAPIError as exc:
        return {"code": _safe_kingdee_code(exc.code), "msg": exc.message, "data": exc.response}
    except Exception as exc:
        return {"code": -1, "msg": str(exc)}


@router.post("/kingdee/evidence/list")
async def kingdee_evidence_list(
    begin_period: int = Query(202501, description="起始期间 YYYYMM"),
    end_period: int = Query(202512, description="截止期间 YYYYMM"),
    is_class: Optional[str] = Query(None, description="含已整理 1=含 0=不含"),
    is_voucher: Optional[str] = Query(None, description="含生成凭证 1=含 0=不含"),
    current_user: User = Depends(require_owner),
):
    """POST /jdyaccouting/evidence/list — 原始凭证查询"""
    from app.integrations.kingdee.client import get_kingdee_client, KingdeeAPIError

    client = get_kingdee_client()
    try:
        params: dict[str, Any] = {
            "beginYearPeriod": str(begin_period),
            "endYearPeriod": str(end_period),
        }
        if is_class is not None:
            params["isClass"] = is_class
        if is_voucher is not None:
            params["isVoucher"] = is_voucher

        data = await client.post("/jdyaccouting/evidence/list", params=params)
        return _kingdee_result(data)
    except KingdeeAPIError as exc:
        return {"code": _safe_kingdee_code(exc.code), "msg": exc.message, "list": [], "count": 0}
    except Exception as exc:
        return {"code": -1, "msg": str(exc), "list": [], "count": 0}


@router.post("/kingdee/evidence/attachments")
async def kingdee_evidence_attachments(
    begin_period: int = Query(202501, description="起始期间 YYYYMM"),
    end_period: int = Query(202512, description="截止期间 YYYYMM"),
    is_class: Optional[str] = Query(None, description="含已整理 1=含 0=不含"),
    is_voucher: Optional[str] = Query(None, description="含生成凭证 1=含 0=不含"),
    current_user: User = Depends(require_owner),
):
    """POST /jdyaccouting/evidence/attachmentList — 附件查询"""
    from app.integrations.kingdee.client import get_kingdee_client, KingdeeAPIError

    client = get_kingdee_client()
    try:
        params: dict[str, Any] = {
            "beginYearPeriod": str(begin_period),
            "endYearPeriod": str(end_period),
        }
        if is_class is not None:
            params["isClass"] = is_class
        if is_voucher is not None:
            params["isVoucher"] = is_voucher

        data = await client.post("/jdyaccouting/evidence/attachmentList", params=params)
        return _kingdee_result(data)
    except KingdeeAPIError as exc:
        return {"code": _safe_kingdee_code(exc.code), "msg": exc.message, "list": [], "count": 0}
    except Exception as exc:
        return {"code": -1, "msg": str(exc), "list": [], "count": 0}


@router.get("/kingdee/general-ledger")
async def kingdee_general_ledger(
    from_period: int = Query(202501, description="开始期间 YYYYMM"),
    to_period: int = Query(202512, description="结束期间 YYYYMM"),
    from_account: Optional[str] = Query(None, description="起始科目编码"),
    to_account: Optional[str] = Query(None, description="结束科目编码"),
    include_item: int = Query(0, description="显示辅助核算 0:不显示 1:显示"),
    balance: int = Query(1, description="余额为0的项 0:不显示 1:显示"),
    happen: int = Query(1, description="无发生额且余额为0 0:不显示 1:显示"),
    from_level: Optional[int] = Query(None, description="科目最小级数"),
    to_level: Optional[int] = Query(None, description="科目最大级数"),
    currency: Optional[str] = Query(None, description="币别如 RMB"),
    current_user: User = Depends(require_owner),
):
    """GET /jdyaccouting/report/genledger — 总账"""
    from app.integrations.kingdee.client import get_kingdee_client, KingdeeAPIError

    client = get_kingdee_client()
    try:
        params: dict[str, Any] = {
            "fromPeriod": str(from_period),
            "toPeriod": str(to_period),
            "includeItem": include_item,
            "balance": balance,
            "happen": happen,
        }
        if from_account:
            params["fromAccountNum"] = from_account
        if to_account:
            params["toAccountNum"] = to_account
        if from_level is not None:
            params["fromLevel"] = from_level
        if to_level is not None:
            params["toLevel"] = to_level
        if currency:
            params["currency"] = currency

        data = await client.get("/jdyaccouting/report/genledger", params=params)
        items = []
        if isinstance(data, dict) and "data" in data:
            inner = data["data"]
            if isinstance(inner, dict):
                items = inner.get("items", [])
        return {"code": 0, "msg": "ok", "list": items, "count": len(items)}
    except KingdeeAPIError as exc:
        return {"code": _safe_kingdee_code(exc.code), "msg": exc.message, "list": [], "count": 0}
    except Exception as exc:
        return {"code": -1, "msg": str(exc), "list": [], "count": 0}


# ── 辅助核算 ──────────────────────────────────────────────────────────

@router.get("/kingdee/itemclass")
async def kingdee_itemclass(
    current_user: User = Depends(require_owner),
):
    """GET /jdyaccouting/itemclass/query — 辅助核算类别列表"""
    from app.integrations.kingdee.client import get_kingdee_client, KingdeeAPIError

    client = get_kingdee_client()
    try:
        data = await client.get("/jdyaccouting/itemclass/query")
        return _kingdee_result(data)
    except KingdeeAPIError as exc:
        return {"code": _safe_kingdee_code(exc.code), "msg": exc.message, "list": [], "count": 0}
    except Exception as exc:
        return {"code": -1, "msg": str(exc), "list": [], "count": 0}


@router.get("/kingdee/items")
async def kingdee_items(
    item_cls_name: str = Query(..., description="辅助核算类别名称，如 客户、供应商"),
    number: Optional[str] = Query(None, description="核算项编码"),
    name: Optional[str] = Query(None, description="核算项名称"),
    page: Optional[int] = Query(None, ge=1, description="页码"),
    page_size: Optional[int] = Query(None, ge=1, le=200, description="每页条数"),
    current_user: User = Depends(require_owner),
):
    """GET /jdyaccouting/item — 辅助核算项查询"""
    from app.integrations.kingdee.client import get_kingdee_client, KingdeeAPIError

    client = get_kingdee_client()
    try:
        params: dict[str, Any] = {"itemClsName": item_cls_name}
        if number:
            params["number"] = number
        if name:
            params["name"] = name
        if page is not None:
            params["page"] = str(page)
        if page_size is not None:
            params["pageSize"] = str(page_size)

        data = await client.get("/jdyaccouting/item", params=params)
        return _kingdee_result(data)
    except KingdeeAPIError as exc:
        return {"code": _safe_kingdee_code(exc.code), "msg": exc.message, "list": [], "count": 0}
    except Exception as exc:
        return {"code": -1, "msg": str(exc), "list": [], "count": 0}


@router.get("/kingdee/account-list")
async def kingdee_account_list(
    current_user: User = Depends(require_owner),
):
    """GET /jdyaccouting/account/list — 科目列表（用于凭证科目映射配置）"""
    from app.integrations.kingdee.client import get_kingdee_client, KingdeeAPIError

    client = get_kingdee_client()
    try:
        data = await client.get("/jdyaccouting/account/list")
        return _kingdee_result(data)
    except KingdeeAPIError as exc:
        return {"code": _safe_kingdee_code(exc.code), "msg": exc.message, "list": []}
    except Exception as exc:
        return {"code": -1, "msg": str(exc), "list": []}


# ---------------------------------------------------------------------------
# Sync logs
# ---------------------------------------------------------------------------

@router.get("/sync-logs", response_model=PageResponse[SyncLogResponse])
async def list_sync_logs(
    entity_type: Optional[str] = Query(None),
    status: Optional[SyncStatus] = Query(None),
    entity_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    """查看同步日志"""
    query = select(SyncLog)

    if entity_type:
        query = query.where(SyncLog.entity_type == entity_type)
    if status:
        query = query.where(SyncLog.status == status)
    if entity_id:
        query = query.where(SyncLog.entity_id == entity_id)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    query = query.order_by(desc(SyncLog.created_at)).offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    items = result.scalars().all()

    return PageResponse(items=items, total=total, page=page, size=size)


@router.get("/sync-logs/stats", response_model=SyncStats)
async def sync_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    """同步统计"""
    total = (await db.execute(select(func.count(SyncLog.id)))).scalar() or 0
    success = (await db.execute(
        select(func.count(SyncLog.id)).where(SyncLog.status == SyncStatus.SUCCESS)
    )).scalar() or 0
    failed = (await db.execute(
        select(func.count(SyncLog.id)).where(SyncLog.status == SyncStatus.FAILED)
    )).scalar() or 0
    pending = (await db.execute(
        select(func.count(SyncLog.id)).where(SyncLog.status == SyncStatus.PENDING)
    )).scalar() or 0
    skipped = (await db.execute(
        select(func.count(SyncLog.id)).where(SyncLog.status == SyncStatus.SKIPPED)
    )).scalar() or 0

    return SyncStats(total=total, success=success, failed=failed, pending=pending, skipped=skipped)


# daily-stats must be before {log_id} to avoid path collision
@router.get("/sync-logs/daily-stats", response_model=list[DailyStatsItem])
async def daily_sync_stats(
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    """最近 N 天的每日同步趋势"""
    since = datetime.utcnow() - timedelta(days=days)
    day_col = cast(SyncLog.created_at, Date)

    rows = (await db.execute(
        select(
            day_col.label("day"),
            func.count(SyncLog.id).label("total"),
            func.count(SyncLog.id).filter(SyncLog.status == SyncStatus.SUCCESS).label("success"),
            func.count(SyncLog.id).filter(SyncLog.status == SyncStatus.FAILED).label("failed"),
        )
        .where(SyncLog.created_at >= since)
        .group_by(day_col)
        .order_by(day_col)
    )).all()

    result: list[DailyStatsItem] = []
    row_map = {str(r.day): r for r in rows}
    for i in range(days):
        d = (datetime.utcnow() - timedelta(days=days - 1 - i)).date()
        ds = str(d)
        r = row_map.get(ds)
        result.append(DailyStatsItem(
            date=ds,
            success=r.success if r else 0,
            failed=r.failed if r else 0,
            total=r.total if r else 0,
        ))
    return result


@router.get("/sync-logs/{log_id}", response_model=SyncLogResponse)
async def get_sync_log(
    log_id: int = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    """查看同步日志详情"""
    log = (await db.execute(select(SyncLog).where(SyncLog.id == log_id))).scalar_one_or_none()
    if not log:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("同步日志", log_id)
    return log


# ---------------------------------------------------------------------------
# Manual sync triggers
# ---------------------------------------------------------------------------

@router.post("/sync/retry/{log_id}", response_model=ManualSyncResponse)
async def retry_sync(
    log_id: int = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    """手动重试失败的同步（直接执行）"""
    from app.integrations.kingdee.sync_service import KingdeeSyncService

    log = (await db.execute(select(SyncLog).where(SyncLog.id == log_id))).scalar_one_or_none()
    if not log:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("同步日志", log_id)

    if log.status != SyncStatus.FAILED:
        from app.core.exceptions import ConflictError
        raise ConflictError("只能重试失败的同步记录")

    svc = KingdeeSyncService()
    method_map = {
        "order": svc.sync_order,
        "procurement": svc.sync_procurement_received,
        "disbursement": svc.sync_disbursement,
        "settlement": svc.sync_settlement,
    }

    method = method_map.get(log.entity_type)
    if not method:
        return ManualSyncResponse(message=f"不支持重试的实体类型: {log.entity_type}", task_ids=[])

    new_log = await method(db, log.entity_id)
    await db.commit()

    return ManualSyncResponse(
        message=f"重试完成，状态: {new_log.status.value}",
        task_ids=[str(new_log.id)],
    )


@router.post("/sync/entity", response_model=ManualSyncResponse)
async def sync_single_entity(
    req: ManualSyncRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    """手动触发单个实体凭证同步（直接执行，不经过 Celery）"""
    from app.integrations.kingdee.sync_service import KingdeeSyncService

    if not req.entity_id:
        from fastapi import HTTPException
        raise HTTPException(400, "entity_id is required")

    svc = KingdeeSyncService()
    method_map = {
        "order": svc.sync_order,
        "procurement": svc.sync_procurement_received,
        "disbursement": svc.sync_disbursement,
        "settlement": svc.sync_settlement,
    }

    method = method_map.get(req.entity_type)
    if not method:
        from fastapi import HTTPException
        raise HTTPException(400, f"不支持的实体类型: {req.entity_type}（仅支持 order/procurement/disbursement/settlement）")

    log = await method(db, req.entity_id)
    await db.commit()

    return ManualSyncResponse(
        message=f"{req.entity_type}#{req.entity_id} 凭证同步完成，状态: {log.status.value}",
        task_ids=[str(log.id)],
    )


@router.post("/sync/master-data", response_model=ManualSyncResponse)
async def sync_all_vouchers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    """手动触发凭证同步测试（仅云会计 API）"""
    from app.integrations.kingdee.client import get_kingdee_client, KingdeeAPIError

    client = get_kingdee_client()
    results: dict = {}

    try:
        await client._ensure_token()
        results["token"] = "OK"
    except Exception as exc:
        results["token"] = f"FAILED: {exc}"
        return ManualSyncResponse(
            message=f"获取 Token 失败: {exc}",
            task_ids=[],
        )

    test_apis = [
        ("POST", "/jdyaccouting/voucherlist", {
            "fromPeriod": 202501, "toPeriod": 202512, "page": 1, "pageSize": 5,
        }),
    ]
    for method, path, body in test_apis:
        try:
            data = await client.post(path, json=body)
            results[path] = {"ok": True, "preview": str(data)[:200]}
        except KingdeeAPIError as exc:
            results[path] = {"ok": False, "code": exc.code, "msg": exc.message}
        except Exception as exc:
            results[path] = {"ok": False, "error": str(exc)}

    ok_count = sum(1 for v in results.values() if isinstance(v, dict) and v.get("ok"))
    return ManualSyncResponse(
        message=f"云会计 API 测试完成：{ok_count}/{len(test_apis)} 个接口可用",
        task_ids=[],
    )


# ---------------------------------------------------------------------------
# Cleanup obsolete sync logs
# ---------------------------------------------------------------------------

OBSOLETE_ENTITY_TYPES = {"customer", "supplier", "product"}


@router.delete("/sync-logs/cleanup", response_model=ManualSyncResponse)
async def cleanup_obsolete_sync_logs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    """删除已废弃的 master-data 同步日志 (customer/supplier/product)"""
    from sqlalchemy import delete as sql_delete

    result = await db.execute(
        sql_delete(SyncLog).where(SyncLog.entity_type.in_(OBSOLETE_ENTITY_TYPES))
    )
    await db.commit()
    count = result.rowcount
    return ManualSyncResponse(
        message=f"已清理 {count} 条旧同步日志（customer/supplier/product）",
        task_ids=[],
    )


# ---------------------------------------------------------------------------
# Sync log detail (with payloads)
# ---------------------------------------------------------------------------

class SyncLogDetailResponse(SyncLogResponse):
    request_payload: Optional[dict] = None
    response_payload: Optional[dict] = None


@router.get("/sync-logs/{log_id}/detail", response_model=SyncLogDetailResponse)
async def get_sync_log_detail(
    log_id: int = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    """查看同步日志详情（含请求/响应体）"""
    log = (await db.execute(select(SyncLog).where(SyncLog.id == log_id))).scalar_one_or_none()
    if not log:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("同步日志", log_id)
    return log


# ---------------------------------------------------------------------------
# AI Error Diagnosis
# ---------------------------------------------------------------------------

class DiagnosisResult(BaseModel):
    log_id: int
    severity: str  # info / warning / critical
    root_cause: str
    suggestions: list[str]
    related_docs: list[str] = []


_ERROR_PATTERNS: list[tuple[str, str, str, list[str]]] = [
    ("token", "critical", "认证 Token 过期或无效",
     ["检查 KINGDEE_APP_SECRET 是否正确", "重新获取 Token 后重试", "确认精斗云实例 ID 与账套匹配"]),
    ("timeout", "warning", "网络超时 — 精斗云 API 响应缓慢",
     ["检查网络连通性", "避免高峰期批量同步", "增大 HTTP timeout 配置"]),
    ("rate limit", "warning", "请求频率超限 — 触发精斗云 API 限流",
     ["降低并发同步任务数", "为 Celery 队列增加 rate_limit", "错峰批量操作"]),
    ("duplicate", "info", "重复单据 — 精斗云已存在相同编号记录",
     ["检查 entity_id 是否已同步成功", "在精斗云控制台确认单据状态", "若为重试导致可忽略"]),
    ("field", "critical", "字段映射错误 — 精斗云拒绝了请求体",
     ["检查 request_payload 中的必填字段", "确认金额、日期格式符合精斗云要求", "对照精斗云 API 文档校验字段名"]),
    ("permission", "critical", "权限不足 — 当前账套无此 API 权限",
     ["确认精斗云 APP 已授权该模块", "联系财务检查账套的接口权限", "检查 INSTANCE_ID 是否正确"]),
    ("connect", "critical", "无法连接精斗云服务器",
     ["检查 KINGDEE_BASE_URL 配置", "确认服务器出网策略是否允许访问 api.jdy.com", "检查 DNS 解析"]),
    ("balance", "warning", "科目余额异常 — 凭证金额可能不平",
     ["检查借贷金额是否一致", "确认科目代码 (AccountCodes) 配置正确", "手动核对金额后重试"]),
]


@router.post("/sync-logs/{log_id}/ai-diagnosis", response_model=DiagnosisResult)
async def ai_diagnose_sync_error(
    log_id: int = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    """AI 智能诊断同步失败原因并给出修复建议"""
    log = (await db.execute(select(SyncLog).where(SyncLog.id == log_id))).scalar_one_or_none()
    if not log:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("同步日志", log_id)

    error_text = (log.error_message or "").lower()
    resp_text = str(log.response_payload or "").lower()
    combined = f"{error_text} {resp_text}"

    for keyword, severity, cause, suggestions in _ERROR_PATTERNS:
        if keyword in combined:
            return DiagnosisResult(
                log_id=log_id,
                severity=severity,
                root_cause=cause,
                suggestions=suggestions,
                related_docs=["https://open.jdy.com/#/files/api/detail"],
            )

    # Fallback: generic analysis based on HTTP status or doc type
    if log.response_payload and isinstance(log.response_payload, dict):
        code = log.response_payload.get("errcode", "")
        if code:
            return DiagnosisResult(
                log_id=log_id,
                severity="warning",
                root_cause=f"精斗云返回错误码: {code} — {log.response_payload.get('description', '未知')}",
                suggestions=[
                    "对照精斗云错误码文档查询具体含义",
                    f"检查 entity_type={log.entity_type}, entity_id={log.entity_id} 的数据完整性",
                    "确认 request_payload 字段值的合法性",
                ],
                related_docs=["https://open.jdy.com/#/files/api/detail"],
            )

    return DiagnosisResult(
        log_id=log_id,
        severity="info",
        root_cause=log.error_message or "未能自动识别根因 — 建议人工排查",
        suggestions=[
            "查看 request_payload 和 response_payload 原始数据",
            "在精斗云控制台检查对应单据状态",
            "若持续失败请联系精斗云技术支持",
        ],
        related_docs=["https://open.jdy.com/#/files/api/detail"],
    )


# ---------------------------------------------------------------------------
# Kingdee Webhook — 消息订阅回调
# ---------------------------------------------------------------------------

_webhook_logger = logging.getLogger("kingdee.webhook")


@router.post("/kingdee/webhook")
async def kingdee_webhook(
    request: Request,
    bizType: str = Query(default=""),
    msgId: str = Query(default=""),
):
    """
    金蝶精斗云消息订阅回调端点。

    配置地址: https://<domain>/api/integration/kingdee/webhook

    金蝶会发送 POST 请求:
      - bizType=test_address : 连通性测试
      - 其他 bizType          : 业务数据推送
    """
    if bizType == "test_address":
        _webhook_logger.info("Kingdee webhook test received, msgId=%s", msgId)
        return {"success": True, "message": "webhook endpoint is reachable"}

    body: Any = None
    try:
        body = await request.json()
    except Exception:
        body = (await request.body()).decode(errors="replace")

    _webhook_logger.info(
        "Kingdee webhook received: bizType=%s, msgId=%s, body=%s",
        bizType, msgId, body,
    )

    # TODO: 根据 bizType 处理具体业务推送（如单据审核通知等）

    return {"success": True, "bizType": bizType, "msgId": msgId}
