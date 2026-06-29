import { useMemo, useState } from 'react'
import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { Alert, Button, Card, Descriptions, Form, Input, Modal, Select, Space, Table, Tag, DatePicker, message } from 'antd'
import { PlusOutlined, RobotOutlined } from '@ant-design/icons'
import { useApiPost, useApiQuery, usePageQuery } from '@lg/react-hooks'
import { http } from '@lg/api-client'
import { PageHeader } from '@/components/common'
import { useFormat } from '@/hooks/useFormat'

export const Route = createFileRoute('/_authenticated/ship-repair/projects')({
  component: ProjectsPage,
})

interface ProjectRecord {
  id: number
  project_name: string
  vessel_name: string
  order_id?: number
  order_no?: string
  customer_name?: string
  ship_owner?: string
  shipyard?: string
  dock_in_date?: string
  dock_out_date?: string
  repair_specification?: string
  status: string
  created_at: string
  updated_at: string
}

function ProjectsPage() {
  const { fmtDate } = useFormat()
  const navigate = useNavigate()
  const [params, setParams] = useState<Record<string, unknown>>({ page: 1, size: 20 })
  const [createOpen, setCreateOpen] = useState(false)
  const [detailOpen, setDetailOpen] = useState(false)
  const [currentRecord, setCurrentRecord] = useState<ProjectRecord | null>(null)
  const [generating, setGenerating] = useState(false)
  const [form] = Form.useForm()

  const { data: ordersData } = useApiQuery<{ items?: Array<{ id: number; order_no: string; customer_name?: string; vessel_name?: string }> }>(
    ['orders', 'select', 'ship-repair'],
    '/orders',
    { page: 1, size: 200 },
  )
  const orderOptions = useMemo(() => (ordersData?.items ?? []).map((o) => ({
    value: o.id,
    label: `${o.order_no}${o.customer_name ? ` - ${o.customer_name}` : ''}${o.vessel_name ? ` / ${o.vessel_name}` : ''}`,
    meta: o,
  })), [ordersData?.items])

  const { data, isLoading, refetch } = usePageQuery<ProjectRecord>(
    ['ship-repair-projects', params],
    '/ship-repair/projects',
    params
  )

  const createMutation = useApiPost<ProjectRecord>('/ship-repair/projects', {
    invalidateKeys: [['ship-repair-projects']],
    onSuccess: () => {
      message.success('项目创建成功')
      setCreateOpen(false)
      form.resetFields()
      refetch()
    },
  })

  const handleGenerateTasks = async (record: ProjectRecord) => {
    setGenerating(true)
    try {
      const res = await http.post<any>(`/ship-repair/projects/${record.id}/ai-generate-tasks`)
      message.success(`AI已生成 ${res.tasks_created ?? 0} 个任务`)
    } catch (e) {
      message.error(e instanceof Error ? e.message : 'AI生成任务失败')
    } finally {
      setGenerating(false)
    }
  }

  const columns = [
    { title: '项目名称', dataIndex: 'project_name', key: 'project_name', width: 180 },
    { title: '船名', dataIndex: 'vessel_name', key: 'vessel_name', width: 160 },
    { title: '关联订单', dataIndex: 'order_no', key: 'order_no', width: 160, render: (v: string) => v || '-' },
    { title: '客户', dataIndex: 'customer_name', key: 'customer_name', width: 160, render: (v: string) => v || '-' },
    { title: '船东', dataIndex: 'ship_owner', key: 'ship_owner', width: 160, render: (v: string) => v || '-' },
    { title: '船厂', dataIndex: 'shipyard', key: 'shipyard', width: 160, render: (v: string) => v || '-' },
    { title: '进坞', dataIndex: 'dock_in_date', key: 'dock_in_date', width: 120, render: (v: string) => v ? fmtDate(v) : '-' },
    { title: '出坞', dataIndex: 'dock_out_date', key: 'dock_out_date', width: 120, render: (v: string) => v ? fmtDate(v) : '-' },
    {
      title: '状态', dataIndex: 'status', key: 'status', width: 120,
      render: (v: string) => <Tag color={v === 'COMPLETED' ? 'success' : v === 'IN_PROGRESS' ? 'processing' : 'default'}>{v}</Tag>,
    },
    {
      title: '操作', key: 'actions', width: 240,
      render: (_: unknown, record: ProjectRecord) => (
        <Space size={0}>
          <Button type="link" size="small" onClick={() => { setCurrentRecord(record); setDetailOpen(true) }}>查看</Button>
          <Button type="link" size="small" icon={<RobotOutlined />} loading={generating} onClick={() => handleGenerateTasks(record)}>AI生成任务</Button>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <PageHeader title="项目 Projects" extra={<Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>新建项目</Button>} />

      <Alert
        style={{ marginBottom: 16 }}
        type="info"
        showIcon
        message="一个项目代表一条船的一次修理任务。维修规范或进坞会议内容作为 AI 拆解任务的输入资料。"
      />

      <Table
        rowKey="id"
        columns={columns}
        dataSource={data?.items}
        loading={isLoading}
        pagination={{
          current: data?.page,
          pageSize: data?.size,
          total: data?.total,
          showTotal: (t) => `共 ${t} 条`,
          onChange: (page, size) => setParams((prev) => ({ ...prev, page, size })),
        }}
      />

      <Modal
        title="新建项目"
        open={createOpen}
        onCancel={() => setCreateOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={createMutation.isPending}
        width={800}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={(values) => createMutation.mutate({
            ...values,
            dock_in_date: values.dock_in_date ? values.dock_in_date.format('YYYY-MM-DD') : undefined,
            dock_out_date: values.dock_out_date ? values.dock_out_date.format('YYYY-MM-DD') : undefined,
          })}
        >
          <Form.Item name="order_id" label="关联订单（可选）">
            <Select
              placeholder="选择订单后自动带出船名"
              allowClear
              showSearch
              optionFilterProp="label"
              options={orderOptions.map((o) => ({ value: o.value, label: o.label }))}
              onChange={(value) => {
                const selected = orderOptions.find((o) => o.value === value)
                const vesselName = selected?.meta?.vessel_name
                if (vesselName) form.setFieldsValue({ vessel_name: vesselName })
              }}
            />
          </Form.Item>
          <Form.Item name="project_name" label="项目名称" rules={[{ required: true }]}>
            <Input placeholder="例如：主机大修项目" />
          </Form.Item>
          <Form.Item name="vessel_name" label="船名" rules={[{ required: true }]}>
            <Input placeholder="例如：MV PACIFIC" />
          </Form.Item>
          <Form.Item name="ship_owner" label="船东">
            <Input />
          </Form.Item>
          <Form.Item name="shipyard" label="船厂">
            <Input />
          </Form.Item>
          <Form.Item name="dock_in_date" label="计划进坞时间">
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="dock_out_date" label="计划出坞时间">
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="repair_specification" label="维修规范 / 进坞会议大计划">
            <Input.TextArea rows={8} placeholder="粘贴维修规范、进坞会议纪要或大计划内容，供 AI 拆解任务使用" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal title="项目详情" open={detailOpen} onCancel={() => setDetailOpen(false)} footer={null} width={900}>
        {currentRecord && (
          <Card bordered={false}>
            <Descriptions bordered column={2}>
              <Descriptions.Item label="项目名称">{currentRecord.project_name}</Descriptions.Item>
              <Descriptions.Item label="船名">{currentRecord.vessel_name}</Descriptions.Item>
              <Descriptions.Item label="关联订单" span={2}>
                {currentRecord.order_id ? (
                  <Button type="link" onClick={() => navigate({ to: `/orders/${currentRecord.order_id}` as any })}>
                    {currentRecord.order_no || `订单#${currentRecord.order_id}`}
                  </Button>
                ) : (
                  '-'
                )}
              </Descriptions.Item>
              <Descriptions.Item label="客户" span={2}>{currentRecord.customer_name || '-'}</Descriptions.Item>
              <Descriptions.Item label="船东">{currentRecord.ship_owner || '-'}</Descriptions.Item>
              <Descriptions.Item label="船厂">{currentRecord.shipyard || '-'}</Descriptions.Item>
              <Descriptions.Item label="计划进坞">{currentRecord.dock_in_date ? fmtDate(currentRecord.dock_in_date) : '-'}</Descriptions.Item>
              <Descriptions.Item label="计划出坞">{currentRecord.dock_out_date ? fmtDate(currentRecord.dock_out_date) : '-'}</Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={currentRecord.status === 'COMPLETED' ? 'success' : currentRecord.status === 'IN_PROGRESS' ? 'processing' : 'default'}>
                  {currentRecord.status}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="创建时间">{fmtDate(currentRecord.created_at)}</Descriptions.Item>
              <Descriptions.Item label="维修规范" span={2}>{currentRecord.repair_specification || '-'}</Descriptions.Item>
            </Descriptions>
          </Card>
        )}
      </Modal>
    </div>
  )
}
