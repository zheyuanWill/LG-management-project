from app.tasks.report_tasks import generate_daily_report_task, generate_weekly_report_task
from app.tasks.knowledge_tasks import ingest_document_task
from app.tasks.risk_tasks import detect_risks_task

__all__ = [
    "generate_daily_report_task",
    "generate_weekly_report_task",
    "ingest_document_task",
    "detect_risks_task",
]