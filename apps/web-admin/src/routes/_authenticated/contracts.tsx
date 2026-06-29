import { useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { Table, Button, Form, Input, Select, Modal, message, Tag, DatePicker, Space, App, Popconfirm } from 'antd'
import { PlusOutlined, AuditOutlined, DeleteOutlined } from '@ant-design/icons'
import { usePageQuery, useApiPost, useApiQuery, useApiDelete } from '@lg/react-hooks'
import { PageHeader, StatusBadge } from '@/components/common'
import { contractStatusOptions, contractStatusColors, currencyOptions } from '@/constants'
import { useFormat } from '@/hooks/useFormat'
import { contractStatusLabels } from '@lg/core'
import { http } from '@lg/api-client'
import { useQueryClient } from '@tanstack/react-query'
import type { Contract, PageResponse } from '@lg/api-client'

export const Route = createFileRoute('/_authenticated/contracts')({
  component: ContractsPage,
})

function ContractsPage() {
  const { fmtDate, fmtMoney, fmtStatus } = useFormat()
  const { message: msg } = App.useApp()
  const queryClient = useQueryClient()
  const [params, setParams] = useState<Record<string, unknown>>({ page: 1, size: 20 })
  const [createOpen, setCreateOpen] = useState(false)
  const [reviewOpen, setReviewOpen] = useState(false)
  const [reviewContractId, setReviewContractId] = useState<number | null>(null)
  const [form] = Form.useForm()
  const [reviewForm] = Form.useForm()

  const { data: customersData } = useApiQuery<PageResponse<{ id: number; name: string }>>(
    ['customers', 'all'], '/customers', { size: 100 },
  )
  const customerOptions = (customersData?.items ?? []).map((c) => ({ value: c.id, label: c.name }))

  const { data, isLoading } = usePageQuery<Contract>(['contracts', params], '/contracts', params)

  const { data: ordersData } = useApiQuery<PageResponse<{ id: number; order_no: string; customer_name?: string }>>(
    ['orders', 'select'], '/orders', { size: 200 },
  )
  const orderOptions = (ordersData?.items ?? []).map((o) => ({
    value: o.id, label: `${o.order_no}${o.customer_name ? ` - ${o.customer_name}` : ''}`,
  }))

  const createMutation = useApiPost<Contract>('/contracts', {
    invalidateKeys: [['contracts']],
    onSuccess: () => { message.success('创建成功'); setCreateOpen(false); form.resetFields() },
  })

  const deleteMutation = useApiDelete('/contracts', {
    invalidateKeys: [['contracts']],
    onSuccess: () => message.success('删除成功'),
  })

  const columns = [
    { title: '合同编号', dataIndex: 'contract_no', key: 'contract_no', width: 160 },
    { title: '标题', dataIndex: 'title', key: 'title', ellipsis: true },
    { title: '客户', dataIndex: 'customer_name', key: 'customer_name', width: 140 },
    { title: '状态', dataIndex: 'status', key: 'status', width: 100, render: (v: string) => <StatusBadge label={fmtStatus(v, 'contract')} colorMap={contractStatusColors} status={v} /> },
    { title: '金额', dataIndex: 'total_amount', key: 'total_amount', width: 130, align: 'right' as const, render: (v: number, r: Contract) => fmtMoney(v, r.currency) },
    { title: '签订日期', dataIndex: 'signed_date', key: 'signed_date', width: 120, render: (v: string) => fmtDate(v) },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 120, render: (v: string) => fmtDate(v) },
    { title: '操作', key: 'actions', width: 150, fixed: 'right' as const, render: (_: any, r: Contract) => (
      <Space size={0}>
        <Button type="link" size="small" icon={<AuditOutlined />} onClick={() => { setReviewContractId(r.id); setReviewOpen(true) }}>评审</Button>
        <Popconfirm
          title="确定要删除该合同吗？"
          onConfirm={() => deleteMutation.mutate(r.id)}
          okText="确定"
          cancelText="取消"
        >
          <Button type="link" size="small" danger icon={<DeleteOutlined />}>删除</Button>
        </Popconfirm>
      </Space>
    ) },
  ]

  const handleReview = async (values: any) => {
    if (!reviewContractId) return
    try {
      await http.post('/iso/contract-reviews', { contract_id: reviewContractId, ...values, review_date: new Date().toISOString().slice(0, 10) })
      msg.success('评审已提交')
      setReviewOpen(false)
      reviewForm.resetFields()
    } catch (e) {
      msg.error('提交失败')
    }
  }

  return (
    <div>
      <PageHeader title="合同管理" extra={<Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>新建合同</Button>} />
      <Form layout="inline" onFinish={(v) => setParams({ ...v, page: 1, size: 20 })} style={{ marginBottom: 16 }}>
        <Form.Item name="keyword"><Input placeholder="搜索合同号/标题/客户" allowClear /></Form.Item>
        <Form.Item name="status"><Select placeholder="状态" options={contractStatusOptions} allowClear style={{ width: 140 }} /></Form.Item>
        <Form.Item name="customer_id"><Select placeholder="客户" showSearch optionFilterProp="label" options={customerOptions} allowClear style={{ width: 160 }} /></Form.Item>
        <Form.Item><Button type="primary" htmlType="submit">搜索</Button></Form.Item>
      </Form>
      <Table rowKey="id" columns={columns} dataSource={data?.items} loading={isLoading} pagination={{ current: data?.page, pageSize: data?.size, total: data?.total, showTotal: (t) => `共 ${t} 条`, onChange: (p, s) => setParams((prev) => ({ ...prev, page: p, size: s })) }} />
      <Modal title="新建合同" open={createOpen} onCancel={() => setCreateOpen(false)} onOk={() => form.submit()} confirmLoading={createMutation.isPending}>
        <Form form={form} layout="vertical" onFinish={(v) => createMutation.mutate(v)}>
          <Form.Item name="order_id" label="关联订单" rules={[{ required: true }]}><Select placeholder="选择订单" showSearch optionFilterProp="label" options={orderOptions} /></Form.Item>
          <Form.Item name="title" label="合同标题" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="contract_type" label="合同类型" initialValue="customer">
            <Select options={[{ label: '客户合同', value: 'customer' }, { label: '采购合同', value: 'procurement' }]} />
          </Form.Item>
          <Form.Item name="currency" label="币种" initialValue="CNY"><Select options={currencyOptions} /></Form.Item>
          <Form.Item name="total_amount" label="合同金额" rules={[{ required: true }]}><Input type="number" /></Form.Item>
          <Form.Item name="warranty_period" label="质保期(月)"><Input type="number" /></Form.Item>
        </Form>
      </Modal>
      <Modal title="合同评审" open={reviewOpen} onCancel={() => setReviewOpen(false)} onOk={() => reviewForm.submit()} width={600}>
        <Form form={reviewForm} layout="vertical" onFinish={handleReview}>
          <Form.Item name="delivery_review" label="交付条款评审"><Input.TextArea rows={2} /></Form.Item>
          <Form.Item name="payment_review" label="付款条款评审"><Input.TextArea rows={2} /></Form.Item>
          <Form.Item name="technical_review" label="技术条款评审"><Input.TextArea rows={2} /></Form.Item>
          <Form.Item name="penalty_review" label="违约条款评审"><Input.TextArea rows={2} /></Form.Item>
          <Form.Item name="warranty_review" label="质保条款评审"><Input.TextArea rows={2} /></Form.Item>
          <Form.Item name="conclusion" label="评审结论" rules={[{ required: true }]}>
            <Select options={[{ label: '通过', value: 'APPROVED' }, { label: '待修改', value: 'PENDING' }, { label: '驳回', value: 'REJECTED' }]} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
