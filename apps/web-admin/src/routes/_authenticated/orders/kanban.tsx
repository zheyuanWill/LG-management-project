import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { Card, Row, Col, Tag, Typography, Spin, Badge, Button } from 'antd'
import { ArrowLeftOutlined } from '@ant-design/icons'
import { useApiQuery } from '@lg/react-hooks'
import { PageHeader } from '@/components/common'
import { useFormat } from '@/hooks/useFormat'
import { orderStatusLabels, OrderStatus } from '@lg/core'
import type { Order, PageResponse } from '@lg/api-client'

export const Route = createFileRoute('/_authenticated/orders/kanban')({
  component: OrderKanbanPage,
})

const kanbanColumns = [
  { status: OrderStatus.DRAFT, title: '草稿', color: '#d9d9d9' },
  { status: OrderStatus.IN_PROGRESS, title: '进行中', color: '#1677ff' },
  { status: OrderStatus.COMPLETED, title: '已完成', color: '#52c41a' },
  { status: OrderStatus.CANCELLED, title: '已取消', color: '#ff4d4f' },
]

function OrderKanbanPage() {
  const navigate = useNavigate()
  const { fmtMoney } = useFormat()

  const { data, isLoading } = useApiQuery<PageResponse<Order>>(
    ['orders', 'kanban'], '/orders', { size: 200 }
  )

  const ordersByStatus = (status: string) =>
    (data?.items ?? []).filter((o) => o.status === status)

  return (
    <div>
      <PageHeader
        title="订单看板"
        extra={
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate({ to: '/orders' })}>
            列表视图
          </Button>
        }
      />

      <Spin spinning={isLoading}>
        <Row gutter={16}>
          {kanbanColumns.map((col) => {
            const orders = ordersByStatus(col.status)
            return (
              <Col key={col.status} xs={24} sm={12} lg={6}>
                <div style={{ marginBottom: 12 }}>
                  <Badge count={orders.length} style={{ backgroundColor: col.color }}>
                    <Typography.Text strong style={{ fontSize: 15 }}>{col.title}</Typography.Text>
                  </Badge>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {orders.map((order) => (
                    <Card
                      key={order.id}
                      size="small"
                      hoverable
                      onClick={() => navigate({ to: '/orders/$id', params: { id: String(order.id) } })}
                    >
                      <Typography.Text strong>{order.order_no}</Typography.Text>
                      <div style={{ color: '#888', fontSize: 13 }}>
                        {order.customer_name} · {fmtMoney(order.total_amount, order.currency)}
                      </div>
                    </Card>
                  ))}
                </div>
              </Col>
            )
          })}
        </Row>
      </Spin>
    </div>
  )
}
