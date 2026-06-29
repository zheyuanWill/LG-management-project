import { useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import {
  Card, Table, Button, Modal, Form, Input, Select, InputNumber, Tabs, Tag, Space, message, Descriptions, Rate, Popconfirm,
} from 'antd'
import { PlusOutlined, ExclamationCircleOutlined, DeleteOutlined } from '@ant-design/icons'
import { usePageQuery, useApiDelete } from '@lg/react-hooks'
import { http } from '@lg/api-client'
import { PageHeader } from '@/components/common'

export const Route = createFileRoute('/_authenticated/after-sales')({
  component: AfterSalesPage,
})

const complaintStatusLabels: Record<string, string> = {
  RECEIVED: '已接收', INVESTIGATING: '调查中', RESOLVED: '已处理', CLOSED: '已关闭',
}
const complaintStatusColors: Record<string, string> = {
  RECEIVED: 'blue', INVESTIGATING: 'orange', RESOLVED: 'green', CLOSED: 'default',
}
const surveyStatusLabels: Record<string, string> = {
  DRAFT: '草稿', SENT: '已发送', RESPONDED: '已回复', CLOSED: '已关闭',
}

function AfterSalesPage() {
  const [activeTab, setActiveTab] = useState('complaints')
  return (
    <div>
      <PageHeader title="售后服务" />
      <Tabs activeKey={activeTab} onChange={setActiveTab} items={[
        { key: 'complaints', label: '客户投诉', children: <ComplaintsTab /> },
        { key: 'surveys', label: '满意度调查', children: <SurveysTab /> },
      ]} />
    </div>
  )
}

function ComplaintsTab() {
  const [page, setPage] = useState(1)
  const [showCreate, setShowCreate] = useState(false)
  const [showDetail, setShowDetail] = useState<Record<string, unknown> | null>(null)
  const [form] = Form.useForm()
  const [handleForm] = Form.useForm()

  const { data, isLoading, refetch } = usePageQuery('/iso/complaints', { page, size: 20 })
  const deleteMutation = useApiDelete('/iso/complaints', {
    onSuccess: () => { message.success('删除成功'); refetch() },
  })

  const handleCreate = async (values: Record<string, unknown>) => {
    await http.post('/iso/complaints', values)
    message.success('投诉记录已创建')
    setShowCreate(false)
    form.resetFields()
    refetch()
  }

  const handleProcess = async (values: Record<string, unknown>) => {
    if (!showDetail) return
    await http.put(`/iso/complaints/${showDetail.id}`, values)
    message.success('投诉已更新')
    setShowDetail(null)
    handleForm.resetFields()
    refetch()
  }

  const columns = [
    { title: '投诉编号', dataIndex: 'complaint_no', width: 120 },
    { title: '客户ID', dataIndex: 'customer_id', width: 80 },
    { title: '来源', dataIndex: 'source', width: 80 },
    { title: '内容', dataIndex: 'content', ellipsis: true },
    { title: '接收时间', dataIndex: 'received_at', width: 160, render: (v: string) => v?.slice(0, 16) },
    {
      title: '状态', dataIndex: 'status', width: 100,
      render: (v: string) => <Tag color={complaintStatusColors[v]}>{complaintStatusLabels[v] || v}</Tag>,
    },
    {
      title: '操作', width: 120, fixed: 'right',
      render: (_: unknown, record: Record<string, unknown>) => (
        <Space size={0}>
          <Button type="link" size="small" onClick={() => setShowDetail(record)}>处理</Button>
          <Popconfirm
            title="确定要删除该投诉记录吗？"
            onConfirm={() => deleteMutation.mutate(record.id as number)}
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
    <Card>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'flex-end' }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setShowCreate(true)}>新增投诉</Button>
      </div>
      <Table
        rowKey="id" columns={columns} dataSource={data?.items || []} loading={isLoading}
        pagination={{ current: page, total: data?.total || 0, pageSize: 20, onChange: setPage }}
      />

      <Modal title="新增投诉记录" open={showCreate} onCancel={() => setShowCreate(false)} onOk={() => form.submit()} destroyOnClose>
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="customer_id" label="客户ID" rules={[{ required: true }]}><Input type="number" /></Form.Item>
          <Form.Item name="order_id" label="关联订单ID"><Input type="number" /></Form.Item>
          <Form.Item name="source" label="投诉来源" initialValue="EMAIL">
            <Select options={[
              { value: 'EMAIL', label: '邮件' }, { value: 'PHONE', label: '电话' }, { value: 'CHAT', label: '聊天' },
            ]} />
          </Form.Item>
          <Form.Item name="content" label="投诉内容" rules={[{ required: true }]}><Input.TextArea rows={4} /></Form.Item>
          <Form.Item name="period_no_complaint" label="本期无投诉标记" valuePropName="checked">
            <Select options={[{ value: false, label: '否' }, { value: true, label: '是（本期无投诉记录）' }]} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={`处理投诉 - ${showDetail?.complaint_no || ''}`} open={!!showDetail}
        onCancel={() => setShowDetail(null)} onOk={() => handleForm.submit()} width={600} destroyOnClose
      >
        {showDetail && (
          <div style={{ marginBottom: 16 }}>
            <Descriptions column={1} size="small" bordered>
              <Descriptions.Item label="投诉内容">{showDetail.content as string}</Descriptions.Item>
              <Descriptions.Item label="接收时间">{(showDetail.received_at as string)?.slice(0, 16)}</Descriptions.Item>
            </Descriptions>
          </div>
        )}
        <Form form={handleForm} layout="vertical" onFinish={handleProcess}>
          <Form.Item name="investigation" label="原因调查"><Input.TextArea rows={3} /></Form.Item>
          <Form.Item name="resolution" label="处理方案"><Input.TextArea rows={3} /></Form.Item>
          <Form.Item name="customer_feedback" label="客户反馈"><Input.TextArea rows={2} /></Form.Item>
          <Form.Item name="status" label="状态" rules={[{ required: true }]}>
            <Select options={[
              { value: 'INVESTIGATING', label: '调查中' },
              { value: 'RESOLVED', label: '已处理' },
              { value: 'CLOSED', label: '已关闭' },
            ]} />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}

function SurveysTab() {
  const [page, setPage] = useState(1)
  const [showCreate, setShowCreate] = useState(false)
  const [showRespond, setShowRespond] = useState<Record<string, unknown> | null>(null)
  const [form] = Form.useForm()
  const [respondForm] = Form.useForm()

  const { data, isLoading, refetch } = usePageQuery('/iso/satisfaction-surveys', { page, size: 20 })
  const deleteMutation = useApiDelete('/iso/satisfaction-surveys', {
    onSuccess: () => { message.success('删除成功'); refetch() },
  })

  const handleCreate = async (values: Record<string, unknown>) => {
    await http.post('/iso/satisfaction-surveys', values)
    message.success('调查问卷已创建')
    setShowCreate(false)
    form.resetFields()
    refetch()
  }

  const handleSend = async (id: number) => {
    await http.post(`/iso/satisfaction-surveys/${id}/send`)
    message.success('问卷已发送')
    refetch()
  }

  const handleRespond = async (values: Record<string, unknown>) => {
    if (!showRespond) return
    await http.post(`/iso/satisfaction-surveys/${showRespond.id}/respond`, values)
    message.success('回复已记录')
    setShowRespond(null)
    respondForm.resetFields()
    refetch()
  }

  const columns = [
    { title: '问卷编号', dataIndex: 'survey_no', width: 120 },
    { title: '客户ID', dataIndex: 'customer_id', width: 80 },
    { title: '年度', dataIndex: 'year', width: 80 },
    { title: '综合满意度', dataIndex: 'overall_satisfaction', width: 120, render: (v: number) => v ? <Rate disabled value={v / 2} allowHalf /> : '-' },
    { title: '状态', dataIndex: 'status', width: 100, render: (v: string) => <Tag>{surveyStatusLabels[v] || v}</Tag> },
    {
      title: '操作', width: 180, fixed: 'right',
      render: (_: unknown, record: Record<string, unknown>) => (
        <Space size={0}>
          {record.status === 'DRAFT' && <Button type="link" size="small" onClick={() => handleSend(record.id as number)}>发送</Button>}
          {record.status === 'SENT' && <Button type="link" size="small" onClick={() => setShowRespond(record)}>录入回复</Button>}
          <Popconfirm
            title="确定要删除该调查问卷吗？"
            onConfirm={() => deleteMutation.mutate(record.id as number)}
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
    <Card>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'flex-end' }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setShowCreate(true)}>新建调查</Button>
      </div>
      <Table
        rowKey="id" columns={columns} dataSource={data?.items || []} loading={isLoading}
        pagination={{ current: page, total: data?.total || 0, pageSize: 20, onChange: setPage }}
      />

      <Modal title="新建满意度调查" open={showCreate} onCancel={() => setShowCreate(false)} onOk={() => form.submit()} destroyOnClose>
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="customer_id" label="客户ID" rules={[{ required: true }]}><Input type="number" /></Form.Item>
          <Form.Item name="year" label="年度" rules={[{ required: true }]}><InputNumber style={{ width: '100%' }} min={2020} max={2030} /></Form.Item>
        </Form>
      </Modal>

      <Modal title="录入满意度回复" open={!!showRespond} onCancel={() => setShowRespond(null)} onOk={() => respondForm.submit()} destroyOnClose>
        <Form form={respondForm} layout="vertical" onFinish={handleRespond}>
          <Form.Item name="service_quality" label="服务质量 (1-10)"><InputNumber min={1} max={10} style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="response_speed" label="响应速度 (1-10)"><InputNumber min={1} max={10} style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="price_reasonability" label="价格合理性 (1-10)"><InputNumber min={1} max={10} style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="communication" label="沟通配合度 (1-10)"><InputNumber min={1} max={10} style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="overall_satisfaction" label="整体满意度 (1-10)"><InputNumber min={1} max={10} style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="comments" label="意见与建议"><Input.TextArea rows={3} /></Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}
