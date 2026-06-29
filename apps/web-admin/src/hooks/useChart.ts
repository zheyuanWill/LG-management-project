import { useEffect, useRef } from 'react'
import * as echarts from 'echarts/core'
import { BarChart, LineChart, PieChart, GaugeChart, CustomChart, FunnelChart, SankeyChart } from 'echarts/charts'
import {
  TitleComponent, TooltipComponent, LegendComponent,
  GridComponent, DatasetComponent, TransformComponent,
  DataZoomComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([
  
  BarChart, LineChart, PieChart, GaugeChart, CustomChart, FunnelChart, SankeyChart,
  TitleComponent, TooltipComponent, LegendComponent,
  GridComponent, DatasetComponent, TransformComponent, DataZoomComponent,
  CanvasRenderer,
])

export function useChart(
  containerRef: React.RefObject<HTMLDivElement | null>,
  options: echarts.EChartsCoreOption,
) {
  const chartRef = useRef<echarts.ECharts | null>(null)

  useEffect(() => {
    if (!containerRef.current) return

    chartRef.current = echarts.init(containerRef.current)
    chartRef.current.setOption(options)

    const handleResize = () => chartRef.current?.resize()
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      chartRef.current?.dispose()
      chartRef.current = null
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    chartRef.current?.setOption(options, { notMerge: true })
  }, [options])

  return chartRef
}
