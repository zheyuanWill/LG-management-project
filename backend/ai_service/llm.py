import json
import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config import settings


class LLMClient:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.base_url = settings.LLM_BASE_URL.rstrip("/")
        self.model = settings.LLM_MODEL
        self.api_key = settings.LLM_API_KEY
        self._client: httpx.Client | None = None

    @property
    def _chat_url(self) -> str:
        if self.provider == "cloud":
            base = self.base_url
            if base.endswith("/v1"):
                return f"{base}/chat/completions"
            return f"{base}/v1/chat/completions"
        return f"{self.base_url}/api/chat"

    @property
    def client(self) -> httpx.Client:
        if self._client is None or self._client.is_closed:
            self._client = httpx.Client(timeout=httpx.Timeout(60.0))
        return self._client

    def chat(self, messages: list[dict], temperature: float = 0.7, model: str | None = None) -> str:
        effective_model = model or self.model
        logger.debug(f"调用 LLM: provider={self.provider}, model={effective_model}, messages={len(messages)}")

        if self.provider == "mock":
            return self._mock_chat(messages)
        elif self.provider == "ollama":
            return self._ollama_chat(messages, temperature, effective_model)
        elif self.provider == "cloud":
            return self._cloud_chat(messages, temperature, effective_model)
        else:
            raise ValueError(f"未知的 LLM provider: {self.provider}")

    def _mock_chat(self, messages: list[dict]) -> str:
        last_user_msg = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_msg = msg.get("content", "")
                break

        mock_responses = [
            f"[Mock 回复] 收到你的消息：「{last_user_msg[:50]}」。这是一条模拟回复，用于开发测试。",
            f"[Mock 回复] 我理解你想了解关于「{last_user_msg[:30]}」的信息。在实际部署时，将由真正的 LLM 提供服务。",
            "[Mock 回复] 这是一个演示回复，AI 推理服务运行正常。",
        ]
        import random
        return random.choice(mock_responses)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.ConnectTimeout)),
        reraise=True,
    )
    def _ollama_chat(self, messages: list[dict], temperature: float, model: str) -> str:
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }

        logger.debug(f"Ollama 请求: url={self._chat_url}, model={model}")
        response = self.client.post(self._chat_url, json=payload)
        response.raise_for_status()

        data = response.json()
        content = data.get("message", {}).get("content", "")
        logger.debug(f"Ollama 响应: length={len(content)}")
        return content

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.ConnectTimeout)),
        reraise=True,
    )
    def _cloud_chat(self, messages: list[dict], temperature: float, model: str) -> str:
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        logger.debug(f"Cloud LLM 请求: url={self._chat_url}, model={model}")
        response = self.client.post(self._chat_url, json=payload, headers=headers)
        response.raise_for_status()

        data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        logger.debug(f"Cloud LLM 响应: length={len(content)}")
        return content

    def close(self):
        if self._client and not self._client.is_closed:
            self._client.close()
            logger.info("LLM HTTP 客户端已关闭")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()