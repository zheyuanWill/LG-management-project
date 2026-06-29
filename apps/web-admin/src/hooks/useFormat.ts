import { useCallback } from 'react'
import { formatDate, formatRelativeTime } from '@lg/core'
import { formatMoney } from '@lg/core'
import {
  orderStatusLabels,
  contractStatusLabels,
  procurementStatusLabels,
  settlementStatusLabels,
  nodeStatusLabels,
} from '@lg/core'

export function useFormat() {
  const fmtDate = useCallback((date?: string | null) => {
    if (!date) return '-'
    return formatDate(date)
  }, [])

  const fmtRelative = useCallback((date?: string | null) => {
    if (!date) return '-'
    return formatRelativeTime(date)
  }, [])

  const fmtMoney = useCallback((amount?: number | null, currency = 'CNY') => {
    if (amount == null) return '-'
    return formatMoney(amount, currency)
  }, [])

  const fmtStatus = useCallback((status: string, type: 'order' | 'contract' | 'procurement' | 'settlement' | 'node') => {
    const maps: Record<string, Record<string, string>> = {
      order: orderStatusLabels,
      contract: contractStatusLabels,
      procurement: procurementStatusLabels,
      settlement: settlementStatusLabels,
      node: nodeStatusLabels,
    }
    return maps[type]?.[status] ?? status
  }, [])

  return { fmtDate, fmtRelative, fmtMoney, fmtStatus }
}
