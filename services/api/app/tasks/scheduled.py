"""Scheduled ISO 9001 tasks — Celery Beat periodic tasks."""
import asyncio
import logging
from datetime import datetime, timezone, timedelta, date

from app.core.celery_app import celery_app

logger = logging.getLogger("tasks.scheduled")


def _run_async(coro):
    """Run an async coroutine from synchronous Celery task."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, coro).result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


@celery_app.task(bind=True)
def check_inquiry_timeout(self):
    """Hourly: mark overdue inquiry records and notify PM."""
    async def _check():
        from sqlalchemy import select
        from app.db.session import async_session_maker
        from app.models.iso_process import InquiryRecord
        from app.models.order import Order
        from app.models.notification import Notification, NotificationType

        now = datetime.now(timezone.utc)
        count = 0
        async with async_session_maker() as db:
            result = await db.execute(
                select(InquiryRecord).where(
                    InquiryRecord.responded == False,
                    InquiryRecord.deadline != None,
                    InquiryRecord.deadline < now,
                )
            )
            overdue = result.scalars().all()
            for rec in overdue:
                order = (await db.execute(
                    select(Order).where(Order.id == rec.order_id)
                )).scalar_one_or_none()
                if not order:
                    continue
                db.add(Notification(
                    user_id=order.pm_id,
                    type=NotificationType.OVERDUE,
                    title=f"询价超时: 订单 {order.order_no}",
                    content=f"供应商 #{rec.supplier_id} 询价已超过截止时间未响应",
                    related_type="inquiry_record",
                    related_id=rec.id,
                ))
                count += 1
            await db.commit()
        return count

    count = _run_async(_check())
    logger.info("Inquiry timeout check: %d notifications", count)
    return {"inquiry_timeout_notifications": count}


@celery_app.task(bind=True)
def check_payment_due(self):
    """Daily 9:00: remind PM about payment plans due within 3 days."""
    async def _check():
        from sqlalchemy import select
        from app.db.session import async_session_maker
        from app.models.contract import PaymentPlan, Contract
        from app.models.order import Order
        from app.models.notification import Notification, NotificationType

        today = date.today()
        soon = today + timedelta(days=3)
        count = 0
        async with async_session_maker() as db:
            result = await db.execute(
                select(PaymentPlan).where(
                    PaymentPlan.planned_date <= soon,
                    PaymentPlan.planned_date >= today,
                    PaymentPlan.actual_date == None,
                )
            )
            due_plans = result.scalars().all()
            for plan in due_plans:
                contract = (await db.execute(
                    select(Contract).where(Contract.id == plan.contract_id)
                )).scalar_one_or_none()
                if not contract:
                    continue
                order = (await db.execute(
                    select(Order).where(Order.id == contract.order_id)
                )).scalar_one_or_none()
                if not order:
                    continue
                days_left = (plan.planned_date - today).days
                db.add(Notification(
                    user_id=order.pm_id,
                    type=NotificationType.REMINDER,
                    title=f"回款提醒: {contract.contract_no}",
                    content=f"合同 {contract.contract_no} 第 {plan.phase} 期回款 ¥{plan.planned_amount} 将于 {days_left} 天后到期",
                    related_type="payment_plan",
                    related_id=plan.id,
                ))
                count += 1
            await db.commit()
        return count

    count = _run_async(_check())
    logger.info("Payment due check: %d notifications", count)
    return {"payment_due_notifications": count}


@celery_app.task(bind=True)
def check_collection_escalation(self):
    """Daily 9:30: escalate to OWNER when payment overdue > 30 days."""
    async def _check():
        from sqlalchemy import select
        from app.db.session import async_session_maker
        from app.models.contract import PaymentPlan, Contract
        from app.models.order import Order
        from app.models.user import User, UserRole
        from app.models.notification import Notification, NotificationType

        today = date.today()
        threshold = today - timedelta(days=30)
        count = 0
        async with async_session_maker() as db:
            result = await db.execute(
                select(PaymentPlan).where(
                    PaymentPlan.planned_date < threshold,
                    PaymentPlan.actual_date == None,
                )
            )
            overdue_plans = result.scalars().all()
            owners = (await db.execute(
                select(User).where(User.role == UserRole.OWNER, User.is_active == True)
            )).scalars().all()

            for plan in overdue_plans:
                contract = (await db.execute(
                    select(Contract).where(Contract.id == plan.contract_id)
                )).scalar_one_or_none()
                if not contract:
                    continue
                overdue_days = (today - plan.planned_date).days
                for owner in owners:
                    db.add(Notification(
                        user_id=owner.id,
                        type=NotificationType.OVERDUE,
                        title=f"催收升级: {contract.contract_no}",
                        content=f"合同 {contract.contract_no} 第 {plan.phase} 期回款已逾期 {overdue_days} 天，请关注",
                        related_type="payment_plan",
                        related_id=plan.id,
                    ))
                    count += 1
            await db.commit()
        return count

    count = _run_async(_check())
    logger.info("Collection escalation: %d notifications", count)
    return {"collection_escalation_notifications": count}


@celery_app.task(bind=True)
def check_warranty_expiry(self):
    """Daily 10:00: notify PM when contract warranty expires within 30 days."""
    async def _check():
        from sqlalchemy import select
        from app.db.session import async_session_maker
        from app.models.contract import Contract
        from app.models.order import Order
        from app.models.notification import Notification, NotificationType

        today = date.today()
        soon = today + timedelta(days=30)
        count = 0
        async with async_session_maker() as db:
            result = await db.execute(
                select(Contract).where(
                    Contract.warranty_end_date != None,
                    Contract.warranty_end_date <= soon,
                    Contract.warranty_end_date >= today,
                )
            )
            contracts = result.scalars().all()
            for contract in contracts:
                order = (await db.execute(
                    select(Order).where(Order.id == contract.order_id)
                )).scalar_one_or_none()
                if not order:
                    continue
                days_left = (contract.warranty_end_date - today).days
                db.add(Notification(
                    user_id=order.pm_id,
                    type=NotificationType.REMINDER,
                    title=f"质保到期提醒: {contract.contract_no}",
                    content=f"合同 {contract.contract_no} 质保期将于 {days_left} 天后到期 ({contract.warranty_end_date})",
                    related_type="contract",
                    related_id=contract.id,
                ))
                count += 1
            await db.commit()
        return count

    count = _run_async(_check())
    logger.info("Warranty expiry check: %d notifications", count)
    return {"warranty_expiry_notifications": count}
