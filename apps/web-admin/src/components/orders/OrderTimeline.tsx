import { Tag } from 'antd'
import { nodeStatusLabels } from '@lg/core'
import { nodeStatusTagColors } from '@/constants'

interface TimelineNode {
  id: number
  name: string
  status: string
  planned_date?: string
  actual_date?: string
  assignee_name?: string
  notes?: string
}

interface Props {
  nodes: TimelineNode[]
}

const statusIcons: Record<string, string> = {
  COMPLETED: '✓',
  IN_PROGRESS: '●',
  PENDING: '○',
  OVERDUE: '!',
  SKIPPED: '—',
}

const statusHexColors: Record<string, string> = {
  COMPLETED: '#52c41a',
  IN_PROGRESS: '#1677ff',
  PENDING: '#d9d9d9',
  OVERDUE: '#ff4d4f',
  SKIPPED: '#faad14',
}

export function OrderTimeline({ nodes }: Props) {
  if (nodes.length === 0) {
    return <div style={{ textAlign: 'center', padding: 40, color: '#c0c4cc' }}>暂无跟踪节点</div>
  }

  return (
    <div style={{ background: '#fff', borderRadius: 12, padding: 24, boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
      <h3 style={{ margin: '0 0 24px', fontSize: 16, fontWeight: 600 }}>订单跟踪时间线</h3>
      <div style={{ position: 'relative', paddingLeft: 24 }}>
        {nodes.map((node, index) => {
          const icon = statusIcons[node.status] ?? statusIcons.PENDING
          const hexColor = statusHexColors[node.status] ?? statusHexColors.PENDING
          const tagColor = nodeStatusTagColors[node.status] ?? 'default'
          const label = nodeStatusLabels[node.status as keyof typeof nodeStatusLabels] ?? node.status
          const isActive = node.status === 'IN_PROGRESS'
          return (
            <div key={node.id} style={{ position: 'relative', paddingBottom: index < nodes.length - 1 ? 28 : 0, paddingLeft: 28 }}>
              {index < nodes.length - 1 && (
                <div style={{ position: 'absolute', left: 0, top: 24, bottom: 0, width: 24, display: 'flex', justifyContent: 'center' }}>
                  <div style={{ width: 2, height: '100%', background: node.status === 'COMPLETED' ? '#52c41a' : '#e4e7ed' }} />
                </div>
              )}
              <div
                style={{
                  position: 'absolute', left: 0, top: 2, width: 24, height: 24, borderRadius: '50%',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, zIndex: 1,
                  background: hexColor, color: node.status === 'PENDING' ? '#c0c4cc' : '#fff',
                  border: node.status === 'PENDING' ? '2px solid #dcdfe6' : 'none',
                  ...(node.status === 'PENDING' && { background: '#fff' }),
                }}
              >
                {icon}
              </div>
              <div
                style={{
                  background: isActive ? '#e6f4ff' : '#fafafa',
                  borderRadius: 8, padding: '12px 16px',
                  border: `1px solid ${isActive ? '#1677ff' : '#ebeef5'}`,
                  transition: 'border-color 0.2s',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span style={{ fontSize: 14, fontWeight: 500 }}>{node.name}</span>
                  <Tag color={tagColor}>{label}</Tag>
                </div>
                <div style={{ fontSize: 12, color: '#909399', display: 'flex', gap: 16 }}>
                  {node.planned_date && <span>计划: {node.planned_date}</span>}
                  {node.actual_date && <span style={{ color: node.status === 'OVERDUE' ? '#ff4d4f' : '#52c41a' }}>完成: {node.actual_date}</span>}
                </div>
                {node.assignee_name && <div style={{ fontSize: 12, color: '#606266', marginTop: 4 }}>负责人: {node.assignee_name}</div>}
                {node.notes && <p style={{ margin: '6px 0 0', fontSize: 12, color: '#909399', lineHeight: 1.5 }}>{node.notes}</p>}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
