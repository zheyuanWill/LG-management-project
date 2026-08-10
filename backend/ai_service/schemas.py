from typing import Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., description="消息角色: system/user/assistant")
    content: str = Field(..., description="消息内容")


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(..., description="对话消息列表")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="生成温度")
    model: Optional[str] = Field(None, description="模型名称，覆盖默认配置")


class UsageInfo(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatResponse(BaseModel):
    content: str = Field(..., description="模型回复内容")
    usage: Optional[UsageInfo] = Field(None, description="Token 使用统计")
    model: Optional[str] = Field(None, description="实际使用的模型名称")


class EmbedRequest(BaseModel):
    texts: list[str] = Field(..., description="待向量化的文本列表")


class EmbedResponse(BaseModel):
    embeddings: list[list[float]] = Field(..., description="向量列表，每个向量 512 维")
    dim: int = Field(512, description="向量维度")


class OCRRequest(BaseModel):
    image_base64: str = Field(..., description="图片的 Base64 编码")


class OCRResponse(BaseModel):
    text: str = Field(..., description="识别出的完整文本")


class ContextChunk(BaseModel):
    text: str = Field(..., description="上下文片段文本")
    doc_title: str = Field(..., description="文档标题")


class QARequest(BaseModel):
    question: str = Field(..., description="用户问题")
    context_chunks: list[ContextChunk] = Field(..., description="参考上下文片段列表")


class Citation(BaseModel):
    doc_title: str = Field(..., description="引用来源的文档标题")
    chunk_text: str = Field(..., description="引用的片段文本")


class QAResponse(BaseModel):
    answer: str = Field(..., description="AI 生成的回答")
    citations: list[Citation] = Field(default_factory=list, description="引用来源列表")


class HealthResponse(BaseModel):
    status: str = "ok"
    provider: str
    model: str