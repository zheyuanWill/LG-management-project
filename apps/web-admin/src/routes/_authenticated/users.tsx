import { useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { Table, Button, Form, Input, Select, Modal, message, Tag, Switch, Popconfirm } from 'antd'
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons'
import { usePageQuery, useApiPost } from '@lg/react-hooks'
import { PageHeader } from '@/components/common'
import { useFormat } from '@/hooks/useFormat'
import type { UserResponse, PageResponse } from '@lg/api-client'
import { http } from '@lg/api-client'
import { useQueryClient } from '@tanstack/react-query'

export const Route = createFileRoute('/_authenticated/users')({
  component: UsersPage,
})

const roleOptions = [
  { value: 'OWNER', label: '管理层' },
  { value: 'PM', label: '项目经理' },
  { value: 'PROC', label: '采购' },
  { value: 'FIN', label: '财务' },
  { value: 'OPS', label: '运营' },
]
const roleColors: Record<string, string> = {
  OWNER: 'purple', PM: 'blue', PROC: 'green', FIN: 'orange', OPS: 'cyan',
}

function UsersPage() {
  const { fmtDate } = useFormat()
  const [params, setParams] = useState<Record<string, unknown>>({ page: 1, size: 20 })
  const [createOpen, setCreateOpen] = useState(false)
  const [form] = Form.useForm()
  const queryClient = useQueryClient()

  const { data, isLoading } = usePageQuery<UserResponse>(['users', params], '/users', params)
  const createMutation = useApiPost<UserResponse>('/users', {
    invalidateKeys: [['users']],
    onSuccess: () => { message.success('创建成功'); setCreateOpen(false); form.resetFields() },
  })

  const handleDelete = async (id: number) => {
    try {
      await http.delete(`/users/${id}`)
      message.success('已删除')
      queryClient.invalidateQueries({ queryKey: ['users'] })
    } catch (e) { message.error(e instanceof Error ? e.message : '删除失败') }
  }

  const columns = [
    { title: '用户名', dataIndex: 'username', key: 'username', width: 120 },
    { title: '姓名', dataIndex: 'real_name', key: 'real_name', width: 100 },
    { title: '角色', dataIndex: 'role', key: 'role', width: 100, render: (v: string) => <Tag color={roleColors[v]}>{roleOptions.find((o) => o.value === v)?.label ?? v}</Tag> },
    { title: '邮箱', dataIndex: 'email', key: 'email', width: 180 },
    { title: '状态', dataIndex: 'is_active', key: 'is_active', width: 80, render: (v: boolean) => <Tag color={v ? 'success' : 'default'}>{v ? '启用' : '禁用'}</Tag> },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 120, render: (v: string) => fmtDate(v) },
    {
      title: '操作', key: 'actions', width: 80,
      render: (_: unknown, r: UserResponse) => (
        <Popconfirm title="确认删除?" onConfirm={() => handleDelete(r.id)}>
          <Button type="link" size="small" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ]

  return (
    <div>
      <PageHeader title="用户管理" extra={<Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>新建用户</Button>} />
      <Form layout="inline" onFinish={(v) => setParams({ ...v, page: 1, size: 20 })} style={{ marginBottom: 16 }}>
        <Form.Item name="keyword"><Input placeholder="搜索用户名/姓名" allowClear /></Form.Item>
        <Form.Item name="role"><Select placeholder="角色" options={roleOptions} allowClear style={{ width: 130 }} /></Form.Item>
        <Form.Item name="is_active"><Select placeholder="状态" options={[{ value: 'true', label: '启用' }, { value: 'false', label: '禁用' }]} allowClear style={{ width: 110 }} /></Form.Item>
        <Form.Item><Button type="primary" htmlType="submit">搜索</Button></Form.Item>
      </Form>
      <Table rowKey="id" columns={columns} dataSource={data?.items} loading={isLoading} pagination={{ current: data?.page, pageSize: data?.size, total: data?.total, showTotal: (t) => `共 ${t} 条`, onChange: (p, s) => setParams((prev) => ({ ...prev, page: p, size: s })) }} />
      <Modal title="新建用户" open={createOpen} onCancel={() => setCreateOpen(false)} onOk={() => form.submit()} confirmLoading={createMutation.isPending}>
        <Form form={form} layout="vertical" onFinish={(v) => createMutation.mutate(v)}>
          <Form.Item name="username" label="用户名" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="password" label="密码" rules={[{ required: true }]}><Input.Password /></Form.Item>
          <Form.Item name="real_name" label="姓名"><Input /></Form.Item>
          <Form.Item name="email" label="邮箱"><Input /></Form.Item>
          <Form.Item name="role" label="角色" rules={[{ required: true }]}><Select options={roleOptions} /></Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
