import ReactEChartsCore from 'echarts-for-react'
import type { RevenueTrendItem } from '@lg/api-client'

interface Props {
  data: RevenueTrendItem[]
}

export function RevenueChart({ data }: Props) {
  const option = {
    tooltip: { trigger: 'axis' as const },
    xAxis: { type: 'category' as const, data: data.map((d) => d.month) },
    yAxis: { type: 'value' as const },
    series: [{
      type: 'line',
      data: data.map((d) => d.revenue),
      smooth: true,
      areaStyle: { opacity: 0.15 },
      itemStyle: { color: '#1677ff' },
    }],
    grid: { left: 40, right: 16, top: 16, bottom: 24 },
  }

  return <ReactEChartsCore option={option} style={{ height: 300 }} />
}
