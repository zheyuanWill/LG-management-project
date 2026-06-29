import { useMemo, useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { Alert, Button, Card, Form, Image, Input, Modal, Select, Space, Table, Tag, Upload, message } from 'antd'
import { PlusOutlined, RobotOutlined, UploadOutlined } from '@ant-design/icons'
import { http } from '@lg/api-client'
import { useApiQuery, usePageQuery } from '@lg/react-hooks'
import { PageHeader } from '@/components/common'
import { useFormat } from '@/hooks/useFormat'

export const Route = createFileRoute('/_authenticated/ship-repair/daily-logs')({
  component: DailyLogsPage,
})

interface ProjectRecord {
  id: number
  project_name: string
  vessel_name: string
}

interface DailyLogRecord {
  id: number
  project_id: number
  log_date: string
  reporter_id: number
  work_done?: string
  discoveries?: string
  tomorrow_plan?: string
  notes?: string
  ai_processed: boolean
  ai_processed_at?: string
  ai_summary?: string
  attachments?: Array<{ id: number; file_name: string; file_path: string }>
  created_at: string
}

function DailyLogsPage() {
  const { fmtDate } = useFormat()
  const [projectId, setProjectId] = useState<number | undefined>()
  const [params, setParams] = useState<Record<string, unknown>>({ page: 1, size: 20 })
  const [createOpen, setCreateOpen] = useState(false)
  const [detailOpen, setDetailOpen] = useState(false)
  const [currentRecord, setCurrentRecord] = useState<DailyLogRecord | null>(null)
  const [saving, setSaving] = useState(false)
  const [aiLoading, setAiLoading] = useState(false)
  const [fileList, setFileList] = useState<any[]>([])
  const [form] = Form.useForm()

  const { data: projectsData } = useApiQuery<{ items?: ProjectRecord[] }>(
    ['ship-repair-projects-for-logs'],
    '/ship-repair/projects',
    { page: 1, size: 200 }
  )

  const projectOptions = (projectsData?.items ?? []).map((p) => ({
    value: p.id,
    label: `${p.project_name} / ${p.vessel_name}`,
  }))

  const logsPath = useMemo(() => projectId ? `/ship-repair/projects/${projectId}/daily-logs` : '', [projectId])

  const { data, isLoading, refetch } = usePageQuery<DailyLogRecord>(
    ['ship-repair-daily-logs', projectId, params],
    logsPath,
    projectId ? params : undefined,
    { enabled: !!projectId }
  )

  const handleCreate = async (values: any) => {
    if (!projectId) {
      message.warning('请先选择项目')
      return
    }
    setSaving(true)
    try {
      const res = await http.post<DailyLogRecord>(`/ship-repair/projects/${projectId}/daily-logs`, values)
      const logId = res.id

      console.log('准备上传图片，文件列表：', fileList)
      for (const fileItem of fileList) {
        if (fileItem.originFileObj) {
          console.log('正在上传：', fileItem.originFileObj.name)
          await http.upload(`/ship-repair/daily-logs/${logId}/attachments`, fileItem.originFileObj, {
            description: values.notes || '',
          })
        }
      }

      message.success('监修记录创建成功')
      setCreateOpen(false)
      setFileList([])
      form.resetFields()
      refetch()
    } catch (e) {
      console.error('创建失败：', e)
      message.error(e instanceof Error ? e.message : '创建监修记录失败')
    } finally {
      setSaving(false)
    }
  }

  const handleAiProcess = async (record: DailyLogRecord) => {
    setAiLoading(true)
    try {
      const res = await http.post<any>(`/ship-repair/daily-logs/${record.id}/ai-process`)
      message.success(res.summary || 'AI处理完成')
      refetch()
    } catch (e) {
      message.error(e instanceof Error ? e.message : 'AI处理失败')
    } finally {
      setAiLoading(false)
    }
  }

  const columns = [
    { title: '日期', dataIndex: 'log_date', key: 'log_date', width: 120, render: (v: string) => fmtDate(v) },
    { title: '今天干了什么', dataIndex: 'work_done', key: 'work_done', ellipsis: true },
    { title: '今天发现了什么', dataIndex: 'discoveries', key: 'discoveries', ellipsis: true },
    { title: '明天准备干什么', dataIndex: 'tomorrow_plan', key: 'tomorrow_plan', ellipsis: true },
    {
      title: 'AI状态', dataIndex: 'ai_processed', key: 'ai_processed', width: 120,
      render: (v: boolean) => <Tag color={v ? 'success' : 'default'}>{v ? '已处理' : '未处理'}</Tag>,
    },
    {
      title: '操作', key: 'actions', width: 220,
      render: (_: unknown, record: DailyLogRecord) => (
        <Space size={0}>
          <Button type="link" size="small" onClick={() => { setCurrentRecord(record); setDetailOpen(true) }}>查看</Button>
          <Button type="link" size="small" icon={<RobotOutlined />} loading={aiLoading} onClick={() => handleAiProcess(record)}>AI处理</Button>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <PageHeader
        title="监修记录 Daily Logs"
        extra={<Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)} disabled={!projectId}>新增记录</Button>}
      />

      <Alert
        style={{ marginBottom: 16 }}
        type="info"
        showIcon
        message="监修工只需要写三件事：今天干了什么、今天发现了什么、明天准备干什么。提交后再点击“AI处理”。"
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

      <Table
        rowKey="id"
        columns={columns}
        dataSource={data?.items ?? []}
        loading={isLoading}
        pagination={{
          current: data?.page,
          pageSize: data?.size,
          total: data?.total,
          showTotal: (t) => `共 ${t} 条`,
          onChange: (page, size) => setParams((prev) => ({ ...prev, page, size })),
        }}
      />

      <Modal title="新增监修记录" open={createOpen} onCancel={() => setCreateOpen(false)} onOk={() => form.submit()} confirmLoading={saving} width={900}>
        <Form form={form} layout="vertical" onFinish={handleCreate} initialValues={{ log_date: new Date().toISOString().slice(0, 10) }}>
          <Form.Item name="log_date" label="记录日期" rules={[{ required: true }]}>
            <Input type="date" />
          </Form.Item>
          <Form.Item name="work_done" label="今天干了什么" rules={[{ required: true }]}>
            <Input.TextArea rows={4} placeholder="例如：完成曲轴测量、拆检主机缸头" />
          </Form.Item>
          <Form.Item name="discoveries" label="今天发现了什么">
            <Input.TextArea rows={4} placeholder="例如：发现2号缸套磨损严重、供应商通知备件延期" />
          </Form.Item>
          <Form.Item name="tomorrow_plan" label="明天准备干什么">
            <Input.TextArea rows={4} placeholder="例如：明天开始更换缸套" />
          </Form.Item>
          <Form.Item name="notes" label="备注">
            <Input.TextArea rows={3} />
          </Form.Item>
          <Form.Item label="附件图片">
            <Upload
              multiple
              beforeUpload={() => false}
              fileList={fileList}
              onChange={({ fileList: newFileList }) => {
                // 确保每个文件都有originFileObj
                const processedList = newFileList.map(item => {
                  if (item.originFileObj) return item
                  // 如果没有，尝试从file属性中获取
                  return {
                    ...item,
                    originFileObj: (item as any).file || item.originFileObj
                  }
                })
                setFileList(processedList)
              }}
            >
              <Button icon={<UploadOutlined />}>选择图片</Button>
            </Upload>
          </Form.Item>
        </Form>
      </Modal>

      <Modal title="监修记录详情" open={detailOpen} onCancel={() => setDetailOpen(false)} footer={null} width={900}>
        {currentRecord && (
          <Card bordered={false}>
            <p><strong>日期：</strong>{fmtDate(currentRecord.log_date)}</p>
            <p><strong>今天干了什么：</strong>{currentRecord.work_done || '-'}</p>
            <p><strong>今天发现了什么：</strong>{currentRecord.discoveries || '-'}</p>
            <p><strong>明天准备干什么：</strong>{currentRecord.tomorrow_plan || '-'}</p>
            <p><strong>备注：</strong>{currentRecord.notes || '-'}</p>
            <p><strong>AI摘要：</strong>{currentRecord.ai_summary || '-'}</p>
            <div>
              <strong>附件图片：</strong>
              <div style={{ marginTop: 8, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                {currentRecord.attachments?.length ? (
                  currentRecord.attachments.map((a) => (
                    <Image
                      key={a.id}
                      src={a.file_path}
                      alt={a.file_name}
                      width={120}
                      height={120}
                      style={{ objectFit: 'cover', borderRadius: 4 }}
                    />
                  ))
                ) : (
                  '-'
                )}
              </div>
            </div>
          </Card>
        )}
      </Modal>
    </div>
  )
}
