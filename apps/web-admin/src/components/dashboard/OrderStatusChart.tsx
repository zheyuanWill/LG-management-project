import ReactEChartsCore from 'echarts-for-react'
import type { OrderStatusDistribution } from '@lg/api-client'

interface Props {
  data: OrderStatusDistribution[]
}

export function OrderStatusChart({ data }: Props) {
  const option = {
    tooltip: { trigger: 'item' as const },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      data: data.map((d) => ({ name: d.label, value: d.count })),
      label: { show: true, formatter: '{b}: {c}' },
    }],
  }

  return <ReactEChartsCore option={option} style={{ height: 300 }} />
}
