import ReactEChartsCore from 'echarts-for-react'
import type { SupplyChainFlowData } from '@lg/api-client'

interface Props {
  data: SupplyChainFlowData
}

export function SupplyChainSankey({ data }: Props) {
  const option = {
    tooltip: { trigger: 'item' as const },
    series: [{
      type: 'sankey',
      data: data.nodes,
      links: data.links,
      emphasis: { focus: 'adjacency' as const },
      lineStyle: { color: 'gradient' as const, curveness: 0.5 },
    }],
  }

  return <ReactEChartsCore option={option} style={{ height: 300 }} />
}
