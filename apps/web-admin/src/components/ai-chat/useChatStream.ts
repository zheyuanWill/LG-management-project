import { useRef, useCallback, useState } from 'react';
import { getToken } from '@lg/api-client';
import type { ChatMessage, ToolCallInfo, SSEEvent } from './types';

let messageCounter = 0;
function nextId() {
  return `msg_${Date.now()}_${++messageCounter}`;
}

export function useChatStream(baseUrl: string) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const contentRef = useRef('');
  const toolsRef = useRef<ToolCallInfo[]>([]);

  const sendMessage = useCallback(async (text: string, imageBase64?: string) => {
    const userMsg: ChatMessage = {
      id: nextId(),
      role: 'user',
      content: imageBase64 ? `[图片] ${text}` : text,
      timestamp: Date.now(),
    };

    const assistantMsg: ChatMessage = {
      id: nextId(),
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
      toolCalls: [],
      isStreaming: true,
    };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setIsStreaming(true);
    contentRef.current = '';
    toolsRef.current = [];

    const abortController = new AbortController();
    abortRef.current = abortController;

    try {
      const token = getToken();
      const response = await fetch(`${baseUrl}/api/ai-agent/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ message: text }),
        signal: abortController.signal,
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      if (!response.body) throw new Error('No response body');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const raw = line.slice(6).trim();
          if (!raw || raw === '[DONE]') continue;

          try {
            const event: SSEEvent = JSON.parse(raw);

            if (event.type === 'token' && event.content) {
              contentRef.current += event.content;
              setMessages((prev) => {
                const updated = [...prev];
                const last = updated[updated.length - 1];
                if (last.role === 'assistant') {
                  updated[updated.length - 1] = {
                    ...last,
                    content: contentRef.current,
                    toolCalls: [...toolsRef.current],
                  };
                }
                return updated;
              });
            } else if (event.type === 'tool_start') {
              toolsRef.current = [
                ...toolsRef.current,
                {
                  tool: event.tool || '',
                  input: event.input || {},
                  status: 'running',
                },
              ];
              setMessages((prev) => {
                const updated = [...prev];
                const last = updated[updated.length - 1];
                if (last.role === 'assistant') {
                  updated[updated.length - 1] = {
                    ...last,
                    toolCalls: [...toolsRef.current],
                  };
                }
                return updated;
              });
            } else if (event.type === 'tool_end') {
              toolsRef.current = toolsRef.current.map((tc) =>
                tc.tool === event.tool && tc.status === 'running'
                  ? { ...tc, status: 'done' as const, output: event.output }
                  : tc,
              );
              setMessages((prev) => {
                const updated = [...prev];
                const last = updated[updated.length - 1];
                if (last.role === 'assistant') {
                  updated[updated.length - 1] = {
                    ...last,
                    toolCalls: [...toolsRef.current],
                  };
                }
                return updated;
              });
            } else if (event.type === 'done') {
              contentRef.current = event.output || contentRef.current;
            } else if (event.type === 'error') {
              contentRef.current += `\n\n❌ 错误: ${event.message}`;
            }
          } catch {
            // ignore parse errors
          }
        }
      }
    } catch (e: unknown) {
      if ((e as Error).name !== 'AbortError') {
        contentRef.current += `\n\n❌ 请求失败: ${(e as Error).message}`;
      }
    } finally {
      setIsStreaming(false);
      setMessages((prev) => {
        const updated = [...prev];
        const last = updated[updated.length - 1];
        if (last.role === 'assistant') {
          updated[updated.length - 1] = {
            ...last,
            content: contentRef.current,
            toolCalls: [...toolsRef.current],
            isStreaming: false,
          };
        }
        return updated;
      });
      abortRef.current = null;
    }
  }, [baseUrl]);

  const stopStream = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return { messages, isStreaming, sendMessage, stopStream, clearMessages };
}
