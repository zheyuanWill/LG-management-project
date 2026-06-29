import { useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import {
  Table, Button, Form, Input, Modal, message, Select,
  DatePicker, Space, Tag, Card, Row, Col, Spin, Alert,
  Divider, Descriptions, Progress, Slider
} from 'antd'
import {
  PlusOutlined, EyeOutlined, RobotOutlined,
  ThunderboltOutlined, EditOutlined
} from '@ant-design/icons'
import { usePageQuery, useApiPost, useApiQuery } from '@lg/react-hooks'
import { PageHeader } from '@/components/common'
import { useFormat } from '@/hooks/useFormat'
import type { PageResponse } from '@lg/api-client'
import { http } from '@lg/api-client'
import { useQueryClient } from '@tanstack/react-query'

const { TextArea } = Input
const { Option } = Select

export const Route = createFileRoute('/_authenticated/ship-repair/repair-plans')({
  component: RepairPlansPage,
})

interface RepairPlan {
  id: number
  order_id: number
  plan_name: string
  vessel_name?: string
  plan_text?: string
  plan_duration_days?: number
  start_date?: string
  end_date?: string
  progress: number
  status: string
  ai_disassembled: boolean
  ai_task_output?: any[]
  human_confirmed: boolean
  notes?: string
  created_at: string
  updated_at: string
}

interface AIDisassembledTask {
  task_name: string
  sub_tasks?: string[]
  category: string
  estimated_days?: number
  estimated_hours?: number
  planned_start_date?: string
  planned_end_date?: string
  start_condition?: string
  dependencies?: string[]
  can_parallel?: boolean
  critical_path?: boolean
  is_critical_path?: boolean
  related_spare_parts?: string
  spare_parts?: Array<{ name: string; spec?: string; quantity: number; is_critical?: boolean }>
  required_staff?: Record<string, number | string | undefined>
  risk_points?: string[]
  priority?: string
  responsible_party?: string
  risk_level?: string
  required_photo_evidence?: string[]
  daily_check_points?: string
  delay_impact?: string
  remarks?: string
}

function RepairPlansPage() {
  const { fmtDate } = useFormat()
  const queryClient = useQueryClient()
  const [params, setParams] = useState<Record<string, unknown>>({ page: 1, size: 20 })
  const [createOpen, setCreateOpen] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [viewOpen, setViewOpen] = useState(false)
  const [aiModalOpen, setAiModalOpen] = useState(false)
  const [currentRecord, setCurrentRecord] = useState<RepairPlan | null>(null)
  const [aiBreakdownResult, setAiBreakdownResult] = useState<any>(null)
  const [isAiLoading, setIsAiLoading] = useState(false)
  const [createForm] = Form.useForm()
  const [editForm] = Form.useForm()

  const { data, isLoading } = usePageQuery<RepairPlan>(
    ['ship-repair/repair-plans', params],
    '/ship-repair/repair-plans',
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

  const createMutation = useApiPost<RepairPlan>('/ship-repair/repair-plans', {
    invalidateKeys: [['ship-repair/repair-plans']],
    onSuccess: () => { message.success('创建成功'); setCreateOpen(false); createForm.resetFields() },
  })

  const handleUpdate = async (id: number, values: Record<string, unknown>) => {
    try {
      await http.put(`/ship-repair/repair-plans/${id}`, values)
      message.success('更新成功')
      queryClient.invalidateQueries({ queryKey: ['ship-repair/repair-plans'] })
      setEditOpen(false)
    } catch (e) {
      message.error(e instanceof Error ? e.message : '更新失败')
    }
  }

  const openEdit = (record: RepairPlan) => {
    setCurrentRecord(record)
    editForm.setFieldsValue({
      progress: record.progress,
      status: record.status,
      notes: record.notes,
    })
    setEditOpen(true)
  }

  const handleAiBreakdown = async (plan: RepairPlan) => {
    setCurrentRecord(plan)
    setAiModalOpen(true)
    setAiBreakdownResult(null)
    
    if (plan.ai_disassembled && plan.ai_task_output) {
      setAiBreakdownResult({
        success: true,
        summary: '已保存的AI拆解结果',
        tasks: plan.ai_task_output
      })
    }
  }

  const executeAiBreakdown = async () => {
    if (!currentRecord) return
    setIsAiLoading(true)
    try {
      const response = await http.post(`/ship-repair/repair-plans/${currentRecord.id}/ai-disassemble`, {
        plan_text: currentRecord.plan_text,
        plan_duration_days: currentRecord.plan_duration_days
      })
      setAiBreakdownResult(response.data)
      message.success('AI拆解完成')
      queryClient.invalidateQueries({ queryKey: ['ship-repair/repair-plans'] })
    } catch (e) {
      message.error(e instanceof Error ? e.message : 'AI拆解失败')
    } finally {
      setIsAiLoading(false)
    }
  }

  const confirmAiBreakdown = async () => {
    if (!currentRecord || !aiBreakdownResult) return
    try {
      await http.post(`/ship-repair/repair-plans/${currentRecord.id}/confirm-ai`, {
        tasks: aiBreakdownResult.tasks,
        notes: 'AI拆解结果已确认'
      })
      message.success('确认成功，已生成任务')
      setAiModalOpen(false)
      queryClient.invalidateQueries({ queryKey: ['ship-repair/repair-plans'] })
    } catch (e) {
      message.error(e instanceof Error ? e.message : '确认失败')
    }
  }

  const statusColor: Record<string, string> = {
    NOT_STARTED: 'default',
    IN_PROGRESS: 'processing',
    COMPLETED: 'success',
  }

  const statusText: Record<string, string> = {
    NOT_STARTED: '未开始',
    IN_PROGRESS: '进行中',
    COMPLETED: '已完成',
  }

  const getCategoryText = (category: string) => {
    switch (category) {
      case 'DOCKING': return '坞修'
      case 'ENGINE': return '轮机'
      case 'ELECTRICAL': return '电气'
      case 'PAINTING': return '涂装'
      case 'SPARE_PARTS': return '备件'
      case 'CLASS_SOCIETY': return '船级社'
      case 'OTHER': return '其他'
      default: return category
    }
  }

  const getRiskLevelColor = (level: string) => {
    switch (level) {
      case 'LOW': return 'green'
      case 'MEDIUM': return 'orange'
      case 'HIGH': return 'red'
      case 'URGENT': return 'red'
      default: return 'default'
    }
  }

  const getRiskLevelText = (level: string) => {
    switch (level) {
      case 'LOW': return '低'
      case 'MEDIUM': return '中'
      case 'HIGH': return '高'
      case 'URGENT': return '紧急'
      default: return level
    }
  }

  const getSourceText = (source: string) => {
    switch (source) {
      case 'SHIPOWNER': return '船东'
      case 'SHIPYARD': return '船厂'
      case 'DOCK_MEETING': return '进坞会议'
      case 'INTERNAL': return '内部'
      default: return source
    }
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
    { title: '计划名称', dataIndex: 'plan_name', key: 'plan_name', width: 200 },
    { title: '船名', dataIndex: 'vessel_name', key: 'vessel_name', width: 120, render: (v: string) => v || '-' },
    { title: '关联订单', dataIndex: 'order_id', key: 'order_id', width: 120, render: (id: number) => {
      const order = orderOptions.find(o => o.value === id)
      return order?.label || id
    }},
    { title: '工期(天)', dataIndex: 'plan_duration_days', key: 'plan_duration_days', width: 100, render: (d: number) => d ? `${d}天` : '-' },
    { title: '进度', dataIndex: 'progress', key: 'progress', width: 140, render: (p: number) => <Progress percent={p} size="small" /> },
    { title: '状态', dataIndex: 'status', key: 'status', width: 100, render: (s: string) => <Tag color={statusColor[s] || 'default'}>{statusText[s] || s}</Tag> },
    { title: 'AI拆解', key: 'ai', width: 80, render: (_: any, r: RepairPlan) => r.ai_disassembled ? <Tag color="blue">已拆解</Tag> : <Tag>未拆解</Tag> },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 150, render: (v: string) => fmtDate(v) },
    { title: '操作', key: 'actions', width: 220, fixed: 'right' as const, render: (_: unknown, record: RepairPlan) => (
      <Space size={0}>
        <Button type="link" size="small" icon={<EyeOutlined />} onClick={() => { setCurrentRecord(record); setViewOpen(true); }}>查看</Button>
        <Button type="link" size="small" icon={<EditOutlined />} onClick={() => openEdit(record)}>更新进度</Button>
        <Button type="link" size="small" icon={<RobotOutlined />} onClick={() => handleAiBreakdown(record)}>AI拆解</Button>
      </Space>
    ) },
  ]

  return (
    <div>
      <PageHeader title="修船计划" extra={<Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>新建计划</Button>} />
      <Form layout="inline" onFinish={(v) => setParams({ ...v, page: 1, size: 20 })} style={{ marginBottom: 16 }}>
        <Form.Item name="order_id">
          <Select placeholder="订单" showSearch optionFilterProp="label" options={orderOptions} allowClear style={{ width: 160 }} />
        </Form.Item>
        <Form.Item><Button type="primary" htmlType="submit">搜索</Button></Form.Item>
      </Form>
      <Table rowKey="id" columns={columns} dataSource={data?.items} loading={isLoading} scroll={{ x: 1500 }} pagination={{ current: data?.page, pageSize: data?.size, total: data?.total, showTotal: (t) => `共 ${t} 条`, onChange: (p, s) => setParams((prev) => ({ ...prev, page: p, size: s })) }} />

      <Modal title="新建修船计划" open={createOpen} onCancel={() => setCreateOpen(false)} onOk={() => createForm.submit()} confirmLoading={createMutation.isPending} width={800}>
        <Form form={createForm} layout="vertical" onFinish={(v) => createMutation.mutate({ ...v, status: 'DRAFT' })}>
          <Form.Item name="order_id" label="关联订单" rules={[{ required: true }]}>
            <Select placeholder="选择订单" showSearch optionFilterProp="label" options={orderOptions} />
          </Form.Item>
          <Form.Item name="plan_name" label="计划名称" rules={[{ required: true }]}>
            <Input placeholder="例如: 主机大修计划" />
          </Form.Item>
          <Form.Item name="vessel_name" label="船名">
            <Input placeholder="例如: 某某轮" />
          </Form.Item>
          <Form.Item name="plan_duration_days" label="计划工期(天)">
            <Input type="number" min={1} placeholder="例如: 30" />
          </Form.Item>
          <Form.Item name="start_date" label="计划开始日期">
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="end_date" label="计划结束日期">
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="plan_text" label="计划文本(供AI拆解使用)">
            <TextArea rows={6} placeholder="粘贴或输入修船计划的详细内容，AI将自动拆解为具体任务..." />
          </Form.Item>
          <Form.Item name="notes" label="备注">
            <TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>

      {/* Edit/Progress Modal */}
      <Modal title="更新进度与状态" open={editOpen} onCancel={() => setEditOpen(false)} onOk={() => editForm.submit()} width={480}>
        <Form form={editForm} layout="vertical" onFinish={async (v) => { if (!currentRecord) return; await handleUpdate(currentRecord.id, v) }}>
          <Form.Item name="status" label="状态" rules={[{ required: true }]}>
            <Select>
              <Option value="NOT_STARTED">未开始</Option>
              <Option value="IN_PROGRESS">进行中</Option>
              <Option value="COMPLETED">已完成</Option>
            </Select>
          </Form.Item>
          <Form.Item name="progress" label="完成进度 (%)">
            <Slider min={0} max={100} marks={{ 0: '0%', 25: '25%', 50: '50%', 75: '75%', 100: '100%' }} />
          </Form.Item>
          <Form.Item name="notes" label="备注">
            <TextArea rows={3} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal title="查看修船计划" open={viewOpen} onCancel={() => setViewOpen(false)} footer={[<Button key="close" onClick={() => setViewOpen(false)}>关闭</Button>]} width={800}>
        {currentRecord && (
          <Descriptions bordered column={2}>
            <Descriptions.Item label="计划名称" span={2}>{currentRecord.plan_name}</Descriptions.Item>
            <Descriptions.Item label="船名">{currentRecord.vessel_name || '-'}</Descriptions.Item>
            <Descriptions.Item label="关联订单">{orderOptions.find((o) => o.value === currentRecord.order_id)?.label || currentRecord.order_id}</Descriptions.Item>
            <Descriptions.Item label="计划工期">{currentRecord.plan_duration_days ? `${currentRecord.plan_duration_days}天` : '-'}</Descriptions.Item>
            <Descriptions.Item label="状态"><Tag color={statusColor[currentRecord.status]}>{statusText[currentRecord.status] || currentRecord.status}</Tag></Descriptions.Item>
            <Descriptions.Item label="开始日期">{currentRecord.start_date ? fmtDate(currentRecord.start_date) : '-'}</Descriptions.Item>
            <Descriptions.Item label="结束日期">{currentRecord.end_date ? fmtDate(currentRecord.end_date) : '-'}</Descriptions.Item>
            <Descriptions.Item label="完成进度" span={2}><Progress percent={currentRecord.progress} /></Descriptions.Item>
            <Descriptions.Item label="AI拆解" span={2}>{currentRecord.ai_disassembled ? <Tag color="blue">已拆解</Tag> : <Tag>未拆解</Tag>}</Descriptions.Item>
            <Descriptions.Item label="计划文本" span={2}><pre style={{ whiteSpace: 'pre-wrap', fontSize: 12 }}>{currentRecord.plan_text || '-'}</pre></Descriptions.Item>
            <Descriptions.Item label="备注" span={2}>{currentRecord.notes || '-'}</Descriptions.Item>
          </Descriptions>
        )}
      </Modal>

      <Modal 
        title={<><RobotOutlined /> AI修船计划拆解</>} 
        open={aiModalOpen} 
        onCancel={() => setAiModalOpen(false)} 
        footer={[<Button key="close" onClick={() => setAiModalOpen(false)}>关闭</Button>]}
        width={1100}
      >
        {currentRecord && (
          <div>
            <Card title="计划信息" size="small" style={{ marginBottom: 16 }}>
              <Row gutter={16}>
                <Col span={12}><p><strong>计划名称：</strong>{currentRecord.plan_name}</p></Col>
                <Col span={12}><p><strong>船名：</strong>{currentRecord.vessel_name || '-'}</p></Col>
                <Col span={12}><p><strong>计划工期：</strong>{currentRecord.plan_duration_days ? `${currentRecord.plan_duration_days}天` : '-'}</p></Col>
                <Col span={12}><p><strong>状态：</strong><Tag color={statusColor[currentRecord.status]}>{statusText[currentRecord.status]}</Tag></p></Col>
              </Row>
              <TextArea value={currentRecord.plan_text} rows={4} readOnly style={{ marginTop: 8 }} />
            </Card>

            {!aiBreakdownResult ? (
              <div style={{ textAlign: 'center', padding: '40px' }}>
                <Button 
                  type="primary" 
                  size="large" 
                  icon={<ThunderboltOutlined />} 
                  onClick={executeAiBreakdown} 
                  loading={isAiLoading}
                  disabled={!currentRecord.plan_text}
                >
                  {isAiLoading ? 'AI正在分析中...' : '开始AI拆解'}
                </Button>
                {!currentRecord.plan_text && <Alert message="请先填写计划文本" type="warning" style={{ marginTop: 16 }} />}
              </div>
            ) : (
              <Spin spinning={isAiLoading}>
                <Card title="AI拆解结果" size="small">
                  {aiBreakdownResult.summary && <Alert message={aiBreakdownResult.summary} type="info" showIcon style={{ marginBottom: 16 }} />}
                  <Row gutter={16} style={{ marginBottom: 16 }}>
                    {aiBreakdownResult.total_estimated_days && <Col span={8}><Tag color="blue">总工期：{aiBreakdownResult.total_estimated_days}天</Tag></Col>}
                    {aiBreakdownResult.total_estimated_hours && <Col span={8}><Tag color="green">总工时：{aiBreakdownResult.total_estimated_hours}小时</Tag></Col>}
                    {aiBreakdownResult.risks_summary && <Col span={8}><Tag color="orange">{aiBreakdownResult.risks_summary}</Tag></Col>}
                  </Row>
                  {aiBreakdownResult.recommended_timeline && <Alert message={aiBreakdownResult.recommended_timeline} type="success" showIcon style={{ marginBottom: 16 }} />}
                  
                  {aiBreakdownResult.tasks && aiBreakdownResult.tasks.length > 0 && (
                    <>
                      <Divider />
                      <h4>待确认任务（共{aiBreakdownResult.tasks.length}个）</h4>
                      <div style={{ maxHeight: '500px', overflowY: 'auto' }}>
                        {aiBreakdownResult.tasks.map((task: AIDisassembledTask, index: number) => (
                          <Card key={index} size="small" style={{ marginBottom: 8 }}>
                            <Row gutter={16}>
                              <Col span={16}>
                                <p><strong>{index + 1}. {task.task_name}</strong></p>
                                <p><small>分类：{getCategoryText(task.category)} | 工期：{task.estimated_days ?? '-'}天 | 工时：{task.estimated_hours ?? '-'}小时</small></p>
                                <Space wrap>
                                  {(task.critical_path || task.is_critical_path) && <Tag color="red">关键路径</Tag>}
                                  {task.priority && <Tag color="purple">优先级：{task.priority}</Tag>}
                                  {task.risk_level && <Tag color={getRiskLevelColor(task.risk_level)}>风险：{getRiskLevelText(task.risk_level)}</Tag>}
                                  {task.can_parallel && <Tag color="blue">可并行</Tag>}
                                </Space>
                              </Col>
                              <Col span={8}>
                                {task.start_condition && <p><small>前置条件：{task.start_condition}</small></p>}
                                {task.required_staff && <p><small>人员：{Object.entries(task.required_staff).filter(([, v]) => v !== undefined && v !== 0 && v !== '').map(([k, v]) => `${k}:${v}`).join('，') || '-'}</small></p>}
                                {task.related_spare_parts && <p><small>相关备件：{task.related_spare_parts}</small></p>}
                              </Col>
                            </Row>
                            {task.sub_tasks && task.sub_tasks.length > 0 && (
                              <p><small>子任务：{task.sub_tasks.join(' → ')}</small></p>
                            )}
                            {task.spare_parts && task.spare_parts.length > 0 && (
                              <p><small>备件预测：{task.spare_parts.map(p => `${p.name}${p.spec ? `(${p.spec})` : ''} × ${p.quantity}${p.is_critical ? ' [关键]' : ''}`).join('；')}</small></p>
                            )}
                            {task.risk_points && task.risk_points.length > 0 && <p><small>风险点：{task.risk_points.join('；')}</small></p>}
                            {task.remarks && <p><small>备注：{task.remarks}</small></p>}
                          </Card>
                        ))}
                      </div>
                    </>
                  )}
                </Card>
              </Spin>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}
