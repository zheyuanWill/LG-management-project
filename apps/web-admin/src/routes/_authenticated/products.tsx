import { useState, useMemo } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { Table, Button, Form, Input, Select, Modal, message, Popconfirm, Space } from 'antd'
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons'
import { usePageQuery, useApiPost, useApiDelete } from '@lg/react-hooks'
import { PageHeader } from '@/components/common'
import { useFormat } from '@/hooks/useFormat'
import type { Product, PageResponse } from '@lg/api-client'

export const Route = createFileRoute('/_authenticated/products')({
  component: ProductsPage,
})

function ProductsPage() {
  const { fmtDate } = useFormat()
  const [params, setParams] = useState<Record<string, unknown>>({ page: 1, size: 20 })
  const [createOpen, setCreateOpen] = useState(false)
  const [form] = Form.useForm()

  const { data, isLoading } = usePageQuery<Product>(['products', params], '/products', params)
  const createMutation = useApiPost<Product>('/products', {
    invalidateKeys: [['products']],
    onSuccess: () => { message.success('创建成功'); setCreateOpen(false); form.resetFields() },
  })

  const deleteMutation = useApiDelete('/products', {
    invalidateKeys: [['products']],
    onSuccess: () => message.success('删除成功'),
  })

  const categoryOptions = useMemo(() => {
    const cats = new Set((data?.items ?? []).map((p) => p.category).filter(Boolean))
    return Array.from(cats).map((c) => ({ value: c, label: c }))
  }, [data])

  const columns = [
    { title: '编码', dataIndex: 'code', key: 'code', width: 120 },
    { title: '名称', dataIndex: 'name', key: 'name', width: 180 },
    { title: '规格', dataIndex: 'specification', key: 'specification', width: 140 },
    { title: '单位', dataIndex: 'unit', key: 'unit', width: 70 },
    { title: '品牌', dataIndex: 'brand', key: 'brand', width: 100 },
    { title: '分类', dataIndex: 'category', key: 'category', width: 100 },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 120, render: (v: string) => fmtDate(v) },
    {
      title: '操作', key: 'actions', width: 80, fixed: 'right',
      render: (_: unknown, record: Product) => (
        <Popconfirm
          title="确定要删除该商品吗？"
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
      <PageHeader title="商品管理" extra={<Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>新建商品</Button>} />
      <Form layout="inline" onFinish={(v) => setParams({ ...v, page: 1, size: 20 })} style={{ marginBottom: 16 }}>
        <Form.Item name="keyword"><Input placeholder="搜索商品名称/编码" allowClear /></Form.Item>
        <Form.Item name="category"><Select placeholder="分类" options={categoryOptions} allowClear style={{ width: 140 }} /></Form.Item>
        <Form.Item><Button type="primary" htmlType="submit">搜索</Button></Form.Item>
      </Form>
      <Table rowKey="id" columns={columns} dataSource={data?.items} loading={isLoading} pagination={{ current: data?.page, pageSize: data?.size, total: data?.total, showTotal: (t) => `共 ${t} 条`, onChange: (p, s) => setParams((prev) => ({ ...prev, page: p, size: s })) }} />
      <Modal title="新建商品" open={createOpen} onCancel={() => setCreateOpen(false)} onOk={() => form.submit()} confirmLoading={createMutation.isPending}>
        <Form form={form} layout="vertical" onFinish={(v) => createMutation.mutate(v)}>
          <Form.Item name="name" label="名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="code" label="编码" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="specification" label="规格"><Input /></Form.Item>
          <Form.Item name="unit" label="单位" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="brand" label="品牌"><Input /></Form.Item>
          <Form.Item name="category" label="分类"><Input /></Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
