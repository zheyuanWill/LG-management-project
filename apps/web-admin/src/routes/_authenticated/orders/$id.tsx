import { useState, useMemo } from 'react'
import { createFileRoute, useNavigate } from '@tanstack/react-router'
import {
  Descriptions, Card, Table, Button, Space, Spin, Row, Col, Modal, Tabs,
  Form, Input, InputNumber, Popconfirm, App, Tag, Rate, Select, DatePicker,
} from 'antd'
import { ArrowLeftOutlined, PlusOutlined, DeleteOutlined } from '@ant-design/icons'
import { useApiQuery } from '@lg/react-hooks'
import { http } from '@lg/api-client'
import { PageHeader, StatusBadge } from '@/components/common'
import { OrderLifecycle } from '@/components/orders/OrderLifecycle'
import { orderStatusColors } from '@/constants'
import { useFormat } from '@/hooks/useFormat'
import { orderStatusLabels, projectTypeLabels } from '@lg/core'
import { useQueryClient, useQuery, useMutation } from '@tanstack/react-query'
import type { Order, OrderLineItem, PageResponse } from '@lg/api-client'

export const Route = createFileRoute('/_authenticated/orders/$id')({
  component: OrderDetailPage,
})

const NEXT_STATUS: Record<string, { value: string; label: string; danger?: boolean }[]> = {
  DRAFT: [{ value: 'IN_PROGRESS', label: '开始执行' }],
  IN_PROGRESS: [
    { value: 'COMPLETED', label: '标记完成' },
    { value: 'CANCELLED', label: '取消订单', danger: true },
  ],
}

