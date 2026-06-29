import { useMemo } from 'react'
import { Tag } from 'antd'
import {
  FileTextOutlined, DollarOutlined, ShoppingCartOutlined, TrophyOutlined,
} from '@ant-design/icons'
import type { Order } from '@lg/api-client'

interface StageInfo {
  key: string
  label: string
  icon: React.ReactNode
  status: 'completed' | 'active' | 'pending'
  count?: number
  countUnit?: string
  time?: string
}

interface Props {
  order: Order
  quoteCount?: number
  procurementCount?: number
}

function getStatus(done: boolean, isCurrentPossible: boolean): 'completed' | 'active' | 'pending' {
  if (done) return 'completed'
  if (isCurrentPossible) return 'active'
  return 'pending'
}

const statusColors = {
  completed: '#52c41a',
  active: '#1677ff',
  pending: '#d9d9d9',
}

export function OrderLifecycle({ order, quoteCount = 0, procurementCount = 0 }: Props) {
  const stages = useMemo<StageInfo[]>(() => {
    return buildMvpStages(order, quoteCount, procurementCount)
  }, [order, quoteCount, procurementCount])

  const completedCount = stages.filter((s) => s.status === 'completed').length

  return (
    <div style={{ background: '#fff', borderRadius: 12, padding: 20, boxShadow: '0 2px 8px rgba(0,0,0,0.06)', marginBottom: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <strong>订单流程（MVP）</strong>
        </div>
        <Tag color={completedCount === stages.length ? 'success' : completedCount >= 3 ? 'processing' : 'default'}>
          {completedCount} / {stages.length} 阶段
        </Tag>
      </div>

      <div style={{ display: 'flex', alignItems: 'flex-start', overflowX: 'auto', padding: '12px 0' }}>
        {stages.map((stage, index) => (
          <div key={stage.key} style={{ display: 'flex', alignItems: 'center', flexShrink: 0 }}>
            {index > 0 && (
              <div style={{ width: 48, display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative' }}>
                <div style={{ width: '100%', height: 2, background: stage.status !== 'pending' ? 'linear-gradient(90deg, #1677ff, #52c41a)' : '#e4e7ed' }} />
              </div>
            )}
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
              <div
                style={{
                  width: 44, height: 44, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 18, transition: 'all 0.3s',
                  border: `2px solid ${statusColors[stage.status]}`,
                  background: stage.status === 'completed' ? '#52c41a' : stage.status === 'active' ? '#e6f4ff' : '#fff',
                  color: stage.status === 'completed' ? '#fff' : stage.status === 'active' ? '#1677ff' : '#c0c4cc',
                  boxShadow: stage.status === 'active' ? '0 0 0 4px rgba(22,119,255,0.15)' : 'none',
                }}
              >
                {stage.icon}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', minWidth: 60 }}>
                <span style={{ fontSize: 12, fontWeight: 600, color: stage.status === 'completed' ? '#52c41a' : stage.status === 'active' ? '#1677ff' : '#c0c4cc' }}>
                  {stage.label}
                </span>
                {stage.count != null && (
                  <span style={{ fontSize: 11, color: '#909399' }}>{stage.count}{stage.countUnit}</span>
                )}
                {stage.time && <span style={{ fontSize: 10, color: '#c0c4cc' }}>{stage.time}</span>}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function buildMvpStages(order: Order, quoteCount: number, procurementCount: number): StageInfo[] {
  const s = order.status
  const hasQuotes = quoteCount > 0
  const hasProcurement = procurementCount > 0
  const isCompleted = s === 'COMPLETED'

  return [
    { key: 'create', label: '创建订单', icon: <FileTextOutlined />, status: 'completed', time: order.created_at?.slice(5, 10) },
    { key: 'quote', label: '报价', icon: <DollarOutlined />, status: getStatus(hasQuotes, !hasQuotes), count: quoteCount, countUnit: '份' },
    { key: 'procurement', label: '采购', icon: <ShoppingCartOutlined />, status: getStatus(hasProcurement, hasQuotes && !hasProcurement), count: procurementCount, countUnit: '个' },
    { key: 'done', label: '完成', icon: <TrophyOutlined />, status: getStatus(isCompleted, false) },
  ]
}
