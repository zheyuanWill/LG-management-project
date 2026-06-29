"""
Kingdee Jingdouyun HTTP Client

Auth flow (based on github.com/zhuger/kingdee PHP SDK):

Credentials (two layers):
  - Client ID (应用ID, e.g. 336930) + Client Secret → used for HMAC request signing
  - AppKey + AppSecret (from 应用集成) → used for computing app_signature to get JWT

Steps:
  1. POST /jdyconnector/app_management/push_app_authorize?outerInstanceId=<id>
     Headers signed with Client ID + Client Secret
     → returns instance appKey + appSecret (may match 应用集成 values)
  2. GET  /jdyconnector/app_management/kingdee_auth_token?app_key=<key>&app_signature=<sig>
     app_signature = base64(hmac_sha256(appKey, appSecret))
     → returns app-token (JWT)
  3. Business APIs use app-token + sId + dbId as query params
"""
import base64
import hashlib
import hmac
import logging
import random
import time
from datetime import datetime, timedelta
from typing import Any, Optional
from urllib.parse import quote

import httpx

from app.core.config import settings

logger = logging.getLogger("kingdee")

TOKEN_REFRESH_BUFFER_SECONDS = 300


class KingdeeAPIError(Exception):
    def __init__(self, code: str, message: str, response: Optional[dict] = None):
        self.code = code
        self.message = message
        self.response = response
        super().__init__(f"[{code}] {message}")


