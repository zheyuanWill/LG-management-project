/**
 * Expo / React Native Storage Adapter
 *
 * Provides async storage functions backed by @react-native-async-storage/async-storage.
 * Since RN AsyncStorage is async while the current storage.ts is sync,
 * this adapter pre-loads tokens at startup and keeps an in-memory cache
 * so getToken() / getUserInfo() remain synchronous for the HTTP client.
 *
 * Usage (in mobile-app entry):
 *
 * ```ts
 * import { configureHttp } from '@lg/api-client'
 * import { initExpoStorage } from '@lg/api-client/expo-adapter'
 *
 * // Call once at app startup, before any API requests
 * await initExpoStorage()
 *
 * configureHttp({
 *   baseUrl: 'https://example.com/api',
 *   onUnauthorized: () => router.replace('/(auth)/login'),
 * })
 * ```
 */

type AsyncStorageStatic = {
  getItem: (key: string) => Promise<string | null>
  setItem: (key: string, value: string) => Promise<void>
  removeItem: (key: string) => Promise<void>
  multiGet: (keys: string[]) => Promise<[string, string | null][]>
  multiRemove: (keys: string[]) => Promise<void>
}

let _asyncStorage: AsyncStorageStatic | null = null

const TOKEN_KEY = 'lg_access_token'
const REFRESH_TOKEN_KEY = 'lg_refresh_token'
const USER_INFO_KEY = 'lg_user_info'

const memoryCache: Record<string, string | null> = {}

function injectStorageGlobals(): void {
  if (typeof globalThis !== 'undefined') {
    ;(globalThis as Record<string, unknown>).__lgStorageGet = (key: string) => memoryCache[key] ?? null
    ;(globalThis as Record<string, unknown>).__lgStorageSet = (key: string, value: string) => {
      memoryCache[key] = value
      _asyncStorage?.setItem(key, value)
    }
    ;(globalThis as Record<string, unknown>).__lgStorageRemove = (key: string) => {
      delete memoryCache[key]
      _asyncStorage?.removeItem(key)
    }
  }
}

/**
 * Initialize Expo storage by pre-loading all auth keys into memory.
 * Must be called before any API operations.
 */
export async function initExpoStorage(asyncStorage: AsyncStorageStatic): Promise<void> {
  _asyncStorage = asyncStorage
  const keys = [TOKEN_KEY, REFRESH_TOKEN_KEY, USER_INFO_KEY]
  const results = await asyncStorage.multiGet(keys)
  for (const [key, value] of results) {
    memoryCache[key] = value
  }
  injectStorageGlobals()
}

export async function clearExpoAuth(): Promise<void> {
  const keys = [TOKEN_KEY, REFRESH_TOKEN_KEY, USER_INFO_KEY]
  for (const key of keys) {
    delete memoryCache[key]
  }
  if (_asyncStorage) {
    await _asyncStorage.multiRemove(keys)
  }
}
