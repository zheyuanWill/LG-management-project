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

    async def chat_stream(self, messages: list[dict], temperature: float = 0.7):
        """流式调用 AI 聊天，异步 yield 文本增量。解析 ai-service 的 SSE。"""
        import json as _json

        url = f"{self.base_url}/v1/chat/stream"
        payload = {"messages": messages, "temperature": temperature}
        try:
            async with self._client.stream("POST", url, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    if not line.startswith("data:"):
                        continue
                    data = line[len("data:"):].strip()
                    if data == "[DONE]":
                        break
                    try:
                        chunk = _json.loads(data)
                    except _json.JSONDecodeError:
                        continue
                    if "error" in chunk:
                        logger.error(f"AI 流式返回错误: {chunk['error']}")
                        raise RuntimeError(chunk["error"])
                    delta = chunk.get("delta")
                    if delta:
                        yield delta
        except httpx.HTTPError as e:
            logger.error(f"AI 流式 chat 请求失败: {e}")
            raise

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