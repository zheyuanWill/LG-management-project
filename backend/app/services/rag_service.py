from datetime import datetime
from typing import Any

from loguru import logger
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.knowledge import KnowledgeDocument, KnowledgeEmbedding
from app.services.ai_client import get_ai_client
from app.services.file_service import upload_to_minio, delete_from_minio


CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    if not text:
        return []

    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk = text[start:end]

        if end < text_len:
            boundary = chunk.rfind("。")
            if boundary > 0:
                chunk = chunk[:boundary + 1]
                end = start + boundary + 1

        if chunk.strip():
            chunks.append(chunk.strip())

        start = end - overlap if end < text_len else end

    return chunks


async def ingest_document(
    db: AsyncSession,
    doc_id: int,
    file_content: bytes,
    file_type: str,
    title: str | None = None,
) -> None:
    ai_client = get_ai_client()

    text = ""
    if file_type == "pdf":
        try:
            from PyPDF2 import PdfReader
            import io
            reader = PdfReader(io.BytesIO(file_content))
            text = "\n".join([page.extract_text() or "" for page in reader.pages])
        except ImportError:
            logger.warning("PyPDF2 not installed, using basic extraction")
            text = file_content.decode("utf-8", errors="ignore")
    elif file_type in ("doc", "docx"):
        text = file_content.decode("utf-8", errors="ignore")
        logger.warning("For proper Word extraction, install python-docx")
    else:
        text = file_content.decode("utf-8", errors="ignore")

    if not text.strip():
        text = f"[Binary content: {len(file_content)} bytes]"

    chunks = _chunk_text(text)
    logger.info(f"Document {doc_id} split into {len(chunks)} chunks")

    if not chunks:
        logger.warning(f"No chunks generated for document {doc_id}")
        return

    batch_size = 10
    all_embeddings = []
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        embeddings = await ai_client.embed(batch)
        all_embeddings.extend(embeddings)

    doc_result = await db.execute(
        select(KnowledgeDocument).where(KnowledgeDocument.id == doc_id)
    )
    doc = doc_result.scalar_one_or_none()
    if doc is None:
        raise ValueError(f"Document not found: {doc_id}")

    doc.original_text = text

    for idx, (chunk, embedding) in enumerate(zip(chunks, all_embeddings)):
        if not embedding:
            logger.warning(f"Skipping chunk {idx} due to empty embedding")
            continue
        emb_entry = KnowledgeEmbedding(
            document_id=doc_id,
            chunk_index=idx,
            chunk_text=chunk,
            embedding=embedding,
        )
        db.add(emb_entry)

    await db.flush()
    logger.info(f"Ingested document {doc_id}: {len(chunks)} chunks, {len(all_embeddings)} embeddings")


async def query(
    db: AsyncSession, question: str, top_k: int = 5, category: str | None = None
) -> dict[str, Any]:
    ai_client = get_ai_client()

    query_embedding = await ai_client.embed([question])
    if not query_embedding:
        return {"answer": "抱歉，AI服务暂时不可用。", "citations": []}

    query_vec = query_embedding[0]

    doc_filter = select(KnowledgeDocument.id)
    if category:
        doc_filter = doc_filter.where(KnowledgeDocument.category == category)
    doc_ids_result = await db.execute(doc_filter)
    doc_ids = [row[0] for row in doc_ids_result.scalars().all()]

    if not doc_ids:
        return {"answer": "知识库为空，请先上传相关文档。", "citations": []}

    embedding_model = KnowledgeEmbedding.embedding
    cosine_sim = embedding_model.cosine_distance(query_vec)

    search_stmt = (
        select(KnowledgeEmbedding, cosine_sim.label("distance"))
        .where(KnowledgeEmbedding.document_id.in_(doc_ids))
        .order_by(KnowledgeEmbedding.embedding.cosine_distance(query_vec))
        .limit(top_k)
    )
    results = await db.execute(search_stmt)
    rows = results.all()

    if not rows:
        return {"answer": "未找到相关内容。", "citations": []}

    context_chunks = []
    citations = []
    for embedding, distance in rows:
        context_chunks.append(embedding.chunk_text)

        doc_result = await db.execute(
            select(KnowledgeDocument).where(KnowledgeDocument.id == embedding.document_id)
        )
        doc = doc_result.scalar_one_or_none()
        citations.append({
            "document_id": embedding.document_id,
            "document_title": doc.title if doc else "未知文档",
            "chunk_index": embedding.chunk_index,
            "chunk_text": embedding.chunk_text[:200],
            "score": float(1.0 - distance),
        })

    messages = [
        {
            "role": "system",
            "content": "你是一个专业的知识问答助手。请基于提供的上下文信息准确回答问题。如果上下文中没有相关信息，请说"抱歉，我没有找到相关信息"。",
        },
        {
            "role": "user",
            "content": f"问题：{question}\n\n相关上下文：\n" + "\n---\n".join(context_chunks),
        },
    ]

    answer = await ai_client.chat(messages, temperature=0.3)

    return {"answer": answer, "citations": citations}