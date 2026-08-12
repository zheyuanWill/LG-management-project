import { useState, useRef, useEffect } from 'react'
import { Send, Sparkles, User, Bot, ChevronDown, ChevronUp } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { useAuthStore } from '@/hooks/useAuth'
import MarkdownView from '@/components/common/MarkdownView'
import CitationList from './CitationList'

interface Citation {
  document_id: string | number
  document_title: string
  chunk_index: number
  chunk_text: string
  score?: number
}

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[]
  created_at: string
}

interface QAResponse {
  answer: string
  citations: Citation[]
}

const sampleQuestions = [
  '如何进行船舶买卖的背景调研?',
  '修船合同中有哪些关键条款?',
  '备件供应的物流流程是怎样的?',
  '如何判断船东的资质?',
]

const STORAGE_KEY = 'lg-qa-chat-history'

export default function QAChat() {
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved) return JSON.parse(saved)
    } catch { /* ignore */ }
    return []
  })
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [expandedCitations, setExpandedCitations] = useState<Record<string, boolean>>({})
  const scrollRef = useRef<HTMLDivElement>(null)
  // 流式过程中持有正在写入的助手消息 id，便于增量更新
  const streamingIdRef = useRef<string | null>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(messages))
    } catch { /* ignore quota errors */ }
  }, [messages])

  const updateMessage = (id: string, patch: Partial<ChatMessage>) => {
    setMessages((prev) => prev.map((m) => (m.id === id ? { ...m, ...patch } : m)))
  }

  const handleSend = async (text?: string) => {
    const question = (text || input).trim()
    if (!question || isLoading) return

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: question,
      created_at: new Date().toISOString(),
    }
    const assistantId = (Date.now() + 1).toString()
    const assistantMessage: ChatMessage = {
      id: assistantId,
      role: 'assistant',
      content: '',
      citations: [],
      created_at: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, userMessage, assistantMessage])
    setInput('')
    setIsLoading(true)
    streamingIdRef.current = assistantId

    const token = useAuthStore.getState().token
    try {
      const resp = await fetch('/api/v1/knowledge/query/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ query: question, top_k: 5 }),
      })

      if (!resp.ok || !resp.body) {
        throw new Error(`请求失败: ${resp.status}`)
      }

      const reader = resp.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let acc = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })

        let sep: number
        while ((sep = buffer.indexOf('\n\n')) !== -1) {
          const rawEvent = buffer.slice(0, sep)
          buffer = buffer.slice(sep + 2)
          let eventName = 'message'
          let dataStr = ''
          for (const line of rawEvent.split('\n')) {
            if (line.startsWith('event:')) eventName = line.slice(6).trim()
            else if (line.startsWith('data:')) dataStr += line.slice(5).trim()
          }
          if (!dataStr) continue
          try {
            const data = JSON.parse(dataStr)
            if (eventName === 'citations') {
              updateMessage(assistantId, { citations: data as Citation[] })
            } else if (typeof data.delta === 'string') {
              acc += data.delta
              updateMessage(assistantId, { content: acc })
            } else if (data.error) {
              acc += `\n\n> ⚠️ ${data.error}`
              updateMessage(assistantId, { content: acc })
            }
          } catch { /* ignore malformed */ }
        }
      }
      if (!acc) {
        updateMessage(assistantId, { content: '抱歉，我没有找到相关信息。' })
      }
    } catch {
      updateMessage(assistantId, {
        content: '抱歉,我暂时无法回答您的问题。请稍后再试。',
      })
    } finally {
      streamingIdRef.current = null
      setIsLoading(false)
    }
  }

  const toggleCitations = (messageId: string) => {
    setExpandedCitations((prev) => ({ ...prev, [messageId]: !prev[messageId] }))
  }

  return (
    <div className="flex flex-col h-full">
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-8">
            <Sparkles className="h-12 w-12 text-primary mb-4" />
            <h3 className="text-lg font-medium mb-2">欢迎使用 RAG 知识库</h3>
            <p className="text-muted-foreground text-sm mb-6">
              基于上传的文档,我可以回答您关于监修、经纪、备件等方面的问题
            </p>
            <div className="flex flex-wrap justify-center gap-2 max-w-md">
              {sampleQuestions.map((q) => (
                <button
                  key={q}
                  onClick={() => handleSend(q)}
                  className="px-3 py-2 text-sm rounded-full border border-border hover:bg-muted transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-3 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
            >
              <div
                className={`flex items-center justify-center w-8 h-8 rounded-full shrink-0 ${
                  message.role === 'user'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted'
                }`}
              >
                {message.role === 'user' ? (
                  <User className="h-4 w-4" />
                ) : (
                  <Bot className="h-4 w-4" />
                )}
              </div>
              <div
                className={`flex-1 max-w-[80%] ${message.role === 'user' ? 'items-end' : 'items-start'}`}
              >
                <div
                  className={`rounded-lg p-3 text-sm ${
                    message.role === 'user'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted'
                  }`}
                >
                  {message.role === 'user' ? (
                    <p className="whitespace-pre-wrap">{message.content}</p>
                  ) : message.content ? (
                    <MarkdownView content={message.content} />
                  ) : (
                    <p className="text-muted-foreground">思考中…</p>
                  )}
                </div>

                {message.role === 'assistant' && message.citations && message.citations.length > 0 && (
                  <div className="mt-2">
                    <button
                      className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
                      onClick={() => toggleCitations(message.id)}
                    >
                      {expandedCitations[message.id] ? (
                        <ChevronUp className="h-3 w-3" />
                      ) : (
                        <ChevronDown className="h-3 w-3" />
                      )}
                      引用来源 ({message.citations.length})
                    </button>
                    {expandedCitations[message.id] && (
                      <div className="mt-2">
                        <CitationList citations={message.citations} />
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))
        )}

        {isLoading && (
          <div className="flex gap-3">
            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-muted shrink-0">
              <Bot className="h-4 w-4" />
            </div>
            <div className="bg-muted rounded-lg p-3">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" />
                <span className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce [animation-delay:0.2s]" />
                <span className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce [animation-delay:0.4s]" />
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="border-t p-4">
        <div className="flex items-center gap-2">
          <Input
            placeholder="输入您的问题..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            disabled={isLoading}
          />
          <Button onClick={() => handleSend()} disabled={isLoading || !input.trim()}>
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  )
}
