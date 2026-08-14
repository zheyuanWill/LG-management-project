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
        """mock 模式：根据 system+user 内容生成「看起来像样」的占位回复。

        不接入真实 LLM 时，开发环境也能让日报/周报生成端到端跑通，
        文本以 [Mock] 前缀开头，便于识别。
        """
        system_msg = ""
        user_msg = ""
        for m in messages:
            if m.get("role") == "system":
                system_msg = m.get("content", "")
            elif m.get("role") == "user":
                user_msg = m.get("content", "")

        # 风险提示请求 → 项目级风险占位
        if "风险" in system_msg and "整个项目" in user_msg:
            return (
                "- [Mock] 现场需持续关注天气与潮汐窗口，避免影响靠泊与试航；\n"
                "- [Mock] 关键备件到货周期长，建议提前 7 天确认采购节点；\n"
                "- [Mock] 与船东/船检的沟通节点请保留书面记录，便于事后追溯。\n"
                "（以上为占位风险提示，未接入真实 LLM；当前 AI 服务 LLM_PROVIDER=mock）"
            )

        # 明日计划请求 → JSON 数组占位
        if "明日计划" in system_msg or "明日计划" in user_msg:
            return (
                '["[Mock] 跟进今日未完成事项并完成日清",'
                ' "[Mock] 与船东/船检确认下一节点时间",'
                ' "[Mock] 复核备件/工具到场情况"]'
            )

        # 周报类（包含"周报"或"本周"）→ 两段式占位
        if "周报" in system_msg or "周报" in user_msg or "下周计划" in user_msg:
            return (
                "1）本周工作摘要\n"
                "- [Mock] 已完成本周日报中记录的关键任务节点；\n"
                "- [Mock] 处理了现场反馈的若干技术问题并闭环；\n"
                "- [Mock] 完成了与船东/船检的阶段性沟通。\n\n"
                "2）下周计划\n"
                "- [Mock] 推进剩余关键路径任务；\n"
                "- [Mock] 准备下一阶段验收材料；\n"
                "- [Mock] 整理本周工作记录并归档。\n"
                "（以上为占位周报，未接入真实 LLM；当前 AI 服务 LLM_PROVIDER=mock）"
            )

        # RAG 问答
        if "问答助手" in system_msg or "严格基于" in user_msg:
            return (
                "[Mock] 根据提供的知识库上下文（mock 模式），"
                "未接入真实 LLM，无法给出更精确的回答。"
                "请在 .env 中设置 LLM_PROVIDER=cloud 并提供 LLM_API_KEY 以启用真实问答。"
            )

        # 通用兜底
        last_user = user_msg[:80] if user_msg else "（空消息）"
        return (
            f"[Mock 回复] 收到：「{last_user}」。"
            "当前 AI 服务 LLM_PROVIDER=mock，未接入真实 LLM。"
            "如需真实推理，请在 .env 中配置 LLM_PROVIDER=cloud + LLM_BASE_URL + LLM_API_KEY，"
            "或本地起 Ollama 后切到 LLM_PROVIDER=ollama。"
        )

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

    def chat_stream(self, messages: list[dict], temperature: float = 0.7, model: str | None = None):
        """流式对话，yield 文本增量（delta）。支持 cloud / ollama / mock。"""
        effective_model = model or self.model
        if self.provider == "mock":
            yield from self._mock_stream(messages)
            return

        if self.provider == "cloud":
            payload = {
                "model": effective_model,
                "messages": messages,
                "temperature": temperature,
                "stream": True,
            }
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            with self.client.stream("POST", self._chat_url, json=payload, headers=headers) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line:
                        continue
                    if line.startswith("data:"):
                        data = line[len("data:"):].strip()
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            delta = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if delta:
                                yield delta
                        except json.JSONDecodeError:
                            continue
        elif self.provider == "ollama":
            payload = {
                "model": effective_model,
                "messages": messages,
                "stream": True,
                "options": {"temperature": temperature},
            }
            with self.client.stream("POST", f"{self.base_url}/api/chat", json=payload) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                        delta = chunk.get("message", {}).get("content", "")
                        if delta:
                            yield delta
                    except json.JSONDecodeError:
                        continue
        else:
            yield self._mock_chat(messages)

    def _mock_stream(self, messages: list[dict]):
        last_user_msg = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_msg = msg.get("content", "")
                break
        full = (
            f"[Mock 流式回复] 收到你的消息：「{last_user_msg[:50]}」。"
            "这是一条模拟流式回复，用于开发测试。在实际部署时将由真正的 LLM 提供服务。"
        )
        for i in range(0, len(full), 8):
            yield full[i : i + 8]