/**
 * Storage Abstraction
 *
 * Unified storage interface that supports:
 * - Web: window.localStorage
 * - uni-app: uni.getStorageSync / uni.setStorageSync
 *
 * The implementation auto-detects the environment at runtime.
 */

const TOKEN_KEY = 'lg_access_token'
const REFRESH_TOKEN_KEY = 'lg_refresh_token'
const USER_INFO_KEY = 'lg_user_info'

// ---------------------------------------------------------------------------
// Environment detection
// ---------------------------------------------------------------------------

function isUniApp(): boolean {
  return typeof uni !== 'undefined' && typeof uni.getStorageSync === 'function'
}

function isBrowser(): boolean {
  return typeof window !== 'undefined' && typeof window.localStorage !== 'undefined'
}

// ---------------------------------------------------------------------------
// Low-level storage helpers
// ---------------------------------------------------------------------------

function storageGet(key: string): string | null {
  if (isUniApp()) {
    try {
      const val = uni.getStorageSync(key)
      return val || null
    } catch {
      return null
    }
  }
  if (isBrowser()) {
    return localStorage.getItem(key)
  }
  return null
}

function storageSet(key: string, value: string): void {
  if (isUniApp()) {
    try {
      uni.setStorageSync(key, value)
    } catch {
      // ignore
    }
    return
  }
  if (isBrowser()) {
    localStorage.setItem(key, value)
  }
}

function storageRemove(key: string): void {
  if (isUniApp()) {
    try {
      uni.removeStorageSync(key)
    } catch {
      // ignore
    }
    return
  }
  if (isBrowser()) {
    localStorage.removeItem(key)
  }
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

export function getToken(): string | null {
  return storageGet(TOKEN_KEY)
}

export function setToken(token: string): void {
  storageSet(TOKEN_KEY, token)
}

export function removeToken(): void {
  storageRemove(TOKEN_KEY)
}

export function getRefreshToken(): string | null {
  return storageGet(REFRESH_TOKEN_KEY)
}

export function setRefreshToken(token: string): void {
  storageSet(REFRESH_TOKEN_KEY, token)
}

export function removeRefreshToken(): void {
  storageRemove(REFRESH_TOKEN_KEY)
}

export function getUserInfo<T = unknown>(): T | null {
  const info = storageGet(USER_INFO_KEY)
  if (!info) return null
  try {
    return JSON.parse(info) as T
  } catch {
    return null
  }
}

export function setUserInfo<T>(user: T): void {
  storageSet(USER_INFO_KEY, JSON.stringify(user))
}

export function clearAuth(): void {
  storageRemove(TOKEN_KEY)
  storageRemove(REFRESH_TOKEN_KEY)
  storageRemove(USER_INFO_KEY)
}
