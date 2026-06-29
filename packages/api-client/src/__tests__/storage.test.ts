import { describe, it, expect, beforeEach } from 'vitest'
import {
  getToken,
  setToken,
  removeToken,
  getRefreshToken,
  setRefreshToken,
  removeRefreshToken,
  getUserInfo,
  setUserInfo,
  clearAuth,
} from '../storage'

// Provide a minimal localStorage mock for Node
const localStorageMock = (() => {
  let store: Record<string, string> = {}
  return {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, value: string) => { store[key] = value },
    removeItem: (key: string) => { delete store[key] },
    clear: () => { store = {} },
  }
})()

// @ts-ignore - Node environment
globalThis.window = { localStorage: localStorageMock } as any

describe('token management', () => {
  beforeEach(() => {
    localStorageMock.clear()
  })

  it('sets and gets token', () => {
    setToken('abc123')
    expect(getToken()).toBe('abc123')
  })

  it('returns null when no token', () => {
    expect(getToken()).toBeNull()
  })

  it('removes token', () => {
    setToken('abc123')
    removeToken()
    expect(getToken()).toBeNull()
  })
})

describe('refresh token management', () => {
  beforeEach(() => {
    localStorageMock.clear()
  })

  it('sets and gets refresh token', () => {
    setRefreshToken('refresh_abc')
    expect(getRefreshToken()).toBe('refresh_abc')
  })

  it('removes refresh token', () => {
    setRefreshToken('refresh_abc')
    removeRefreshToken()
    expect(getRefreshToken()).toBeNull()
  })
})

describe('user info management', () => {
  beforeEach(() => {
    localStorageMock.clear()
  })

  it('sets and gets user info', () => {
    const user = { id: 1, name: 'Test', role: 'OWNER' }
    setUserInfo(user)
    expect(getUserInfo()).toEqual(user)
  })

  it('returns null when no user info', () => {
    expect(getUserInfo()).toBeNull()
  })
})

describe('clearAuth', () => {
  beforeEach(() => {
    localStorageMock.clear()
  })

  it('clears all auth data', () => {
    setToken('token')
    setRefreshToken('refresh')
    setUserInfo({ id: 1 })

    clearAuth()

    expect(getToken()).toBeNull()
    expect(getRefreshToken()).toBeNull()
    expect(getUserInfo()).toBeNull()
  })
})
