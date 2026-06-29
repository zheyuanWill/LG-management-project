import { useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import {
  Card, Table, Button, Modal, Form, Input, Select, DatePicker, Tabs, Tag, Space, message, Popconfirm,
} from 'antd'
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons'
import { useApiQuery, usePageQuery, useApiDelete } from '@lg/react-hooks'
import { http } from '@lg/api-client'
import { PageHeader } from '@/components/common'

export const Route = createFileRoute('/_authenticated/quality')({
  component: QualityPage,
})

const inspectionResultColors: Record<string, string> = {
  PASS: 'green', FAIL: 'red', CONDITIONAL: 'orange',
}

const changeStatusColors: Record<string, string> = {
  PENDING: 'blue', APPROVED: 'green', REJECTED: 'red',
}

function QualityPage() {
  const [activeTab, setActiveTab] = useState('inspections')

  return (
    <div>
      <PageHeader title="质量管理" />
      <Tabs activeKey={activeTab} onChange={setActiveTab} items={[
        { key: 'inspections', label: '质量检验', children: <InspectionsTab /> },
        { key: 'changes', label: '项目变更', children: <ChangesTab /> },
        { key: 'acceptances', label: '项目验收', children: <AcceptancesTab /> },
      ]} />
    </div>
  )
}

function InspectionsTab() {
  const [page, setPage] = useState(1)
  const [showCreate, setShowCreate] = useState(false)
  const [form] = Form.useForm()

  const { data, isLoading, refetch } = usePageQuery('/iso/quality-inspections', { page, size: 20 })
  const deleteMutation = useApiDelete('/iso/quality-inspections', {
    onSuccess: () => { message.success('删除成功'); refetch() },
  })

  const handleCreate = async (values: Record<string, unknown>) => {
    await http.post('/iso/quality-inspections', values)
    message.success('质检记录已创建')
    setShowCreate(false)
    form.resetFields()
    refetch()
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    { title: '订单ID', dataIndex: 'order_id', width: 80 },
    { title: '检验类型', dataIndex: 'inspection_type', width: 120 },
    { title: '检验日期', dataIndex: 'inspection_date', width: 120 },
    {
      title: '结果', dataIndex: 'result', width: 100,
      render: (v: string) => v ? <Tag color={inspectionResultColors[v] || 'default'}>{v}</Tag> : '-',
    },
    { title: '发现', dataIndex: 'findings', ellipsis: true },
    { title: '创建时间', dataIndex: 'created_at', width: 160, render: (v: string) => v?.slice(0, 16) },
    {
      title: '操作', width: 80, fixed: 'right',
      render: (_: unknown, r: any) => (
        <Popconfirm
          title="确定要删除该记录吗？"
          onConfirm={() => deleteMutation.mutate(r.id)}
          okText="确定"
          cancelText="取消"
        >
          <Button type="link" size="small" danger icon={<DeleteOutlined />}>删除</Button>
        </Popconfirm>
      ),
    },
  ]

  return (
    <Card>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'flex-end' }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setShowCreate(true)}>新增检验</Button>
      </div>
      <Table
        rowKey="id" columns={columns} dataSource={data?.items || []} loading={isLoading}
        pagination={{ current: page, total: data?.total || 0, pageSize: 20, onChange: setPage }}
      />
      <Modal title="新增质量检验" open={showCreate} onCancel={() => setShowCreate(false)} onOk={() => form.submit()} destroyOnClose>
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="order_id" label="订单ID" rules={[{ required: true }]}><Input type="number" /></Form.Item>
          <Form.Item name="inspection_type" label="检验类型" rules={[{ required: true }]}>
            <Select options={[
              { value: 'incoming', label: '来料检验' },
              { value: 'process', label: '过程检验' },
              { value: 'final', label: '最终检验' },
            ]} />
          </Form.Item>
          <Form.Item name="inspection_date" label="检验日期"><DatePicker style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="result" label="结果">
            <Select options={[
              { value: 'PASS', label: '合格' },
              { value: 'FAIL', label: '不合格' },
              { value: 'CONDITIONAL', label: '有条件通过' },
            ]} />
          </Form.Item>
          <Form.Item name="findings" label="发现/备注"><Input.TextArea rows={3} /></Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}

