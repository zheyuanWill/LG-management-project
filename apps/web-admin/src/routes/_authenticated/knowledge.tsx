import { useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import {
  Card, Table, Button, Modal, Form, Input, Select, Tag, Space, message, Popconfirm, Typography,
} from 'antd'
import { PlusOutlined, DeleteOutlined, EyeOutlined, BookOutlined } from '@ant-design/icons'
import { usePageQuery } from '@lg/react-hooks'
import { http } from '@lg/api-client'
import { PageHeader } from '@/components/common'

const { Paragraph } = Typography

export const Route = createFileRoute('/_authenticated/knowledge')({
  component: KnowledgePage,
})

const docTypeLabels: Record<string, string> = {
  emergency_plan: '紧急预案',
  project_experience: '项目经验',
  iso_document: 'ISO文件',
  regulation: '法规标准',
  complaint_resolution: '投诉处理经验',
  manual: '手动录入',
}

const docTypeColors: Record<string, string> = {
  emergency_plan: 'red',
  project_experience: 'blue',
  iso_document: 'green',
  regulation: 'purple',
  complaint_resolution: 'orange',
  manual: 'default',
}

function KnowledgePage() {
  const [page, setPage] = useState(1)
  const [keyword, setKeyword] = useState('')
  const [docType, setDocType] = useState<string | undefined>()
  const [showCreate, setShowCreate] = useState(false)
  const [showDetail, setShowDetail] = useState<Record<string, unknown> | null>(null)
  const [form] = Form.useForm()

  const { data, isLoading, refetch } = usePageQuery('/iso/knowledge', {
    page, size: 20, keyword: keyword || undefined, doc_type: docType,
  })

  const handleCreate = async (values: { title: string; content: string; doc_type: string }) => {
    await http.post('/iso/knowledge', null, { params: values })
    message.success('知识文档已创建')
    setShowCreate(false)
    form.resetFields()
    refetch()
  }

  const handleDelete = async (id: number) => {
    await http.delete(`/iso/knowledge/${id}`)
    message.success('已删除')
    refetch()
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    { title: '标题', dataIndex: 'title', ellipsis: true },
    {
      title: '类型', dataIndex: 'doc_type', width: 120,
      render: (v: string) => <Tag color={docTypeColors[v] || 'default'}>{docTypeLabels[v] || v}</Tag>,
    },
    {
      title: '来源', dataIndex: 'source_type', width: 100,
      render: (v: string) => v || '-',
    },
    { title: '创建时间', dataIndex: 'created_at', width: 160, render: (v: string) => v?.slice(0, 16) },
    {
      title: '操作', width: 120,
      render: (_: unknown, record: Record<string, unknown>) => (
        <Space>
          <Button type="link" size="small" icon={<EyeOutlined />} onClick={() => setShowDetail(record)} />
          <Popconfirm title="确定删除？" onConfirm={() => handleDelete(record.id as number)}>
            <Button type="link" size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <PageHeader title="知识库管理" />
      <Card>
        <div style={{ marginBottom: 16, display: 'flex', gap: 12, justifyContent: 'space-between', flexWrap: 'wrap' }}>
          <Space>
            <Input.Search
              placeholder="搜索标题" allowClear style={{ width: 240 }}
              onSearch={(v) => { setKeyword(v); setPage(1) }}
            />
            <Select
              placeholder="文档类型" allowClear style={{ width: 150 }}
              onChange={(v) => { setDocType(v); setPage(1) }}
              options={Object.entries(docTypeLabels).map(([k, v]) => ({ value: k, label: v }))}
            />
          </Space>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setShowCreate(true)}>新增文档</Button>
        </div>
        <Table
          rowKey="id" columns={columns} dataSource={data?.items || []} loading={isLoading}
          pagination={{ current: page, total: data?.total || 0, pageSize: 20, onChange: setPage }}
        />
      </Card>

      <Modal title="新增知识文档" open={showCreate} onCancel={() => setShowCreate(false)} onOk={() => form.submit()} width={640} destroyOnClose>
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="title" label="标题" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="doc_type" label="文档类型" rules={[{ required: true }]}>
            <Select options={Object.entries(docTypeLabels).map(([k, v]) => ({ value: k, label: v }))} />
          </Form.Item>
          <Form.Item name="content" label="内容" rules={[{ required: true }]}><Input.TextArea rows={10} /></Form.Item>
        </Form>
      </Modal>

      <Modal title="文档详情" open={!!showDetail} onCancel={() => setShowDetail(null)} footer={null} width={640}>
        {showDetail && (
          <div>
            <h3>{showDetail.title as string}</h3>
            <Tag color={docTypeColors[showDetail.doc_type as string]}>{docTypeLabels[showDetail.doc_type as string]}</Tag>
            <Paragraph style={{ marginTop: 16, whiteSpace: 'pre-wrap' }}>
              {showDetail.content as string || '无内容'}
            </Paragraph>
          </div>
        )}
      </Modal>
    </div>
  )
}
