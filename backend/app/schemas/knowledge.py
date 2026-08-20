from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    category: str | None = None
    file_key: str
    original_text: str | None = None
    uploaded_by: int | None = None
    created_at: datetime


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(default=5, ge=1, le=20)
    category: str | None = Field(default=None, max_length=64)


class CitationItem(BaseModel):
    document_id: int
    document_title: str
    chunk_index: int
    chunk_text: str
    score: float
    book_title: str | None = None
    chapter: str | None = None
    section: str | None = None
    source: str | None = None


class QueryResponse(BaseModel):
    answer: str
    citations: list[CitationItem]


class KnowledgeDocumentListResponse(BaseModel):
    items: list[DocumentUploadResponse]
    total: int


class KnowledgeChatMessageCreate(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1)
    citations: list[dict] | None = None


class KnowledgeChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    role: str
    content: str
    citations: list[dict] | None = None
    created_at: datetime


class KnowledgeChatMessageListResponse(BaseModel):
    items: list[KnowledgeChatMessageResponse]
    total: int