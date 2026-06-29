import { useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { Table, Button, Form, Input, Modal, message, Popconfirm } from 'antd'
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons'
import { usePageQuery, useApiPost, useApiDelete } from '@lg/react-hooks'
import { PageHeader } from '@/components/common'
import { useFormat } from '@/hooks/useFormat'
import type { Customer, PageResponse } from '@lg/api-client'

export const Route = createFileRoute('/_authenticated/customers')({
  component: CustomersPage,
})

function CustomersPage() {
  const { fmtDate } = useFormat()
  const [params, setParams] = useState<Record<string, unknown>>({ page: 1, size: 20 })
  const [createOpen, setCreateOpen] = useState(false)
  const [form] = Form.useForm()

  const { data, isLoading } = usePageQuery<Customer>(['customers', params], '/customers', params)
  const createMutation = useApiPost<Customer>('/customers', {
    invalidateKeys: [['customers']],
    onSuccess: () => { message.success('创建成功'); setCreateOpen(false); form.resetFields() },
  })

  const deleteMutation = useApiDelete('/customers', {
    invalidateKeys: [['customers']],
    onSuccess: () => message.success('删除成功'),
  })

  const columns = [
    { title: '编码', dataIndex: 'code', key: 'code', width: 100 },
    { title: '名称', dataIndex: 'name', key: 'name', width: 200 },
    { title: '联系人', dataIndex: 'contact_person', key: 'contact_person', width: 100 },
    { title: '联系电话', dataIndex: 'contact_phone', key: 'contact_phone', width: 130 },
    { title: '邮箱', dataIndex: 'contact_email', key: 'contact_email', width: 180 },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 120, render: (v: string) => fmtDate(v) },
    {
      title: '操作', key: 'actions', width: 80, fixed: 'right',
      render: (_: unknown, record: Customer) => (
        <Popconfirm
          title="确定要删除该客户吗？"
          onConfirm={() => deleteMutation.mutate(record.id)}
          okText="确定"
          cancelText="取消"
        >
          <Button type="link" danger icon={<DeleteOutlined />}>
            删除
          </Button>
        </Popconfirm>
      ),
    },
  ]

  return (
    <div>
      <PageHeader title="客户/船舶" extra={<Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>新建客户</Button>} />
      <Form layout="inline" onFinish={(v) => setParams({ ...v, page: 1, size: 20 })} style={{ marginBottom: 16 }}>
        <Form.Item name="keyword"><Input placeholder="搜索客户名称" allowClear /></Form.Item>
        <Form.Item><Button type="primary" htmlType="submit">搜索</Button></Form.Item>
      </Form>
      <Table rowKey="id" columns={columns} dataSource={data?.items} loading={isLoading} pagination={{ current: data?.page, pageSize: data?.size, total: data?.total, showTotal: (t) => `共 ${t} 条`, onChange: (p, s) => setParams((prev) => ({ ...prev, page: p, size: s })) }} />
      <Modal title="新建客户" open={createOpen} onCancel={() => setCreateOpen(false)} onOk={() => form.submit()} confirmLoading={createMutation.isPending}>
        <Form form={form} layout="vertical" onFinish={(v) => createMutation.mutate(v)}>
          <Form.Item name="name" label="客户名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="code" label="客户编码" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="contact_person" label="联系人"><Input /></Form.Item>
          <Form.Item name="contact_phone" label="联系电话"><Input /></Form.Item>
          <Form.Item name="contact_email" label="邮箱"><Input /></Form.Item>
          <Form.Item name="address" label="地址"><Input.TextArea rows={2} /></Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
