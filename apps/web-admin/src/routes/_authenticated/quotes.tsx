import { useMemo, useState } from 'react'
import { createFileRoute, useNavigate, Outlet, useMatches } from '@tanstack/react-router'
import { Table, Button, Form, Input, Select, Modal, message, Tag, Space, DatePicker, App, Popconfirm } from 'antd'
import { PlusOutlined, SendOutlined, CopyOutlined, DeleteOutlined } from '@ant-design/icons'
import { usePageQuery, useApiPost, useApiQuery, useApiDelete } from '@lg/react-hooks'
import { http } from '@lg/api-client'
import { PageHeader, StatusBadge } from '@/components/common'
import { useFormat } from '@/hooks/useFormat'
import { useQueryClient } from '@tanstack/react-query'
import type { Quote, PageResponse } from '@lg/api-client'
import { QuoteStatus, quoteStatusLabels } from '@lg/core'

export const Route = createFileRoute('/_authenticated/quotes')({
  component: QuotesPage,
})

const quoteStatusColors: Record<string, string> = {
  DRAFT: 'default', SENT: 'processing', FEEDBACK: 'warning', ACCEPTED: 'success', REJECTED: 'error',
}

const quoteStatusOptions = Object.entries(quoteStatusLabels).map(([v, l]) => ({ value: v, label: l }))

function QuotesPage() {
  const { fmtDate, fmtMoney } = useFormat()
  const { message: msg } = App.useApp()
  const navigate = useNavigate()
  const matches = useMatches()
  const isExcel = useMemo(() => {
    const currentPath = matches[matches.length - 1]?.pathname ?? ''
    return currentPath.startsWith('/quotes/excel')
  }, [matches])
  const queryClient = useQueryClient()
  const [params, setParams] = useState<Record<string, unknown>>({ page: 1, size: 20 })
  const [createOpen, setCreateOpen] = useState(false)
  const [form] = Form.useForm()

  const handleSubmitApproval = async (quoteId: number) => {
    try {
      const result = await http.post<any>(`/quotes/${quoteId}/submit-approval`)
      const level = result.approval_level
      const margin = result.gross_margin_pct?.toFixed(1)
      if (level === 'AUTO') msg.success(`毛利率 ${margin}% > 30%，已自动通过审批`)
      else if (level === 'PM_OR_OWNER') msg.info(`毛利率 ${margin}%，需项目经理或总经理审批`)
      else msg.warning(`毛利率 ${margin}% < 15%，需总经理审批`)
      queryClient.invalidateQueries({ queryKey: ['quotes'] })
    } catch (e) { msg.error('提交失败') }
  }

  const handleDuplicate = async (quoteId: number) => {
    try {
      await http.post(`/quotes/${quoteId}/duplicate`)
      msg.success('已创建新版本')
      queryClient.invalidateQueries({ queryKey: ['quotes'] })
    } catch (e) { msg.error('复制失败') }
  }

  const { data, isLoading } = usePageQuery<Quote>(['quotes', params], '/quotes', params)

  const { data: ordersData } = useApiQuery<PageResponse<{ id: number; order_no: string; customer_name?: string }>>(
    ['orders', 'select'], '/orders', { size: 200 },
  )
  const orderOptions = (ordersData?.items ?? []).map((o) => ({
    value: o.id, label: `${o.order_no}${o.customer_name ? ` - ${o.customer_name}` : ''}`,
  }))

  const createMutation = useApiPost<Quote>('/quotes', {
    invalidateKeys: [['quotes']],
    onSuccess: () => { message.success('创建成功'); setCreateOpen(false); form.resetFields() },
  })

  const deleteMutation = useApiDelete('/quotes', {
    invalidateKeys: [['quotes']],
    onSuccess: () => message.success('删除成功'),
  })

  const columns = [
    { title: '报价编号', dataIndex: 'quote_no', key: 'quote_no', width: 160 },
    { title: '关联订单', dataIndex: 'order_no', key: 'order_no', width: 140 },
    { title: '版本', dataIndex: 'version', key: 'version', width: 70 },
    { title: '状态', dataIndex: 'status', key: 'status', width: 100, render: (v: string) => <Tag color={quoteStatusColors[v]}>{quoteStatusLabels[v as QuoteStatus] ?? v}</Tag> },
    { title: '金额', dataIndex: 'total_amount', key: 'total_amount', width: 130, align: 'right' as const, render: (v: number, r: Quote) => fmtMoney(v, r.currency) },
    { title: '有效期', dataIndex: 'valid_until', key: 'valid_until', width: 120, render: (v: string) => fmtDate(v) },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 120, render: (v: string) => fmtDate(v) },
    {
      title: '操作', key: 'actions', width: 220, fixed: 'right' as const,
      render: (_: any, r: Quote) => (
        <Space size={0}>
          {r.status === 'DRAFT' && <Button type="link" size="small" icon={<SendOutlined />} onClick={() => handleSubmitApproval(r.id)}>提交审批</Button>}
          <Button type="link" size="small" icon={<CopyOutlined />} onClick={() => handleDuplicate(r.id)}>新版本</Button>
          <Popconfirm
            title="确定要删除该报价吗？"
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

  if (isExcel) return <Outlet />

  return (
    <div>
      <PageHeader
        title="报价管理"
        extra={(
          <Space>
            <Button onClick={() => navigate({ to: '/quotes/excel' })}>报价Excel</Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>新建报价</Button>
          </Space>
        )}
      />
      <Form layout="inline" onFinish={(v) => setParams({ ...v, page: 1, size: 20 })} style={{ marginBottom: 16 }}>
        <Form.Item name="order_id"><Select placeholder="关联订单" showSearch optionFilterProp="label" options={orderOptions} allowClear style={{ width: 220 }} /></Form.Item>
        <Form.Item name="status">
          <Select placeholder="状态" options={quoteStatusOptions} allowClear style={{ width: 120 }} />
        </Form.Item>
        <Form.Item><Button type="primary" htmlType="submit">搜索</Button></Form.Item>
      </Form>
      <Table rowKey="id" columns={columns} dataSource={data?.items} loading={isLoading} pagination={{ current: data?.page, pageSize: data?.size, total: data?.total, showTotal: (t) => `共 ${t} 条`, onChange: (p, s) => setParams((prev) => ({ ...prev, page: p, size: s })) }} />
      <Modal title="新建报价" open={createOpen} onCancel={() => setCreateOpen(false)} onOk={() => form.submit()} confirmLoading={createMutation.isPending}>
        <Form form={form} layout="vertical" onFinish={(v) => createMutation.mutate(v)}>
          <Form.Item name="order_id" label="关联订单" rules={[{ required: true }]}><Select placeholder="选择订单" showSearch optionFilterProp="label" options={orderOptions} /></Form.Item>
          <Form.Item name="notes" label="备注"><Input.TextArea rows={3} /></Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
