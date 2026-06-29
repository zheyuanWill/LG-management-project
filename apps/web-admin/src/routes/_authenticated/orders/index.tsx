import { useState } from 'react'
import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { Table, Button, Form, Input, Select, Space, Modal, message, Tag, Popconfirm } from 'antd'
import { PlusOutlined, EyeOutlined, SearchOutlined, DeleteOutlined } from '@ant-design/icons'
import { usePageQuery, useApiPost, useApiQuery, useApiDelete } from '@lg/react-hooks'
import { http } from '@lg/api-client'
import { PageHeader, StatusBadge } from '@/components/common'
import { orderStatusOptions, projectTypeOptions, orderStatusColors, currencyOptions } from '@/constants'
import { useFormat } from '@/hooks/useFormat'
import type { Order, PageResponse } from '@lg/api-client'
import { orderStatusLabels, projectTypeLabels } from '@lg/core'
import { useQueryClient } from '@tanstack/react-query'
import type { ColumnsType } from 'antd/es/table'

export const Route = createFileRoute('/_authenticated/orders/')({
  component: OrdersPage,
})

function OrdersPage() {
  const navigate = useNavigate()
  const { fmtDate, fmtMoney, fmtStatus } = useFormat()
  const [searchParams, setSearchParams] = useState<Record<string, unknown>>({ page: 1, size: 20 })
  const queryClient = useQueryClient()
  const [createOpen, setCreateOpen] = useState(false)
  const [inquiryOpen, setInquiryOpen] = useState(false)
  const [inquiryLoading, setInquiryLoading] = useState(false)
  const [form] = Form.useForm()
  const [inquiryForm] = Form.useForm()

  const { data, isLoading } = usePageQuery<Order>(
    ['orders', searchParams],
    '/orders',
    searchParams,
  )

  const { data: customersData } = useApiQuery<PageResponse<{ id: number; name: string }>>(
    ['customers', 'all'], '/customers', { size: 100 },
  )

  const selectedCustomerId = Form.useWatch('customer_id', form)
  const { data: vesselsData } = useApiQuery<{ id: number; name: string }[]>(
    ['vessels', 'customer', selectedCustomerId],
    `/customers/${selectedCustomerId}/vessels`,
    {},
    { enabled: !!selectedCustomerId },
  )

  const createMutation = useApiPost<Order>('/orders', {
    invalidateKeys: [['orders']],
    onSuccess: () => {
      message.success('创建成功')
      setCreateOpen(false)
      form.resetFields()
    },
  })

  const deleteMutation = useApiDelete('/orders', {
    invalidateKeys: [['orders']],
    onSuccess: () => message.success('删除成功'),
  })

  const columns: ColumnsType<Order> = [
    { title: '订单编号', dataIndex: 'order_no', key: 'order_no', width: 160 },
    { title: '客户', dataIndex: 'customer_name', key: 'customer_name', width: 140 },
    { title: '船舶', dataIndex: 'vessel_name', key: 'vessel_name', width: 120 },
    {
      title: '项目类型', dataIndex: 'project_type', key: 'project_type', width: 110,
      render: (v: string) => projectTypeLabels[v] ?? v,
    },
    {
      title: '状态', dataIndex: 'status', key: 'status', width: 100,
      render: (v: string) => <StatusBadge label={fmtStatus(v, 'order')} colorMap={orderStatusColors} status={v} />,
    },
    {
      title: '金额', dataIndex: 'total_amount', key: 'total_amount', width: 130, align: 'right',
      render: (v: number, r: Order) => fmtMoney(v, r.currency),
    },
    { title: '项目经理', dataIndex: 'pm_name', key: 'pm_name', width: 100 },
    {
      title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 120,
      render: (v: string) => fmtDate(v),
    },
    {
      title: '操作', key: 'actions', width: 140, fixed: 'right',
      render: (_: unknown, record: Order) => (
        <Space size={0}>
          <Button type="link" icon={<EyeOutlined />} onClick={() => navigate({ to: '/orders/$id', params: { id: String(record.id) } })}>
            详情
          </Button>
          <Popconfirm
            title="确定要删除该订单吗？"
            onConfirm={() => deleteMutation.mutate(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  const handleSearch = (values: Record<string, unknown>) => {
    setSearchParams({ ...values, page: 1, size: 20 })
  }

  return (
    <div>
      <PageHeader
        title="订单管理"
        extra={
          <Space>
            <Button icon={<SearchOutlined />} onClick={() => setInquiryOpen(true)}>
              创建询价
            </Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>
              新建订单
            </Button>
          </Space>
        }
      />

      <Form layout="inline" onFinish={handleSearch} style={{ marginBottom: 16 }}>
        <Form.Item name="keyword">
          <Input placeholder="搜索订单号/客户" allowClear />
        </Form.Item>
        <Form.Item name="status">
          <Select placeholder="订单状态" options={orderStatusOptions} allowClear style={{ width: 140 }} />
        </Form.Item>
        <Form.Item name="project_type">
          <Select placeholder="项目类型" options={projectTypeOptions} allowClear style={{ width: 140 }} />
        </Form.Item>
        <Form.Item name="customer_id">
          <Select placeholder="客户" showSearch optionFilterProp="label" options={(customersData?.items ?? []).map((c) => ({ value: c.id, label: c.name }))} allowClear style={{ width: 160 }} />
        </Form.Item>
        <Form.Item>
          <Button type="primary" htmlType="submit">搜索</Button>
        </Form.Item>
      </Form>

      <Table<Order>
        rowKey="id"
        columns={columns}
        dataSource={data?.items}
        loading={isLoading}
        scroll={{ x: 1100 }}
        pagination={{
          current: data?.page,
          pageSize: data?.size,
          total: data?.total,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条`,
          onChange: (page, size) => setSearchParams((prev) => ({ ...prev, page, size })),
        }}
      />

      <Modal
        title="新建订单"
        open={createOpen}
        onCancel={() => setCreateOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={createMutation.isPending}
      >
        <Form form={form} layout="vertical" onFinish={(v) => createMutation.mutate(v)}>
          <Form.Item name="customer_id" label="客户" rules={[{ required: true, message: '请选择客户' }]}>
            <Select
              placeholder="选择客户"
              showSearch
              optionFilterProp="label"
              options={(customersData?.items ?? []).map((c) => ({ value: c.id, label: c.name }))}
            />
          </Form.Item>
          <Form.Item name="vessel_id" label="船舶">
            <Select
              placeholder="选择船舶（可选）"
              allowClear
              showSearch
              optionFilterProp="label"
              options={(Array.isArray(vesselsData) ? vesselsData : []).map((v) => ({ value: v.id, label: v.name }))}
            />
          </Form.Item>
          <Form.Item name="project_type" label="项目类型" rules={[{ required: true }]}>
            <Select options={projectTypeOptions} placeholder="选择项目类型" />
          </Form.Item>
          <Form.Item name="currency" label="币种" initialValue="CNY">
            <Select options={currencyOptions} />
          </Form.Item>
          <Form.Item name="notes" label="备注">
            <Input.TextArea rows={3} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="创建询价单"
        open={inquiryOpen}
        onCancel={() => setInquiryOpen(false)}
        onOk={() => inquiryForm.submit()}
        confirmLoading={inquiryLoading}
      >
        <Form form={inquiryForm} layout="vertical" onFinish={async (v) => {
          setInquiryLoading(true)
          try {
            await http.post('/orders/inquiry', v)
            message.success('询价单已创建')
            setInquiryOpen(false)
            inquiryForm.resetFields()
            queryClient.invalidateQueries({ queryKey: ['orders'] })
          } catch (e) {
            message.error(e instanceof Error ? e.message : '创建失败')
          } finally {
            setInquiryLoading(false)
          }
        }}>
          <Form.Item name="customer_id" label="客户" rules={[{ required: true }]}>
            <Select placeholder="选择客户" showSearch optionFilterProp="label" options={(customersData?.items ?? []).map((c) => ({ value: c.id, label: c.name }))} />
          </Form.Item>
          <Form.Item name="vessel_id" label="船舶">
            <Select placeholder="选择船舶" allowClear showSearch optionFilterProp="label" options={(Array.isArray(vesselsData) ? vesselsData : []).map((v) => ({ value: v.id, label: v.name }))} />
          </Form.Item>
          <Form.Item name="project_type" label="项目类型" rules={[{ required: true }]}>
            <Select options={projectTypeOptions} placeholder="选择项目类型" />
          </Form.Item>
          <Form.Item name="currency" label="币种" initialValue="CNY">
            <Select options={currencyOptions} />
          </Form.Item>
          <Form.Item name="inquiry_source" label="询价来源">
            <Select options={[{ label: '邮件', value: 'EMAIL' }, { label: '电话', value: 'PHONE' }, { label: '传真', value: 'FAX' }, { label: '网站', value: 'WEB' }]} allowClear />
          </Form.Item>
          <Form.Item name="notes" label="备注">
            <Input.TextArea rows={3} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
