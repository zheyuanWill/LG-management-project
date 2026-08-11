from app.services.project_service import generate_project_number, get_project_stats
from app.services.photo_service import check_daily_photo_limit, upload_photo
from app.services.report_service import (
    generate_daily_report,
    generate_weekly_report,
    _build_completed_items,
)
from app.services.risk_service import detect_risks, build_risk_summary
from app.services.ai_client import AIClient, get_ai_client
from app.services.rag_service import ingest_document, query as rag_query
from app.services.quick_save_service import (
    recognize_content,
    suggest_projects,
    confirm_save,
)
from app.services.file_service import (
    upload_to_minio,
    get_minio_url,
    detect_file_type,
)

__all__ = [
    "generate_project_number",
    "get_project_stats",
    "check_daily_photo_limit",
    "upload_photo",
    "generate_daily_report",
    "generate_weekly_report",
    "_build_completed_items",
    "detect_risks",
    "build_risk_summary",
    "AIClient",
    "get_ai_client",
    "ingest_document",
    "rag_query",
    "recognize_content",
    "suggest_projects",
    "confirm_save",
    "upload_to_minio",
    "get_minio_url",
    "detect_file_type",
]