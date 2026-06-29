import { useEffect, useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { Table, Button, Form, Input, Modal, message, Select, DatePicker, Space, Tag, Popconfirm, Descriptions, Alert } from 'antd'
import { PlusOutlined, EyeOutlined, CheckOutlined, CloseOutlined, RobotOutlined } from '@ant-design/icons'
import { usePageQuery, useApiPost, useApiQuery } from '@lg/react-hooks'
import { PageHeader } from '@/components/common'
import { useFormat } from '@/hooks/useFormat'
import type { PageResponse } from '@lg/api-client'
import { http } from '@lg/api-client'
import { useQueryClient } from '@tanstack/react-query'
import dayjs from 'dayjs'

const { TextArea } = Input
const { Option } = Select

export const Route = createFileRoute('/_authenticated/ship-repair/ncrs')({
  component: IssuesNCRPage,
})

interface NCR {
  id: number
  ncr_number: string
  order_id: number
  task_id?: number
  anomaly_id?: number
  issue_description: string
  discovered_by: number
  discovered_date: string
  responsible_party: string
  priority: string
  responsible_person?: string
  rectification_deadline?: string
  root_cause_analysis?: string
  rectification_requirements?: string
  rectification_responsible_id?: number
  planned_completion_date?: string
  rectification_measures?: string
  review_result?: string
  closed_by?: number
  closed_at?: string
  status: string
  created_at: string
  updated_at: string
}

function IssuesNCRPage() {
  const { fmtDate } = useFormat()
  const queryClient = useQueryClient()
  const [params, setParams] = useState<Record<string, unknown>>({ page: 1, size: 20 })
  const [createOpen, setCreateOpen] = useState(false)
  const [viewOpen, setViewOpen] = useState(false)
  const [aiAnalysisOpen, setAiAnalysisOpen] = useState(false)
  const [aiAnalysisLoading, setAiAnalysisLoading] = useState(false)
  const [aiAnalysisResult, setAiAnalysisResult] = useState<any>(null)
  const [currentRecord, setCurrentRecord] = useState<NCR | null>(null)
  const [form] = Form.useForm()

  useEffect(() => {
    if (createOpen) {
      const now = dayjs()
      form.setFieldsValue({
        ncr_number: `NCR-${now.format('YYYYMMDD')}-001`,
        discovered_date: now,
        priority: 'MEDIUM',
        responsible_party: 'SHIPYARD',
        discovered_by: 1,
      })
    }
  }, [createOpen, form])

  const { data, isLoading } = usePageQuery<NCR>(
    ['ship-repair/ncrs', params],
    '/ship-repair/ncrs',
    params
  )

  const { data: ordersData } = useApiQuery<PageResponse<{ id: number; order_no: string }>>(
    ['orders', 'select'],
    '/orders',
    { size: 200 }
  )
  
  const orderOptions = (ordersData?.items ?? []).map((o) => ({
    value: o.id,
    label: o.order_no
  }))

  const createMutation = useApiPost<NCR>('/ship-repair/ncrs', {
    invalidateKeys: [['ship-repair/ncrs']],
    onSuccess: () => { message.success('提交成功'); setCreateOpen(false); form.resetFields() },
  })

  const handleAiAnalysis = async (record: NCR) => {
    setCurrentRecord(record)
    setAiAnalysisOpen(true)
    setAiAnalysisLoading(true)
    setAiAnalysisResult(null)
    try {
      const response = await http.post(`/ship-repair/ncrs/${record.id}/ai-risk-analysis`)
      setAiAnalysisResult(response.data)
    } catch (e) {
      message.error(e instanceof Error ? e.message : 'AI分析失败')
      setAiAnalysisOpen(false)
    } finally {
      setAiAnalysisLoading(false)
    }
  }

  const statusColor: Record<string, string> = {
    PENDING: 'default',
    IN_PROGRESS: 'processing',
    PENDING_REVIEW: 'orange',
    CLOSED: 'success',
    OVERDUE: 'error',
    CANCELLED: 'default',
  }

  const statusText: Record<string, string> = {
    PENDING: '待处理',
    IN_PROGRESS: '处理中',
    PENDING_REVIEW: '待复查',
    CLOSED: '已关闭',
    OVERDUE: '已逾期',
    CANCELLED: '已取消',
  }

  const priorityColor: Record<string, string> = {
    URGENT: 'red',
    HIGH: 'orange',
    MEDIUM: 'blue',
    LOW: 'default',
  }

  const priorityText: Record<string, string> = {
    URGENT: '紧急',
    HIGH: '高',
    MEDIUM: '中',
    LOW: '低',
  }

  const columns = [
    { title: '编号', dataIndex: 'ncr_number', key: 'ncr_number', width: 160 },
    {
      title: '关联订单', dataIndex: 'order_id', key: 'order_id', width: 130,
      render: (id: number) => orderOptions.find(o => o.value === id)?.label || id,
    },
    { title: '问题描述', dataIndex: 'issue_description', key: 'issue_description', width: 280, ellipsis: true },
    {
      title: '优先级', dataIndex: 'priority', key: 'priority', width: 90,
      render: (p: string) => <Tag color={priorityColor[p] || 'default'}>{priorityText[p] || p}</Tag>,
    },
    {
      title: '状态', dataIndex: 'status', key: 'status', width: 100,
      render: (s: string) => <Tag color={statusColor[s] || 'default'}>{statusText[s] || s}</Tag>,
    },
    {
      title: '整改期限', dataIndex: 'rectification_deadline', key: 'rectification_deadline', width: 110,
      render: (v: string) => v ? fmtDate(v) : '-',
    },
    { title: '负责人', dataIndex: 'responsible_person', key: 'responsible_person', width: 100, render: (v: string) => v || '-' },
    {
      title: '操作', key: 'actions', width: 160, fixed: 'right' as const,
      render: (_: unknown, record: NCR) => (
        <Space size={0}>
          <Button type="link" size="small" icon={<EyeOutlined />} onClick={() => { setCurrentRecord(record); setViewOpen(true) }}>查看</Button>
          <Button type="link" size="small" icon={<RobotOutlined />} onClick={() => handleAiAnalysis(record)}>AI分析</Button>
        </Space>
      ),
    },
  ]

  const handleFormSubmit = (values: any) => {
    const payload: Record<string, unknown> = { ...values, status: 'PENDING' }
    if (values.discovered_date) payload.discovered_date = values.discovered_date.format('YYYY-MM-DD')
    if (values.rectification_deadline) payload.rectification_deadline = values.rectification_deadline.format('YYYY-MM-DD')
    createMutation.mutate(payload)
  }

  return (
    <div>
      <PageHeader title="问题/NCR" extra={<Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>上报问题/NCR</Button>} />
      <Form layout="inline" onFinish={(v) => setParams({ ...v, page: 1, size: 20 })} style={{ marginBottom: 16 }}>
        <Form.Item name="order_id">
          <Select placeholder="按订单筛选" showSearch optionFilterProp="label" options={orderOptions} allowClear style={{ width: 160 }} />
        </Form.Item>
        <Form.Item name="status">
          <Select placeholder="按状态筛选" allowClear style={{ width: 140 }}>
            <Option value="PENDING">待处理</Option>
            <Option value="IN_PROGRESS">处理中</Option>
            <Option value="CLOSED">已关闭</Option>
          </Select>
        </Form.Item>
        <Form.Item><Button type="primary" htmlType="submit">搜索</Button></Form.Item>
      </Form>
      <Table
        rowKey="id"
        columns={columns}
        dataSource={data?.items}
        loading={isLoading}
        scroll={{ x: 1300 }}
        pagination={{
          current: data?.page,
          pageSize: data?.size,
          total: data?.total,
          showTotal: (t) => `共 ${t} 条`,
          onChange: (p, s) => setParams((prev) => ({ ...prev, page: p, size: s })),
        }}
      />

      <Modal title="上报问题/NCR" open={createOpen} onCancel={() => { setCreateOpen(false); form.resetFields() }} onOk={() => form.submit()} confirmLoading={createMutation.isPending} width={800}>
        <Alert message="监修过程中发现的任何异常、质量问题、安全隐患请在此上报，系统将自动开启NCR流程。" type="info" showIcon style={{ marginBottom: 16 }} />
        <Form form={form} layout="vertical" onFinish={handleFormSubmit}>
          <Form.Item name="order_id" label="关联订单/船舶" rules={[{ required: true }]}>
            <Select placeholder="选择订单" showSearch optionFilterProp="label" options={orderOptions} />
          </Form.Item>
          <Form.Item name="ncr_number" label="问题编号" rules={[{ required: true }]}>
            <Input placeholder="例如: NCR-20240101-001" />
          </Form.Item>
          <Form.Item name="issue_description" label="问题描述" rules={[{ required: true }]}>
            <TextArea rows={6} placeholder="请详细描述发现的问题、位置、影响范围..." />
          </Form.Item>
          <Form.Item name="priority" label="优先级" rules={[{ required: true }]}>
            <Select>
              <Option value="URGENT">紧急</Option>
              <Option value="HIGH">高</Option>
              <Option value="MEDIUM">中</Option>
              <Option value="LOW">低</Option>
            </Select>
          </Form.Item>
          <Form.Item name="responsible_person" label="负责人/责任方">
            <Input placeholder="例如: 张三 或 某某船厂" />
          </Form.Item>
          <Form.Item name="rectification_deadline" label="整改期限">
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="discovered_date" label="发现日期" rules={[{ required: true }]}>
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal title="查看NCR" open={viewOpen} onCancel={() => setViewOpen(false)} footer={[<Button key="close" onClick={() => setViewOpen(false)}>关闭</Button>]} width={900}>
        {currentRecord && (
          <Descriptions bordered column={2}>
            <Descriptions.Item label="NCR编号" span={2}>{currentRecord.ncr_number}</Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={statusColor[currentRecord.status]}>{statusText[currentRecord.status] || currentRecord.status}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="优先级">
              <Tag color={priorityColor[currentRecord.priority]}>{priorityText[currentRecord.priority] || currentRecord.priority}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="问题描述" span={2}>{currentRecord.issue_description}</Descriptions.Item>
            <Descriptions.Item label="发现日期">{fmtDate(currentRecord.discovered_date)}</Descriptions.Item>
            <Descriptions.Item label="负责人/责任方">{currentRecord.responsible_person || '-'}</Descriptions.Item>
            <Descriptions.Item label="整改期限">{currentRecord.rectification_deadline ? fmtDate(currentRecord.rectification_deadline) : '-'}</Descriptions.Item>
            <Descriptions.Item label="计划完成日期">{currentRecord.planned_completion_date ? fmtDate(currentRecord.planned_completion_date) : '-'}</Descriptions.Item>
            {currentRecord.root_cause_analysis && (
              <Descriptions.Item label="根本原因分析" span={2}>{currentRecord.root_cause_analysis}</Descriptions.Item>
            )}
            {currentRecord.rectification_measures && (
              <Descriptions.Item label="整改措施" span={2}>{currentRecord.rectification_measures}</Descriptions.Item>
            )}
            {currentRecord.review_result && (
              <Descriptions.Item label="复查结果" span={2}>{currentRecord.review_result}</Descriptions.Item>
            )}
            {currentRecord.closed_at && (
              <Descriptions.Item label="关闭时间" span={2}>{fmtDate(currentRecord.closed_at)}</Descriptions.Item>
            )}
            <Descriptions.Item label="创建时间">{fmtDate(currentRecord.created_at)}</Descriptions.Item>
            <Descriptions.Item label="更新时间">{fmtDate(currentRecord.updated_at)}</Descriptions.Item>
          </Descriptions>
        )}
      </Modal>

      <Modal title={<><RobotOutlined /> AI风险与事件分析</>} open={aiAnalysisOpen} onCancel={() => setAiAnalysisOpen(false)} footer={[<Button key="close" onClick={() => setAiAnalysisOpen(false)}>关闭</Button>]} width={900}>
        {aiAnalysisLoading && <Alert message="AI正在根据问题/NCR生成风险和事件分析..." type="info" showIcon />}
        {!aiAnalysisLoading && aiAnalysisResult && (
          <Descriptions bordered column={1}>
            <Descriptions.Item label="NCR编号">{currentRecord?.ncr_number}</Descriptions.Item>
            <Descriptions.Item label="分析摘要">{aiAnalysisResult.summary}</Descriptions.Item>
            <Descriptions.Item label="风险等级">
              <Tag color={priorityColor[aiAnalysisResult.risk_level] || 'default'}>{aiAnalysisResult.risk_level}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="风险点">{(aiAnalysisResult.risk_points || []).join('；') || '-'}</Descriptions.Item>
            <Descriptions.Item label="根因分析">{aiAnalysisResult.root_cause_analysis || '-'}</Descriptions.Item>
            <Descriptions.Item label="影响评估">
              {aiAnalysisResult.impact_assessment
                ? Object.entries(aiAnalysisResult.impact_assessment).map(([k, v]) => <div key={k}><strong>{k}:</strong> {String(v)}</div>)
                : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="建议措施">{(aiAnalysisResult.recommended_actions || []).join('；') || '-'}</Descriptions.Item>
            <Descriptions.Item label="纠正措施">{(aiAnalysisResult.corrective_actions || []).join('；') || '-'}</Descriptions.Item>
            <Descriptions.Item label="预防措施">{(aiAnalysisResult.preventive_actions || []).join('；') || '-'}</Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </div>
  )
}
