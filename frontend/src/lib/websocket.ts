import { io, Socket } from 'socket.io-client'

class WebSocketClient {
  private socket: Socket | null = null
  private url: string

  constructor(url: string = window.location.origin) {
    this.url = url
  }

  connect(token?: string) {
    if (this.socket?.connected) return this.socket

    this.socket = io(this.url, {
      path: '/ws',
      transports: ['websocket'],
      reconnection: true,
      reconnectionAttempts: Infinity,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      autoConnect: true,
      auth: token ? { token } : undefined,
    })

    this.socket.on('connect', () => {
      console.log('[WebSocket] 已连接')
    })

    this.socket.on('disconnect', (reason) => {
      console.log('[WebSocket] 已断开:', reason)
    })

    this.socket.on('connect_error', (error) => {
      console.error('[WebSocket] 连接错误:', error.message)
    })

    return this.socket
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
    }
  }

  on<T = unknown>(event: string, callback: (data: T) => void) {
    this.socket?.on(event, callback)
  }

  off(event: string, callback?: (...args: unknown[]) => void) {
    if (callback) {
      this.socket?.off(event, callback)
    } else {
      this.socket?.off(event)
    }
  }

  emit<T = unknown>(event: string, data: T) {
    this.socket?.emit(event, data)
  }

  isConnected() {
    return this.socket?.connected ?? false
  }

  getSocket() {
    return this.socket
  }
}

export const wsClient = new WebSocketClient()