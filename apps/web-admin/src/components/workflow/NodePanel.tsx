import { Card, Typography, Divider } from 'antd'
import {
  PlayCircleOutlined, StopOutlined,
  BellOutlined, BranchesOutlined, ClockCircleOutlined,
  BlockOutlined, AuditOutlined,
  DollarOutlined, CopyOutlined, ShoppingCartOutlined,
  CarOutlined, MoneyCollectOutlined, TrophyOutlined, PushpinOutlined,
} from '@ant-design/icons'
import { BUSINESS_NODE_TRIGGERS } from './types'

interface NodePanelProps {
  onAdd: (type: string, data: Record<string, unknown>) => void
}

const businessNodes = [
  { type: 'quote', label: '报价', icon: <DollarOutlined style={{ color: '#1677ff' }} /> },
  { type: 'contract', label: '合同', icon: <CopyOutlined style={{ color: '#722ed1' }} /> },
  { type: 'procurement', label: '采购', icon: <ShoppingCartOutlined style={{ color: '#fa8c16' }} /> },
  { type: 'delivery', label: '发货', icon: <CarOutlined style={{ color: '#13c2c2' }} /> },
  { type: 'payment', label: '回款', icon: <MoneyCollectOutlined style={{ color: '#52c41a' }} /> },
  { type: 'settlement', label: '结项', icon: <TrophyOutlined style={{ color: '#eb2f96' }} /> },
  { type: 'custom', label: '自定义', icon: <PushpinOutlined style={{ color: '#909399' }} /> },
]

const flowNodes = [
  { type: 'start', label: '开始', icon: <PlayCircleOutlined style={{ color: '#52c41a' }} /> },
  { type: 'end', label: '结束', icon: <StopOutlined style={{ color: '#ff4d4f' }} /> },
  { type: 'approval', label: '审批', icon: <AuditOutlined style={{ color: '#faad14' }} /> },
  { type: 'notification', label: '通知', icon: <BellOutlined style={{ color: '#722ed1' }} /> },
  { type: 'condition', label: '条件', icon: <BranchesOutlined style={{ color: '#13c2c2' }} /> },
  { type: 'parallel', label: '并行网关', icon: <BlockOutlined style={{ color: '#2f54eb' }} /> },
  { type: 'timer', label: '定时器', icon: <ClockCircleOutlined style={{ color: '#fa8c16' }} /> },
]

function NodeItem({ item, onAdd }: { item: typeof businessNodes[0]; onAdd: NodePanelProps['onAdd'] }) {
  const trigger = BUSINESS_NODE_TRIGGERS[item.type]
  const defaultConfig = trigger ? { trigger } : {}

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        padding: '6px 8px',
        borderRadius: 6,
        cursor: 'grab',
        border: '1px solid #f0f0f0',
        transition: 'background 0.2s',
      }}
      draggable
      onDragEnd={() => onAdd(item.type, { label: item.label, nodeType: item.type, config: defaultConfig })}
      onClick={() => onAdd(item.type, { label: item.label, nodeType: item.type, config: defaultConfig })}
    >
      {item.icon}
      <Typography.Text style={{ fontSize: 13 }}>{item.label}</Typography.Text>
    </div>
  )
}

export function NodePanel({ onAdd }: NodePanelProps) {
  return (
    <Card size="small" title="节点面板" style={{ width: 180 }}>
      <Typography.Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>业务节点</Typography.Text>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 6 }}>
        {businessNodes.map((item) => (
          <NodeItem key={item.type} item={item} onAdd={onAdd} />
        ))}
      </div>

      <Divider style={{ margin: '10px 0' }} />

      <Typography.Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>流程节点</Typography.Text>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 6 }}>
        {flowNodes.map((item) => (
          <NodeItem key={item.type} item={item} onAdd={onAdd} />
        ))}
      </div>
    </Card>
  )
}
