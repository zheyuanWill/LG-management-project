import { useRef, useMemo } from 'react'
import { useChart } from '@/hooks/useChart'
import type { CompletionRate } from '@lg/api-client'

interface Props {
  data?: CompletionRate
}

export function PerformanceGauge({ data }: Props) {
  const chartRef = useRef<HTMLDivElement>(null)
  const rate = data?.rate ?? 0

  const options = useMemo(
    () => ({
      series: [
        {
          type: 'gauge' as const,
          startAngle: 200,
          endAngle: -20,
          min: 0,
          max: 100,
          center: ['50%', '55%'],
          radius: '90%',
          progress: { show: true, width: 20 },
          pointer: { show: false },
          axisLine: { lineStyle: { width: 20, color: [[1, '#e4e7ed']] } },
          axisTick: { show: false },
          splitLine: { show: false },
          axisLabel: { show: false },
          detail: {
            valueAnimation: true,
            fontSize: 32,
            fontWeight: 'bold' as const,
            formatter: '{value}%',
            color: '#303133',
            offsetCenter: [0, '10%'],
          },
          data: [
            {
              value: rate,
              itemStyle: {
                color: {
                  type: 'linear' as const,
                  x: 0, y: 0, x2: 1, y2: 0,
                  colorStops: [
                    { offset: 0, color: '#1677ff' },
                    { offset: 1, color: '#52c41a' },
                  ],
                },
              },
            },
          ],
        },
      ],
    }),
    [rate],
  )

  useChart(chartRef, options)

  return <div ref={chartRef} style={{ height: 300 }} />
}
