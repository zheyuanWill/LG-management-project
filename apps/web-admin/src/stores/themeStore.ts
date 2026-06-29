import { create } from 'zustand'

interface ThemeState {
  isDark: boolean
  toggle: () => void
}

export const useThemeStore = create<ThemeState>((set) => ({
  isDark: localStorage.getItem('lg_theme') === 'dark',
  toggle: () =>
    set((state) => {
      const next = !state.isDark
      localStorage.setItem('lg_theme', next ? 'dark' : 'light')
      return { isDark: next }
    }),
}))
