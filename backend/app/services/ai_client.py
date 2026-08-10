from typing import Any

import httpx
from loguru import logger

from app.config import settings


class AIClient:
    def __init__(self, base_url: str = None):
        self.base_url = base_url or settings.AI_SERVICE_URL.rstrip("/")
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(60.0))

    async def chat(self, messages: list[dict], temperature: float = 0.7) -> str:
        url = f"{self.base_url}/v1/chat"
        payload = {
            "messages": messages,
            "temperature": temperature,
        }
        try:
            response = await self._client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            logger.info("AI chat request completed")
            return data.get("content", "")
        except httpx.HTTPError as e:
            logger.error(f"AI chat request failed: {e}")
            return f"AI服务暂时不可用: {e}"

    async def embed(self, texts: list[str]) -> list[list[float]]:
        url = f"{self.base_url}/v1/embed"
        payload = {"texts": texts}
        try:
            response = await self._client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            embeddings = data.get("embeddings", [])
            logger.info(f"Embedded {len(texts)} texts")
            return embeddings
        except httpx.HTTPError as e:
            logger.error(f"AI embed request failed: {e}")
            return []

    async def ocr(self, image_bytes: bytes) -> str:
        url = f"{self.base_url}/v1/ocr"
        try:
            files = {"image": ("image.jpg", image_bytes, "image/jpeg")}
            response = await self._client.post(url, files=files)
            response.raise_for_status()
            data = response.json()
            logger.info("OCR request completed")
            return data.get("text", "")
        except httpx.HTTPError as e:
            logger.error(f"AI OCR request failed: {e}")
            return ""

    async def qa(self, question: str, context_chunks: list[str]) -> dict[str, Any]:
        url = f"{self.base_url}/v1/qa"
        payload = {
            "question": question,
            "context_chunks": context_chunks,
        }
        try:
            response = await self._client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            logger.info("AI QA request completed")
            return {
                "answer": data.get("answer", ""),
                "citations": data.get("citations", []),
            }
        except httpx.HTTPError as e:
            logger.error(f"AI QA request failed: {e}")
            return {"answer": f"AI服务暂时不可用: {e}", "citations": []}

    async def close(self) -> None:
        await self._client.aclose()


_ai_client: AIClient | None = None


def get_ai_client() -> AIClient:
    global _ai_client
    if _ai_client is None:
        _ai_client = AIClient()
    return _ai_client