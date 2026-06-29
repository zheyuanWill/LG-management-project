import { useState } from 'react'
import { createFileRoute, useNavigate } from '@tanstack/react-router'
import {
  Table, Button, Form, Input, Select, Tag, Modal, Popconfirm,
  Card, Segmented, App, Tabs, Progress, Alert,
} from 'antd'
import { PlusOutlined, UnorderedListOutlined, BarChartOutlined } from '@ant-design/icons'
import { usePageQuery, useApiPost, useApiQuery } from '@lg/react-hooks'
import { PageHeader } from '@/components/common'
import { GanttChart } from '@/components/tracking/GanttChart'
import { nodeStatusOptions, nodeStatusTagColors } from '@/constants'
import { useFormat } from '@/hooks/useFormat'
import type { TrackingNode, WorkflowInstance, PageResponse } from '@lg/api-client'
import { http } from '@lg/api-client'
import { useQueryClient } from '@tanstack/react-query'

export const Route = createFileRoute('/_authenticated/tracking')({
  component: TrackingPage,
})

const INSTANCE_STATUS_TAGS: Record<string, { color: string; label: string }> = {
  PENDING: { color: 'default', label: '待启动' },
  RUNNING: { color: 'processing', label: '运行中' },
  COMPLETED: { color: 'success', label: '已完成' },
  CANCELLED: { color: 'error', label: '已取消' },
}

function getInstanceProgress(inst: WorkflowInstance) {
  const states = Object.values(inst.node_states || {})
  if (states.length === 0) return 0
  const completed = states.filter((s) => s.status === 'COMPLETED' || s.status === 'SKIPPED').length
  return Math.round((completed / states.length) * 100)
}

