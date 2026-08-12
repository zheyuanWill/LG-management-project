from datetime import datetime

from loguru import logger

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.celery_app import celery_app
from app.dependencies import get_current_user, get_db
from app.models.knowledge import KnowledgeDocument
from app.models.user import User
from app.schemas.knowledge import (
    CitationItem,
    DocumentUploadResponse,
    KnowledgeDocumentListResponse,
    QueryRequest,
    QueryResponse,
)
from app.services.file_service import upload_to_minio
from app.services.rag_service import query as rag_query_service

router = APIRouter()


@router.post(
    "/documents",
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    title: str = Form(...),
    category: str | None = Form(default=None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    content = await file.read()
    filename = file.filename or "document.pdf"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "pdf"

    allowed_types = {"pdf", "doc", "docx", "txt", "md"}
    if ext not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型: {ext}。支持的类型: {', '.join(sorted(allowed_types))}",
        )

    storage_key = await upload_to_minio(content, ext=ext)

    doc = KnowledgeDocument(
        title=title,
        category=category,
        file_key=storage_key,
        original_text=None,
        uploaded_by=current_user.id,
    )
    db.add(doc)
    await db.flush()

    task = celery_app.send_task(
        "app.tasks.knowledge_tasks.ingest_document_task",
        args=[doc.id],
    )

    return DocumentUploadResponse(
        id=doc.id,
        title=doc.title,
        category=doc.category,
        file_key=doc.file_key,
        original_text=doc.original_text,
        uploaded_by=doc.uploaded_by,
        created_at=doc.created_at,
    )


@router.get("/documents", response_model=KnowledgeDocumentListResponse)
async def list_documents(
    category: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = select(KnowledgeDocument)
    if category:
        query = query.where(KnowledgeDocument.category == category)

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.execute(count_query)
    total = total.scalar() or 0

    result = await db.execute(query.order_by(KnowledgeDocument.created_at.desc()))
    docs = result.scalars().all()

    return KnowledgeDocumentListResponse(
        items=[DocumentUploadResponse.model_validate(d) for d in docs],
        total=total,
    )


@router.get("/documents/{doc_id}", response_model=DocumentUploadResponse)
async def get_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(KnowledgeDocument).where(KnowledgeDocument.id == doc_id)
    )
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文档不存在")
    return DocumentUploadResponse.model_validate(doc)


@router.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(KnowledgeDocument).where(KnowledgeDocument.id == doc_id)
    )
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文档不存在")

    # Delete via the ORM instance so the embeddings relationship cascade
    # ("all, delete-orphan") fires and removes child knowledge_embeddings rows
    # first, avoiding a foreign-key violation.
    await db.delete(doc)


@router.post("/query", response_model=QueryResponse)
async def query_knowledge(
    payload: QueryRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await rag_query_service(
        db,
        question=payload.query,
        top_k=payload.top_k,
        category=payload.category,
    )

    citations = [
        CitationItem(
            document_id=c["document_id"],
            document_title=c["document_title"],
            chunk_index=c["chunk_index"],
            chunk_text=c["chunk_text"],
            score=c["score"],
        )
        for c in result.get("citations", [])
    ]

    return QueryResponse(
        answer=result.get("answer", ""),
        citations=citations,
    )


@router.post("/query/stream")
async def query_knowledge_stream(
    payload: QueryRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """流式 RAG 问答（SSE）。
    先返回检索到的引用（event: citations），随后逐块流式返回答案（data: {...delta}）。
    """
    import json as _json

    from app.services.ai_client import get_ai_client

    async def event_generator():
        try:
            ai_client = get_ai_client()
            query_embedding = await ai_client.embed([payload.query])
            if not query_embedding:
                yield f"data: {_json.dumps({'error': 'AI 服务暂时不可用'}, ensure_ascii=False)}\n\n"
                return

            # 复用检索逻辑
            result = await rag_query_service(
                db,
                question=payload.query,
                top_k=payload.top_k,
                category=payload.category,
            )

            citations = result.get("citations", [])
            if citations:
                yield f"event: citations\ndata: {_json.dumps(citations, ensure_ascii=False)}\n\n"

            if not result.get("answer") and not citations:
                yield f"data: {_json.dumps({'delta': '抱歉，我没有找到相关信息。'}, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
                return

            messages = [
                {
                    "role": "system",
                    "content": "你是一个专业的知识问答助手。请基于提供的上下文信息准确回答问题，使用 Markdown 格式（可用标题、列表、加粗）。如果上下文中没有相关信息，请说'抱歉，我没有找到相关信息'。",
                },
                {
                    "role": "user",
                    "content": f"问题：{payload.query}\n\n相关上下文：\n"
                    + "\n---\n".join(
                        [c.get("chunk_text", "") for c in citations]
                    ),
                },
            ]
            async for delta in ai_client.chat_stream(messages, temperature=0.3):
                yield f"data: {_json.dumps({'delta': delta}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"流式问答失败: {e}")
            yield f"data: {_json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")