class KingdeeClient:
    def __init__(
        self,
        client_id: str = "",
        client_secret: str = "",
        app_key: str = "",
        app_secret: str = "",
        instance_id: str = "",
        base_url: str = "",
        sid: str = "",
        db_id: str = "",
        domain: str = "",
    ):
        self.client_id = client_id or settings.KINGDEE_CLIENT_ID
        self.client_secret = client_secret or settings.KINGDEE_CLIENT_SECRET
        self.app_key = app_key or settings.KINGDEE_APP_KEY
        self.app_secret = app_secret or settings.KINGDEE_APP_SECRET
        self.instance_id = instance_id or settings.KINGDEE_INSTANCE_ID
        self.base_url = (base_url or settings.KINGDEE_BASE_URL).rstrip("/")
        self.sid = sid or settings.KINGDEE_SID
        self.db_id = db_id or settings.KINGDEE_DB_ID or self.sid
        self.domain = domain or getattr(settings, "KINGDEE_DOMAIN", "")

        self._app_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self._http: Optional[httpx.AsyncClient] = None

    @property
    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret and self.instance_id)

    async def _get_http(self) -> httpx.AsyncClient:
        if self._http is None or self._http.is_closed:
            self._http = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(30.0, connect=10.0),
            )
        return self._http

    async def close(self) -> None:
        if self._http and not self._http.is_closed:
            await self._http.aclose()
            self._http = None

    # ------------------------------------------------------------------
    # HMAC-SHA256 request signing (matches PHP SDK)
    # Uses Client ID for X-Api-ClientID and Client Secret as HMAC key
    # ------------------------------------------------------------------

    def _sign_headers(self, method: str, path: str, query_params: dict, *, skip_app_token: bool = False) -> dict:
        ts = str(int(time.time() * 1000))
        nonce = str(random.randint(1000000, 9999999))

        encoded_params = ""
        if query_params:
            parts = []
            for k, v in sorted(query_params.items()):
                ek = quote(quote(str(k), safe=""), safe="")
                ev = quote(quote(str(v), safe=""), safe="")
                parts.append(f"{ek}={ev}")
            encoded_params = "&".join(parts)

        sign_data = (
            f"{method.upper()}\n"
            f"{quote(path, safe='')}\n"
            f"{encoded_params}\n"
            f"x-api-nonce:{nonce}\n"
            f"x-api-timestamp:{ts}\n"
        )

        signature = base64.b64encode(
            hmac.new(
                self.client_secret.encode(),
                sign_data.encode(),
                hashlib.sha256,
            ).hexdigest().encode()
        ).decode()

        headers = {
            "Content-Type": "application/json; charset=UTF-8",
            "X-Api-SignHeaders": "X-Api-TimeStamp,X-Api-Nonce",
            "X-Api-Auth-Version": "2.0",
            "X-Api-ClientID": self.client_id,
            "X-Api-TimeStamp": ts,
            "X-Api-Nonce": nonce,
            "X-Api-Signature": signature,
        }
        if self._app_token and not skip_app_token:
            headers["app-token"] = self._app_token
        return headers

    # ------------------------------------------------------------------
    # Token acquisition
    # ------------------------------------------------------------------

    def _token_valid(self) -> bool:
        if not self._app_token or not self._token_expires_at:
            return False
        return datetime.utcnow() < self._token_expires_at - timedelta(seconds=TOKEN_REFRESH_BUFFER_SECONDS)

    async def _ensure_token(self) -> str:
        if self._token_valid():
            return self._app_token  # type: ignore

        inst_app_key, inst_app_secret = await self._authorize_instance()

        app_signature = base64.b64encode(
            hmac.new(
                inst_app_secret.encode(),
                inst_app_key.encode(),
                hashlib.sha256,
            ).hexdigest().encode()
        ).decode()

        path = "/jdyconnector/app_management/kingdee_auth_token"
        params: dict[str, str] = {
            "app_key": inst_app_key,
            "app_signature": app_signature,
        }

        http = await self._get_http()

        # First call: get uid + access_token
        headers = self._sign_headers("GET", path, params)
        resp = await http.get(path, params=params, headers=headers)
        try:
            data = resp.json()
        except Exception:
            data = {"_raw": resp.text[:2000], "_status": resp.status_code}
        logger.info("Token step1 status=%d response: %s", resp.status_code, str(data)[:300])

        if resp.status_code >= 400:
            err_msg = data.get("description", "") if isinstance(data, dict) else ""
            raw = data.get("_raw", "") if isinstance(data, dict) else ""
            err_code = str(data.get("errcode", resp.status_code)) if isinstance(data, dict) else str(resp.status_code)
            raise KingdeeAPIError(err_code, err_msg or raw or f"HTTP {resp.status_code}", data if isinstance(data, dict) else {"_raw": str(data)[:500]})

        if isinstance(data, dict) and data.get("errcode") and str(data["errcode"]) != "0":
            raise KingdeeAPIError(str(data["errcode"]), data.get("description", "Token 获取失败"), data)

        token_data = data.get("data", data)
        uid = str(token_data.get("uid", ""))

        # If we got a uid, try again with uid to get JWT app-token
        if uid:
            params["uid"] = uid
            headers = self._sign_headers("GET", path, params)
            resp2 = await http.get(path, params=params, headers=headers)
            try:
                data2 = resp2.json()
            except Exception:
                data2 = {"_raw": resp2.text[:2000], "_status": resp2.status_code}
            logger.info("Token step2 (with uid) status=%d response: %s", resp2.status_code, str(data2)[:300])

            if isinstance(data2, dict) and not (data2.get("errcode") and str(data2["errcode"]) != "0"):
                token_data2 = data2.get("data", data2)
                jwt_token = token_data2.get("app-token") or token_data2.get("app_token")
                if jwt_token:
                    self._app_token = jwt_token
                    expires_ms = token_data2.get("expires")
                    if expires_ms:
                        self._token_expires_at = datetime.utcfromtimestamp(expires_ms / 1000)
                    else:
                        self._token_expires_at = datetime.utcnow() + timedelta(hours=2)
                    logger.info("Kingdee JWT app-token acquired, expires at %s", self._token_expires_at)
                    return self._app_token

        # Fallback: use the access_token from step1
        self._app_token = (
            token_data.get("access_token")
            or token_data.get("app-token")
            or token_data.get("app_token")
        )
        if not self._app_token:
            raise KingdeeAPIError("TOKEN_FAIL", f"响应中没有 token: {data}", data)

        expires_ms = token_data.get("expires")
        if expires_ms:
            self._token_expires_at = datetime.utcfromtimestamp(expires_ms / 1000)
        else:
            self._token_expires_at = datetime.utcnow() + timedelta(hours=2)
        logger.info("Kingdee access_token acquired (no JWT), expires at %s", self._token_expires_at)
        return self._app_token

    async def _authorize_instance(self) -> tuple[str, str]:
        """Step 1: Get instance-level appKey/appSecret via outerInstanceId."""
        path = "/jdyconnector/app_management/push_app_authorize"
        params = {"outerInstanceId": self.instance_id}
        headers = self._sign_headers("POST", path, params)

        http = await self._get_http()
        resp = await http.post(path, params=params, headers=headers)
        try:
            data = resp.json()
        except Exception:
            data = {"_raw": resp.text[:2000], "_status": resp.status_code}
        logger.info("Authorize instance status=%d response: %s", resp.status_code, str(data)[:300])

        if resp.status_code >= 400:
            err_msg = data.get("description", "") if isinstance(data, dict) else ""
            raw = data.get("_raw", "") if isinstance(data, dict) else ""
            err_code = str(data.get("errcode", resp.status_code)) if isinstance(data, dict) else str(resp.status_code)
            raise KingdeeAPIError(err_code, err_msg or raw or f"HTTP {resp.status_code}", data if isinstance(data, dict) else {})

        if isinstance(data, dict) and data.get("errcode") and str(data["errcode"]) != "0":
            raise KingdeeAPIError(str(data["errcode"]), data.get("description", "授权失败"), data)

        items = data.get("data", data)
        item: Optional[dict] = None
        if isinstance(items, list) and len(items) > 0:
            item = items[0]
        elif isinstance(items, dict) and "appKey" in items:
            item = items

        if not item:
            raise KingdeeAPIError("AUTH_FAIL", f"授权响应异常: {data}", data if isinstance(data, dict) else {})

        # Auto-detect domain for X-GW-Router-Addr if not already configured
        if not self.domain and item.get("domain"):
            self.domain = item["domain"]
            logger.info("Auto-detected Kingdee domain: %s", self.domain)

        return item["appKey"], item["appSecret"]

    # ------------------------------------------------------------------
    # Core request
    # ------------------------------------------------------------------

    async def request(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        params: Optional[dict] = None,
        extra_headers: Optional[dict] = None,
        max_retries: int = 2,
    ) -> dict[str, Any]:
        await self._ensure_token()
        http = await self._get_http()

        is_accounting = path.startswith("/jdyaccouting")

        query_params: dict[str, Any] = {
            "access_token": self._app_token,
            "sId": self.sid,
            "dbId": self.db_id,
        }
        if params:
            query_params.update(params)

        headers = self._sign_headers(method, path, query_params, skip_app_token=is_accounting)
        if self.domain:
            headers["X-GW-Router-Addr"] = self.domain
        if is_accounting:
            headers["Authorization"] = f"Bearer {self._app_token}"
        if extra_headers:
            headers.update(extra_headers)

        auth_retries = 0
        for attempt in range(1, max_retries + 2):
            try:
                resp = await http.request(method, path, json=json, params=query_params, headers=headers)
                body = None
                try:
                    body = resp.json()
                except Exception:
                    body = {"_raw": resp.text[:2000]}

                logger.info(
                    "Kingdee %s %s → %d body=%s",
                    method, path, resp.status_code, str(body)[:300],
                )

                if resp.status_code == 401 and auth_retries < 1:
                    auth_retries += 1
                    self._app_token = None
                    await self._ensure_token()
                    query_params["access_token"] = self._app_token
                    headers = self._sign_headers(method, path, query_params, skip_app_token=is_accounting)
                    if self.domain:
                        headers["X-GW-Router-Addr"] = self.domain
                    if extra_headers:
                        headers.update(extra_headers)
                    continue

                if resp.status_code >= 400:
                    err_code = str(body.get("errcode", resp.status_code)) if isinstance(body, dict) else str(resp.status_code)
                    err_msg = ""
                    if isinstance(body, dict):
                        err_msg = body.get("description") or body.get("msg") or body.get("message") or ""
                    err_msg = err_msg or f"HTTP {resp.status_code}"
                    raise KingdeeAPIError(err_code, err_msg, body if isinstance(body, dict) else {"_raw": str(body)})

                if isinstance(body, dict) and body.get("errcode") and str(body["errcode"]) != "0":
                    raise KingdeeAPIError(
                        str(body["errcode"]),
                        body.get("description") or body.get("msg", "Unknown"),
                        body,
                    )
                return body

            except KingdeeAPIError:
                raise

            except httpx.TransportError as exc:
                if attempt <= max_retries:
                    wait = 2 ** attempt
                    logger.warning("Kingdee %s %s transport: %s, retry in %ds", method, path, exc, wait)
                    import asyncio; await asyncio.sleep(wait)
                    continue
                raise

        raise RuntimeError("Unexpected retry loop exit")

    async def get(self, path: str, *, params=None, extra_headers=None, **kwargs) -> dict:
        return await self.request("GET", path, params=params, extra_headers=extra_headers, **kwargs)

    async def post(self, path: str, *, json=None, params=None, extra_headers=None, **kwargs) -> dict:
        return await self.request("POST", path, json=json, params=params, extra_headers=extra_headers, **kwargs)

    async def test_connection(self) -> dict[str, Any]:
        try:
            token = await self._ensure_token()
            return {
                "connected": True,
                "message": "连接成功",
                "token_preview": token[:8] + "..." if token else None,
            }
        except Exception as exc:
            return {"connected": False, "message": f"连接失败: {exc}"}



_client: Optional[KingdeeClient] = None


def get_kingdee_client() -> KingdeeClient:
    global _client
    if _client is None:
        _client = KingdeeClient()
    return _client
