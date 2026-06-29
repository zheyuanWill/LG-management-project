import { useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { Card, Row, Col, Statistic, Table, Select, Space, Tag, Typography, Empty } from 'antd'
import { WarningOutlined, ExclamationCircleOutlined, ToolOutlined, AlertOutlined } from '@ant-design/icons'
import { useApiQuery } from '@lg/react-hooks'
import { PageHeader } from '@/components/common'

const { Title, Text } = Typography
const { Option } = Select

export const Route = createFileRoute('/_authenticated/ship-repair/risk-dashboard')({
  component: RiskDashboardPage,
})

interface DailyReport {
  id: number
  report_date: string
  site_status: string
  one_line_summary?: string
}

interface RiskDashboardData {
  anomaly_count: number
  ncr_count: number
  spare_part_risk_count: number
  recent_daily_reports: DailyReport[]
}

function RiskDashboardPage() {
  const [orderId, setOrderId] = useState<string | undefined>()

  const { data, isLoading } = useApiQuery<RiskDashboardData>(
    ['ship-repair/risk-dashboard', orderId],
    () => {
      let url = '/ship-repair/risk-dashboard'
      if (orderId) {
        url += `?order_id=${orderId}`
      }
      return url
    }
  )

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'NORMAL': return 'green'
      case 'HAS_RISK': return 'orange'
      case 'DELAYED': return 'red'
      case 'UNCERTAIN': return 'blue'
      default: return 'default'
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'NORMAL': return '正常'
      case 'HAS_RISK': return '有风险'
      case 'DELAYED': return '已延期'
      case 'UNCERTAIN': return '不确定'
      default: return status
    }
  }

  const reportColumns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
    { title: '日期', dataIndex: 'report_date', key: 'report_date', width: 150 },
    {
      title: '现场状态',
      dataIndex: 'site_status',
      key: 'site_status',
      width: 120,
      render: (status: string) => (
        <Tag color={getStatusColor(status)}>{getStatusText(status)}</Tag>
      ),
    },
    { title: '概要', dataIndex: 'one_line_summary', key: 'one_line_summary' },
  ]

  return (
    <div>
      <PageHeader title="修船风险驾驶舱" />
      
      <div style={{ marginBottom: 16 }}>
        <Select
          placeholder="选择项目（可选）"
          style={{ width: 300 }}
          allowClear
          onChange={setOrderId}
        >
          {/* 这里应该有项目选择器，暂时留空 */}
        </Select>
      </div>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="未关闭异常"
              value={data?.anomaly_count || 0}
              prefix={<WarningOutlined style={{ color: '#faad14' }} />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="未关闭NCR"
              value={data?.ncr_count || 0}
              prefix={<ExclamationCircleOutlined style={{ color: '#f5222d' }} />}
              valueStyle={{ color: '#f5222d' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="缺备件风险"
              value={data?.spare_part_risk_count || 0}
              prefix={<ToolOutlined style={{ color: '#1890ff' }} />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="今日日报"
              value={data?.recent_daily_reports?.length || 0}
              prefix={<AlertOutlined style={{ color: '#52c41a' }} />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      <Card title="最近日报" style={{ marginBottom: 16 }}>
        {data?.recent_daily_reports && data.recent_daily_reports.length > 0 ? (
          <Table
            rowKey="id"
            columns={reportColumns}
            dataSource={data.recent_daily_reports}
            loading={isLoading}
            pagination={false}
          />
        ) : (
          <Empty description="暂无日报数据" />
        )}
      </Card>

      <Row gutter={16}>
        <Col xs={24} md={12}>
          <Card title="AI 项目状态摘要">
            <Text type="secondary">
              （AI 功能开发中...）
              <br />
              这里将会显示：
              <br />
              • 今日项目状态
              <br />
              • 主要进展
              <br />
              • 主要风险
              <br />
              • 延期原因
              <br />
              • 需要总经理决策事项
              <br />
              • 对船东沟通建议
            </Text>
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <Card title="日报信息缺口检查">
            <Text type="secondary">
              （AI 功能开发中...）
              <br />
              这里将会检查：
              <br />
              • 有风险但无原因
              <br />
              • 有未完成但无预计完成时间
              <br />
              • 有缺备件但无型号/数量/图片
              <br />
              • 有问题照片但无说明
              <br />
              • 有延期但无影响任务
              <br />
              • 有供应商反馈但无交期
            </Text>
          </Card>
        </Col>
      </Row>
    </div>
  )
}