function TrackingPage() {
  const { fmtDate, fmtStatus } = useFormat()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('workflow')
  const [params, setParams] = useState<Record<string, unknown>>({ page: 1, size: 50 })
  const [instanceParams, setInstanceParams] = useState<Record<string, unknown>>({ page: 1, size: 50 })
  const [createOpen, setCreateOpen] = useState(false)
  const [viewMode, setViewMode] = useState<string>('table')
  const [form] = Form.useForm()
  const queryClient = useQueryClient()
  const { message } = App.useApp()

  const { data: ordersData } = useApiQuery<PageResponse<{ id: number; order_no: string; customer_name?: string }>>(
    ['orders', 'select'], '/orders', { size: 200 },
  )
  const orderOptions = (ordersData?.items ?? []).map((o) => ({
    value: o.id, label: `${o.order_no}${o.customer_name ? ` - ${o.customer_name}` : ''}`,
  }))

  const { data: instanceData, isLoading: instanceLoading } = usePageQuery<WorkflowInstance>(
    ['workflow', 'instances', 'tracking', instanceParams], '/workflows/instances', instanceParams,
  )

  const { data, isLoading } = usePageQuery<TrackingNode>(['tracking', params], '/tracking/nodes', params)
  const createMutation = useApiPost<TrackingNode>('/tracking/nodes', {
    invalidateKeys: [['tracking']],
    onSuccess: () => { message.success('创建成功'); setCreateOpen(false); form.resetFields() },
  })

  const handleStatusUpdate = async (id: number, status: string) => {
    try {
      await http.put(`/tracking/nodes/${id}/status`, { status })
      message.success('状态已更新')
      queryClient.invalidateQueries({ queryKey: ['tracking'] })
    } catch (e) { message.error(e instanceof Error ? e.message : '操作失败') }
  }

  const instanceColumns = [
    { title: '流程名称', dataIndex: 'name', key: 'name', width: 180 },
    {
      title: '订单号', dataIndex: 'order_no', key: 'order_no', width: 140,
      render: (v: string, r: WorkflowInstance) => v ? (
        <Button type="link" size="small" onClick={() => navigate({ to: '/orders/$id', params: { id: String(r.order_id) } })}>{v}</Button>
      ) : '-',
    },
    { title: '模板', dataIndex: 'template_name', key: 'template_name', width: 140 },
    {
      title: '状态', dataIndex: 'status', key: 'status', width: 100,
      render: (v: string) => {
        const tag = INSTANCE_STATUS_TAGS[v] || INSTANCE_STATUS_TAGS.PENDING
        return <Tag color={tag.color}>{tag.label}</Tag>
      },
    },
    {
      title: '进度', key: 'progress', width: 160,
      render: (_: unknown, r: WorkflowInstance) => <Progress percent={getInstanceProgress(r)} size="small" />,
    },
    { title: '启动时间', dataIndex: 'started_at', key: 'started_at', width: 120, render: (v: string) => fmtDate(v) },
    { title: '完成时间', dataIndex: 'completed_at', key: 'completed_at', width: 120, render: (v: string) => fmtDate(v) },
    {
      title: '操作', key: 'actions', width: 100,
      render: (_: unknown, r: WorkflowInstance) =>
        r.order_id ? (
          <Button type="link" size="small" onClick={() => navigate({ to: '/orders/$id', params: { id: String(r.order_id) } })}>
            查看订单
          </Button>
        ) : '-',
    },
  ]

  const trackingColumns = [
    { title: '节点名称', dataIndex: 'name', key: 'name', width: 160 },
    { title: '订单号', dataIndex: 'order_no', key: 'order_no', width: 140 },
    { title: '状态', dataIndex: 'status', key: 'status', width: 100, render: (v: string) => <Tag color={nodeStatusTagColors[v] ?? 'default'}>{fmtStatus(v, 'node')}</Tag> },
    { title: '负责人', dataIndex: 'assignee_name', key: 'assignee_name', width: 100 },
    { title: '计划日期', dataIndex: 'planned_date', key: 'planned_date', width: 120, render: (v: string) => fmtDate(v) },
    { title: '实际日期', dataIndex: 'actual_date', key: 'actual_date', width: 120, render: (v: string) => fmtDate(v) },
    {
      title: '操作', key: 'actions', width: 160, fixed: 'right' as const,
      render: (_: unknown, r: TrackingNode) => (
        <span>
          {r.status === 'PENDING' && <Popconfirm title="开始此节点?" onConfirm={() => handleStatusUpdate(r.id, 'IN_PROGRESS')}><Button type="link" size="small">开始</Button></Popconfirm>}
          {r.status === 'IN_PROGRESS' && <Popconfirm title="完成此节点?" onConfirm={() => handleStatusUpdate(r.id, 'COMPLETED')}><Button type="link" size="small">完成</Button></Popconfirm>}
        </span>
      ),
    },
  ]

  const nodes = data?.items ?? []

  return (
    <div>
      <PageHeader title="跟单进度" />

      <Tabs activeKey={activeTab} onChange={setActiveTab} items={[
        {
          key: 'workflow',
          label: `工作流进度 (${instanceData?.total ?? 0})`,
          children: (
            <div>
              <Form layout="inline" onFinish={(v) => setInstanceParams({ ...v, page: 1, size: 50 })} style={{ marginBottom: 16 }}>
                <Form.Item name="status">
                  <Select placeholder="状态" allowClear style={{ width: 130 }} options={[
                    { value: 'RUNNING', label: '运行中' },
                    { value: 'PENDING', label: '待启动' },
                    { value: 'COMPLETED', label: '已完成' },
                    { value: 'CANCELLED', label: '已取消' },
                  ]} />
                </Form.Item>
                <Form.Item><Button type="primary" htmlType="submit">搜索</Button></Form.Item>
              </Form>
              <Table
                rowKey="id"
                columns={instanceColumns}
                dataSource={instanceData?.items ?? []}
                loading={instanceLoading}
                scroll={{ x: 1060 }}
                pagination={{
                  current: instanceData?.page,
                  pageSize: instanceData?.size,
                  total: instanceData?.total,
                  showTotal: (t: number) => `共 ${t} 条`,
                  onChange: (p, s) => setInstanceParams((prev) => ({ ...prev, page: p, size: s })),
                }}
              />
            </div>
          ),
        },
        {
          key: 'nodes',
          label: `跟单节点（旧）`,
          children: (
            <div>
              <Alert
                type="info"
                showIcon
                message="跟单节点功能已迁移至工作流"
                description="新项目请使用上方「工作流进度」标签页。在工作流编辑器中，拖入「自定义」节点即可替代手动跟单节点。"
                style={{ marginBottom: 16 }}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
                <Form layout="inline" onFinish={(v) => setParams({ ...v, page: 1, size: 50 })}>
                  <Form.Item name="order_id"><Select placeholder="选择订单" showSearch optionFilterProp="label" options={orderOptions} allowClear style={{ width: 220 }} /></Form.Item>
                  <Form.Item name="status"><Select placeholder="状态" options={nodeStatusOptions} allowClear style={{ width: 130 }} /></Form.Item>
                  <Form.Item><Button type="primary" htmlType="submit">搜索</Button></Form.Item>
                </Form>
                <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                  <Segmented
                    value={viewMode}
                    onChange={(v) => setViewMode(v as string)}
                    options={[
                      { value: 'table', icon: <UnorderedListOutlined /> },
                      { value: 'gantt', icon: <BarChartOutlined /> },
                    ]}
                  />
                  <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>新建节点</Button>
                </div>
              </div>

              {viewMode === 'table' ? (
                <Table
                  rowKey="id"
                  columns={trackingColumns}
                  dataSource={nodes}
                  loading={isLoading}
                  scroll={{ x: 900 }}
                  pagination={{
                    current: data?.page,
                    pageSize: data?.size,
                    total: data?.total,
                    showTotal: (t: number) => `共 ${t} 条`,
                    onChange: (p, s) => setParams((prev) => ({ ...prev, page: p, size: s })),
                  }}
                />
              ) : (
                <Card>
                  {nodes.length > 0 ? (
                    <GanttChart nodes={nodes} />
                  ) : (
                    <div style={{ textAlign: 'center', padding: 60, color: '#999' }}>暂无跟踪节点数据</div>
                  )}
                </Card>
              )}
            </div>
          ),
        },
      ]} />

      <Modal title="新建跟踪节点" open={createOpen} onCancel={() => setCreateOpen(false)} onOk={() => form.submit()} confirmLoading={createMutation.isPending}>
        <Form form={form} layout="vertical" onFinish={(v) => createMutation.mutate(v)}>
          <Form.Item name="order_id" label="关联订单" rules={[{ required: true }]}><Select placeholder="选择订单" showSearch optionFilterProp="label" options={orderOptions} /></Form.Item>
          <Form.Item name="name" label="节点名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="planned_date" label="计划日期"><Input type="date" /></Form.Item>
          <Form.Item name="notes" label="备注"><Input.TextArea rows={2} /></Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
