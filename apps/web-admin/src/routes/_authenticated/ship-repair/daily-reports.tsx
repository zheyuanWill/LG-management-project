import { useEffect, useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import {
  Table, Button, Form, Input, Modal, message, Select,
  DatePicker, Radio, Space, Tag, Descriptions, Alert
} from 'antd'
import { PlusOutlined, EyeOutlined, EditOutlined, RobotOutlined } from '@ant-design/icons'
import { usePageQuery, useApiPost, useApiQuery } from '@lg/react-hooks'
import { PageHeader } from '@/components/common'
import { useFormat } from '@/hooks/useFormat'
import type { PageResponse } from '@lg/api-client'
import { http } from '@lg/api-client'
import { useQueryClient } from '@tanstack/react-query'
import dayjs from 'dayjs'

const { TextArea } = Input

export const Route = createFileRoute('/_authenticated/ship-repair/daily-reports')({
  component: TodayRecordsPage,
})

interface DailyReport {
  id: number
  order_id: number
  report_date: string
  reporter_id: number
  site_status: string
  today_work?: string
  tomorrow_plan?: string
  affects_schedule: boolean
  estimated_delay_days?: number
  notes?: string
  linked_ncr_id?: number
  created_at: string
  updated_at: string
}

interface NCR {
  id: number
  ncr_number: string
  issue_description: string
}

function TodayRecordsPage() {
  const { fmtDate } = useFormat()
  const queryClient = useQueryClient()
  const [params, setParams] = useState<Record<string, unknown>>({ page: 1, size: 20 })
  const [createOpen, setCreateOpen] = useState(false)
  const [viewOpen, setViewOpen] = useState(false)
  const [aiOpen, setAiOpen] = useState(false)
  const [aiLoading, setAiLoading] = useState(false)
  const [aiResult, setAiResult] = useState<any>(null)
  const [currentRecord, setCurrentRecord] = useState<DailyReport | null>(null)
  const [form] = Form.useForm()
  const affectsSchedule = Form.useWatch('affects_schedule', form)

  useEffect(() => {
    if (createOpen) {
      form.setFieldsValue({
        report_date: dayjs(),
        site_status: 'NORMAL',
        affects_schedule: false,
      })
    }
  }, [createOpen, form])

  const { data, isLoading } = usePageQuery<DailyReport>(
    ['ship-repair/daily-reports', params],
    '/ship-repair/daily-reports',
    params
  )

  const { data: ordersData } = useApiQuery<PageResponse<{ id: number; order_no: string }>>(
    ['orders', 'select'],
    '/orders',
    { size: 200 }
  )

  const orderOptions = (ordersData?.items ?? []).map((o) => ({
    value: o.id,
    label: o.order_no,
  }))

  const { data: ncrsData } = useApiQuery<PageResponse<NCR>>(
    ['ship-repair/ncrs', 'select'],
    '/ship-repair/ncrs',
    { size: 200 }
  )

  const ncrOptions = (ncrsData?.items ?? []).map((n) => ({
    value: n.id,
    label: `${n.ncr_number} - ${n.issue_description.slice(0, 40)}`,
  }))

  const createMutation = useApiPost<DailyReport>('/ship-repair/daily-reports', {
    invalidateKeys: [['ship-repair/daily-reports']],
    onSuccess: () => { message.success('创建成功'); setCreateOpen(false); form.resetFields() },
  })

  const handleAiReport = async (record: DailyReport) => {
    setCurrentRecord(record)
    setAiOpen(true)
    setAiLoading(true)
    setAiResult(null)
    try {
      const resp = await http.post(`/ship-repair/daily-reports/${record.id}/ai-generate-summary`)
      setAiResult(resp.data)
    } catch (e) {
      message.error(e instanceof Error ? e.message : 'AI日报生成失败')
      setAiOpen(false)
    } finally {
      setAiLoading(false)
    }
  }

  const siteStatusColor: Record<string, string> = {
    NORMAL: 'green',
    HAS_RISK: 'orange',
    DELAYED: 'red',
  }
  const siteStatusText: Record<string, string> = {
    NORMAL: '正常',
    HAS_RISK: '有风险',
    DELAYED: '已延期',
  }

  const columns = [
    {
      title: '关联订单',
      dataIndex: 'order_id',
      key: 'order_id',
      width: 130,
      render: (id: number) => orderOptions.find((o) => o.value === id)?.label || id,
    },
    {
      title: '日期',
      dataIndex: 'report_date',
      key: 'report_date',
      width: 110,
      render: (v: string) => fmtDate(v),
    },
    {
      title: '现场状态',
      dataIndex: 'site_status',
      key: 'site_status',
      width: 100,
      render: (s: string) => <Tag color={siteStatusColor[s] || 'default'}>{siteStatusText[s] || s}</Tag>,
    },
    {
      title: '今日工作内容',
      dataIndex: 'today_work',
      key: 'today_work',
      width: 260,
      ellipsis: true,
    },
    {
      title: '明日计划',
      dataIndex: 'tomorrow_plan',
      key: 'tomorrow_plan',
      width: 200,
      ellipsis: true,
    },
    {
      title: '影响工期',
      dataIndex: 'affects_schedule',
      key: 'affects_schedule',
      width: 90,
      render: (v: boolean) => v ? <Tag color="red">是</Tag> : <Tag>否</Tag>,
    },
    {
      title: '操作',
      key: 'actions',
      width: 180,
      fixed: 'right' as const,
      render: (_: unknown, record: DailyReport) => (
        <Space size={0}>
          <Button type="link" size="small" icon={<EyeOutlined />} onClick={() => { setCurrentRecord(record); setViewOpen(true) }}>查看</Button>
          <Button type="link" size="small" icon={<RobotOutlined />} onClick={() => handleAiReport(record)}>AI日报</Button>
        </Space>
      ),
    },
  ]

  const handleFormSubmit = (values: any) => {
    const payload: Record<string, unknown> = { ...values }
    if (values.report_date) payload.report_date = values.report_date.format('YYYY-MM-DD')
    createMutation.mutate(payload)
  }

  return (
    <div>
      <PageHeader
        title="今日记录"
        extra={<Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>新建记录</Button>}
      />

      <Form layout="inline" onFinish={(v) => setParams({ ...v, page: 1, size: 20 })} style={{ marginBottom: 16 }}>
        <Form.Item name="order_id">
          <Select placeholder="按订单筛选" showSearch optionFilterProp="label" options={orderOptions} allowClear style={{ width: 160 }} />
        </Form.Item>
        <Form.Item>
          <Button type="primary" htmlType="submit">搜索</Button>
        </Form.Item>
      </Form>

      <Table
        rowKey="id"
        columns={columns}
        dataSource={data?.items}
        loading={isLoading}
        scroll={{ x: 1200 }}
        pagination={{
          current: data?.page,
          pageSize: data?.size,
          total: data?.total,
          showTotal: (t) => `共 ${t} 条`,
          onChange: (p, s) => setParams((prev) => ({ ...prev, page: p, size: s })),
        }}
      />

      {/* Create Modal */}
      <Modal
        title="新建今日记录"
        open={createOpen}
        onCancel={() => { setCreateOpen(false); form.resetFields() }}
        onOk={() => form.submit()}
        confirmLoading={createMutation.isPending}
        width={800}
      >
        <Form form={form} layout="vertical" onFinish={handleFormSubmit}>
          <Form.Item name="order_id" label="关联订单/船舶" rules={[{ required: true }]}>
            <Select placeholder="选择订单" showSearch optionFilterProp="label" options={orderOptions} />
          </Form.Item>
          <Form.Item name="report_date" label="记录日期" rules={[{ required: true }]}>
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="site_status" label="今日现场状态" rules={[{ required: true }]} initialValue="NORMAL">
            <Radio.Group>
              <Radio value="NORMAL">正常</Radio>
              <Radio value="HAS_RISK">有风险</Radio>
              <Radio value="DELAYED">已延期</Radio>
            </Radio.Group>
          </Form.Item>
          <Form.Item name="today_work" label="今日工作内容" rules={[{ required: true }]}>
            <TextArea rows={4} placeholder="请输入今日已完成的工作..." />
          </Form.Item>
          <Form.Item name="tomorrow_plan" label="明日计划内容">
            <TextArea rows={3} placeholder="请输入明日计划开展的工作..." />
          </Form.Item>
          <Form.Item name="affects_schedule" label="是否影响工期" initialValue={false}>
            <Radio.Group>
              <Radio value={false}>否</Radio>
              <Radio value={true}>是</Radio>
            </Radio.Group>
          </Form.Item>
          {affectsSchedule === true && (
            <Form.Item name="estimated_delay_days" label="预计影响天数">
              <Input type="number" min={1} placeholder="请输入天数" style={{ width: 200 }} />
            </Form.Item>
          )}
          <Form.Item name="linked_ncr_id" label="关联问题/NCR (如有)">
            <Select placeholder="选择关联NCR" options={ncrOptions} allowClear showSearch optionFilterProp="label" />
          </Form.Item>
          <Form.Item name="notes" label="备注">
            <TextArea rows={2} placeholder="其他需要补充的情况..." />
          </Form.Item>
        </Form>
      </Modal>

      {/* View Modal */}
      <Modal
        title="查看今日记录"
        open={viewOpen}
        onCancel={() => setViewOpen(false)}
        footer={[<Button key="close" onClick={() => setViewOpen(false)}>关闭</Button>]}
        width={800}
      >
        {currentRecord && (
          <Descriptions bordered column={2}>
            <Descriptions.Item label="关联订单">{orderOptions.find((o) => o.value === currentRecord.order_id)?.label || currentRecord.order_id}</Descriptions.Item>
            <Descriptions.Item label="报告日期">{fmtDate(currentRecord.report_date)}</Descriptions.Item>
            <Descriptions.Item label="现场状态" span={2}>
              <Tag color={siteStatusColor[currentRecord.site_status]}>{siteStatusText[currentRecord.site_status] || currentRecord.site_status}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="今日工作内容" span={2}>{currentRecord.today_work || '-'}</Descriptions.Item>
            <Descriptions.Item label="明日计划" span={2}>{currentRecord.tomorrow_plan || '-'}</Descriptions.Item>
            <Descriptions.Item label="影响工期">{currentRecord.affects_schedule ? '是' : '否'}</Descriptions.Item>
            <Descriptions.Item label="预计延期天数">{currentRecord.affects_schedule ? (currentRecord.estimated_delay_days ?? '-') : '-'}</Descriptions.Item>
            <Descriptions.Item label="关联NCR">
              {currentRecord.linked_ncr_id ? ncrOptions.find((n) => n.value === currentRecord.linked_ncr_id)?.label || `NCR #${currentRecord.linked_ncr_id}` : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="备注">{currentRecord.notes || '-'}</Descriptions.Item>
            <Descriptions.Item label="创建时间">{fmtDate(currentRecord.created_at)}</Descriptions.Item>
            <Descriptions.Item label="更新时间">{fmtDate(currentRecord.updated_at)}</Descriptions.Item>
          </Descriptions>
        )}
      </Modal>

      {/* AI Daily Report Modal */}
      <Modal
        title={<><RobotOutlined /> AI生成日报</>}
        open={aiOpen}
        onCancel={() => setAiOpen(false)}
        footer={[<Button key="close" onClick={() => setAiOpen(false)}>关闭</Button>]}
        width={900}
      >
        {aiLoading && <Alert message="AI正在根据今日记录和关联NCR生成日报..." type="info" showIcon />}
        {!aiLoading && aiResult && (
          <Descriptions bordered column={1}>
            <Descriptions.Item label="日期">{aiResult.report_date || currentRecord?.report_date}</Descriptions.Item>
            <Descriptions.Item label="日报摘要">{aiResult.summary}</Descriptions.Item>
            <Descriptions.Item label="今日工作">
              {(aiResult.work_summary || []).map((item: any, i: number) => (
                <div key={i}>{item.area ? `[${item.area}] ` : ''}{item.task}{item.status ? ` (${item.status})` : ''}</div>
              ))}
            </Descriptions.Item>
            <Descriptions.Item label="问题/NCR">
              {(aiResult.issues_summary || []).length > 0
                ? (aiResult.issues_summary || []).map((item: any, i: number) => (
                    <div key={i}>{item.ncr_number ? `${item.ncr_number}: ` : ''}{item.description}{item.action ? ` — ${item.action}` : ''}</div>
                  ))
                : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="风险提醒">{(aiResult.risks || []).join('；') || '-'}</Descriptions.Item>
            <Descriptions.Item label="明日计划">{(aiResult.tomorrow_plan || []).join('；') || '-'}</Descriptions.Item>
            <Descriptions.Item label="管理层关注">{(aiResult.manager_attention || []).join('；') || '-'}</Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </div>
  )
}
