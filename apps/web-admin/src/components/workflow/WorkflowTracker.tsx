import { useState, useEffect, useCallback } from 'react'
import { Tag, Button, Empty, Spin, App } from 'antd'
import { workflowApi } from '@lg/api-client'
import type { WorkflowInstance, WorkflowAuditLog } from '@lg/api-client'

interface NodeState {
  status: string
  label?: string
  startedAt?: string
  completedAt?: string
  condition_result?: boolean
}

interface Props {
  orderId?: number
  instanceId?: number
  onCreateInstance?: () => void
  onUpdated?: () => void
}

const STATUS_TAG: Record<string, { color: string; label: string }> = {
  PENDING: { color: 'default', label: '待启动' },
  RUNNING: { color: 'processing', label: '运行中' },
  COMPLETED: { color: 'success', label: '已完成' },
  CANCELLED: { color: 'error', label: '已取消' },
}

const NODE_STATUS_STYLES: Record<string, React.CSSProperties> = {
  COMPLETED: { borderColor: '#52c41a', background: '#f6ffed' },
  RUNNING: { borderColor: '#1677ff', background: '#e6f4ff', boxShadow: '0 0 0 3px rgba(22,119,255,0.15)' },
  SKIPPED: { borderColor: '#c0c4cc', background: '#f5f7fa', opacity: 0.6 },
  FAILED: { borderColor: '#ff4d4f', background: '#fff2f0' },
  WAITING: { borderColor: '#faad14', background: '#fffbe6', borderStyle: 'dashed' },
  PENDING: { borderColor: '#e4e7ed', background: '#fff' },
}

const ACTION_LABELS: Record<string, string> = {
  instance_start: '流程启动',
  instance_complete: '流程完成',
  instance_cancel: '流程取消',
  node_advance: '节点完成',
  node_skip: '节点跳过',
  node_completed: '节点完成',
  condition_evaluate: '条件评估',
  gateway_fork: '并行分叉',
  gateway_join: '并行汇聚',
  timer_start: '定时器启动',
  timer_fire: '定时器触发',
}