function ChangesTab() {
  const [page, setPage] = useState(1)
  const [showCreate, setShowCreate] = useState(false)
  const [form] = Form.useForm()

  const { data, isLoading, refetch } = usePageQuery('/iso/project-changes', { page, size: 20 })
  const deleteMutation = useApiDelete('/iso/project-changes', {
    onSuccess: () => { message.success('删除成功'); refetch() },
  })

  const handleCreate = async (values: Record<string, unknown>) => {
    await http.post('/iso/project-changes', values)
    message.success('变更单已创建')
    setShowCreate(false)
    form.resetFields()
    refetch()
  }

  const columns = [
    { title: '变更编号', dataIndex: 'change_no', width: 120 },
    { title: '订单ID', dataIndex: 'order_id', width: 80 },
    { title: '变更类型', dataIndex: 'change_type', width: 100 },
    { title: '描述', dataIndex: 'description', ellipsis: true },
    {
      title: '客户确认', dataIndex: 'customer_confirmation', width: 100,
      render: (v: boolean) => v ? <Tag color="green">已确认</Tag> : <Tag color="orange">待确认</Tag>,
    },
    {
      title: '状态', dataIndex: 'status', width: 100,
      render: (v: string) => <Tag color={changeStatusColors[v] || 'default'}>{v}</Tag>,
    },
    { title: '创建时间', dataIndex: 'created_at', width: 160, render: (v: string) => v?.slice(0, 16) },
    {
      title: '操作', width: 80, fixed: 'right',
      render: (_: unknown, r: any) => (
        <Popconfirm
          title="确定要删除该变更单吗？"
          onConfirm={() => deleteMutation.mutate(r.id)}
          okText="确定"
          cancelText="取消"
        >
          <Button type="link" size="small" danger icon={<DeleteOutlined />}>删除</Button>
        </Popconfirm>
      ),
    },
  ]

  return (
    <Card>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'flex-end' }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setShowCreate(true)}>新增变更</Button>
      </div>
      <Table
        rowKey="id" columns={columns} dataSource={data?.items || []} loading={isLoading}
        pagination={{ current: page, total: data?.total || 0, pageSize: 20, onChange: setPage }}
      />
      <Modal title="新增项目变更" open={showCreate} onCancel={() => setShowCreate(false)} onOk={() => form.submit()} destroyOnClose>
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="order_id" label="订单ID" rules={[{ required: true }]}><Input type="number" /></Form.Item>
          <Form.Item name="change_type" label="变更类型" rules={[{ required: true }]}>
            <Select options={[
              { value: 'REQUIREMENT', label: '需求变更' },
              { value: 'PRICE', label: '价格变更' },
              { value: 'SCHEDULE', label: '交期变更' },
              { value: 'SCOPE', label: '范围变更' },
            ]} />
          </Form.Item>
          <Form.Item name="description" label="变更描述" rules={[{ required: true }]}><Input.TextArea rows={3} /></Form.Item>
          <Form.Item name="impact_analysis" label="影响分析"><Input.TextArea rows={3} /></Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}

function AcceptancesTab() {
  const [page, setPage] = useState(1)
  const [showCreate, setShowCreate] = useState(false)
  const [form] = Form.useForm()

  const { data, isLoading, refetch } = usePageQuery('/iso/project-acceptances', { page, size: 20 })
  const deleteMutation = useApiDelete('/iso/project-acceptances', {
    onSuccess: () => { message.success('删除成功'); refetch() },
  })

  const handleCreate = async (values: Record<string, unknown>) => {
    await http.post('/iso/project-acceptances', values)
    message.success('验收单已创建')
    setShowCreate(false)
    form.resetFields()
    refetch()
  }

  const columns = [
    { title: '验收编号', dataIndex: 'acceptance_no', width: 120 },
    { title: '订单ID', dataIndex: 'order_id', width: 80 },
    { title: '验收类型', dataIndex: 'acceptance_type', width: 100 },
    { title: '验收日期', dataIndex: 'acceptance_date', width: 120 },
    {
      title: '客户确认', dataIndex: 'customer_confirmed', width: 100,
      render: (v: boolean) => v ? <Tag color="green">已确认</Tag> : <Tag color="orange">待确认</Tag>,
    },
    { title: '状态', dataIndex: 'status', width: 100 },
    { title: '创建时间', dataIndex: 'created_at', width: 160, render: (v: string) => v?.slice(0, 16) },
    {
      title: '操作', width: 80, fixed: 'right',
      render: (_: unknown, r: any) => (
        <Popconfirm
          title="确定要删除该验收单吗？"
          onConfirm={() => deleteMutation.mutate(r.id)}
          okText="确定"
          cancelText="取消"
        >
          <Button type="link" size="small" danger icon={<DeleteOutlined />}>删除</Button>
        </Popconfirm>
      ),
    },
  ]

  return (
    <Card>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'flex-end' }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setShowCreate(true)}>新增验收</Button>
      </div>
      <Table
        rowKey="id" columns={columns} dataSource={data?.items || []} loading={isLoading}
        pagination={{ current: page, total: data?.total || 0, pageSize: 20, onChange: setPage }}
      />
      <Modal title="新增项目验收" open={showCreate} onCancel={() => setShowCreate(false)} onOk={() => form.submit()} destroyOnClose>
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="order_id" label="订单ID" rules={[{ required: true }]}><Input type="number" /></Form.Item>
          <Form.Item name="acceptance_type" label="验收类型" rules={[{ required: true }]}>
            <Select options={[
              { value: 'goods', label: '货物验收' },
              { value: 'service', label: '服务验收' },
            ]} />
          </Form.Item>
          <Form.Item name="notes" label="备注"><Input.TextArea rows={3} /></Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}
