"""
LangChain 1.x Agent with tool calling and SSE streaming.

Uses `create_agent` from LangChain 1.x (backed by LangGraph).
Falls back to direct httpx LLM calls if LangChain is not installed.
"""
import json
import logging
from typing import AsyncGenerator

from app.core.config import settings
from app.services.agent.prompts import SYSTEM_PROMPT
from app.services.agent.tools import TOOL_DEFINITIONS

logger = logging.getLogger(__name__)


def _get_llm_config():
    return {
        "api_key": settings.DEEPSEEK_API_KEY,
        "base_url": settings.DEEPSEEK_BASE_URL,
        "model": settings.DEEPSEEK_MODEL,
    }


def build_agent():
    """Create a LangChain 1.x agent (CompiledGraph).

    Returns (graph, True) if successful, (None, False) otherwise.
    """
    config = _get_llm_config()
    if not config["api_key"]:
        logger.warning("DEEPSEEK_API_KEY not set")
        return None, False

    try:
        from langchain.agents import create_agent
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            api_key=config["api_key"],
            base_url=config["base_url"],
            model=config["model"],
            temperature=0.3,
            streaming=True,
        )

        tool_funcs = [td["func"] for td in TOOL_DEFINITIONS]

        graph = create_agent(
            model=llm,
            tools=tool_funcs,
            system_prompt=SYSTEM_PROMPT,
        )
        logger.info("LangChain 1.x agent created successfully")
        return graph, True

    except ImportError as e:
        logger.warning(f"LangChain not available: {e}")
        return None, False
    except Exception as e:
        logger.error(f"Agent creation failed: {e}", exc_info=True)
        return None, False


# ===========================================================================
# Public API
# ===========================================================================

async def run_agent(query: str, chat_history: list = None) -> dict:
    """Non-streaming agent invocation."""
    graph, ok = build_agent()
    if ok and graph:
        return await _run_graph(graph, query, chat_history)
    return await _fallback_run(query)


async def run_agent_stream(query: str, chat_history: list = None) -> AsyncGenerator[str, None]:
    """Streaming agent invocation (SSE events)."""
    graph, ok = build_agent()
    if ok and graph:
        async for event in _stream_graph(graph, query, chat_history):
            yield event
    else:
        async for event in _fallback_stream(query):
            yield event


# ===========================================================================
# LangGraph streaming
# ===========================================================================

async def _run_graph(graph, query: str, chat_history: list = None) -> dict:
    try:
        messages = _build_messages(chat_history, query)
        result = await graph.ainvoke({"messages": messages})

        output_messages = result.get("messages", [])
        final_text = ""
        steps = []

        for msg in output_messages:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    steps.append({
                        "tool": tc.get("name", ""),
                        "tool_input": tc.get("args", {}),
                    })
            if hasattr(msg, "type") and msg.type == "ai" and hasattr(msg, "content") and msg.content:
                if not (hasattr(msg, "tool_calls") and msg.tool_calls):
                    final_text = msg.content

        return {"output": final_text, "steps": steps}

    except Exception as e:
        logger.error(f"Agent run error: {e}", exc_info=True)
        return {"output": f"处理请求时出错: {str(e)}", "steps": []}


async def _stream_graph(graph, query: str, chat_history: list = None) -> AsyncGenerator[str, None]:
    """Stream via LangGraph `astream(stream_mode="updates")`.

    Each update is a dict of {node_name: {messages: [...]}} containing
    AI messages (with possible tool_calls) and Tool messages (results).
    """
    try:
        messages = _build_messages(chat_history, query)
        full_output = ""

        async for chunk in graph.astream(
            {"messages": messages},
            stream_mode="updates",
        ):
            for _node_name, node_output in chunk.items():
                for msg in node_output.get("messages", []):
                    # AI message requesting tool call(s)
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        for tc in msg.tool_calls:
                            yield _sse({
                                "type": "tool_start",
                                "tool": tc.get("name", ""),
                                "input": tc.get("args", {}),
                            })

                    # Tool message (execution result)
                    if hasattr(msg, "type") and msg.type == "tool" and hasattr(msg, "content"):
                        output = msg.content
                        if isinstance(output, str) and len(output) > 2000:
                            output = output[:2000] + "..."
                        yield _sse({
                            "type": "tool_end",
                            "tool": getattr(msg, "name", ""),
                            "output": output,
                        })

                    # Final AI response (no tool_calls = final answer)
                    if (
                        hasattr(msg, "type") and msg.type == "ai"
                        and hasattr(msg, "content") and msg.content
                        and not (hasattr(msg, "tool_calls") and msg.tool_calls)
                    ):
                        full_output = msg.content
                        for token in _chunk_text(msg.content, 6):
                            yield _sse({"type": "token", "content": token})

        yield _sse({"type": "done", "output": full_output})

    except Exception as e:
        logger.error(f"Agent stream error: {e}", exc_info=True)
        yield _sse({"type": "error", "message": str(e)})


# ===========================================================================
# Fallback (no LangChain — direct LLM call)
# ===========================================================================

async def _fallback_run(query: str) -> dict:
    config = _get_llm_config()
    if not config["api_key"]:
        return {"output": "AI 未配置，请设置 DEEPSEEK_API_KEY 环境变量。", "steps": []}
    try:
        import httpx
        headers = {
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": config["model"],
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": query},
            ],
            "temperature": 0.3,
            "max_tokens": 4000,
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{config['base_url']}/chat/completions",
                headers=headers, json=payload,
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            return {"output": content, "steps": []}
    except Exception as e:
        return {"output": f"AI 调用失败: {str(e)}", "steps": []}


async def _fallback_stream(query: str) -> AsyncGenerator[str, None]:
    config = _get_llm_config()
    if not config["api_key"]:
        yield _sse({"type": "error", "message": "AI 未配置，请设置 DEEPSEEK_API_KEY"})
        return
    try:
        import httpx
        headers = {
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": config["model"],
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": query},
            ],
            "temperature": 0.3,
            "max_tokens": 4000,
            "stream": True,
        }
        full_output = ""
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{config['base_url']}/chat/completions",
                headers=headers,
                json=payload,
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            content = chunk["choices"][0].get("delta", {}).get("content", "")
                            if content:
                                full_output += content
                                yield _sse({"type": "token", "content": content})
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue
        yield _sse({"type": "done", "output": full_output})
    except Exception as e:
        yield _sse({"type": "error", "message": str(e)})


# ===========================================================================
# Helpers
# ===========================================================================

def _build_messages(chat_history: list | None, query: str) -> list:
    messages = []
    if chat_history:
        messages.extend(chat_history)
    messages.append({"role": "user", "content": query})
    return messages


def _chunk_text(text: str, size: int) -> list[str]:
    return [text[i:i + size] for i in range(0, len(text), size)]


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
