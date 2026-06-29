import { useRef, useMemo } from 'react'
import { useChart } from '@/hooks/useChart'
import { nodeStatusLabels } from '@lg/core'
import type { TrackingNode } from '@lg/api-client'

const STATUS_COLORS: Record<string, string> = {
  PENDING: '#d9d9d9',
  IN_PROGRESS: '#1677ff',
  COMPLETED: '#52c41a',
  OVERDUE: '#ff4d4f',
  SKIPPED: '#909399',
}

interface Props {
  nodes: TrackingNode[]
}

function parseDate(d: string | undefined): number {
  if (!d) return NaN
  const t = new Date(d).getTime()
  return isNaN(t) ? NaN : t
}

function fmtDate(d: string | undefined) {
  if (!d) return '-'
  return new Date(d).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

export function GanttChart({ nodes }: Props) {
  const chartRef = useRef<HTMLDivElement>(null)

  const height = useMemo(() => {
    const count = nodes.length
    if (count === 0) return 200
    return Math.max(200, count * 36 + 80)
  }, [nodes.length])

  const options = useMemo(() => {
    const sorted = [...nodes].sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0))
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const todayTs = today.getTime()

    const yAxisData = sorted.map((n) => n.name)
    const data = sorted.map((node, idx) => {
      const planned = parseDate(node.planned_date)
      let endTs: number
      if (node.actual_date) endTs = parseDate(node.actual_date)
      else if (node.status === 'IN_PROGRESS') endTs = todayTs
      else endTs = planned
      const startTs = isNaN(planned) ? todayTs : planned
      const end = isNaN(endTs) ? startTs + 86400000 : endTs
      const color = STATUS_COLORS[node.status] ?? '#d9d9d9'
      return [startTs, end, color, node, idx] as [number, number, string, TrackingNode, number]
    })

    const validData = data.filter((d) => !isNaN(d[0]))
    const allTimes = validData.flatMap((d) => [d[0], d[1]])
    const minTime = allTimes.length ? Math.min(...allTimes) : todayTs - 7 * 86400000
    const maxTime = allTimes.length ? Math.max(...allTimes) : todayTs + 30 * 86400000
    const padding = (maxTime - minTime) * 0.05 || 86400000

    return {
      tooltip: {
        trigger: 'item' as const,
        formatter: (params: { data: unknown[] }) => {
          const [, , , node] = params.data as [number, number, string, TrackingNode, number]
          if (!node) return ''
          return [
            `<div style="font-weight:600;margin-bottom:6px">${node.name}</div>`,
            `<div>状态: ${nodeStatusLabels[node.status as keyof typeof nodeStatusLabels] || node.status}</div>`,
            `<div>计划: ${fmtDate(node.planned_date)}</div>`,
            `<div>实际: ${fmtDate(node.actual_date)}</div>`,
            node.assignee_name ? `<div>负责人: ${node.assignee_name}</div>` : '',
          ].join('')
        },
      },
      grid: { left: 120, right: 40, top: 20, bottom: 60, containLabel: false },
      xAxis: {
        type: 'time' as const,
        min: minTime - padding,
        max: maxTime + padding,
        axisLabel: {
          formatter: (value: number) => {
            const d = new Date(value)
            return `${d.getMonth() + 1}/${d.getDate()}`
          },
        },
        splitLine: { show: false },
      },
      yAxis: {
        type: 'category' as const,
        data: yAxisData,
        axisLabel: { width: 100, overflow: 'truncate' as const, ellipsis: '...' },
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { show: true, lineStyle: { type: 'dashed' as const, color: '#ebeef5' } },
        inverse: true,
      },
      dataZoom: [
        { type: 'slider' as const, xAxisIndex: 0, start: 0, end: 100, bottom: 10, height: 20 },
        { type: 'inside' as const, xAxisIndex: 0, start: 0, end: 100 },
      ],
      series: [
        {
          type: 'custom' as const,
          renderItem: (_params: unknown, api: any) => {
            const dataIndex = (api as any).value(4)
            const item = data[dataIndex]
            if (!item) return null
            const [startTs, endTs, color] = item
            const startPoint = api.coord([startTs, dataIndex])
            const endPoint = api.coord([endTs, dataIndex])
            if (!startPoint || !endPoint) return null
            const barHeight = 20
            return {
              type: 'rect',
              shape: { x: startPoint[0], y: startPoint[1] - barHeight / 2, width: Math.max(2, endPoint[0] - startPoint[0]), height: barHeight, r: 4 },
              style: api.style({ fill: color }),
            }
          },
          encode: { x: [0, 1], y: 4 },
          data,
        },
      ],
    }
  }, [nodes])

  useChart(chartRef, options)

  return <div ref={chartRef} style={{ width: '100%', height }} />
}
