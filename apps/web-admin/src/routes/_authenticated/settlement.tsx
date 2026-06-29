import { useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { Table, Button, Form, Input, Select, Modal, message, Tag, Space, Popconfirm } from 'antd'
import { PlusOutlined, CheckOutlined, CloseOutlined, DeleteOutlined } from '@ant-design/icons'
import { usePageQuery, useApiPost, useApiQuery, useApiDelete } from '@lg/react-hooks'
import { PageHeader, StatusBadge } from '@/components/common'
import { settlementStatusOptions } from '@/constants'
import { useFormat } from '@/hooks/useFormat'
import { settlementStatusLabels } from '@lg/core'
import type { Settlement, PageResponse } from '@lg/api-client'
import { http } from '@lg/api-client'
import { useQueryClient } from '@tanstack/react-query'

export const Route = createFileRoute('/_authenticated/settlement')({
  component: SettlementPage,
})

const statusColors: Record<string, string> = {
  DRAFT: 'default', PENDING_APPROVAL: 'warning', APPROVING: 'processing', APPROVED: 'success', REJECTED: 'error', COMPLETED: 'default',
}

function SettlementPage() {
  const { fmtDate, fmtMoney, fmtStatus } = useFormat()
  const [params, setParams] = useState<Record<string, unknown>>({ page: 1, size: 20 })
  const [createOpen, setCreateOpen] = useState(false)
  const [form] = Form.useForm()
  const queryClient = useQueryClient()

  const { data: ordersData } = useApiQuery<PageResponse<{ id: number; order_no: string; customer_name?: string }>>(
    ['orders', 'select'], '/orders', { size: 200 },
  )
  const orderOptions = (ordersData?.items ?? []).map((o) => ({
    value: o.id, label: `${o.order_no}${o.customer_name ? ` - ${o.customer_name}` : ''}`,
  }))

  const { data: contractsData } = useApiQuery<PageResponse<{ id: number; contract_no: string }>>(
    ['contracts', 'select'], '/contracts', { size: 200 },
  )
  const contractOptions = (contractsData?.items ?? []).map((c) => ({
    value: c.id, label: c.contract_no,
  }))

  const { data, isLoading } = usePageQuery<Settlement>(['settlements', params], '/settlements', params)
  const createMutation = useApiPost<Settlement>('/settlements', {
    invalidateKeys: [['settlements']],
    onSuccess: () => { message.success('创建成功'); setCreateOpen(false); form.resetFields() },
  })

  const deleteMutation = useApiDelete('/settlements', {
    invalidateKeys: [['settlements']],
    onSuccess: () => message.success('删除成功'),
  })

  const handleApprove = async (id: number, approved: boolean) => {
    try {
      await http.post(`/settlements/${id}/approve`, { approved })
      message.success(approved ? '审批通过' : '已驳回')
      queryClient.invalidateQueries({ queryKey: ['settlements'] })
    } catch (e) { message.error(e instanceof Error ? e.message : '操作失败') }
  }

  const columns = [
    { title: '结算编号', dataIndex: 'settlement_no', key: 'settlement_no', width: 160 },
    { title: '状态', dataIndex: 'status', key: 'status', width: 100, render: (v: string) => <Tag color={statusColors[v]}>{fmtStatus(v, 'settlement')}</Tag> },
    { title: '总营收', dataIndex: 'total_revenue', key: 'total_revenue', width: 120, align: 'right' as const, render: (v: number) => fmtMoney(v) },
    { title: '总成本', dataIndex: 'total_cost', key: 'total_cost', width: 120, align: 'right' as const, render: (v: number) => fmtMoney(v) },
    { title: '毛利', dataIndex: 'gross_profit', key: 'gross_profit', width: 120, align: 'right' as const, render: (v: number) => fmtMoney(v) },
    { title: '毛利率', dataIndex: 'gross_profit_rate', key: 'gross_profit_rate', width: 90, render: (v: number) => `${(v * 100).toFixed(1)}%` },
    { title: '申请日期', dataIndex: 'apply_date', key: 'apply_date', width: 120, render: (v: string) => fmtDate(v) },
    {
      title: '操作', key: 'actions', width: 150, fixed: 'right' as const,
      render: (_: unknown, r: Settlement) => (
        <Space size={0}>
          {(r.status === 'PENDING_APPROVAL' || r.status === 'APPROVING') && (
            <>
              <Popconfirm title="确认审批通过?" onConfirm={() => handleApprove(r.id, true)}><Button type="link" size="small" icon={<CheckOutlined />}>通过</Button></Popconfirm>
              <Popconfirm title="确认驳回?" onConfirm={() => handleApprove(r.id, false)}><Button type="link" size="small" danger icon={<CloseOutlined />}>驳回</Button></Popconfirm>
            </>
          )}
          <Popconfirm
            title="确定要删除该结算单吗？"
            onConfirm={() => deleteMutation.mutate(r.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <PageHeader title="结项管理" extra={<Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>新建结算</Button>} />
      <Form layout="inline" onFinish={(v) => setParams({ ...v, page: 1, size: 20 })} style={{ marginBottom: 16 }}>
        <Form.Item name="keyword"><Input placeholder="搜索结算编号" allowClear /></Form.Item>
        <Form.Item name="status"><Select placeholder="状态" options={settlementStatusOptions} allowClear style={{ width: 140 }} /></Form.Item>
        <Form.Item><Button type="primary" htmlType="submit">搜索</Button></Form.Item>
      </Form>
      <Table rowKey="id" columns={columns} dataSource={data?.items} loading={isLoading} scroll={{ x: 1100 }} pagination={{ current: data?.page, pageSize: data?.size, total: data?.total, showTotal: (t) => `共 ${t} 条`, onChange: (p, s) => setParams((prev) => ({ ...prev, page: p, size: s })) }} />
      <Modal title="新建结算" open={createOpen} onCancel={() => setCreateOpen(false)} onOk={() => form.submit()} confirmLoading={createMutation.isPending}>
        <Form form={form} layout="vertical" onFinish={(v) => createMutation.mutate(v)}>
          <Form.Item name="order_id" label="关联订单" rules={[{ required: true }]}><Select placeholder="选择订单" showSearch optionFilterProp="label" options={orderOptions} /></Form.Item>
          <Form.Item name="contract_id" label="关联合同"><Select placeholder="选择合同（可选）" showSearch optionFilterProp="label" options={contractOptions} allowClear /></Form.Item>
          <Form.Item name="notes" label="备注"><Input.TextArea rows={3} /></Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
