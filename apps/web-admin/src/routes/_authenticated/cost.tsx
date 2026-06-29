import { useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { Table, Button, Form, Select, Card, Statistic, Row, Col, Alert } from 'antd'
import { useQuery } from '@tanstack/react-query'
import { http } from '@lg/api-client'
import { useApiQuery } from '@lg/react-hooks'
import { PageHeader } from '@/components/common'
import { useFormat } from '@/hooks/useFormat'
import type { PageResponse } from '@lg/api-client'

export const Route = createFileRoute('/_authenticated/cost')({
  component: CostPage,
})

function CostPage() {
  const { fmtDate, fmtMoney } = useFormat()
  const [orderId, setOrderId] = useState<number | null>(null)

  const { data: ordersData } = useApiQuery<PageResponse<{ id: number; order_no: string; customer_name?: string }>>(
    ['orders', 'select'], '/orders', { size: 200 },
  )
  const orderOptions = (ordersData?.items ?? []).map((o) => ({
    value: o.id, label: `${o.order_no}${o.customer_name ? ` - ${o.customer_name}` : ''}`,
  }))

  const { data: costs, isLoading } = useApiQuery<{ items: any[]; total: number }>(
    ['costs', orderId], '/settlements/costs', orderId ? { order_id: orderId, size: 100 } : { size: 100 },
  )

  const columns = [
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
    { title: '分类', dataIndex: 'category_id', key: 'category_id', width: 100 },
    { title: '金额', dataIndex: 'amount', key: 'amount', width: 120, align: 'right' as const, render: (v: number) => fmtMoney(v) },
    { title: '人民币金额', dataIndex: 'amount_cny', key: 'amount_cny', width: 120, align: 'right' as const, render: (v: number) => fmtMoney(v) },
    { title: '发票号', dataIndex: 'invoice_no', key: 'invoice_no', width: 130 },
    { title: '发票日期', dataIndex: 'invoice_date', key: 'invoice_date', width: 120, render: (v: string) => fmtDate(v) },
  ]

  return (
    <div>
      <PageHeader title="成本核算" />
      <Form layout="inline" onFinish={({ oid }) => setOrderId(oid ?? null)} style={{ marginBottom: 16 }}>
        <Form.Item name="oid"><Select placeholder="选择订单" showSearch optionFilterProp="label" options={orderOptions} allowClear style={{ width: 260 }} /></Form.Item>
        <Form.Item><Button type="primary" htmlType="submit">查询</Button></Form.Item>
      </Form>
      {orderId && <BreakevenCard orderId={orderId} />}
      <Table rowKey="id" columns={columns} dataSource={costs?.items} loading={isLoading} pagination={false} />
    </div>
  )
}

function BreakevenCard({ orderId }: { orderId: number }) {
  const { data } = useQuery({
    queryKey: ['breakeven', orderId],
    queryFn: () => http.get<any>(`/settlements/breakeven/${orderId}`),
  })
  if (!data) return null
  return (
    <Card size="small" style={{ marginBottom: 16 }}>
      <Row gutter={24}>
        <Col><Statistic title="总成本(CNY)" value={data.total_cost} precision={2} /></Col>
        <Col><Statistic title="已付款(CNY)" value={data.total_disbursed} precision={2} /></Col>
        <Col><Statistic title="盈亏平衡收入(CNY)" value={data.breakeven_revenue} precision={2} valueStyle={{ color: '#cf1322' }} /></Col>
      </Row>
    </Card>
  )
}
