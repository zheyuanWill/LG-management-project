import { Empty, Button } from 'antd'
import type { ReactNode } from 'react'

interface EmptyStateProps {
  description?: string
  action?: ReactNode
}

export function EmptyState({ description = '暂无数据', action }: EmptyStateProps) {
  return (
    <Empty description={description} style={{ padding: 48 }}>
      {action}
    </Empty>
  )
}
