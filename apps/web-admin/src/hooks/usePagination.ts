import { useState, useCallback, useMemo } from 'react'

export interface PaginationState {
  page: number
  size: number
}

export interface UsePaginationOptions {
  defaultPage?: number
  defaultSize?: number
}

export function usePagination(options: UsePaginationOptions = {}) {
  const { defaultPage = 1, defaultSize = 20 } = options

  const [pagination, setPagination] = useState<PaginationState>({
    page: defaultPage,
    size: defaultSize,
  })

  const paginationParams = useMemo(
    () => ({ page: pagination.page, size: pagination.size }),
    [pagination],
  )

  const handlePageChange = useCallback((page: number, size?: number) => {
    setPagination((prev) => ({ page, size: size ?? prev.size }))
  }, [])

  const handleSizeChange = useCallback((size: number) => {
    setPagination({ page: 1, size })
  }, [])

  const reset = useCallback(() => {
    setPagination({ page: defaultPage, size: defaultSize })
  }, [defaultPage, defaultSize])

  return { pagination, paginationParams, handlePageChange, handleSizeChange, reset }
}
