import ReactEChartsCore from 'echarts-for-react'
import type { FunnelItem } from '@lg/api-client'

interface Props {
  data: FunnelItem[]
}

export function OrderFunnel({ data }: Props) {
  const option = {
    tooltip: { trigger: 'item' as const },
    series: [{
      type: 'funnel',
      data: data.map((d) => ({ name: d.name, value: d.value })),
      left: '10%',
      width: '80%',
      label: { position: 'inside', formatter: '{b}: {c}' },
    }],
  }

  return <ReactEChartsCore option={option} style={{ height: 300 }} />
}
