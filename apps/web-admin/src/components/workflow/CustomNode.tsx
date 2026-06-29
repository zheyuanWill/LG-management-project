import { memo } from 'react'
import { Handle, Position, type NodeProps } from '@xyflow/react'
import { Tag } from 'antd'
import {
  PlayCircleOutlined, StopOutlined, CheckCircleOutlined,
  BellOutlined, BranchesOutlined, ClockCircleOutlined,
  BlockOutlined, AuditOutlined,
  DollarOutlined, CopyOutlined, ShoppingCartOutlined,
  CarOutlined, MoneyCollectOutlined, TrophyOutlined, PushpinOutlined,
} from '@ant-design/icons'
import { BUSINESS_NODE_TYPES } from './types'

const nodeTypeConfig: Record<string, { icon: React.ReactNode; color: string }> = {
  start: { icon: <PlayCircleOutlined />, color: '#52c41a' },
  end: { icon: <StopOutlined />, color: '#ff4d4f' },
  approval: { icon: <AuditOutlined />, color: '#faad14' },
  notification: { icon: <BellOutlined />, color: '#722ed1' },
  condition: { icon: <BranchesOutlined />, color: '#13c2c2' },
  parallel: { icon: <BlockOutlined />, color: '#2f54eb' },
  timer: { icon: <ClockCircleOutlined />, color: '#fa8c16' },
  quote: { icon: <DollarOutlined />, color: '#1677ff' },
  contract: { icon: <CopyOutlined />, color: '#722ed1' },
  procurement: { icon: <ShoppingCartOutlined />, color: '#fa8c16' },
  delivery: { icon: <CarOutlined />, color: '#13c2c2' },
  payment: { icon: <MoneyCollectOutlined />, color: '#52c41a' },
  settlement: { icon: <TrophyOutlined />, color: '#eb2f96' },
  custom: { icon: <PushpinOutlined />, color: '#909399' },
}

function CustomNodeComponent({ data, selected }: NodeProps) {
  const nodeType = (data.nodeType as string) ?? 'custom'
  const config = nodeTypeConfig[nodeType] ?? nodeTypeConfig.custom
  const isBusiness = (BUSINESS_NODE_TYPES as readonly string[]).includes(nodeType)

  return (
    <div
      style={{
        padding: '8px 14px',
        borderRadius: isBusiness ? 10 : 8,
        background: isBusiness ? `${config.color}08` : '#fff',
        border: `2px ${isBusiness ? 'solid' : 'solid'} ${selected ? config.color : isBusiness ? `${config.color}60` : '#e8e8e8'}`,
        boxShadow: selected ? `0 0 8px ${config.color}40` : '0 1px 4px rgba(0,0,0,0.08)',
        minWidth: 120,
        textAlign: 'center',
      }}
    >
      <Handle type="target" position={Position.Top} />
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, justifyContent: 'center' }}>
        <span style={{ color: config.color }}>{config.icon}</span>
        <span style={{ fontSize: 13, fontWeight: 500 }}>{String(data.label ?? nodeType)}</span>
      </div>
      {data.assignee ? (
        <Tag style={{ marginTop: 4, fontSize: 11 }}>{String(data.assignee)}</Tag>
      ) : null}
      <Handle type="source" position={Position.Bottom} />
      {nodeType === 'condition' && (
        <>
          <Handle type="source" position={Position.Left} id="false" style={{ background: '#ff4d4f' }} />
          <Handle type="source" position={Position.Right} id="true" style={{ background: '#52c41a' }} />
        </>
      )}
    </div>
  )
}

export const CustomNode = memo(CustomNodeComponent)
