/**
 * Authentication API
 */
import { http } from './http'
import { setToken, setRefreshToken, setUserInfo, clearAuth, getUserInfo } from './storage'
import type { LoginRequest, LoginResponse, User, CurrentUser } from './types'

/**
 * 认证 API
 */
export const authApi = {
  /**
   * 用户登录
   */
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await http.post<{
      access_token: string
      refresh_token: string
      token_type: string
      expires_in: number
      user: {
        id: number
        username: string
        real_name?: string
        role: string
      }
    }>('/auth/login', credentials)

    // 保存 token
    setToken(response.access_token)
    setRefreshToken(response.refresh_token)
    setUserInfo(response.user)

    // 转换为统一格式
    return {
      accessToken: response.access_token,
      refreshToken: response.refresh_token,
      tokenType: response.token_type,
      expiresIn: response.expires_in,
      user: {
        id: response.user.id,
        username: response.user.username,
        realName: response.user.real_name,
        role: response.user.role as 'OWNER' | 'PM' | 'PROC' | 'FIN' | 'OPS'
      }
    }
  },

  /**
   * 刷新 Token
   */
  async refresh(refreshToken: string): Promise<LoginResponse> {
    const response = await http.post<{
      access_token: string
      refresh_token: string
      token_type: string
      expires_in: number
      user: {
        id: number
        username: string
        real_name?: string
        role: string
      }
    }>('/auth/refresh', { refresh_token: refreshToken })

    // 保存新 token
    setToken(response.access_token)
    setRefreshToken(response.refresh_token)
    setUserInfo(response.user)

    return {
      accessToken: response.access_token,
      refreshToken: response.refresh_token,
      tokenType: response.token_type,
      expiresIn: response.expires_in,
      user: {
        id: response.user.id,
        username: response.user.username,
        realName: response.user.real_name,
        role: response.user.role as 'OWNER' | 'PM' | 'PROC' | 'FIN' | 'OPS'
      }
    }
  },

  /**
   * 获取当前用户信息
   */
  async me(): Promise<User> {
    return http.get<User>('/auth/me')
  },

  /**
   * 登出
   */
  async logout(): Promise<void> {
    try {
      await http.post('/auth/logout')
    } finally {
      // 无论是否成功，都清除本地 token
      clearAuth()
    }
  },

  /**
   * 获取缓存的用户信息
   */
  getCachedUser(): LoginResponse['user'] | null {
    return getUserInfo<LoginResponse['user']>()
  }
}

export default authApi
