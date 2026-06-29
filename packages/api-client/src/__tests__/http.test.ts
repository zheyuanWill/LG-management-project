import { describe, it, expect, vi, beforeEach } from 'vitest'
import { configureHttp, http, type HttpTransport, type TransportResponse } from '../http'

// Mock storage module
vi.mock('../storage', () => ({
  getToken: vi.fn(() => 'test-token'),
  removeToken: vi.fn(),
}))

/**
 * Creates a mock transport that returns the given response data and status.
 */
function createMockTransport(
  status: number = 200,
  data: unknown = {},
): HttpTransport {
  return vi.fn(async () => ({ status, data } as TransportResponse))
}

describe('HttpClient', () => {
  let mockTransport: ReturnType<typeof vi.fn>

  beforeEach(() => {
    mockTransport = vi.fn(async () => ({ status: 200, data: {} }))
    configureHttp({
      baseUrl: 'http://test.com/api',
      transport: mockTransport,
    })
  })

  it('sends GET request with correct URL', async () => {
    const transport = createMockTransport(200, { items: [] })
    configureHttp({ transport })

    await http.get('/orders', { page: 1, size: 10 })

    expect(transport).toHaveBeenCalledWith(
      expect.objectContaining({
        url: expect.stringContaining('/orders?page=1&size=10'),
        method: 'GET',
      }),
    )
  })

  it('sends POST request with body', async () => {
    const transport = createMockTransport(200, { id: 1 })
    configureHttp({ transport })

    const body = { name: 'test', value: 123 }
    await http.post('/orders', body)

    expect(transport).toHaveBeenCalledWith(
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify(body),
      }),
    )
  })

  it('sends PUT request', async () => {
    const transport = createMockTransport(200, { id: 1, status: 'updated' })
    configureHttp({ transport })

    await http.put('/orders/1', { status: 'IN_PROGRESS' })

    expect(transport).toHaveBeenCalledWith(
      expect.objectContaining({
        method: 'PUT',
        body: JSON.stringify({ status: 'IN_PROGRESS' }),
      }),
    )
  })

  it('sends DELETE request', async () => {
    const transport = createMockTransport(200, { deleted: true })
    configureHttp({ transport })

    await http.delete('/orders/1')

    expect(transport).toHaveBeenCalledWith(
      expect.objectContaining({
        method: 'DELETE',
      }),
    )
  })

  it('includes authorization header when token exists', async () => {
    const transport = createMockTransport(200, {})
    configureHttp({ transport })

    await http.get('/orders')

    expect(transport).toHaveBeenCalledWith(
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer test-token',
        }),
      }),
    )
  })

  it('skips undefined params in query string', async () => {
    const transport = createMockTransport(200, {})
    configureHttp({ transport })

    await http.get('/orders', { page: 1, status: undefined, name: null })

    expect(transport).toHaveBeenCalledWith(
      expect.objectContaining({
        url: expect.stringContaining('page=1'),
      }),
    )
    // undefined and null should not appear
    const calledUrl = (transport as ReturnType<typeof vi.fn>).mock.calls[0][0].url
    expect(calledUrl).not.toContain('status')
    expect(calledUrl).not.toContain('name')
  })

  it('throws on 400+ error with detail message', async () => {
    const transport = createMockTransport(404, { detail: '订单不存在' })
    configureHttp({ transport })

    await expect(http.get('/orders/999')).rejects.toThrow('订单不存在')
  })

  it('throws generic error when no detail', async () => {
    const transport = createMockTransport(500, {})
    configureHttp({ transport })

    await expect(http.get('/fail')).rejects.toThrow('Request failed')
  })

  it('calls onUnauthorized on 401', async () => {
    const transport = createMockTransport(401, { detail: 'Unauthorized' })
    const onUnauthorized = vi.fn()
    configureHttp({ transport, onUnauthorized })

    await expect(http.get('/protected')).rejects.toThrow('Unauthorized')
    expect(onUnauthorized).toHaveBeenCalled()
  })
})

describe('configureHttp', () => {
  it('allows partial configuration', () => {
    // Should not throw
    configureHttp({ baseUrl: 'http://example.com/api' })
    configureHttp({ onUnauthorized: () => {} })
  })
})
