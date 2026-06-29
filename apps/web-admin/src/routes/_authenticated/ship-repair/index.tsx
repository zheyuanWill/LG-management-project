import { Link, createFileRoute } from '@tanstack/react-router'
import { Card, Col, Row, Space, Typography } from 'antd'
import { DashboardOutlined, FileTextOutlined, ToolOutlined, CalendarOutlined } from '@ant-design/icons'
import { PageHeader } from '@/components/common'

const { Title, Text } = Typography

export const Route = createFileRoute('/_authenticated/ship-repair/')({
  component: ShipRepairPage,
})

function ShipRepairPage() {
  const modules = [
    {
      title: 'Dashboard',
      description: '查看项目状态、任务统计、开放问题及 AI 报告生成入口',
      icon: <DashboardOutlined style={{ fontSize: '32px' }} />,
      path: '/_authenticated/ship-repair/dashboard',
    },
    {
      title: 'Projects',
      description: '维护修船项目、维修规范和 AI 任务拆解入口',
      icon: <FileTextOutlined style={{ fontSize: '32px' }} />,
      path: '/_authenticated/ship-repair/projects',
    },
    {
      title: 'Tasks',
      description: '查看和维护 AI 生成的任务，更新执行状态',
      icon: <ToolOutlined style={{ fontSize: '32px' }} />,
      path: '/_authenticated/ship-repair/tasks',
    },
    {
      title: 'Daily Logs',
      description: '监修工每天填写：今天干了什么、发现了什么、明天准备干什么，并上传附件',
      icon: <CalendarOutlined style={{ fontSize: '32px' }} />,
      path: '/_authenticated/ship-repair/daily-logs',
    },
  ]

  return (
    <div>
      <PageHeader title="修船监修模块" />
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        {modules.map((module) => (
          <Col xs={24} sm={12} md={12} lg={6} key={module.title}>
            <Link to={module.path} style={{ textDecoration: 'none' }}>
              <Card hoverable style={{ height: '100%' }}>
                <Space direction="vertical" style={{ width: '100%', textAlign: 'center' }}>
                  <div style={{ color: '#1890ff' }}>{module.icon}</div>
                  <Title level={4} style={{ marginBottom: 8 }}>{module.title}</Title>
                  <Text type="secondary">{module.description}</Text>
                </Space>
              </Card>
            </Link>
          </Col>
        ))}
      </Row>
    </div>
  )
}
