"""
MinIO Client — lazy initialization with graceful fallback.

When MinIO is not available (e.g. Zeabur without MinIO addon),
file-upload endpoints will return a clear error instead of crashing
the whole application on startup.
"""
from __future__ import annotations

import logging
from typing import Optional

from minio import Minio
from app.core.config import settings

logger = logging.getLogger(__name__)

_client: Optional[Minio] = None
_initialized = False


def get_minio_client() -> Optional[Minio]:
    global _client, _initialized
    if _initialized:
        return _client

    _initialized = True
    try:
        _client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_USE_SSL,
        )
        if not _client.bucket_exists(settings.MINIO_BUCKET):
            _client.make_bucket(settings.MINIO_BUCKET)
        logger.info("MinIO connected: %s/%s", settings.MINIO_ENDPOINT, settings.MINIO_BUCKET)
    except Exception as e:
        logger.warning("MinIO unavailable, file features disabled: %s", e)
        _client = None

    return _client


# Backwards-compatible module-level reference (lazy — no network call at import time)
minio_client: Optional[Minio] = None


def _ensure_client() -> Minio:
    """Return an active MinIO client or raise a clear error."""
    client = get_minio_client()
    if client is None:
        raise RuntimeError("MinIO is not configured or unreachable. File operations are unavailable.")
    return client
