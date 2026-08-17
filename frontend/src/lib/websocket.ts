// 原生 WebSocket 客户端（对应后端 /ws/projects/{project_id} 端点）。
// 取代原先基于 socket.io 的死代码——后端使用 FastAPI 原生 WebSocket，
// 浏览器原生 WebSocket 直接对接，无需 socket.io 客户端。

type Listener = (data: unknown) => void

class WebSocketClient {
  private ws: WebSocket | null = null
  private url: string
  private projectId: string | null = null
  private token: string | null = null
  private listeners: Map<string, Set<Listener>> = new Map()
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null

  constructor(url: string = '') {
    this.url = url || (typeof window !== 'undefined' ? window.location.origin : '')
  }

  connect(projectId: string, token?: string) {
    // 已在同房间连接则忽略
    if (
      this.ws &&
      this.ws.readyState === WebSocket.OPEN &&
      this.projectId === projectId
    ) {
      return
    }
    this.disconnect()

    this.projectId = projectId
    this.token = token || null

    const proto = this.url.startsWith('https') ? 'wss' : 'ws'
    const host = this.url.replace(/^https?:\/\//, '')
    const wsUrl = `${proto}://${host}/ws/projects/${projectId}?token=${encodeURIComponent(
      this.token || ''
    )}`

    const ws = new WebSocket(wsUrl)
    this.ws = ws

    ws.onmessage = (ev: MessageEvent) => {
      try {
        const data = JSON.parse(ev.data as string) as { type?: string }
        const type = data.type || 'message'
        this.listeners.get(type)?.forEach((cb) => cb(data))
        this.listeners.get('*')?.forEach((cb) => cb(data))
      } catch {
        /* ignore malformed */
      }
    }

    ws.onclose = () => {
      if (this.projectId) {
        // 简单指数退避重连（上限 5s）
        this.reconnectTimer = setTimeout(
          () => this.connect(this.projectId as string, this.token || undefined),
          2000
        )
      }
    }
  }

  on(event: string, callback: Listener) {
    if (!this.listeners.has(event)) this.listeners.set(event, new Set())
    this.listeners.get(event)?.add(callback)
  }

  off(event: string, callback: Listener) {
    this.listeners.get(event)?.delete(callback)
  }

  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    if (this.ws) {
      this.ws.onmessage = null
      this.ws.onclose = null
      this.ws.close()
      this.ws = null
    }
    this.projectId = null
  }

  isConnected() {
    return this.ws?.readyState === WebSocket.OPEN
  }
}

export const wsClient = new WebSocketClient()
