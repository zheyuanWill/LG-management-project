export interface AuthState {
  token: string | null
  user: {
    id: number
    username: string
    realName?: string
    role: string
    avatar?: string
  } | null
  login: (username: string, password: string) => Promise<void>
  logout: () => Promise<void>
  init: () => void
}
