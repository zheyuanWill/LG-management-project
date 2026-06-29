import { useEffect, useRef, useState } from 'react'
import type { DashboardStats } from '@lg/api-client'

interface StatItem {
  title: string
  value: number
  prefix: string
  suffix: string
  icon: string
  color: string
  bgColor: string
  trend?: number
}

function useCountUp(target: number, duration = 1200) {
  const [display, setDisplay] = useState(0)
  const prevRef = useRef(0)

  useEffect(() => {
    const from = prevRef.current
    prevRef.current = target
    const diff = target - from
    if (diff === 0) return

    const start = performance.now()
    let frame: number

    function tick(now: number) {
      const elapsed = now - start
      const progress = Math.min(elapsed / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      setDisplay(Math.round(from + diff * eased))
      if (progress < 1) frame = requestAnimationFrame(tick)
    }

    frame = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(frame)
  }, [target, duration])

  return display
}

function StatValue({ value, prefix, suffix }: { value: number; prefix: string; suffix: string }) {
  const animated = useCountUp(value)
  return (
    <div style={{ fontSize: 28, fontWeight: 700, color: '#303133', lineHeight: 1.2 }}>
      {prefix}{animated.toLocaleString()}{suffix}
    </div>
  )
}

interface Props {
  stats?: DashboardStats
}

export function StatCards({ stats }: Props) {
  const items: StatItem[] = [
    { title: '活跃订单', value: stats?.active_orders ?? 0, prefix: '', suffix: '', icon: '📦', color: '#1677ff', bgColor: '#e6f4ff', trend: undefined },
    { title: '本月营收', value: stats ? Math.round(stats.monthly_revenue / 100) : 0, prefix: '¥', suffix: '', icon: '💰', color: '#52c41a', bgColor: '#f6ffed', trend: stats?.revenue_trend },
    { title: '待审批', value: stats?.pending_approval ?? 0, prefix: '', suffix: '', icon: '⏳', color: '#faad14', bgColor: '#fffbe6', trend: undefined },
    { title: '逾期节点', value: stats?.overdue_nodes ?? 0, prefix: '', suffix: '', icon: '⚠️', color: '#ff4d4f', bgColor: '#fff2f0', trend: undefined },
  ]

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
      {items.map((item, index) => (
        <div
          key={item.title}
          style={{
            background: '#fff',
            borderRadius: 12,
            padding: 20,
            boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
            borderLeft: `4px solid ${item.color}`,
            transition: 'transform 0.2s, box-shadow 0.2s',
            cursor: 'default',
            animation: `cardSlideUp 0.5s ease-out ${index * 0.1}s both`,
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'translateY(-2px)'
            e.currentTarget.style.boxShadow = '0 4px 16px rgba(0,0,0,0.1)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'translateY(0)'
            e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.06)'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
            <span style={{ width: 40, height: 40, borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 20, background: item.bgColor }}>
              {item.icon}
            </span>
            {item.trend != null && item.trend !== 0 && (
              <span style={{ fontSize: 12, fontWeight: 500, padding: '2px 8px', borderRadius: 4, color: item.trend > 0 ? '#52c41a' : '#ff4d4f', background: item.trend > 0 ? '#f6ffed' : '#fff2f0' }}>
                {item.trend > 0 ? '+' : ''}{item.trend}%
              </span>
            )}
          </div>
          <StatValue value={item.value} prefix={item.prefix} suffix={item.suffix} />
          <div style={{ fontSize: 13, color: '#909399', marginTop: 4 }}>{item.title}</div>
        </div>
      ))}
    </div>
  )
}
