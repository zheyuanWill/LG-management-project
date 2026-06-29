/**
 * uni-app Transport Adapter
 *
 * Provides a `HttpTransport` implementation backed by `uni.request`,
 * allowing the shared `@lg/api-client` to work in uni-app (H5 / WeChat / App).
 *
 * Usage (in mobile-app main.ts or App.vue):
 *
 * ```ts
 * import { configureHttp } from '@lg/api-client'
 * import { createUniTransport } from '@lg/api-client/uni-adapter'
 *
 * configureHttp({
 *   baseUrl: 'http://localhost:8000/api',
 *   transport: createUniTransport(),
 *   onUnauthorized: () => {
 *     uni.reLaunch({ url: '/pages/login/index' })
 *   },
 * })
 * ```
 */
import type { HttpTransport, TransportResponse } from './http'

/**
 * Create a transport that delegates to `uni.request`.
 */
export function createUniTransport(): HttpTransport {
  return async (req): Promise<TransportResponse> => {
    return new Promise((resolve, reject) => {
      uni.request({
        url: req.url,
        method: req.method as 'GET' | 'POST' | 'PUT' | 'DELETE',
        header: req.headers,
        data: req.body ? JSON.parse(req.body) : undefined,
        success(res: { statusCode: number; data: unknown }) {
          resolve({
            status: res.statusCode,
            data: res.data,
          })
        },
        fail(err: { errMsg: string }) {
          reject(new Error(err.errMsg || 'Network request failed'))
        },
      })
    })
  }
}