function OrderDetailPage() {
  const { id } = Route.useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { fmtDate, fmtMoney, fmtStatus } = useFormat()
  const { message } = App.useApp()

  const [addItemOpen, setAddItemOpen] = useState(false)
  const [addItemLoading, setAddItemLoading] = useState(false)
  const [cancelOpen, setCancelOpen] = useState(false)
  const [cancelForm] = Form.useForm()
  const [itemForm] = Form.useForm()

  const { data: order, isLoading } = useApiQuery<Order>(
    ['orders', id], `/orders/${id}`,
  )

  const { data: quoteData } = useApiQuery<PageResponse<any>>(
    ['quotes', 'order', id], `/quotes`, { order_id: id, size: 1 },
  )

  const { data: procurementData } = useApiQuery<PageResponse<any>>(
    ['procurements', 'order', id], `/procurements`, { order_id: id, size: 1 },
  )

  if (isLoading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />
  if (!order) return <div>订单不存在</div>

  const refresh = () => queryClient.invalidateQueries({ queryKey: ['orders', id] })

  const handleStatusChange = async (newStatus: string) => {
    if (newStatus === 'CANCELLED') {
      setCancelOpen(true)
      return
    }
    try {
      await http.put(`/orders/${order.id}/status`, { status: newStatus })
      message.success('状态已更新')
      refresh()
    } catch (e) {
      message.error(e instanceof Error ? e.message : '操作失败')
    }
  }

  const handleCancel = async (values: any) => {
    try {
      await http.put(`/orders/${order.id}/status`, {
        status: 'CANCELLED',
        cancellation_reason: values.cancellation_reason,
        cancellation_category: values.cancellation_category,
      })
      message.success('订单已取消')
      setCancelOpen(false)
      cancelForm.resetFields()
      refresh()
    } catch (e) {
      message.error(e instanceof Error ? e.message : '操作失败')
    }
  }

  const handleAddItem = async (values: any) => {
    setAddItemLoading(true)
    try {
      await http.post(`/orders/${order.id}/line-items`, values)
      message.success('明细已添加')
      itemForm.resetFields()
      setAddItemOpen(false)
      refresh()
    } catch (e) {
      message.error(e instanceof Error ? e.message : '添加失败')
    } finally {
      setAddItemLoading(false)
    }
  }

  const handleDeleteItem = async (itemId: number) => {
    try {
      await http.delete(`/orders/${order.id}/line-items/${itemId}`)
      message.success('已删除')
      refresh()
    } catch (e) {
      message.error(e instanceof Error ? e.message : '删除失败')
    }
  }

  const lineItemColumns = [
    { title: '产品', dataIndex: 'product_name', key: 'product_name' },
    { title: '规格', dataIndex: 'specification', key: 'specification' },
    { title: '单位', dataIndex: 'unit', key: 'unit', width: 60 },
    { title: '数量', dataIndex: 'quantity', key: 'quantity', width: 80, align: 'right' as const },
    { title: '单价', dataIndex: 'unit_price', key: 'unit_price', width: 100, align: 'right' as const, render: (v: number) => fmtMoney(v, order.currency) },
    { title: '金额', dataIndex: 'amount', key: 'amount', width: 120, align: 'right' as const, render: (v: number) => fmtMoney(v, order.currency) },
    { title: '备注', dataIndex: 'notes', key: 'notes' },
    ...(order.status === 'DRAFT' ? [{
      title: '操作', key: 'actions', width: 60,
      render: (_: unknown, r: OrderLineItem) => (
        <Popconfirm title="确认删除?" onConfirm={() => handleDeleteItem(r.id)}>
          <Button type="link" danger size="small" icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    }] : []),
  ]

  const statusActions = NEXT_STATUS[order.status] ?? []

  return (
    <div>
      <PageHeader
        title={`订单详情 - ${order.order_no}`}
        extra={
          <Space>
            <Button icon={<ArrowLeftOutlined />} onClick={() => navigate({ to: '/orders' })}>
              返回列表
            </Button>
            {statusActions.map((action) => (
              <Popconfirm key={action.value} title={`确认${action.label}？`} onConfirm={() => handleStatusChange(action.value)}>
                <Button type={action.danger ? 'default' : 'primary'} danger={action.danger}>
                  {action.label}
                </Button>
              </Popconfirm>
            ))}
          </Space>
        }
      />

      <OrderLifecycle
        order={order}
        quoteCount={quoteData?.total ?? 0}
        procurementCount={procurementData?.total ?? 0}
      />

      <Row gutter={16}>
        <Col xs={24} lg={16}>
          <Card>
            <Descriptions bordered column={{ xs: 1, sm: 2, lg: 3 }}>
              <Descriptions.Item label="订单编号">{order.order_no}</Descriptions.Item>
              <Descriptions.Item label="询价单号">{(order as any).inquiry_no ?? '-'}</Descriptions.Item>
              <Descriptions.Item label="项目编码">{(order as any).project_code ? <Tag color="blue">{(order as any).project_code}</Tag> : '-'}</Descriptions.Item>
              <Descriptions.Item label="客户">{order.customer_name}</Descriptions.Item>
              <Descriptions.Item label="船舶">{order.vessel_name ?? '-'}</Descriptions.Item>
              <Descriptions.Item label="项目类型">{projectTypeLabels[order.project_type] ?? order.project_type}</Descriptions.Item>
              <Descriptions.Item label="状态">
                <StatusBadge label={fmtStatus(order.status, 'order')} colorMap={orderStatusColors} status={order.status} />
              </Descriptions.Item>
              <Descriptions.Item label="币种">{order.currency}</Descriptions.Item>
              <Descriptions.Item label="总金额">{fmtMoney(order.total_amount, order.currency)}</Descriptions.Item>
              <Descriptions.Item label="项目经理">{order.pm_name ?? '-'}</Descriptions.Item>
              <Descriptions.Item label="交付日期">{fmtDate(order.delivery_date)}</Descriptions.Item>
              <Descriptions.Item label="创建时间">{fmtDate(order.created_at)}</Descriptions.Item>
              <Descriptions.Item label="更新时间">{fmtDate(order.updated_at)}</Descriptions.Item>
              {order.status === 'CANCELLED' && (order as any).cancellation_reason && (
                <Descriptions.Item label="取消原因" span={3}>{(order as any).cancellation_reason}</Descriptions.Item>
              )}
              <Descriptions.Item label="备注" span={3}>{order.notes ?? '-'}</Descriptions.Item>
            </Descriptions>
          </Card>

          <Card
            title="订单明细"
            style={{ marginTop: 16 }}
            extra={
              order.status === 'DRAFT' && (
                <Button type="primary" icon={<PlusOutlined />} size="small" onClick={() => setAddItemOpen(true)}>
                  添加明细
                </Button>
              )
            }
          >
            {order.line_items && order.line_items.length > 0 ? (
              <Table<OrderLineItem>
                rowKey="id"
                columns={lineItemColumns}
                dataSource={order.line_items}
                pagination={false}
                summary={(data) => {
                  const total = data.reduce((sum, item) => sum + item.amount, 0)
                  return (
                    <Table.Summary.Row>
                      <Table.Summary.Cell index={0} colSpan={5} align="right"><strong>合计</strong></Table.Summary.Cell>
                      <Table.Summary.Cell index={5} align="right"><strong>{fmtMoney(total, order.currency)}</strong></Table.Summary.Cell>
                      <Table.Summary.Cell index={6} />
                      {order.status === 'DRAFT' && <Table.Summary.Cell index={7} />}
                    </Table.Summary.Row>
                  )
                }}
              />
            ) : (
              <div style={{ textAlign: 'center', padding: '24px 0', color: '#999' }}>
                暂无明细
                {order.status === 'DRAFT' && (
                  <>，<Button type="link" onClick={() => setAddItemOpen(true)}>点击添加</Button></>
                )}
              </div>
            )}
          </Card>

        </Col>

        <Col xs={24} lg={8}>
          <Card title="快捷操作">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Button block onClick={() => navigate({ to: '/quotes', search: { order_id: order.id } as any })}>
                查看报价 ({quoteData?.total ?? 0})
              </Button>
              <Button block onClick={() => navigate({ to: '/quotes/excel' })}>
                生成报价Excel
              </Button>
              <Button block onClick={() => navigate({ to: '/procurement', search: { order_id: order.id } as any })}>
                采购管理 ({procurementData?.total ?? 0})
              </Button>
            </Space>
          </Card>
        </Col>
      </Row>

      {/* ISO 9001 Process Tabs */}
      <Card style={{ marginTop: 16 }}>
        <Tabs defaultActiveKey="risk" items={[
          {
            key: 'risk',
            label: '风险评估',
            children: <RiskAssessmentTab orderId={order.id} />,
          },
          {
            key: 'inquiry-records',
            label: '对外询价',
            children: <InquiryRecordTab orderId={order.id} />,
          },
          {
            key: 'comparison',
            label: '比价分析',
            children: <ComparisonTab orderId={order.id} />,
          },
          {
            key: 'changes',
            label: '项目变更',
            children: <ProjectChangeTab orderId={order.id} />,
          },
          {
            key: 'acceptance',
            label: '项目验收',
            children: <AcceptanceTab orderId={order.id} />,
          },
          {
            key: 'closure',
            label: '项目关闭',
            children: <ClosureTab orderId={order.id} />,
          },
          {
            key: 'collection',
            label: '催收记录',
            children: <CollectionRecordTab orderId={order.id} />,
          },
          {
            key: 'changelog',
            label: '变更日志',
            children: <ChangeLogTab orderId={order.id} />,
          },
        ]} />
      </Card>

      <Modal
        title="添加订单明细"
        open={addItemOpen}
        onCancel={() => setAddItemOpen(false)}
        onOk={() => itemForm.submit()}
        confirmLoading={addItemLoading}
      >
        <Form form={itemForm} layout="vertical" onFinish={handleAddItem}>
          <Form.Item name="product_name" label="产品名称" rules={[{ required: true }]}>
            <Input placeholder="如：船用柴油滤芯" />
          </Form.Item>
          <Form.Item name="specification" label="规格型号">
            <Input placeholder="如：DN50-PN16" />
          </Form.Item>
          <Row gutter={12}>
            <Col span={8}>
              <Form.Item name="unit" label="单位" rules={[{ required: true }]} initialValue="个">
                <Input />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="quantity" label="数量" rules={[{ required: true }]}>
                <InputNumber min={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="unit_price" label="单价" rules={[{ required: true }]}>
                <InputNumber min={0} step={0.01} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="notes" label="备注">
            <Input.TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal title="取消订单" open={cancelOpen} onCancel={() => setCancelOpen(false)} onOk={() => cancelForm.submit()}>
        <Form form={cancelForm} layout="vertical" onFinish={handleCancel}>
          <Form.Item name="cancellation_category" label="取消类别" rules={[{ required: true }]}>
            <Select options={[
              { label: '价格原因', value: 'PRICE' },
              { label: '交期原因', value: 'DELIVERY' },
              { label: '需求变更', value: 'REQUIREMENT_CHANGE' },
              { label: '竞争对手', value: 'COMPETITOR' },
              { label: '其它', value: 'OTHER' },
            ]} />
          </Form.Item>
          <Form.Item name="cancellation_reason" label="取消原因" rules={[{ required: true }]}>
            <Input.TextArea rows={3} placeholder="请详细说明取消原因，用于季度/年度分析" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}


/* ============ ISO Process Sub-Components ============ */

function RiskAssessmentTab({ orderId }: { orderId: number }) {
  const { message } = App.useApp()
  const [form] = Form.useForm()
  const [open, setOpen] = useState(false)
  const queryClient = useQueryClient()

  const { data } = useQuery({
    queryKey: ['risk-assessments', orderId],
    queryFn: () => http.get<any>('/iso/risk-assessments', { order_id: orderId }),
  })

  const create = useMutation({
    mutationFn: (values: any) => http.post('/iso/risk-assessments', { order_id: orderId, ...values }),
    onSuccess: () => { message.success('已创建'); setOpen(false); form.resetFields(); queryClient.invalidateQueries({ queryKey: ['risk-assessments', orderId] }) },
  })

  const approve = async (id: number, approved: boolean) => {
    await http.post(`/iso/risk-assessments/${id}/approve`, { approved })
    message.success(approved ? '已批准' : '已驳回')
    queryClient.invalidateQueries({ queryKey: ['risk-assessments', orderId] })
  }

  const columns = [
    { title: '客户信用', dataIndex: 'customer_credit', width: 100 },
    { title: '可行性', dataIndex: 'project_feasibility', width: 100 },
    { title: '付款风险', dataIndex: 'payment_risk', width: 100 },
    { title: '整体风险', dataIndex: 'overall_risk', width: 100, render: (v: string) => <Tag color={v === 'HIGH' ? 'red' : v === 'MEDIUM' ? 'orange' : 'green'}>{v}</Tag> },
    { title: '状态', dataIndex: 'status', width: 80, render: (v: string) => <Tag color={v === 'APPROVED' ? 'green' : v === 'REJECTED' ? 'red' : 'blue'}>{v}</Tag> },
    { title: '操作', key: 'act', width: 150, render: (_: any, r: any) => r.status === 'PENDING' && (
      <Space><Button size="small" type="primary" onClick={() => approve(r.id, true)}>批准</Button><Button size="small" danger onClick={() => approve(r.id, false)}>驳回</Button></Space>
    ) },
  ]

  return (
    <>
      <Button type="primary" size="small" icon={<PlusOutlined />} onClick={() => setOpen(true)} style={{ marginBottom: 12 }}>新增风险评估</Button>
      <Table rowKey="id" columns={columns} dataSource={data?.items ?? []} size="small" pagination={false} />
      <Modal title="新增风险评估" open={open} onCancel={() => setOpen(false)} onOk={() => form.submit()} confirmLoading={create.isPending}>
        <Form form={form} layout="vertical" onFinish={(v) => create.mutate(v)}>
          <Form.Item name="customer_credit" label="客户信用"><Input /></Form.Item>
          <Form.Item name="project_feasibility" label="项目可行性"><Input /></Form.Item>
          <Form.Item name="payment_risk" label="付款风险"><Input /></Form.Item>
          <Form.Item name="overall_risk" label="整体风险" rules={[{ required: true }]}>
            <Select options={[{ label: '低', value: 'LOW' }, { label: '中', value: 'MEDIUM' }, { label: '高', value: 'HIGH' }]} />
          </Form.Item>
          <Form.Item name="assessment_notes" label="备注"><Input.TextArea rows={2} /></Form.Item>
        </Form>
      </Modal>
    </>
  )
}

function InquiryRecordTab({ orderId }: { orderId: number }) {
  const { message } = App.useApp()
  const [form] = Form.useForm()
  const [open, setOpen] = useState(false)
  const queryClient = useQueryClient()

  const { data } = useQuery({
    queryKey: ['inquiry-records', orderId],
    queryFn: () => http.get<any>('/iso/inquiry-records', { order_id: orderId }),
  })

  const create = useMutation({
    mutationFn: (values: any) => http.post('/iso/inquiry-records', { order_id: orderId, ...values }),
    onSuccess: () => { message.success('已创建'); setOpen(false); form.resetFields(); queryClient.invalidateQueries({ queryKey: ['inquiry-records', orderId] }) },
  })

  const markResponded = async (id: number) => {
    await http.put(`/iso/inquiry-records/${id}`, { responded: true, response_time: new Date().toISOString() })
    message.success('已标记响应')
    queryClient.invalidateQueries({ queryKey: ['inquiry-records', orderId] })
  }

  const columns = [
    { title: '供应商ID', dataIndex: 'supplier_id', width: 80 },
    { title: '询价方式', dataIndex: 'inquiry_method', width: 80 },
    { title: '询价时间', dataIndex: 'inquiry_time', width: 150 },
    { title: '截止时间', dataIndex: 'deadline', width: 150 },
    { title: '已响应', dataIndex: 'responded', width: 80, render: (v: boolean) => v ? <Tag color="green">是</Tag> : <Tag color="red">否</Tag> },
    { title: '备注', dataIndex: 'notes' },
    { title: '操作', key: 'act', width: 100, render: (_: any, r: any) => !r.responded && <Button size="small" onClick={() => markResponded(r.id)}>标记响应</Button> },
  ]

  return (
    <>
      <Button type="primary" size="small" icon={<PlusOutlined />} onClick={() => setOpen(true)} style={{ marginBottom: 12 }}>新增询价记录</Button>
      <Table rowKey="id" columns={columns} dataSource={data?.items ?? []} size="small" pagination={false} />
      <Modal title="新增询价记录" open={open} onCancel={() => setOpen(false)} onOk={() => form.submit()} confirmLoading={create.isPending}>
        <Form form={form} layout="vertical" onFinish={(v) => create.mutate(v)}>
          <Form.Item name="supplier_id" label="供应商ID" rules={[{ required: true }]}><InputNumber style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="inquiry_method" label="询价方式" initialValue="EMAIL">
            <Select options={[{ label: '邮件', value: 'EMAIL' }, { label: '电话', value: 'PHONE' }, { label: '传真', value: 'FAX' }]} />
          </Form.Item>
          <Form.Item name="notes" label="备注"><Input.TextArea rows={2} /></Form.Item>
        </Form>
      </Modal>
    </>
  )
}

function ComparisonTab({ orderId }: { orderId: number }) {
  const { message } = App.useApp()
  const [form] = Form.useForm()
  const [open, setOpen] = useState(false)
  const queryClient = useQueryClient()

  const { data } = useQuery({
    queryKey: ['supplier-comparisons', orderId],
    queryFn: () => http.get<any>('/iso/supplier-comparisons', { order_id: orderId }),
  })

  const create = useMutation({
    mutationFn: (values: any) => http.post('/iso/supplier-comparisons', { order_id: orderId, ...values }),
    onSuccess: () => { message.success('已创建'); setOpen(false); form.resetFields(); queryClient.invalidateQueries({ queryKey: ['supplier-comparisons', orderId] }) },
  })

  const columns = [
    { title: '标题', dataIndex: 'title' },
    { title: '选定供应商', dataIndex: 'selected_supplier_id', width: 120 },
    { title: '选择理由', dataIndex: 'selection_reason' },
    { title: '比价数据', dataIndex: 'comparison_data', render: (v: any) => v ? <Tag color="blue">{Object.keys(v).length} 家供应商</Tag> : '-' },
    { title: '创建时间', dataIndex: 'created_at', width: 150 },
  ]

  return (
    <>
      <Space style={{ marginBottom: 12 }}>
        <Button type="primary" size="small" icon={<PlusOutlined />} onClick={() => setOpen(true)}>新增比价（自动拉取报价）</Button>
      </Space>
      <Table rowKey="id" columns={columns} dataSource={data?.items ?? []} size="small" pagination={false} />
      <Modal title="新增比价分析" open={open} onCancel={() => setOpen(false)} onOk={() => form.submit()} confirmLoading={create.isPending}>
        <Form form={form} layout="vertical" onFinish={(v) => create.mutate(v)}>
          <Form.Item name="title" label="标题"><Input /></Form.Item>
          <Form.Item name="selected_supplier_id" label="选定供应商ID"><InputNumber style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="selection_reason" label="选择理由"><Input.TextArea rows={2} /></Form.Item>
        </Form>
      </Modal>
    </>
  )
}

function ProjectChangeTab({ orderId }: { orderId: number }) {
  const { message } = App.useApp()
  const [form] = Form.useForm()
  const [open, setOpen] = useState(false)
  const queryClient = useQueryClient()

  const { data } = useQuery({
    queryKey: ['project-changes', orderId],
    queryFn: () => http.get<any>('/iso/project-changes', { order_id: orderId }),
  })

  const create = useMutation({
    mutationFn: (values: any) => http.post('/iso/project-changes', { order_id: orderId, ...values }),
    onSuccess: () => { message.success('已创建'); setOpen(false); form.resetFields(); queryClient.invalidateQueries({ queryKey: ['project-changes', orderId] }) },
  })

  const confirm = async (id: number) => {
    await http.post(`/iso/project-changes/${id}/confirm`, { customer_confirmation: true, confirmation_date: new Date().toISOString().slice(0, 10) })
    message.success('已确认')
    queryClient.invalidateQueries({ queryKey: ['project-changes', orderId] })
  }

  const columns = [
    { title: '变更号', dataIndex: 'change_no', width: 120 },
    { title: '变更类型', dataIndex: 'change_type', width: 100 },
    { title: '描述', dataIndex: 'description' },
    { title: '影响分析', dataIndex: 'impact_analysis' },
    { title: '客户确认', dataIndex: 'customer_confirmation', width: 80, render: (v: boolean) => v ? <Tag color="green">已确认</Tag> : <Tag>待确认</Tag> },
    { title: '状态', dataIndex: 'status', width: 80, render: (v: string) => <Tag color={v === 'APPROVED' ? 'green' : v === 'REJECTED' ? 'red' : 'blue'}>{v}</Tag> },
    { title: '操作', key: 'act', width: 100, render: (_: any, r: any) => r.status === 'PENDING' && <Button size="small" onClick={() => confirm(r.id)}>客户确认</Button> },
  ]

  return (
    <>
      <Button type="primary" size="small" icon={<PlusOutlined />} onClick={() => setOpen(true)} style={{ marginBottom: 12 }}>新增变更</Button>
      <Table rowKey="id" columns={columns} dataSource={data?.items ?? []} size="small" pagination={false} />
      <Modal title="新增项目变更" open={open} onCancel={() => setOpen(false)} onOk={() => form.submit()} confirmLoading={create.isPending}>
        <Form form={form} layout="vertical" onFinish={(v) => create.mutate(v)}>
          <Form.Item name="change_type" label="变更类型" rules={[{ required: true }]}>
            <Select options={[{ label: '规格变更', value: 'SPEC' }, { label: '数量变更', value: 'QTY' }, { label: '交期变更', value: 'DELIVERY' }, { label: '其它', value: 'OTHER' }]} />
          </Form.Item>
          <Form.Item name="description" label="描述" rules={[{ required: true }]}><Input.TextArea rows={3} /></Form.Item>
          <Form.Item name="impact_analysis" label="影响分析"><Input.TextArea rows={2} /></Form.Item>
        </Form>
      </Modal>
    </>
  )
}

function AcceptanceTab({ orderId }: { orderId: number }) {
  const { message } = App.useApp()
  const [form] = Form.useForm()
  const [open, setOpen] = useState(false)
  const queryClient = useQueryClient()

  const { data } = useQuery({
    queryKey: ['project-acceptances', orderId],
    queryFn: () => http.get<any>('/iso/project-acceptances', { order_id: orderId }),
  })

  const create = useMutation({
    mutationFn: (values: any) => http.post('/iso/project-acceptances', { order_id: orderId, ...values }),
    onSuccess: () => { message.success('已创建'); setOpen(false); form.resetFields(); queryClient.invalidateQueries({ queryKey: ['project-acceptances', orderId] }) },
  })

  const confirmAcceptance = async (id: number) => {
    await http.post(`/iso/project-acceptances/${id}/confirm`, { customer_confirmed: true, confirmation_method: 'EMAIL', confirmation_date: new Date().toISOString().slice(0, 10) })
    message.success('客户已确认验收')
    queryClient.invalidateQueries({ queryKey: ['project-acceptances', orderId] })
  }

  const columns = [
    { title: '验收号', dataIndex: 'acceptance_no', width: 120 },
    { title: '验收类型', dataIndex: 'acceptance_type', width: 100 },
    { title: '验收日期', dataIndex: 'acceptance_date', width: 120 },
    { title: '客户确认', dataIndex: 'customer_confirmed', width: 80, render: (v: boolean) => v ? <Tag color="green">已确认</Tag> : <Tag>待确认</Tag> },
    { title: '备注', dataIndex: 'notes' },
    { title: '操作', key: 'act', width: 100, render: (_: any, r: any) => !r.customer_confirmed && <Button size="small" onClick={() => confirmAcceptance(r.id)}>客户确认</Button> },
  ]

  return (
    <>
      <Button type="primary" size="small" icon={<PlusOutlined />} onClick={() => setOpen(true)} style={{ marginBottom: 12 }}>新增验收</Button>
      <Table rowKey="id" columns={columns} dataSource={data?.items ?? []} size="small" pagination={false} />
      <Modal title="新增项目验收" open={open} onCancel={() => setOpen(false)} onOk={() => form.submit()} confirmLoading={create.isPending}>
        <Form form={form} layout="vertical" onFinish={(v) => create.mutate(v)}>
          <Form.Item name="acceptance_type" label="验收类型" rules={[{ required: true }]}>
            <Select options={[{ label: '初步验收', value: 'PRELIMINARY' }, { label: '最终验收', value: 'FINAL' }]} />
          </Form.Item>
          <Form.Item name="notes" label="备注"><Input.TextArea rows={2} /></Form.Item>
        </Form>
      </Modal>
    </>
  )
}

function ClosureTab({ orderId }: { orderId: number }) {
  const { message } = App.useApp()
  const [form] = Form.useForm()
  const [open, setOpen] = useState(false)
  const queryClient = useQueryClient()

  const { data } = useQuery({
    queryKey: ['project-closures', orderId],
    queryFn: () => http.get<any>('/iso/project-closures', { order_id: orderId }),
  })

  const create = useMutation({
    mutationFn: (values: any) => http.post('/iso/project-closures', { order_id: orderId, ...values }),
    onSuccess: () => { message.success('已创建'); setOpen(false); form.resetFields(); queryClient.invalidateQueries({ queryKey: ['project-closures', orderId] }) },
  })

  const submit = async (id: number) => {
    await http.post(`/iso/project-closures/${id}/submit`)
    message.success('已提交审批')
    queryClient.invalidateQueries({ queryKey: ['project-closures', orderId] })
  }

  const columns = [
    { title: '关闭编号', dataIndex: 'closure_no', width: 120 },
    { title: '状态', dataIndex: 'status', width: 80, render: (v: string) => <Tag color={v === 'CLOSED' ? 'green' : v === 'PENDING' ? 'orange' : 'blue'}>{v}</Tag> },
    { title: '回款结清', dataIndex: 'all_payments_settled', width: 80, render: (v: boolean) => v ? <Tag color="green">是</Tag> : <Tag>否</Tag> },
    { title: '应收回收', dataIndex: 'all_receivables_collected', width: 80, render: (v: boolean) => v ? <Tag color="green">是</Tag> : <Tag>否</Tag> },
    { title: '档案归档', dataIndex: 'documents_archived', width: 80, render: (v: boolean) => v ? <Tag color="green">是</Tag> : <Tag>否</Tag> },
    { title: '经验教训', dataIndex: 'lessons_learned', ellipsis: true },
    { title: '操作', key: 'act', width: 100, render: (_: any, r: any) => r.status === 'DRAFT' && <Button size="small" type="primary" onClick={() => submit(r.id)}>提交审批</Button> },
  ]

  return (
    <>
      <Button type="primary" size="small" icon={<PlusOutlined />} onClick={() => setOpen(true)} style={{ marginBottom: 12 }}>新增关闭申请</Button>
      <Table rowKey="id" columns={columns} dataSource={data?.items ?? []} size="small" pagination={false} />
      <Modal title="项目关闭申请" open={open} onCancel={() => setOpen(false)} onOk={() => form.submit()} confirmLoading={create.isPending}>
        <Form form={form} layout="vertical" onFinish={(v) => create.mutate(v)}>
          <Form.Item name="lessons_learned" label="经验教训"><Input.TextArea rows={3} /></Form.Item>
          <Form.Item name="improvement_suggestions" label="改进建议"><Input.TextArea rows={3} /></Form.Item>
        </Form>
      </Modal>
    </>
  )
}

function CollectionRecordTab({ orderId }: { orderId: number }) {
  const { message } = App.useApp()
  const [form] = Form.useForm()
  const [open, setOpen] = useState(false)
  const queryClient = useQueryClient()

  const { data } = useQuery({
    queryKey: ['collection-records', orderId],
    queryFn: () => http.get<any>('/iso/collection-records', { order_id: orderId }),
  })

  const create = useMutation({
    mutationFn: (values: any) => http.post('/iso/collection-records', { ...values, order_id: orderId }),
    onSuccess: () => { message.success('已添加'); setOpen(false); form.resetFields(); queryClient.invalidateQueries({ queryKey: ['collection-records', orderId] }) },
  })

  const columns = [
    { title: '催收日期', dataIndex: 'collection_date', width: 110 },
    { title: '方式', dataIndex: 'method', width: 80 },
    { title: '内容', dataIndex: 'content', ellipsis: true },
    { title: '下次跟进', dataIndex: 'next_followup_date', width: 110 },
  ]

  return (
    <>
      <Button type="primary" size="small" icon={<PlusOutlined />} onClick={() => setOpen(true)} style={{ marginBottom: 12 }}>新增催收记录</Button>
      <Table rowKey="id" columns={columns} dataSource={data?.items ?? []} size="small" pagination={false} />
      <Modal title="催收记录" open={open} onCancel={() => setOpen(false)} onOk={() => form.submit()} confirmLoading={create.isPending}>
        <Form form={form} layout="vertical" onFinish={(v) => create.mutate(v)}>
          <Form.Item name="collection_date" label="催收日期" rules={[{ required: true }]}><Input type="date" /></Form.Item>
          <Form.Item name="method" label="方式" rules={[{ required: true }]}>
            <Select options={[{ label: '邮件', value: '邮件' }, { label: '电话', value: '电话' }, { label: '聊天', value: '聊天' }]} />
          </Form.Item>
          <Form.Item name="content" label="催收内容"><Input.TextArea rows={3} /></Form.Item>
          <Form.Item name="next_followup_date" label="下次跟进日期"><Input type="date" /></Form.Item>
        </Form>
      </Modal>
    </>
  )
}

function ChangeLogTab({ orderId }: { orderId: number }) {
  const { message } = App.useApp()
  const [form] = Form.useForm()
  const [open, setOpen] = useState(false)
  const queryClient = useQueryClient()

  const { data } = useQuery({
    queryKey: ['change-logs', 'order', orderId],
    queryFn: () => http.get<any>('/iso/change-logs', { entity_type: 'order', entity_id: orderId }),
  })

  const create = useMutation({
    mutationFn: (values: any) => http.post('/iso/change-logs', { entity_type: 'order', entity_id: orderId, ...values }),
    onSuccess: () => { message.success('已记录'); setOpen(false); form.resetFields(); queryClient.invalidateQueries({ queryKey: ['change-logs', 'order', orderId] }) },
  })

  const columns = [
    { title: '变更原因', dataIndex: 'change_reason' },
    { title: '变更前版本', dataIndex: 'version_before', width: 100 },
    { title: '变更后版本', dataIndex: 'version_after', width: 100 },
    { title: '操作人', dataIndex: 'changed_by', width: 80 },
    { title: '时间', dataIndex: 'created_at', width: 160 },
  ]

  return (
    <>
      <Button type="primary" size="small" icon={<PlusOutlined />} onClick={() => setOpen(true)} style={{ marginBottom: 12 }}>记录变更</Button>
      <Table rowKey="id" columns={columns} dataSource={data?.items ?? []} size="small" pagination={false} />
      <Modal title="记录变更" open={open} onCancel={() => setOpen(false)} onOk={() => form.submit()} confirmLoading={create.isPending}>
        <Form form={form} layout="vertical" onFinish={(v) => create.mutate(v)}>
          <Form.Item name="change_reason" label="变更原因" rules={[{ required: true }]}><Input.TextArea rows={2} /></Form.Item>
          <Form.Item name="version_before" label="变更前版本"><Input /></Form.Item>
          <Form.Item name="version_after" label="变更后版本"><Input /></Form.Item>
        </Form>
      </Modal>
    </>
  )
}
