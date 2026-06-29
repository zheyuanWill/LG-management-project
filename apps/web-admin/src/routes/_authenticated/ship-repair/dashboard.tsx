import { useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { Alert, Button, Card, Col, Empty, Modal, Row, Select, Space, Statistic, Typography, message } from 'antd'
import { DashboardOutlined, FileTextOutlined, CheckCircleOutlined, ClockCircleOutlined, WarningOutlined, RobotOutlined } from '@ant-design/icons'
import { useApiQuery } from '@lg/react-hooks'
import { http } from '@lg/api-client'
import { PageHeader } from '@/components/common'

export const Route = createFileRoute('/_authenticated/ship-repair/dashboard')({
  component: ShipRepairDashboard,
})

interface DashboardStats {
  projects_total: number
  projects_active: number
  tasks_total: number
  tasks_completed: number
  tasks_in_progress: number
  tasks_pending: number
  issues_open: number
  issues_high_risk: number
}

interface ProjectOption {
  id: number
  project_name: string
  vessel_name: string
}

function ShipRepairDashboard() {
  const [reportProjectId, setReportProjectId] = useState<number | undefined>()
  const [reportModal, setReportModal] = useState<'daily' | 'weekly' | 'summary' | null>(null)
  const [reportLoading, setReportLoading] = useState(false)
  const [reportContent, setReportContent] = useState('')

  const { data: stats, isLoading } = useApiQuery<DashboardStats>(
    ['ship-repair-dashboard-stats'],
    '/ship-repair/dashboard/stats'
  )

  const { data: projectsData } = useApiQuery<{ items?: ProjectOption[] }>(
    ['ship-repair-projects-for-dashboard'],
    '/ship-repair/projects',
    { page: 1, size: 200 }
  )

  const projectOptions = (projectsData?.items ?? []).map((p) => ({
    value: p.id,
    label: `${p.project_name} / ${p.vessel_name}`,
  }))

  const openReport = async (type: 'daily' | 'weekly' | 'summary') => {
    if (!reportProjectId) {
      message.warning('请先选择项目')
      return
    }

    setReportModal(type)
    setReportLoading(true)
    setReportContent('')

    const endpointMap = {
      daily: `/ship-repair/projects/${reportProjectId}/generate-daily-report`,
      weekly: `/ship-repair/projects/${reportProjectId}/generate-weekly-report`,
      summary: `/ship-repair/projects/${reportProjectId}/generate-summary`,
    }

    try {
      const res = await http.post<any>(endpointMap[type])
      setReportContent(res.content || '暂无内容')
    } catch (e) {
      message.error(e instanceof Error ? e.message : '生成报告失败')
      setReportModal(null)
    } finally {
      setReportLoading(false)
    }
  }

  const data = stats ?? {
    projects_total: 0,
    projects_active: 0,
    tasks_total: 0,
    tasks_completed: 0,
    tasks_in_progress: 0,
    tasks_pending: 0,
    issues_open: 0,
    issues_high_risk: 0,
  }

  return (
    <div>
      <PageHeader
        title="修船监修 Dashboard"
        extra={
          <Space>
            <Select
              placeholder="选择项目后生成报告"
              options={projectOptions}
              value={reportProjectId}
              onChange={setReportProjectId}
              style={{ width: 280 }}
              allowClear
              showSearch
              optionFilterProp="label"
            />
            <Button icon={<RobotOutlined />} onClick={() => openReport('daily')}>生成日报</Button>
            <Button icon={<RobotOutlined />} onClick={() => openReport('weekly')}>生成周报</Button>
            <Button type="primary" icon={<RobotOutlined />} onClick={() => openReport('summary')}>项目总结</Button>
          </Space>
        }
      />

      {data.issues_high_risk > 0 && (
        <Alert
          style={{ marginBottom: 16 }}
          type="warning"
          showIcon
          message={`当前有 ${data.issues_high_risk} 个高风险问题需要关注`}
        />
      )}

      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card loading={isLoading}><Statistic title="项目总数" value={data.projects_total} prefix={<DashboardOutlined />} /></Card>
        </Col>
        <Col span={6}>
          <Card loading={isLoading}><Statistic title="进行中项目" value={data.projects_active} valueStyle={{ color: '#1890ff' }} prefix={<ClockCircleOutlined />} /></Card>
        </Col>
        <Col span={6}>
          <Card loading={isLoading}><Statistic title="任务总数" value={data.tasks_total} prefix={<FileTextOutlined />} /></Card>
        </Col>
        <Col span={6}>
          <Card loading={isLoading}><Statistic title="已完成任务" value={data.tasks_completed} valueStyle={{ color: '#52c41a' }} prefix={<CheckCircleOutlined />} /></Card>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={8}>
          <Card loading={isLoading}><Statistic title="进行中任务" value={data.tasks_in_progress} valueStyle={{ color: '#1677ff' }} /></Card>
        </Col>
        <Col span={8}>
          <Card loading={isLoading}><Statistic title="待开始任务" value={data.tasks_pending} valueStyle={{ color: '#faad14' }} /></Card>
        </Col>
        <Col span={8}>
          <Card loading={isLoading}><Statistic title="开放问题" value={data.issues_open} valueStyle={{ color: data.issues_open > 0 ? '#fa541c' : undefined }} prefix={<WarningOutlined />} /></Card>
        </Col>
      </Row>

      <Card title="系统说明">
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="监修工只维护项目、任务、监修记录；AI负责更新任务、识别问题并生成日报/周报/项目总结。"
        />
      </Card>

      <Modal
        title={reportModal === 'daily' ? 'AI日报' : reportModal === 'weekly' ? 'AI周报' : 'AI项目总结'}
        open={!!reportModal}
        onCancel={() => setReportModal(null)}
        footer={null}
        width={900}
        confirmLoading={reportLoading}
      >
        <Typography.Paragraph style={{ whiteSpace: 'pre-wrap', marginBottom: 0 }}>
          {reportLoading ? 'AI正在生成报告...' : reportContent || '暂无内容'}
        </Typography.Paragraph>
      </Modal>
    </div>
  )
}
