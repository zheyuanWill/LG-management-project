import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import apiClient from '@/lib/api'
import type { User, UserLogin } from '@/types'

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (data: UserLogin) => Promise<void>
  logout: () => void
  setUser: (user: User) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,

      login: async (data) => {
        set({ isLoading: true })
        try {
          const response = await apiClient.post<{
            access_token: string
            user: User
          }>('/auth/login', data)
          const { access_token, user } = response.data
          set({
            token: access_token,
            user,
            isAuthenticated: true,
            isLoading: false,
          })
        } catch (error) {
          set({ isLoading: false })
          throw error
        }
      },

      logout: () => {
        set({
          user: null,
          token: null,
          isAuthenticated: false,
        })
      },

      setUser: (user) => set({ user }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)

export function useAuth() {
  const { user, token, login, logout, isAuthenticated, isLoading } =
    useAuthStore()
  return { user, token, login, logout, isAuthenticated, isLoading }
}