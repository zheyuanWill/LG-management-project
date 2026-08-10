from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.celery_app import celery_app
from app.dependencies import get_current_user, get_db
from app.models.knowledge import KnowledgeDocument
from app.models.user import User
from app.schemas.knowledge import (
    CitationItem,
    DocumentUploadResponse,
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


@router.get("/documents", response_model=list[DocumentUploadResponse])
async def list_documents(
    category: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = select(KnowledgeDocument)
    if category:
        query = query.where(KnowledgeDocument.category == category)

    result = await db.execute(query.order_by(KnowledgeDocument.created_at.desc()))
    docs = result.scalars().all()

    return [DocumentUploadResponse.model_validate(d) for d in docs]


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