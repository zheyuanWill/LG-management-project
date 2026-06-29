import { useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import {
  Table, Button, Form, Input, Select, Modal, message, Tag, Tabs, Card,
  InputNumber, Space, TreeSelect, Cascader, Upload, App, Popconfirm,
} from 'antd'
import { PlusOutlined, UploadOutlined, DeleteOutlined } from '@ant-design/icons'
import { usePageQuery, useApiPost, useApiDelete } from '@lg/react-hooks'
import { useQuery } from '@tanstack/react-query'
import { http, supplierCategoryApi } from '@lg/api-client'
import { PageHeader } from '@/components/common'
import { useFormat } from '@/hooks/useFormat'
import type { Supplier, SupplierCategoryTree } from '@lg/api-client'
import { supplierTypeLabels } from '@lg/core'

export const Route = createFileRoute('/_authenticated/suppliers')({
  component: SuppliersPage,
})

const supplierTypeOptions = Object.entries(supplierTypeLabels).map(([v, l]) => ({ value: v, label: l }))

const qualStatusColors: Record<string, string> = {
  QUALIFIED: 'green', PENDING: 'blue', OBSERVED: 'orange', ELIMINATED: 'red',
}
const qualStatusLabels: Record<string, string> = {
  QUALIFIED: '合格', PENDING: '待审', OBSERVED: '观察', ELIMINATED: '淘汰',
}
const evalLevelLabels: Record<string, string> = {
  EXCELLENT: '优选', QUALIFIED: '合格', OBSERVED: '观察', ELIMINATED: '淘汰',
}

function useCategoryTree() {
  return useQuery({
    queryKey: ['supplier-categories', 'tree'],
    queryFn: () => supplierCategoryApi.tree(),
    staleTime: 5 * 60 * 1000,
  })
}

function buildTreeSelectData(tree: SupplierCategoryTree[]) {
  return tree.map((l1) => ({
    title: l1.name,
    value: l1.id,
    key: l1.id,
    children: (l1.children || []).map((l2) => ({
      title: l2.name,
      value: l2.id,
      key: l2.id,
    })),
  }))
}

function buildCascaderOptions(tree: SupplierCategoryTree[]) {
  return tree.map((l1) => ({
    label: l1.name,
    value: l1.id,
    children: (l1.children || []).map((l2) => ({
      label: l2.name,
      value: l2.id,
    })),
  }))
}

function SuppliersPage() {
  const [activeTab, setActiveTab] = useState('list')

  return (
    <div>
      <PageHeader title="供应商" />
      <Tabs activeKey={activeTab} onChange={setActiveTab} items={[
        { key: 'list', label: '供应商列表', children: <SupplierListTab /> },
        { key: 'directory', label: '合格名录', children: <QualifiedDirectoryTab /> },
        { key: 'admissions', label: '准入审批', children: <AdmissionsTab /> },
        { key: 'evaluations', label: '年度评价', children: <EvaluationsTab /> },
      ]} />
    </div>
  )
}

function SupplierListTab() {
  const { fmtDate } = useFormat()
  const [params, setParams] = useState<Record<string, unknown>>({ page: 1, size: 20 })
  const [createOpen, setCreateOpen] = useState(false)
  const [form] = Form.useForm()
  const { data: categoryTree } = useCategoryTree()

  const { data, isLoading } = usePageQuery<Supplier>(['suppliers', params], '/suppliers', params)
  const createMutation = useApiPost<Supplier>('/suppliers', {
    invalidateKeys: [['suppliers']],
    onSuccess: () => { message.success('创建成功'); setCreateOpen(false); form.resetFields() },
  })
  const deleteMutation = useApiDelete('/suppliers', {
    invalidateKeys: [['suppliers']],
    onSuccess: () => message.success('删除成功'),
  })

  const treeData = categoryTree ? buildTreeSelectData(categoryTree) : []
  const cascaderOpts = categoryTree ? buildCascaderOptions(categoryTree) : []

  const columns = [
    { title: '编码', dataIndex: 'code', width: 100 },
    { title: '名称', dataIndex: 'name', width: 160 },
    { title: '类型', dataIndex: 'type', width: 80, render: (v: string) => supplierTypeLabels[v] ?? v },
    {
      title: '业务分类', dataIndex: 'categories', width: 200, ellipsis: true,
      render: (_: unknown, record: Supplier) => {
        const cats = record.categories || []
        if (cats.length === 0) return <span style={{ color: '#999' }}>未分类</span>
        return (
          <Space size={[0, 4]} wrap>
            {cats.filter((c) => c.level === 2).map((c) => (
              <Tag key={c.id} color="blue" style={{ margin: 0 }}>{c.name}</Tag>
            ))}
            {cats.filter((c) => c.level === 1).map((c) => (
              <Tag key={c.id} color="cyan" style={{ margin: 0 }}>{c.name}</Tag>
            ))}
          </Space>
        )
      },
    },
    { title: '联系人', dataIndex: 'contact_person', width: 100 },
    { title: '电话', dataIndex: 'contact_phone', width: 120 },
    {
      title: '资质状态', dataIndex: 'qualification_status', width: 100,
      render: (v: string) => <Tag color={qualStatusColors[v] || 'default'}>{qualStatusLabels[v] || v || '合格'}</Tag>,
    },
    {
      title: '评分', dataIndex: 'evaluation_score', width: 80,
      render: (v: number) => v ? <span>{v}分</span> : '-',
    },
    {
      title: '等级', dataIndex: 'evaluation_level', width: 80,
      render: (v: string) => v ? <Tag color={qualStatusColors[v]}>{evalLevelLabels[v] || v}</Tag> : '-',
    },
    { title: '优选', dataIndex: 'is_preferred', width: 60, render: (v: boolean) => v ? <Tag color="gold">优选</Tag> : null },
    { title: '创建时间', dataIndex: 'created_at', width: 110, render: (v: string) => fmtDate(v) },
    {
      title: '操作', key: 'actions', width: 80, fixed: 'right',
      render: (_: unknown, record: Supplier) => (
        <Popconfirm
          title="确定要删除该供应商吗？"
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

  const handleCreate = (values: Record<string, unknown>) => {
    const categoryIds: number[] = []
    const cascaderVal = values.category_cascader as number[][] | undefined
    if (cascaderVal) {
      for (const path of cascaderVal) {
        categoryIds.push(path[path.length - 1])
      }
    }
    const { category_cascader, ...rest } = values
    createMutation.mutate({ ...rest, category_ids: categoryIds })
  }

  return (
    <Card>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
        <Form layout="inline" onFinish={(v) => setParams({ ...v, page: 1, size: 20 })}>
          <Form.Item name="keyword"><Input placeholder="搜索供应商" allowClear /></Form.Item>
          <Form.Item name="type"><Select placeholder="类型" options={supplierTypeOptions} allowClear style={{ width: 120 }} /></Form.Item>
          <Form.Item name="category_id">
            <TreeSelect
              placeholder="按分类筛选"
              treeData={treeData}
              allowClear
              treeDefaultExpandAll
              style={{ width: 180 }}
            />
          </Form.Item>
          <Form.Item><Button type="primary" htmlType="submit">搜索</Button></Form.Item>
        </Form>
        <Space>
          <Upload
            accept=".xlsx,.xls"
            showUploadList={false}
            customRequest={async ({ file }) => {
              const formData = new FormData()
              formData.append('file', file as File)
              try {
                const res = await fetch('/api/suppliers/quotes/import', {
                  method: 'POST',
                  body: formData,
                  headers: { Authorization: `Bearer ${localStorage.getItem('token') || ''}` },
                })
                const data = await res.json()
                message.success(data.message || '导入成功')
              } catch { message.error('导入失败') }
            }}
          >
            <Button icon={<UploadOutlined />}>导入报价Excel</Button>
          </Upload>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>新建供应商</Button>
        </Space>
      </div>
      <Table rowKey="id" columns={columns} dataSource={data?.items} loading={isLoading} scroll={{ x: 1300 }}
        pagination={{ current: data?.page, pageSize: data?.size, total: data?.total, showTotal: (t) => `共 ${t} 条`, onChange: (p, s) => setParams((prev) => ({ ...prev, page: p, size: s })) }}
      />
      <Modal title="新建供应商" open={createOpen} onCancel={() => setCreateOpen(false)} onOk={() => form.submit()} confirmLoading={createMutation.isPending} width={600}>
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="name" label="名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="code" label="编码" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="type" label="类型" rules={[{ required: true }]}><Select options={supplierTypeOptions} /></Form.Item>
          <Form.Item name="category_cascader" label="业务分类（一级→二级，可多选）">
            <Cascader
              options={cascaderOpts}
              multiple
              maxTagCount="responsive"
              placeholder="选择分类"
              showCheckedStrategy="SHOW_CHILD"
            />
          </Form.Item>
          <Form.Item name="contact_person" label="联系人"><Input /></Form.Item>
          <Form.Item name="contact_phone" label="联系电话"><Input /></Form.Item>
          <Form.Item name="contact_email" label="邮箱"><Input /></Form.Item>
          <Form.Item name="business_license" label="营业执照号"><Input /></Form.Item>
          <Form.Item name="industry_qualification" label="行业资质"><Input.TextArea rows={2} /></Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}

function AdmissionsTab() {
  const [page, setPage] = useState(1)
  const [showCreate, setShowCreate] = useState(false)
  const [form] = Form.useForm()

  const { data, isLoading, refetch } = usePageQuery('/iso/supplier-admissions', { page, size: 20 })
  const deleteMutation = useApiDelete('/iso/supplier-admissions', {
    onSuccess: () => { message.success('删除成功'); refetch() },
  })

  const handleCreate = async (values: Record<string, unknown>) => {
    await http.post('/iso/supplier-admissions', values)
    message.success('准入申请已创建')
    setShowCreate(false)
    form.resetFields()
    refetch()
  }

  const handleApprove = async (id: number, approved: boolean) => {
    await http.post(`/iso/supplier-admissions/${id}/approve`, { approved })
    message.success(approved ? '已通过' : '已驳回')
    refetch()
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    { title: '供应商ID', dataIndex: 'supplier_id', width: 90 },
    { title: '营业执照', dataIndex: 'business_license_verified', width: 100, render: (v: boolean) => v ? <Tag color="green">已验证</Tag> : <Tag>未验证</Tag> },
    { title: '行业资质', dataIndex: 'industry_qualification_verified', width: 100, render: (v: boolean) => v ? <Tag color="green">已验证</Tag> : <Tag>未验证</Tag> },
    { title: '试合作结果', dataIndex: 'trial_result', width: 100 },
    {
      title: '状态', dataIndex: 'approval_status', width: 100,
      render: (v: string) => <Tag color={v === 'APPROVED' ? 'green' : v === 'REJECTED' ? 'red' : 'blue'}>{v === 'APPROVED' ? '已通过' : v === 'REJECTED' ? '已驳回' : '待审批'}</Tag>,
    },
    {
      title: '操作', width: 200, fixed: 'right',
      render: (_: unknown, r: Record<string, unknown>) => (
        <Space size={0}>
          {r.approval_status === 'PENDING' && (
            <>
              <Button type="link" size="small" onClick={() => handleApprove(r.id as number, true)}>通过</Button>
              <Button type="link" size="small" danger onClick={() => handleApprove(r.id as number, false)}>驳回</Button>
            </>
          )}
          <Popconfirm
            title="确定要删除该准入申请吗？"
            onConfirm={() => deleteMutation.mutate(r.id as number)}
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
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setShowCreate(true)}>新增准入申请</Button>
      </div>
      <Table rowKey="id" columns={columns} dataSource={data?.items || []} loading={isLoading}
        pagination={{ current: page, total: data?.total || 0, pageSize: 20, onChange: setPage }}
      />
      <Modal title="新增供应商准入" open={showCreate} onCancel={() => setShowCreate(false)} onOk={() => form.submit()} destroyOnClose>
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="supplier_id" label="供应商ID" rules={[{ required: true }]}><Input type="number" /></Form.Item>
          <Form.Item name="business_license_verified" label="营业执照已验证" valuePropName="checked" initialValue={false}>
            <Select options={[{ value: true, label: '是' }, { value: false, label: '否' }]} />
          </Form.Item>
          <Form.Item name="industry_qualification_verified" label="行业资质已验证" valuePropName="checked" initialValue={false}>
            <Select options={[{ value: true, label: '是' }, { value: false, label: '否' }]} />
          </Form.Item>
          <Form.Item name="case_references" label="案例参考"><Input.TextArea rows={2} /></Form.Item>
          <Form.Item name="trial_evaluation" label="试合作评估"><Input.TextArea rows={2} /></Form.Item>
          <Form.Item name="trial_result" label="试合作结果">
            <Select options={[{ value: 'pass', label: '通过' }, { value: 'fail', label: '不通过' }]} />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}

function EvaluationsTab() {
  const [page, setPage] = useState(1)
  const [showCreate, setShowCreate] = useState(false)
  const [form] = Form.useForm()

  const { data, isLoading, refetch } = usePageQuery('/iso/supplier-evaluations', { page, size: 20 })
  const deleteMutation = useApiDelete('/iso/supplier-evaluations', {
    onSuccess: () => { message.success('删除成功'); refetch() },
  })

  const handleCreate = async (values: Record<string, unknown>) => {
    await http.post('/iso/supplier-evaluations', values)
    message.success('评价已创建')
    setShowCreate(false)
    form.resetFields()
    refetch()
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    { title: '供应商ID', dataIndex: 'supplier_id', width: 90 },
    { title: '年度', dataIndex: 'year', width: 70 },
    { title: '质量(25%)', dataIndex: 'quality_score', width: 90 },
    { title: '交期(25%)', dataIndex: 'delivery_score', width: 90 },
    { title: '价格(25%)', dataIndex: 'price_score', width: 90 },
    { title: '服务(25%)', dataIndex: 'service_score', width: 90 },
    {
      title: '总分', dataIndex: 'total_score', width: 80,
      render: (v: number) => v ? <span style={{ fontWeight: 600 }}>{Number(v).toFixed(1)}</span> : '-',
    },
    {
      title: '等级', dataIndex: 'level', width: 100,
      render: (v: string) => v ? <Tag color={qualStatusColors[v]}>{evalLevelLabels[v] || v}</Tag> : '-',
    },
    { title: '评价日期', dataIndex: 'evaluation_date', width: 110 },
    {
      title: '操作', width: 80, fixed: 'right',
      render: (_: unknown, r: Record<string, unknown>) => (
        <Popconfirm
          title="确定要删除该评价吗？"
          onConfirm={() => deleteMutation.mutate(r.id as number)}
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
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setShowCreate(true)}>新增评价</Button>
      </div>
      <Table rowKey="id" columns={columns} dataSource={data?.items || []} loading={isLoading}
        pagination={{ current: page, total: data?.total || 0, pageSize: 20, onChange: setPage }}
      />
      <Modal title="供应商年度评价" open={showCreate} onCancel={() => setShowCreate(false)} onOk={() => form.submit()} destroyOnClose width={500}>
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="supplier_id" label="供应商ID" rules={[{ required: true }]}><Input type="number" /></Form.Item>
          <Form.Item name="year" label="年度" rules={[{ required: true }]}><InputNumber style={{ width: '100%' }} min={2020} max={2030} /></Form.Item>
          <Form.Item name="quality_score" label="质量评分 (满分100，权重25%)"><InputNumber min={0} max={100} style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="delivery_score" label="交期评分 (满分100，权重25%)"><InputNumber min={0} max={100} style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="price_score" label="价格评分 (满分100，权重25%)"><InputNumber min={0} max={100} style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="service_score" label="服务配合评分 (满分100，权重25%)"><InputNumber min={0} max={100} style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="notes" label="评价说明"><Input.TextArea rows={3} /></Form.Item>
          <div style={{ background: '#f5f5f5', padding: 12, borderRadius: 6, fontSize: 13 }}>
            <strong>评价标准：</strong><br/>
            90分以上：优选供应商<br/>
            70-89分：合格供应商<br/>
            60-69分：观察供应商（限制使用）<br/>
            60分以下：淘汰（移出合格名录）
          </div>
        </Form>
      </Modal>
    </Card>
  )
}


function QualifiedDirectoryTab() {
  const { fmtDate } = useFormat()
  const [params, setParams] = useState<Record<string, unknown>>({ page: 1, size: 20, qualification_status: 'QUALIFIED' })
  const { data, isLoading } = usePageQuery<Supplier>(['suppliers-directory', params], '/suppliers', params)

  const columns = [
    { title: '编码', dataIndex: 'code', width: 100 },
    { title: '名称', dataIndex: 'name', width: 160 },
    { title: '类型', dataIndex: 'type', width: 80, render: (v: string) => supplierTypeLabels[v] ?? v },
    {
      title: '业务分类', dataIndex: 'categories', width: 200, ellipsis: true,
      render: (_: unknown, record: Supplier) => {
        const cats = record.categories || []
        return (
          <Space size={[0, 4]} wrap>
            {cats.map((c) => <Tag key={c.id} color={c.level === 1 ? 'cyan' : 'blue'} style={{ margin: 0 }}>{c.name}</Tag>)}
          </Space>
        )
      },
    },
    { title: '联系人', dataIndex: 'contact_person', width: 100 },
    { title: '电话', dataIndex: 'contact_phone', width: 120 },
    { title: '评分', dataIndex: 'evaluation_score', width: 80, render: (v: number) => v ? <span>{v}分</span> : '-' },
    { title: '等级', dataIndex: 'evaluation_level', width: 80, render: (v: string) => v ? <Tag color={qualStatusColors[v]}>{evalLevelLabels[v] || v}</Tag> : '-' },
    { title: '准入日期', dataIndex: 'admission_date', width: 110, render: (v: string) => fmtDate(v) },
    { title: '首选', dataIndex: 'is_preferred', width: 60, render: (v: boolean) => v ? <Tag color="gold">是</Tag> : '-' },
  ]

  return (
    <Card title="合格供应商名录" extra={<Tag color="green">{data?.total ?? 0} 家合格供应商</Tag>}>
      <Table rowKey="id" columns={columns} dataSource={data?.items} loading={isLoading}
        pagination={{ current: data?.page, pageSize: data?.size, total: data?.total, showTotal: (t) => `共 ${t} 条`, onChange: (p, s) => setParams((prev) => ({ ...prev, page: p, size: s })) }}
      />
    </Card>
  )
}
