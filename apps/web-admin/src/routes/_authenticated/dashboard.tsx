import { createFileRoute } from '@tanstack/react-router'
import { Row, Col, Card, Timeline, Spin, Typography } from 'antd'
import { useApiQuery } from '@lg/react-hooks'
import { useFormat } from '@/hooks/useFormat'
import type { DashboardStats, OrderStatusDistribution, RevenueTrendItem, ActivityItem, FunnelItem, SupplyChainFlowData, CompletionRate } from '@lg/api-client'
import { RevenueChart, OrderStatusChart, OrderFunnel, SupplyChainSankey, PerformanceGauge, StatCards } from '@/components/dashboard'
import { PageHeader } from '@/components/common'

export const Route = createFileRoute('/_authenticated/dashboard')({
  component: DashboardPage,
})

function DashboardPage() {
  const { fmtDate } = useFormat()

  const { data: stats, isLoading: loadingStats } = useApiQuery<DashboardStats>(
    ['dashboard', 'stats'], '/dashboard/stats'
  )
  const { data: statusDist } = useApiQuery<OrderStatusDistribution[]>(
    ['dashboard', 'status-dist'], '/dashboard/order-status-distribution'
  )
  const { data: revenueTrend } = useApiQuery<RevenueTrendItem[]>(
    ['dashboard', 'revenue-trend'], '/dashboard/revenue-trend'
  )
  const { data: activities } = useApiQuery<ActivityItem[]>(
    ['dashboard', 'activities'], '/dashboard/recent-activities'
  )
  const { data: funnel } = useApiQuery<FunnelItem[]>(
    ['dashboard', 'funnel'], '/dashboard/funnel'
  )
  const { data: supplyChain } = useApiQuery<SupplyChainFlowData>(
    ['dashboard', 'supply-chain'], '/dashboard/supply-chain-flow'
  )
  const { data: completionRate } = useApiQuery<CompletionRate>(
    ['dashboard', 'completion-rate'], '/dashboard/completion-rate'
  )

  return (
    <div>
      <PageHeader title="工作台" subtitle="项目概览与核心指标" />

      <Spin spinning={loadingStats}>
        <StatCards stats={stats} />
      </Spin>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={16}>
          <Card title="营收趋势">
            <RevenueChart data={revenueTrend ?? []} />
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="项目完成率">
            <PerformanceGauge data={completionRate} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={8}>
          <Card title="订单状态分布">
            <OrderStatusChart data={statusDist ?? []} />
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="订单转化漏斗">
            <OrderFunnel data={funnel ?? []} />
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="供应链流向">
            <SupplyChainSankey data={supplyChain ?? { nodes: [], links: [] }} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24}>
          <Card title="最近动态">
            <Timeline
              items={(activities ?? []).slice(0, 8).map((item) => ({
                color: item.color || 'blue',
                children: (
                  <div>
                    <div>{item.text}</div>
                    <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                      {item.time ? fmtDate(item.time) : ''}
                    </Typography.Text>
                  </div>
                ),
              }))}
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}
