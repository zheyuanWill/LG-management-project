"""
Celery tasks for Kingdee Cloud Accounting (jdyaccouting) voucher sync.

Each task runs in a Celery worker process. Since the sync service uses
async SQLAlchemy + httpx, we run the async code via asyncio.run().
"""
import asyncio
import logging

from app.core.celery_app import celery_app
from app.core.config import settings

logger = logging.getLogger("kingdee.tasks")


def _run_async(coro):
    """Run an async coroutine in a sync Celery task."""
    return asyncio.get_event_loop().run_until_complete(coro)


async def _get_session_and_service():
    from app.db.session import async_session_maker
    from app.integrations.kingdee.sync_service import KingdeeSyncService
    return async_session_maker(), KingdeeSyncService()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def sync_order_to_jdy(self, order_id: int):
    """Sync an order to Kingdee as a sale voucher."""
    if not settings.KINGDEE_ENABLED:
        return {"status": "skipped", "reason": "Kingdee integration disabled"}

    async def _run():
        session_maker, svc = await _get_session_and_service()
        async with session_maker() as db:
            try:
                log = await svc.sync_order(db, order_id)
                await db.commit()
                return {"status": log.status.value, "kingdee_doc_no": log.kingdee_doc_no}
            except Exception as exc:
                await db.rollback()
                raise

    try:
        return _run_async(_run())
    except Exception as exc:
        logger.error("sync_order_to_jdy failed for order %d: %s", order_id, exc)
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def sync_procurement_to_jdy(self, procurement_id: int):
    """Sync a procurement receiving event to Kingdee as a purchase voucher."""
    if not settings.KINGDEE_ENABLED:
        return {"status": "skipped", "reason": "Kingdee integration disabled"}

    async def _run():
        session_maker, svc = await _get_session_and_service()
        async with session_maker() as db:
            try:
                log = await svc.sync_procurement_received(db, procurement_id)
                await db.commit()
                return {"status": log.status.value, "kingdee_doc_no": log.kingdee_doc_no}
            except Exception as exc:
                await db.rollback()
                raise

    try:
        return _run_async(_run())
    except Exception as exc:
        logger.error("sync_procurement_to_jdy failed for procurement %d: %s", procurement_id, exc)
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def sync_disbursement_to_jdy(self, disbursement_id: int):
    """Sync a procurement payment to Kingdee as a payment voucher."""
    if not settings.KINGDEE_ENABLED:
        return {"status": "skipped", "reason": "Kingdee integration disabled"}

    async def _run():
        session_maker, svc = await _get_session_and_service()
        async with session_maker() as db:
            try:
                log = await svc.sync_disbursement(db, disbursement_id)
                await db.commit()
                return {"status": log.status.value, "kingdee_doc_no": log.kingdee_doc_no}
            except Exception as exc:
                await db.rollback()
                raise

    try:
        return _run_async(_run())
    except Exception as exc:
        logger.error("sync_disbursement_to_jdy failed for disbursement %d: %s", disbursement_id, exc)
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def sync_settlement_to_jdy(self, settlement_id: int):
    """Sync an approved settlement to Kingdee as a summary voucher."""
    if not settings.KINGDEE_ENABLED:
        return {"status": "skipped", "reason": "Kingdee integration disabled"}

    async def _run():
        session_maker, svc = await _get_session_and_service()
        async with session_maker() as db:
            try:
                log = await svc.sync_settlement(db, settlement_id)
                await db.commit()
                return {"status": log.status.value, "kingdee_doc_no": log.kingdee_doc_no}
            except Exception as exc:
                await db.rollback()
                raise

    try:
        return _run_async(_run())
    except Exception as exc:
        logger.error("sync_settlement_to_jdy failed for settlement %d: %s", settlement_id, exc)
        raise self.retry(exc=exc)



# Master data sync tasks (customer/supplier/product) have been removed.
# Only accounting voucher sync is supported via jdyaccouting API.