function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('zh-CN', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

export function WorkflowTracker({ orderId, instanceId, onCreateInstance, onUpdated }: Props) {
  const [loading, setLoading] = useState(false)
  const [instance, setInstance] = useState<WorkflowInstance | null>(null)
  const [auditLogs, setAuditLogs] = useState<WorkflowAuditLog[]>([])
  const [showAudit, setShowAudit] = useState(false)
  const { message } = App.useApp()

  const fetchInstance = useCallback(async () => {
    setLoading(true)
    try {
      if (instanceId) {
        const inst = await workflowApi.getInstance(instanceId)
        setInstance(inst)
        setAuditLogs(inst.audit_logs || [])
      } else if (orderId) {
        const res = await workflowApi.listInstances({ order_id: orderId, size: 1 })
        if (res.items.length > 0) {
          const inst = await workflowApi.getInstance(res.items[0].id)
          setInstance(inst)
          setAuditLogs(inst.audit_logs || [])
        }
      }
    } catch (err) {
      if (err instanceof Error && !err.message.includes('Not Found')) {
        console.warn('[WorkflowTracker]', err.message)
      }
    } finally {
      setLoading(false)
    }
  }, [orderId, instanceId])

  useEffect(() => { fetchInstance() }, [fetchInstance])

  const getNodeState = (nodeId: string): NodeState | null => {
    return (instance?.node_states as Record<string, NodeState> | undefined)?.[nodeId] ?? null
  }

  const getNodeStatus = (nodeId: string) => getNodeState(nodeId)?.status || 'PENDING'

  const canAdvance = (nodeId: string) => {
    return getNodeState(nodeId)?.status === 'RUNNING' && instance?.status === 'RUNNING'
  }

  const advanceNode = async (nodeId: string, status: string) => {
    if (!instance) return
    try {
      const updated = await workflowApi.advanceNode(instance.id, { node_id: nodeId, status })
      setInstance((prev) => prev ? { ...prev, ...updated } : prev)
      onUpdated?.()
      message.success(status === 'COMPLETED' ? '节点已完成' : '节点已跳过')
      const res = await workflowApi.getAuditLogs(instance.id, { size: 100 })
      setAuditLogs(res.items)
    } catch (err) {
      message.error(err instanceof Error ? err.message : '操作失败')
    }
  }

  if (loading) return <Spin style={{ display: 'block', margin: '40px auto' }} />
  if (!instance) {
    return (
      <Empty description="暂无工作流实例">
        {onCreateInstance && <Button type="primary" onClick={onCreateInstance}>创建工作流实例</Button>}
      </Empty>
    )
  }

  const defNodes = (instance.definition?.nodes as any[]) || []
  const tagInfo = STATUS_TAG[instance.status] || STATUS_TAG.PENDING

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
        <strong>{instance.name}</strong>
        <Tag color={tagInfo.color}>{tagInfo.label}</Tag>
        {instance.started_at && <span style={{ fontSize: 12, color: '#909399' }}>启动: {formatDate(instance.started_at)}</span>}
        {instance.completed_at && <span style={{ fontSize: 12, color: '#909399' }}>完成: {formatDate(instance.completed_at)}</span>}
      </div>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, marginBottom: 16 }}>
        {defNodes.map((node: any) => {
          const status = getNodeStatus(node.id)
          const state = getNodeState(node.id)
          const styles = NODE_STATUS_STYLES[status] || NODE_STATUS_STYLES.PENDING
          return (
            <div
              key={node.id}
              style={{
                minWidth: 180, maxWidth: 240, border: '2px solid', borderRadius: 8,
                padding: '10px 14px', fontSize: 13, ...styles,
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 6 }}>
                <span style={{ fontWeight: 600 }}>{node.data?.label}</span>
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: styles.borderColor }} />
              </div>
              {state?.completedAt && <div style={{ fontSize: 11, color: '#909399', marginTop: 4 }}>{formatDate(state.completedAt)}</div>}
              {state?.status === 'RUNNING' && !state.completedAt && <div style={{ fontSize: 11, color: '#1677ff', marginTop: 4, fontWeight: 500 }}>进行中...</div>}
              {canAdvance(node.id) && (
                <div style={{ marginTop: 6, display: 'flex', gap: 4 }}>
                  <Button size="small" type="primary" onClick={() => advanceNode(node.id, 'COMPLETED')}>完成</Button>
                  <Button size="small" onClick={() => advanceNode(node.id, 'SKIPPED')}>跳过</Button>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {auditLogs.length > 0 && (
        <div style={{ borderTop: '1px solid #f0f0f0' }}>
          <div onClick={() => setShowAudit(!showAudit)} style={{ padding: '10px 0', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <strong style={{ fontSize: 13 }}>审计日志 <Tag>{auditLogs.length}</Tag></strong>
            <span>{showAudit ? '▲' : '▼'}</span>
          </div>
          {showAudit && (
            <div style={{ maxHeight: 300, overflowY: 'auto', paddingLeft: 12 }}>
              {auditLogs.map((log) => (
                <div key={log.id} style={{ display: 'flex', gap: 10, padding: '6px 0', fontSize: 12 }}>
                  <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#1677ff', flexShrink: 0, marginTop: 5 }} />
                  <span style={{ flex: 1, color: '#606266' }}>
                    <strong>{ACTION_LABELS[log.action] || log.action}</strong>
                    {log.node_id && <span style={{ color: '#1677ff', marginLeft: 4 }}>{log.node_id}</span>}
                    {log.new_status && <span style={{ color: '#909399', marginLeft: 4 }}>→ {log.new_status}</span>}
                    {log.operator_name && <span style={{ color: '#c0c4cc', fontStyle: 'italic', marginLeft: 4 }}>by {log.operator_name}</span>}
                  </span>
                  <span style={{ fontSize: 11, color: '#c0c4cc', whiteSpace: 'nowrap' }}>{formatDate(log.created_at)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
