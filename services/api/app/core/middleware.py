"""
Performance testing middleware.

Simulates realistic slow-query behavior when the database has millions of rows.

Usage:
    # Enable via environment variable:
    SLOW_QUERY_ENABLED=true uvicorn app.main:app

    # Configure delay range (in milliseconds):
    SLOW_QUERY_MIN_MS=200 SLOW_QUERY_MAX_MS=3000 SLOW_QUERY_ENABLED=true uvicorn app.main:app

    # Only slow down list endpoints (not individual GETs):
    SLOW_QUERY_LIST_ONLY=true SLOW_QUERY_ENABLED=true uvicorn app.main:app

How it works:
    - Adds random delay (uniform distribution) to API responses.
    - List endpoints (GET without trailing ID) get higher delay to simulate
      COUNT(*) + JOIN + ORDER BY on 10M+ rows.
    - Detail endpoints (GET with /123) get lower delay.
    - Mutations (POST/PUT/DELETE) get minimal delay.
    - Logs timing to console for analysis.
"""
import asyncio
import logging
import os
import random
import re
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("slow-query-sim")


def _is_list_endpoint(path: str, method: str) -> bool:
    """Detect list endpoints: GET /api/orders, GET /api/products, etc."""
    if method != "GET":
        return False
    # Match /api/resource (list) but not /api/resource/123 (detail)
    return bool(re.match(r"^/api/[a-z]+/?$", path))


def _is_detail_endpoint(path: str, method: str) -> bool:
    """Detect detail endpoints: GET /api/orders/123"""
    if method != "GET":
        return False
    return bool(re.match(r"^/api/[a-z]+/\d+", path))


class SlowQueryMiddleware(BaseHTTPMiddleware):
    """Simulates database slowness for performance testing."""

    def __init__(self, app):
        super().__init__(app)
        self.min_ms = int(os.environ.get("SLOW_QUERY_MIN_MS", "200"))
        self.max_ms = int(os.environ.get("SLOW_QUERY_MAX_MS", "3000"))
        self.list_only = os.environ.get("SLOW_QUERY_LIST_ONLY", "").lower() in ("true", "1")
        self.list_multiplier = float(os.environ.get("SLOW_QUERY_LIST_MULTIPLIER", "3.0"))

        logger.info(
            "SlowQueryMiddleware enabled: delay=%d-%dms, list_only=%s, list_multiplier=%.1f",
            self.min_ms, self.max_ms, self.list_only, self.list_multiplier,
        )

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        method = request.method

        # Skip non-API routes
        if not path.startswith("/api/"):
            return await call_next(request)

        # Skip health check
        if path in ("/api/health", "/api/auth/login", "/api/auth/refresh"):
            return await call_next(request)

        # Determine delay
        delay_ms = 0
        if _is_list_endpoint(path, method):
            # List queries are slowest (full table scan + count)
            base = random.uniform(self.min_ms, self.max_ms)
            delay_ms = base * self.list_multiplier
            # Extra delay based on page size
            try:
                size = int(request.query_params.get("size", "20"))
                if size > 50:
                    delay_ms *= 1.5
                if size > 100:
                    delay_ms *= 2.0
            except (ValueError, TypeError):
                pass
        elif _is_detail_endpoint(path, method):
            if not self.list_only:
                delay_ms = random.uniform(self.min_ms * 0.5, self.max_ms * 0.3)
        elif method in ("POST", "PUT", "PATCH", "DELETE"):
            if not self.list_only:
                delay_ms = random.uniform(self.min_ms * 0.2, self.max_ms * 0.2)

        # Apply delay
        if delay_ms > 0:
            delay_s = delay_ms / 1000
            logger.info(
                "⏳ [SLOW] %s %s → simulated delay %.0fms",
                method, path, delay_ms,
            )
            await asyncio.sleep(delay_s)

        # Execute actual request and measure real time
        t0 = time.time()
        response = await call_next(request)
        real_ms = (time.time() - t0) * 1000

        logger.info(
            "✅ [PERF] %s %s → delay=%.0fms, real=%.0fms, total=%.0fms, status=%d",
            method, path, delay_ms, real_ms, delay_ms + real_ms, response.status_code,
        )

        # Add timing headers for frontend analysis
        response.headers["X-Simulated-Delay-Ms"] = str(int(delay_ms))
        response.headers["X-Real-Processing-Ms"] = str(int(real_ms))

        return response
