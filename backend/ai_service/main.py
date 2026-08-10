import base64
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from config import settings
from schemas import (
    ChatRequest,
    ChatResponse,
    EmbedRequest,
    EmbedResponse,
    OCRRequest,
    OCRResponse,
    QARequest,
    QAResponse,
    Citation,
    HealthResponse,
)
from llm import LLMClient
from embedding import EmbeddingService
from ocr_service import OCRService
from prompts import RAG_QA_PROMPT


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.validate()
    llm_client = LLMClient()
    embedding_svc = EmbeddingService()
    ocr_svc = OCRService()

    app.state.llm = llm_client
    app.state.embedding = embedding_svc
    app.state.ocr = ocr_svc

    logger.info(f"AI 推理服务已启动: http://{settings.API_HOST}:{settings.API_PORT}")
    try:
        yield
    finally:
        llm_client.close()
        logger.info("AI 推理服务已关闭")


app = FastAPI(
    title="AI 推理服务",
    description="独立的 AI 推理服务，提供对话、向量化、OCR 和 RAG 问答能力",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"未处理的异常: {type(exc).__name__}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误", "message": str(exc)},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTP 异常: status={exc.status_code}, detail={exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="ok",
        provider=settings.LLM_PROVIDER,
        model=settings.LLM_MODEL,
    )


@app.post("/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        messages = [{"role": m.role, "content": m.content} for m in request.messages]
        llm_client: LLMClient = app.state.llm

        content = llm_client.chat(
            messages=messages,
            temperature=request.temperature,
            model=request.model,
        )

        return ChatResponse(
            content=content,
            model=request.model or settings.LLM_MODEL,
        )
    except Exception as e:
        logger.error(f"Chat 接口调用失败: {e}")
        raise HTTPException(status_code=500, detail=f"LLM 调用失败: {str(e)}")


@app.post("/v1/embed", response_model=EmbedResponse)
async def embed(request: EmbedRequest):
    try:
        embedding_svc: EmbeddingService = app.state.embedding
        embeddings = embedding_svc.embed_batch(request.texts)
        return EmbedResponse(
            embeddings=embeddings,
            dim=embedding_svc.dim,
        )
    except Exception as e:
        logger.error(f"Embed 接口调用失败: {e}")
        raise HTTPException(status_code=500, detail=f"向量化失败: {str(e)}")


@app.post("/v1/ocr", response_model=OCRResponse)
async def ocr(request: OCRRequest):
    try:
        ocr_svc: OCRService = app.state.ocr
        image_bytes = base64.b64decode(request.image_base64)
        text = ocr_svc.recognize_image(image_bytes)
        return OCRResponse(text=text)
    except Exception as e:
        logger.error(f"OCR 接口调用失败: {e}")
        raise HTTPException(status_code=500, detail=f"OCR 识别失败: {str(e)}")


@app.post("/v1/qa", response_model=QAResponse)
async def qa(request: QARequest):
    try:
        context_text = ""
        citations = []
        for chunk in request.context_chunks:
            context_text += f"### {chunk.doc_title}\n{chunk.text}\n\n"
            citations.append(Citation(doc_title=chunk.doc_title, chunk_text=chunk.text))

        prompt = RAG_QA_PROMPT.format(
            context=context_text.strip(),
            question=request.question,
        )

        messages = [
            {"role": "system", "content": "你是一位专业的问答助手，请严格基于提供的上下文回答问题。"},
            {"role": "user", "content": prompt},
        ]

        llm_client: LLMClient = app.state.llm
        answer = llm_client.chat(messages=messages, temperature=0.3)

        return QAResponse(answer=answer, citations=citations)
    except Exception as e:
        logger.error(f"QA 接口调用失败: {e}")
        raise HTTPException(status_code=500, detail=f"RAG 问答失败: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=False,
        log_level=settings.LOG_LEVEL.lower(),
    )