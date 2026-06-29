import { useMemo, useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { Button, Form, Input, Modal, Select, Space, Table, Tag, message } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { http } from '@lg/api-client'
import { useApiQuery } from '@lg/react-hooks'
import { PageHeader } from '@/components/common'

export const Route = createFileRoute('/_authenticated/ship-repair/tasks')({
  component: TasksPage,
})

interface ProjectRecord {
  id: number
  project_name: string
  vessel_name: string
}

interface TaskRecord {
  id: number
  project_id: number
  task_name: string
  description?: string
  category: string
  status: string
  planned_start?: string
  planned_end?: string
  actual_start?: string
  actual_end?: string
  ai_generated: boolean
  sort_order: number
  notes?: string
}

function TasksPage() {
  const [projectId, setProjectId] = useState<number | undefined>()
  const [createOpen, setCreateOpen] = useState(false)
  const [editRecord, setEditRecord] = useState<TaskRecord | null>(null)
  const [saving, setSaving] = useState(false)
  const [form] = Form.useForm()

  const { data: projectsData } = useApiQuery<{ items?: ProjectRecord[] }>(
    ['ship-repair-projects-for-tasks'],
    '/ship-repair/projects',
    { page: 1, size: 200 }
  )

  const projectOptions = (projectsData?.items ?? []).map((p) => ({
    value: p.id,
    label: `${p.project_name} / ${p.vessel_name}`,
  }))

  const tasksQueryPath = useMemo(() => projectId ? `/ship-repair/projects/${projectId}/tasks` : '', [projectId])

  const { data: tasksData, refetch, isLoading } = useApiQuery<TaskRecord[]>(
    ['ship-repair-tasks', projectId],
    tasksQueryPath,
    undefined,
    { enabled: !!projectId }
  )

  const handleCreate = async (values: any) => {
    if (!projectId) {
      message.warning('请先选择项目')
      return
    }
    setSaving(true)
    try {
      await http.post(`/ship-repair/projects/${projectId}/tasks`, values)
      message.success('任务创建成功')
      setCreateOpen(false)
      form.resetFields()
      refetch()
    } catch (e) {
      message.error(e instanceof Error ? e.message : '任务创建失败')
    } finally {
      setSaving(false)
    }
  }

  const handleUpdate = async (values: any) => {
    if (!editRecord) return
    setSaving(true)
    try {
      await http.put(`/ship-repair/tasks/${editRecord.id}`, values)
      message.success('任务更新成功')
      setEditRecord(null)
      form.resetFields()
      refetch()
    } catch (e) {
      message.error(e instanceof Error ? e.message : '任务更新失败')
    } finally {
      setSaving(false)
    }
  }

  const columns = [
    { title: '任务名称', dataIndex: 'task_name', key: 'task_name', width: 220 },
    { title: '类别', dataIndex: 'category', key: 'category', width: 120 },
    {
      title: '状态', dataIndex: 'status', key: 'status', width: 120,
      render: (v: string) => <Tag color={v === 'COMPLETED' ? 'success' : v === 'IN_PROGRESS' ? 'processing' : v === 'CANCELLED' ? 'default' : 'warning'}>{v}</Tag>,
    },
    { title: 'AI生成', dataIndex: 'ai_generated', key: 'ai_generated', width: 100, render: (v: boolean) => v ? '是' : '否' },
    { title: '说明', dataIndex: 'description', key: 'description', ellipsis: true },
    {
      title: '操作', key: 'actions', width: 140,
      render: (_: unknown, record: TaskRecord) => (
        <Button
          type="link"
          size="small"
          onClick={() => {
            setEditRecord(record)
            form.setFieldsValue(record)
          }}
        >
          编辑
        </Button>
      ),
    },
  ]

  return (
    <div>
      <PageHeader
        title="任务 Tasks"
        extra={<Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)} disabled={!projectId}>新增任务</Button>}
      />

      <div style={{ marginBottom: 16 }}>
        <Select
          placeholder="先选择项目"
          options={projectOptions}
          value={projectId}
          onChange={setProjectId}
          style={{ width: 320 }}
          allowClear
          showSearch
          optionFilterProp="label"
        />
      </div>

      <Table rowKey="id" columns={columns} dataSource={tasksData ?? []} loading={isLoading} />

      <Modal title="新增任务" open={createOpen} onCancel={() => setCreateOpen(false)} onOk={() => form.submit()} confirmLoading={saving}>
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="task_name" label="任务名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="description" label="任务说明">
            <Input.TextArea rows={4} />
          </Form.Item>
          <Form.Item name="category" label="任务类别" initialValue="OTHER">
            <Select options={[
              { value: 'ENGINE', label: 'ENGINE' },
              { value: 'ELECTRICAL', label: 'ELECTRICAL' },
              { value: 'HULL', label: 'HULL' },
              { value: 'PAINTING', label: 'PAINTING' },
              { value: 'PIPING', label: 'PIPING' },
              { value: 'DECK', label: 'DECK' },
              { value: 'SAFETY', label: 'SAFETY' },
              { value: 'CLASS_SURVEY', label: 'CLASS_SURVEY' },
              { value: 'OTHER', label: 'OTHER' },
            ]} />
          </Form.Item>
          <Form.Item name="notes" label="备注">
            <Input.TextArea rows={3} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal title="编辑任务" open={!!editRecord} onCancel={() => { setEditRecord(null); form.resetFields() }} onOk={() => form.submit()} confirmLoading={saving}>
        <Form form={form} layout="vertical" onFinish={handleUpdate}>
          <Form.Item name="task_name" label="任务名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="description" label="任务说明">
            <Input.TextArea rows={4} />
          </Form.Item>
          <Form.Item name="category" label="任务类别">
            <Select options={[
              { value: 'ENGINE', label: 'ENGINE' },
              { value: 'ELECTRICAL', label: 'ELECTRICAL' },
              { value: 'HULL', label: 'HULL' },
              { value: 'PAINTING', label: 'PAINTING' },
              { value: 'PIPING', label: 'PIPING' },
              { value: 'DECK', label: 'DECK' },
              { value: 'SAFETY', label: 'SAFETY' },
              { value: 'CLASS_SURVEY', label: 'CLASS_SURVEY' },
              { value: 'OTHER', label: 'OTHER' },
            ]} />
          </Form.Item>
          <Form.Item name="status" label="状态">
            <Select options={[
              { value: 'PENDING', label: 'PENDING' },
              { value: 'IN_PROGRESS', label: 'IN_PROGRESS' },
              { value: 'COMPLETED', label: 'COMPLETED' },
              { value: 'CANCELLED', label: 'CANCELLED' },
            ]} />
          </Form.Item>
          <Form.Item name="notes" label="备注">
            <Input.TextArea rows={3} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
