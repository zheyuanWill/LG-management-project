import { create } from 'zustand'
import { authApi, getToken, clearAuth } from '@lg/api-client'
import type { LoginResponse } from '@lg/api-client'
import { router } from 'expo-router'

type AuthUser = LoginResponse['user']

interface AuthState {
  token: string | null
  user: AuthUser | null
  isLoggedIn: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => Promise<void>
  init: () => void
}

export const useAuthStore = create<AuthState>((set, get) => ({
  token: null,
  user: null,
  get isLoggedIn() {
    return !!get().token && !!get().user
  },

  login: async (username, password) => {
    const res = await authApi.login({ username, password })
    set({ token: res.accessToken, user: res.user })
  },

  logout: async () => {
    try {
      await authApi.logout()
    } finally {
      clearAuth()
      set({ token: null, user: null })
      router.replace('/(auth)/login')
    }
  },

  init: () => {
    const token = getToken()
    const user = authApi.getCachedUser()
    if (token && user) {
      set({ token, user })
    }
  },
}))
