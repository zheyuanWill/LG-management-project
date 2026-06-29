"""
Celery Application Configuration
"""
from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "lg_management",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.export",
        "app.tasks.notification",
        "app.tasks.kingdee_tasks",
        "app.tasks.scheduled",
    ],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    worker_prefetch_multiplier=1,
    result_expires=3600,  # 1 hour
)

# Task routing
celery_app.conf.task_routes = {
    "app.tasks.export.*": {"queue": "export"},
    "app.tasks.notification.*": {"queue": "notification"},
    "app.tasks.kingdee_tasks.*": {"queue": "kingdee"},
    "app.tasks.scheduled.*": {"queue": "notification"},
}

# Beat schedule — periodic ISO 9001 tasks
celery_app.conf.beat_schedule = {
    "inquiry-timeout-check": {
        "task": "app.tasks.scheduled.check_inquiry_timeout",
        "schedule": crontab(minute=0),  # every hour
    },
    "payment-due-reminder": {
        "task": "app.tasks.scheduled.check_payment_due",
        "schedule": crontab(hour=9, minute=0),  # daily 9:00
    },
    "collection-escalation": {
        "task": "app.tasks.scheduled.check_collection_escalation",
        "schedule": crontab(hour=9, minute=30),  # daily 9:30
    },
    "warranty-expiry-reminder": {
        "task": "app.tasks.scheduled.check_warranty_expiry",
        "schedule": crontab(hour=10, minute=0),  # daily 10:00
    },
    "overdue-node-check": {
        "task": "app.tasks.notification.check_overdue_nodes",
        "schedule": crontab(hour="*/6", minute=0),  # every 6 hours
    },
}

