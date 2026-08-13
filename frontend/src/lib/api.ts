import axios from 'axios'
import { useAuthStore } from '@/hooks/useAuth'

const apiClient = axios.create({
  baseURL: '/api/v1',
  timeout: 15000,
  // 不设默认 Content-Type：axios 会根据 data 类型自动选择
  // (FormData → multipart/form-data, 普通 object → application/json)
})

apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout()
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default apiClient

export async function apiFetch<T>(
  url: string,
  options: {
    method?: string
    body?: unknown
    params?: Record<string, unknown>
    headers?: Record<string, string>
  } = {}
): Promise<T> {
  const { method = 'GET', body, params, headers } = options
  const response = await apiClient.request<T>({
    url,
    method,
    data: body,
    params,
    headers,
  })
  return response.data
}