import { useState } from 'react'
import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { Table, Button, Form, Input, Select, Modal, message, Tag, Popconfirm, Space } from 'antd'
import { PlusOutlined, CheckOutlined, CloseOutlined, DeleteOutlined } from '@ant-design/icons'
import { usePageQuery, useApiPost, useApiQuery, useApiDelete } from '@lg/react-hooks'
import { PageHeader, StatusBadge } from '@/components/common'
import { procurementStatusOptions, procurementStatusColors, currencyOptions } from '@/constants'
import { useFormat } from '@/hooks/useFormat'
import { procurementStatusLabels } from '@lg/core'
import type { Procurement, PageResponse } from '@lg/api-client'
import { http } from '@lg/api-client'
import { useQueryClient } from '@tanstack/react-query'

export const Route = createFileRoute('/_authenticated/procurement')({
  component: ProcurementPage,
})

function ProcurementPage() {
  const navigate = useNavigate()
  const { fmtDate, fmtMoney, fmtStatus } = useFormat()
  const [params, setParams] = useState<Record<string, unknown>>({ page: 1, size: 20 })
  const [createOpen, setCreateOpen] = useState(false)
  const [form] = Form.useForm()
  const queryClient = useQueryClient()

  const { data, isLoading } = usePageQuery<Procurement>(['procurements', params], '/procurements', params)

  const { data: ordersData } = useApiQuery<PageResponse<{ id: number; order_no: string; customer_name?: string }>>(
    ['orders', 'select'], '/orders', { size: 200 },
  )
  const orderOptions = (ordersData?.items ?? []).map((o) => ({
    value: o.id, label: `${o.order_no}${o.customer_name ? ` - ${o.customer_name}` : ''}`,
  }))

  const { data: suppliersData } = useApiQuery<PageResponse<{ id: number; name: string }>>(
    ['suppliers', 'select'], '/suppliers', { size: 200 },
  )
  const supplierOptions = (suppliersData?.items ?? []).map((s) => ({
    value: s.id, label: s.name,
  }))

  const createMutation = useApiPost<Procurement>('/procurements', {
    invalidateKeys: [['procurements']],
    onSuccess: () => { message.success('创建成功'); setCreateOpen(false); form.resetFields() },
  })

  const deleteMutation = useApiDelete('/procurements', {
    invalidateKeys: [['procurements']],
    onSuccess: () => message.success('删除成功'),
  })

  const handleApprove = async (id: number, approved: boolean) => {
    try {
      await http.post(`/procurements/${id}/approve`, { approved })
      message.success(approved ? '审批通过' : '已驳回')
      queryClient.invalidateQueries({ queryKey: ['procurements'] })
    } catch (e) { message.error(e instanceof Error ? e.message : '操作失败') }
  }

  const columns = [
    { title: '采购编号', dataIndex: 'procurement_no', key: 'procurement_no', width: 160 },
    { title: '供应商', dataIndex: 'supplier_name', key: 'supplier_name', width: 140 },
    { title: '关联订单', dataIndex: 'order_no', key: 'order_no', width: 140 },
    { title: '状态', dataIndex: 'status', key: 'status', width: 110, render: (v: string) => <StatusBadge label={fmtStatus(v, 'procurement')} colorMap={procurementStatusColors} status={v} /> },
    { title: '金额', dataIndex: 'total_amount', key: 'total_amount', width: 130, align: 'right' as const, render: (v: number, r: Procurement) => fmtMoney(v, r.currency) },
    { title: '期望交付', dataIndex: 'expected_date', key: 'expected_date', width: 120, render: (v: string) => fmtDate(v) },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 120, render: (v: string) => fmtDate(v) },
    {
      title: '操作', key: 'actions', width: 220, fixed: 'right' as const,
      render: (_: unknown, r: Procurement) => (
        <Space size={0}>
          <Button type="link" size="small" onClick={() => navigate({ to: `/procurement/${r.id}` as any })}>详情</Button>
          {r.status === 'PENDING_APPROVAL' && (
            <>
              <Popconfirm title="确认审批通过?" onConfirm={() => handleApprove(r.id, true)}><Button type="link" size="small" icon={<CheckOutlined />}>通过</Button></Popconfirm>
              <Popconfirm title="确认驳回?" onConfirm={() => handleApprove(r.id, false)}><Button type="link" size="small" danger icon={<CloseOutlined />}>驳回</Button></Popconfirm>
            </>
          )}
          <Popconfirm
            title="确定要删除该采购单吗？"
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
      <PageHeader title="采购管理" extra={<Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>新建采购</Button>} />
      <Form layout="inline" onFinish={(v) => setParams({ ...v, page: 1, size: 20 })} style={{ marginBottom: 16 }}>
        <Form.Item name="keyword"><Input placeholder="搜索采购号" allowClear /></Form.Item>
        <Form.Item name="status"><Select placeholder="状态" options={procurementStatusOptions} allowClear style={{ width: 140 }} /></Form.Item>
        <Form.Item name="supplier_id"><Select placeholder="供应商" showSearch optionFilterProp="label" options={supplierOptions} allowClear style={{ width: 160 }} /></Form.Item>
        <Form.Item><Button type="primary" htmlType="submit">搜索</Button></Form.Item>
      </Form>
      <Table rowKey="id" columns={columns} dataSource={data?.items} loading={isLoading} scroll={{ x: 1100 }} pagination={{ current: data?.page, pageSize: data?.size, total: data?.total, showTotal: (t) => `共 ${t} 条`, onChange: (p, s) => setParams((prev) => ({ ...prev, page: p, size: s })) }} />
      <Modal title="新建采购单" open={createOpen} onCancel={() => setCreateOpen(false)} onOk={() => form.submit()} confirmLoading={createMutation.isPending}>
        <Form form={form} layout="vertical" onFinish={(v) => createMutation.mutate(v)}>
          <Form.Item name="supplier_id" label="供应商" rules={[{ required: true }]}><Select placeholder="选择供应商" showSearch optionFilterProp="label" options={supplierOptions} /></Form.Item>
          <Form.Item name="order_id" label="关联订单"><Select placeholder="选择订单（可选）" showSearch optionFilterProp="label" options={orderOptions} allowClear /></Form.Item>
          <Form.Item name="currency" label="币种" initialValue="CNY"><Select options={currencyOptions} /></Form.Item>
          <Form.Item name="expected_date" label="期望交付日期"><Input type="date" /></Form.Item>
          <Form.Item name="notes" label="备注"><Input.TextArea rows={3} /></Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
