/**
 * HTTP Client with pluggable transport
 *
 * Supports both `fetch` (web) and `uni.request` (uni-app mobile) via
 * a transport adapter pattern. Call `configureHttp()` to set the base URL
 * and optionally inject a custom transport before using the client.
 */
import { getToken, removeToken } from './storage'

// ---------------------------------------------------------------------------
// Transport abstraction
// ---------------------------------------------------------------------------

export interface TransportRequest {
  url: string
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'
  headers: Record<string, string>
  body?: string
}

export interface TransportResponse {
  status: number
  data: unknown
  headers?: Record<string, string>
}

/**
 * A transport is a function that takes a request and returns a response.
 * This allows swapping fetch for uni.request or any other HTTP implementation.
 */
export type HttpTransport = (req: TransportRequest) => Promise<TransportResponse>

// ---------------------------------------------------------------------------
// Default fetch-based transport
// ---------------------------------------------------------------------------

const MAX_RETRIES = 2
const RETRY_DELAY_MS = 1500

const fetchTransport: HttpTransport = async (req) => {
  let lastError: unknown
  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    try {
      const response = await fetch(req.url, {
        method: req.method,
        headers: req.headers,
        body: req.body,
      })

      let data: unknown
      const contentType = response.headers.get('content-type') || ''
      if (contentType.includes('application/json')) {
        data = await response.json()
      } else {
        const text = await response.text()
        try {
          data = JSON.parse(text)
        } catch {
          data = text
        }
      }

      return { status: response.status, data }
    } catch (err) {
      lastError = err
      if (attempt < MAX_RETRIES) {
        await new Promise(r => setTimeout(r, RETRY_DELAY_MS * (attempt + 1)))
      }
    }
  }
  throw lastError
}

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

interface HttpConfig {
  baseUrl: string
  transport: HttpTransport
  onUnauthorized?: () => void
}

const config: HttpConfig = {
  baseUrl: '/api',
  transport: fetchTransport,
  onUnauthorized: () => {
    removeToken()
    if (typeof window !== 'undefined') {
      window.location.href = '/login'
    }
  },
}

/**
 * Configure the HTTP client. Call this once during app initialization.
 *
 * @example
 * // Web (auto-detected, usually not needed)
 * configureHttp({ baseUrl: '/api' })
 *
 * // uni-app mobile
 * configureHttp({
 *   baseUrl: 'http://localhost:8000/api',
 *   transport: uniTransport,
 *   onUnauthorized: () => uni.reLaunch({ url: '/pages/login/index' }),
 * })
 */
export function configureHttp(options: Partial<HttpConfig>): void {
  if (options.baseUrl !== undefined) config.baseUrl = options.baseUrl
  if (options.transport) config.transport = options.transport
  if (options.onUnauthorized) config.onUnauthorized = options.onUnauthorized
}

// Auto-detect base URL for Vite web apps
function autoDetectBaseUrl(): void {
  if (typeof window !== 'undefined') {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const win = window as any
    if (win.__API_BASE_URL__) {
      config.baseUrl = win.__API_BASE_URL__ as string
      return
    }
  }
  try {
    // @ts-ignore — Vite environment variable
    if (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_BASE_URL) {
      // @ts-ignore
      config.baseUrl = import.meta.env.VITE_API_BASE_URL + '/api'
    }
  } catch {
    // Not in Vite environment, keep default
  }
}

autoDetectBaseUrl()

// ---------------------------------------------------------------------------
// Request config
// ---------------------------------------------------------------------------

interface RequestConfig {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'
  headers?: Record<string, string>
  body?: unknown
  params?: Record<string, unknown>
}

// ---------------------------------------------------------------------------
// HttpClient class
// ---------------------------------------------------------------------------

class HttpClient {
  private buildUrl(endpoint: string, params?: Record<string, unknown>): string {
    let url = `${config.baseUrl}${endpoint}`
    if (params) {
      const searchParams = new URLSearchParams()
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, String(value))
        }
      })
      const queryString = searchParams.toString()
      if (queryString) {
        url += `?${queryString}`
      }
    }
    return url
  }

  private getHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }
    const token = getToken()
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    return headers
  }

  async request<T>(endpoint: string, reqConfig: RequestConfig = {}): Promise<T> {
    const { method = 'GET', headers = {}, body, params } = reqConfig
    const url = this.buildUrl(endpoint, params)

    const response = await config.transport({
      url,
      method,
      headers: { ...this.getHeaders(), ...headers },
      body: body ? JSON.stringify(body) : undefined,
    })

    if (response.status === 401) {
      config.onUnauthorized?.()
      throw new Error('Unauthorized')
    }

    if (response.status >= 400) {
      const errorData = response.data as Record<string, unknown> | null
      const message = (errorData?.message as string) || (errorData?.detail as string) || 'Request failed'
      throw new Error(message)
    }

    return response.data as T
  }

  get<T>(endpoint: string, params?: Record<string, unknown>): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET', params })
  }

  post<T>(endpoint: string, body?: unknown): Promise<T> {
    return this.request<T>(endpoint, { method: 'POST', body })
  }

  put<T>(endpoint: string, body?: unknown): Promise<T> {
    return this.request<T>(endpoint, { method: 'PUT', body })
  }

  delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' })
  }

  patch<T>(endpoint: string, body?: unknown): Promise<T> {
    return this.request<T>(endpoint, { method: 'PATCH', body })
  }

  async postFormData<T>(endpoint: string, formData: FormData): Promise<T> {
    const url = this.buildUrl(endpoint)
    const headers: Record<string, string> = {}
    const token = getToken()
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: formData,
    })

    if (response.status === 401) {
      config.onUnauthorized?.()
      throw new Error('Unauthorized')
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Request failed' }))
      throw new Error((error as any).message || (error as any).detail || 'Request failed')
    }

    return response.json()
  }

  /**
   * File upload via FormData.
   * Uses fetch when available (web), falls back to transport for uni-app.
   */
  async upload<T>(
    endpoint: string,
    file: File,
    extraData?: Record<string, unknown>,
  ): Promise<T> {
    const url = this.buildUrl(endpoint)
    const headers: Record<string, string> = {}
    const token = getToken()
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    // If using a custom transport (e.g. uni-app), delegate to it
    if (config.transport !== fetchTransport) {
      // For non-fetch transports, send as base64-encoded JSON payload
      const reader = new FileReader()
      const base64 = await new Promise<string>((resolve) => {
        reader.onload = () => resolve(reader.result as string)
        reader.readAsDataURL(file)
      })
      const body: Record<string, unknown> = {
        file_data: base64,
        file_name: file.name,
        mime_type: file.type,
        ...extraData,
      }
      return this.request<T>(endpoint, { method: 'POST', body })
    }

    // Standard fetch-based FormData upload
    const formData = new FormData()
    formData.append('file', file)
    if (extraData) {
      Object.entries(extraData).forEach(([key, value]) => {
        formData.append(key, String(value))
      })
    }

    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: formData,
    })

    if (response.status === 401) {
      config.onUnauthorized?.()
      throw new Error('Unauthorized')
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Upload failed' }))
      throw new Error(error.message || error.detail || 'Upload failed')
    }

    return response.json()
  }
}

export const http = new HttpClient()

export default http
