import { useApiQuery } from '@lg/react-hooks'
import type { Procurement, PageResponse } from '@lg/api-client'

export function useApprovals() {
  return useApiQuery<PageResponse<Procurement>>(
    ['approvals'],
    '/procurements',
    { status: 'PENDING_APPROVAL', size: 50 }
  )
}
