import { useApiQuery } from '@lg/react-hooks'
import type { TrackingNode, PageResponse } from '@lg/api-client'

export function useTasks(params?: Record<string, unknown>) {
  return useApiQuery<PageResponse<TrackingNode>>(
    ['tasks', params],
    '/tracking/nodes',
    { ...params, size: 50 }
  )
}
