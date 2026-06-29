import { Tag } from 'antd'
import type { WorkflowInstance } from '@lg/api-client'

interface Props {
  instance: WorkflowInstance | null
}

const STATUS_ICONS: Record<string, string> = {
  COMPLETED: '✓',
  RUNNING: '●',
  PENDING: '○',
  SKIPPED: '—',
  FAILED: '!',
  WAITING: '◌',
}

const STATUS_COLORS: Record<string, string> = {
  COMPLETED: '#52c41a',
  RUNNING: '#1677ff',
  PENDING: '#d9d9d9',
  SKIPPED: '#faad14',
  FAILED: '#ff4d4f',
  WAITING: '#faad14',
}

const STATUS_LABELS: Record<string, { color: string; label: string }> = {
  COMPLETED: { color: 'success', label: '已完成' },
  RUNNING: { color: 'processing', label: '进行中' },
  PENDING: { color: 'default', label: '待开始' },
  SKIPPED: { color: 'warning', label: '已跳过' },
  FAILED: { color: 'error', label: '失败' },
  WAITING: { color: 'warning', label: '等待中' },
}

export function WorkflowTimeline({ instance }: Props) {
  if (!instance) {
    return <div style={{ textAlign: 'center', padding: 40, color: '#c0c4cc' }}>暂无工作流实例</div>
  }

  const nodes = Object.entries(instance.node_states ?? {})
    .filter(([_, s]) => !['start', 'end'].includes(s.nodeType))
    .sort(([a], [b]) => a.localeCompare(b))

  if (nodes.length === 0) {
    return <div style={{ textAlign: 'center', padding: 40, color: '#c0c4cc' }}>暂无节点数据</div>
  }

  return (
    <div style={{ background: '#fff', borderRadius: 12, padding: 24, boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
      <h3 style={{ margin: '0 0 24px', fontSize: 16, fontWeight: 600 }}>工作流进度</h3>
      <div style={{ position: 'relative', paddingLeft: 24 }}>
        {nodes.map(([nodeId, state], index) => {
          const icon = STATUS_ICONS[state.status] ?? STATUS_ICONS.PENDING
          const hexColor = STATUS_COLORS[state.status] ?? STATUS_COLORS.PENDING
          const tagInfo = STATUS_LABELS[state.status] ?? STATUS_LABELS.PENDING
          const isActive = state.status === 'RUNNING'

          return (
            <div key={nodeId} style={{ position: 'relative', paddingBottom: index < nodes.length - 1 ? 28 : 0, paddingLeft: 28 }}>
              {index < nodes.length - 1 && (
                <div style={{ position: 'absolute', left: 0, top: 24, bottom: 0, width: 24, display: 'flex', justifyContent: 'center' }}>
                  <div style={{ width: 2, height: '100%', background: state.status === 'COMPLETED' ? '#52c41a' : '#e4e7ed' }} />
                </div>
              )}
              <div
                style={{
                  position: 'absolute', left: 0, top: 2, width: 24, height: 24, borderRadius: '50%',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, zIndex: 1,
                  background: hexColor, color: state.status === 'PENDING' ? '#c0c4cc' : '#fff',
                  border: state.status === 'PENDING' ? '2px solid #dcdfe6' : 'none',
                  ...(state.status === 'PENDING' && { background: '#fff' }),
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
                  <span style={{ fontSize: 14, fontWeight: 500 }}>{state.label || nodeId}</span>
                  <Tag color={tagInfo.color}>{tagInfo.label}</Tag>
                </div>
                <div style={{ fontSize: 12, color: '#909399', display: 'flex', gap: 16 }}>
                  {state.startedAt && <span>开始: {state.startedAt.slice(0, 10)}</span>}
                  {state.completedAt && <span style={{ color: '#52c41a' }}>完成: {state.completedAt.slice(0, 10)}</span>}
                </div>
                {state.assignee && <div style={{ fontSize: 12, color: '#606266', marginTop: 4 }}>负责人: {state.assignee}</div>}
                {state.notes && <p style={{ margin: '6px 0 0', fontSize: 12, color: '#909399', lineHeight: 1.5 }}>{state.notes}</p>}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
