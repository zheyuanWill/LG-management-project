from datetime import datetime
import re
from typing import Any

from loguru import logger
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.knowledge import KnowledgeDocument, KnowledgeEmbedding
from app.services.ai_client import get_ai_client
from app.services.document_processor import process_document, sections_to_chunks
from app.services.file_service import upload_to_minio, delete_from_minio


# 旧常量保留只为兼容外部 import；新流程不再使用固定 500 字切分
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """已废弃：保留只为兼容旧调用。新流程使用 document_processor.sections_to_chunks。"""
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


# ── 出处前缀解析（用于 retrieve/query 返回结构化 citation） ──────

_PREFIX_RE = re.compile(r"^【([^】]*)】")


def _parse_chunk_prefix(chunk_text: str) -> dict[str, str]:
    """从 chunk_text 前缀解析章节元数据。

    chunk_text 形如：`【《书名》/ 第3章 / 第2节】实际内容...`
    """
    if not chunk_text:
        return {}
    m = _PREFIX_RE.match(chunk_text)
    if not m:
        return {}
    parts = [p.strip() for p in m.group(1).split("/") if p.strip()]
    meta: dict[str, str] = {}
    for part in parts:
        if part.startswith("《") and part.endswith("》"):
            meta["book_title"] = part[1:-1]
        elif "chapter" not in meta:
            meta["chapter"] = part
        elif "section" not in meta:
            meta["section"] = part
    return meta


async def ingest_document(
    db: AsyncSession,
    doc_id: int,
    file_content: bytes,
    file_type: str,
    title: str | None = None,
) -> None:
    """ingest 阶段：多格式清洗 + 按章节切分 + 向量化入库。

    扫描版 PDF / 不支持的格式 / 空内容 → 拒绝入库，写日志不抛异常。
    """
    ai_client = get_ai_client()

    result = process_document(file_content, file_type, title or "")
    if result.rejected:
        logger.warning(f"Document {doc_id} rejected: {result.rejected}")
        # 把拒绝原因写到 original_text 供前端查看
        doc_result = await db.execute(
            select(KnowledgeDocument).where(KnowledgeDocument.id == doc_id)
        )
        doc = doc_result.scalar_one_or_none()
        if doc is not None:
            doc.original_text = f"[INGEST REJECTED] {result.rejected}"
        await db.flush()
        return

    chunks = sections_to_chunks(result.sections, title or "")
    logger.info(f"Document {doc_id} split into {len(chunks)} chunks (format={file_type})")

    if not chunks:
        logger.warning(f"No chunks generated for document {doc_id}")
        return

    # 把清洗后的全文存回 original_text（拼接所有 chunk 去前缀）
    full_cleaned = "\n\n".join(
        re.sub(r"^【[^】]*】", "", chunk) for chunk in chunks
    )

    batch_size = 10
    all_embeddings: list[list[float]] = []
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

    doc.original_text = full_cleaned[:50000]  # 截断保护，避免 Text 列过大

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


async def retrieve(
    db: AsyncSession, question: str, top_k: int = 5, category: str | None = None
) -> list[str]:
    """检索与问题最相关的知识库片段文本（仅检索，不调用 LLM 作答）。

    用于把修船知识库要点作为上下文拼进 prompt，避免 `query()` 额外做一次问答。
    """
    ai_client = get_ai_client()

    query_embedding = await ai_client.embed([question])
    if not query_embedding:
        return []

    query_vec = query_embedding[0]

    doc_filter = select(KnowledgeDocument.id)
    if category:
        doc_filter = doc_filter.where(KnowledgeDocument.category == category)
    doc_ids_result = await db.execute(doc_filter)
    doc_ids = list(doc_ids_result.scalars().all())

    if not doc_ids:
        return []

    search_stmt = (
        select(KnowledgeEmbedding)
        .where(KnowledgeEmbedding.document_id.in_(doc_ids))
        .order_by(KnowledgeEmbedding.embedding.cosine_distance(query_vec))
        .limit(top_k)
    )
    rows = (await db.execute(search_stmt)).scalars().all()

    return [r.chunk_text for r in rows if r.chunk_text]


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
    doc_ids = list(doc_ids_result.scalars().all())

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

    # 预加载所有 doc 标题，避免 N+1
    doc_ids_in_results = list({emb.document_id for emb, _ in rows})
    docs_result = await db.execute(
        select(KnowledgeDocument).where(KnowledgeDocument.id.in_(doc_ids_in_results))
    )
    docs_map = {d.id: d for d in docs_result.scalars().all()}

    for embedding, distance in rows:
        context_chunks.append(embedding.chunk_text)
        doc = docs_map.get(embedding.document_id)
        # 从 chunk 前缀解析章节元数据
        meta = _parse_chunk_prefix(embedding.chunk_text)
        citations.append({
            "document_id": embedding.document_id,
            "document_title": doc.title if doc else "未知文档",
            "chunk_index": embedding.chunk_index,
            "chunk_text": embedding.chunk_text[:300],
            "book_title": meta.get("book_title", ""),
            "chapter": meta.get("chapter", ""),
            "section": meta.get("section", ""),
            "source": (
                f"《{meta['book_title']}》"
                + (f" / {meta['chapter']}" if meta.get("chapter") else "")
                + (f" / {meta['section']}" if meta.get("section") else "")
            ).lstrip("《》/ ") or (doc.title if doc else ""),
            "score": float(1.0 - distance),
        })

    messages = [
        {
            "role": "system",
            "content": "你是一个专业的知识问答助手。请基于提供的上下文信息准确回答问题。如果上下文中没有相关信息，请说'抱歉，我没有找到相关信息'。",
        },
        {
            "role": "user",
            "content": f"问题：{question}\n\n相关上下文：\n" + "\n---\n".join(context_chunks),
        },
    ]

    answer = await ai_client.chat(messages, temperature=0.3)

    return {"answer": answer, "citations": citations}
