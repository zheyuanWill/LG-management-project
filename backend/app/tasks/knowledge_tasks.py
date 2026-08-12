import tempfile
from pathlib import Path

from loguru import logger

from app.async_utils import run_async
from app.celery_app import celery_app


@celery_app.task(name="app.tasks.knowledge_tasks.ingest_document_task")
def ingest_document_task(doc_id: int) -> dict:
    logger.info(f"Starting document ingestion: doc_id={doc_id}")

    async def _run():
        from app.db import async_session_maker
        from app.config import settings
        from app.dependencies import get_minio_client
        from app.models.knowledge import KnowledgeDocument
        from app.services.rag_service import ingest_document

        async with async_session_maker() as db:
            try:
                result = await db.execute(
                    KnowledgeDocument.__table__.select().where(KnowledgeDocument.id == doc_id)
                )
                doc_row = result.fetchone()
                if doc_row is None:
                    logger.error(f"Document not found: {doc_id}")
                    return {"status": "failed", "error": "Document not found"}

                doc_dict = dict(doc_row._mapping) if hasattr(doc_row, '_mapping') else doc_row._asdict()
                file_key = doc_dict.get("file_key", "")
                title = doc_dict.get("title", "unknown")

                client = get_minio_client()

                with tempfile.NamedTemporaryFile(delete=False) as tmp:
                    client.fget_object(settings.MINIO_BUCKET, file_key, tmp.name)
                    tmp_path = Path(tmp.name)
                    file_content = tmp_path.read_bytes()

                # 用 file_key（保留原始扩展名，如 xxx.docx）判定类型，
                # 不能用 title（标题通常不带扩展名），否则会误判成 txt 导致二进制乱码。
                file_type = file_key.rsplit(".", 1)[-1].lower() if "." in file_key else "txt"
                if file_type not in ("pdf", "doc", "docx", "txt", "md"):
                    file_type = "txt"

                await ingest_document(db, doc_id, file_content, file_type, title=title)

                tmp_path.unlink(missing_ok=True)

                await db.commit()
                logger.info(f"Document ingestion completed: doc_id={doc_id}")
                return {"status": "success", "doc_id": doc_id}
            except Exception as e:
                logger.error(f"Document ingestion failed: {e}")
                await db.rollback()
                raise

    try:
        return run_async(_run())
    except Exception as e:
        logger.error(f"Document ingestion task failed: {e}")
        return {"status": "failed", "error": str(e)}