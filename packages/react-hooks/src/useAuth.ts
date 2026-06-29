import { create } from 'zustand'
import { authApi, getToken } from '@lg/api-client'
import type { LoginResponse } from '@lg/api-client'

type AuthUser = LoginResponse['user']

interface AuthState {
  token: string | null
  user: AuthUser | null
  login: (username: string, password: string) => Promise<void>
  logout: () => Promise<void>
  init: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  user: null,

  login: async (username, password) => {
    const res = await authApi.login({ username, password })
    set({ token: res.accessToken, user: res.user })
  },

  logout: async () => {
    await authApi.logout()
    set({ token: null, user: null })
  },

  init: () => {
    const token = getToken()
    const user = authApi.getCachedUser()
    if (token && user) {
      set({ token, user })
    }
  },
}))
