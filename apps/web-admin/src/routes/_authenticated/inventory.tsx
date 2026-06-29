import { useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { Table, Button, Form, Input, Select, Tabs, Card, Statistic, Row, Col, Spin } from 'antd'
import { useApiQuery } from '@lg/react-hooks'
import { PageHeader } from '@/components/common'
import { useFormat } from '@/hooks/useFormat'
import { http } from '@lg/api-client'

export const Route = createFileRoute('/_authenticated/inventory')({
  component: InventoryPage,
})

function InventoryPage() {
  const { fmtDate } = useFormat()
  const [keyword, setKeyword] = useState('')
  const [movementType, setMovementType] = useState<string | undefined>(undefined)
  const [activeTab, setActiveTab] = useState('batches')

  const { data: batches, isLoading: loadingBatches } = useApiQuery<{ items: any[]; total: number }>(
    ['inventory', 'batches', keyword], '/inventory/batches', { keyword, size: 50 }
  )
  const movementParams: Record<string, unknown> = { size: 50 }
  if (movementType) movementParams.type = movementType
  const { data: movements, isLoading: loadingMovements } = useApiQuery<{ items: any[]; total: number }>(
    ['inventory', 'movements', movementType], '/inventory/movements', movementParams, { enabled: activeTab === 'movements' }
  )
  const { data: summary } = useApiQuery<any[]>(
    ['inventory', 'summary', keyword], '/inventory/summary', { keyword }
  )

  const batchColumns = [
    { title: '批次号', dataIndex: 'batch_no', key: 'batch_no', width: 140 },
    { title: '产品ID', dataIndex: 'product_id', key: 'product_id', width: 80 },
    { title: '数量', dataIndex: 'quantity', key: 'quantity', width: 80, align: 'right' as const },
    { title: '单位成本', dataIndex: 'unit_cost', key: 'unit_cost', width: 100, align: 'right' as const },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 120, render: (v: string) => fmtDate(v) },
  ]

  const movementColumns = [
    { title: '类型', dataIndex: 'type', key: 'type', width: 80 },
    { title: '产品ID', dataIndex: 'product_id', key: 'product_id', width: 80 },
    { title: '批次ID', dataIndex: 'batch_id', key: 'batch_id', width: 80 },
    { title: '数量', dataIndex: 'quantity', key: 'quantity', width: 80, align: 'right' as const },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 120, render: (v: string) => fmtDate(v) },
  ]

  return (
    <div>
      <PageHeader title="库存管理" />
      <Form layout="inline" onFinish={({ kw }) => setKeyword(kw ?? '')} style={{ marginBottom: 16 }}>
        <Form.Item name="kw"><Input placeholder="搜索产品" allowClear /></Form.Item>
        <Form.Item><Button type="primary" htmlType="submit">搜索</Button></Form.Item>
      </Form>
      <Tabs activeKey={activeTab} onChange={setActiveTab} items={[
        { key: 'batches', label: '库存批次', children: <Table rowKey="id" columns={batchColumns} dataSource={batches?.items} loading={loadingBatches} pagination={false} /> },
        { key: 'movements', label: '出入库记录', children: (
          <div>
            <Form layout="inline" onFinish={({ type }) => setMovementType(type ?? undefined)} style={{ marginBottom: 16 }}>
              <Form.Item name="type"><Select placeholder="类型" options={[{ value: 'IN', label: '入库' }, { value: 'OUT', label: '出库' }, { value: 'ADJUST', label: '调整' }]} allowClear style={{ width: 120 }} /></Form.Item>
              <Form.Item><Button type="primary" htmlType="submit">搜索</Button></Form.Item>
            </Form>
            <Table rowKey="id" columns={movementColumns} dataSource={movements?.items} loading={loadingMovements} pagination={false} />
          </div>
        ) },
      ]} />
    </div>
  )
}
