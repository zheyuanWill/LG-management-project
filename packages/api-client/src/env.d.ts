/**
 * Global type declarations for @lg/api-client
 *
 * Provides minimal uni-app API types so the package can compile
 * without depending on the full @dcloudio/types package.
 */

declare const uni: {
  getStorageSync(key: string): string
  setStorageSync(key: string, data: string): void
  removeStorageSync(key: string): void
  request(options: {
    url: string
    method?: string
    header?: Record<string, string>
    data?: unknown
    success?: (res: { statusCode: number; data: unknown }) => void
    fail?: (err: { errMsg: string }) => void
  }): void
  reLaunch(options: { url: string }): void
}
