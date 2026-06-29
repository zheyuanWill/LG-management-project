"""Notification tasks — Celery workers for async notification delivery."""
import logging
from datetime import datetime, timezone, timedelta

from app.core.celery_app import celery_app

logger = logging.getLogger("tasks.notification")


@celery_app.task(bind=True)
def send_notification(self, user_id: int, title: str, content: str):
    """Send notification to user (fire-and-forget from sync context)."""
    from app.db.session import SessionLocal
    from app.models.notification import Notification, NotificationType

    with SessionLocal() as db:
        notification = Notification(
            user_id=user_id,
            type=NotificationType.INFO,
            title=title,
            content=content,
        )
        db.add(notification)
        db.commit()

    return {"status": "success", "user_id": user_id}


@celery_app.task(bind=True)
def check_overdue_nodes(self):
    """
    Periodic task: scan running workflow instances for nodes that have been
    RUNNING longer than a configured threshold and send reminder notifications.

    Default threshold: 48 hours since node startedAt.
    """
    import asyncio
    from sqlalchemy import select
    from app.db.session import async_session_factory
    from app.models.workflow import WorkflowInstance, WorkflowStatus, WorkflowNodeStatus
    from app.models.notification import NotificationType
    from app.models.user import User

    async def _check():
        async with async_session_factory() as db:
            result = await db.execute(
                select(WorkflowInstance).where(
                    WorkflowInstance.status == WorkflowStatus.RUNNING,
                )
            )
            instances = result.scalars().all()
            overdue_count = 0
            threshold = datetime.now(timezone.utc) - timedelta(hours=48)

            for instance in instances:
                node_states = instance.node_states or {}
                for node_id, state in node_states.items():
                    if state.get("status") != WorkflowNodeStatus.RUNNING.value:
                        continue

                    started_at_str = state.get("startedAt")
                    if not started_at_str:
                        continue

                    try:
                        started_at = datetime.fromisoformat(started_at_str.replace("Z", "+00:00"))
                    except (ValueError, TypeError):
                        continue

                    if started_at > threshold:
                        continue

                    assignee_name = state.get("assignee")
                    if not assignee_name:
                        continue

                    user = (await db.execute(
                        select(User).where(User.real_name == assignee_name, User.is_active == True).limit(1)
                    )).scalar_one_or_none()

                    if not user:
                        continue

                    from app.routers.notification import create_notification
                    await create_notification(
                        db,
                        user_id=user.id,
                        type=NotificationType.OVERDUE,
                        title=f"催办: {state.get('label', node_id)}",
                        content=f"工作流「{instance.name}」的节点「{state.get('label', node_id)}」已超过48小时未处理，请尽快处理。",
                        related_type="workflow",
                        related_id=instance.id,
                    )
                    overdue_count += 1

            await db.commit()
            return overdue_count

    try:
        count = asyncio.get_event_loop().run_until_complete(_check())
    except RuntimeError:
        count = asyncio.run(_check())

    logger.info("Overdue check completed: %d notifications sent", count)
    return {"status": "success", "overdue_notifications": count}
