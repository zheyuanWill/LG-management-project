export type WorkflowNodeType =
  | 'start'
  | 'end'
  | 'approval'
  | 'condition'
  | 'notification'
  | 'parallel_gateway'
  | 'timer'
  | 'quote'
  | 'contract'
  | 'procurement'
  | 'delivery'
  | 'payment'
  | 'settlement'
  | 'custom'

export interface WorkflowNodeData {
  label: string
  description?: string
  nodeType: WorkflowNodeType
  days?: number
  assignee?: string
  config?: Record<string, unknown>
}

export interface SerializedNode {
  id: string
  type: string
  position: { x: number; y: number }
  data: WorkflowNodeData
}

export interface SerializedEdge {
  id: string
  source: string
  target: string
  sourceHandle?: string
  targetHandle?: string
  label?: string
  type?: string
  style?: Record<string, unknown>
}

export interface ValidationError {
  type: 'error' | 'warning'
  message: string
  nodeIds?: string[]
  edgeIds?: string[]
}

export interface ValidationResult {
  valid: boolean
  errors: ValidationError[]
  warnings: ValidationError[]
}

export interface HistoryEntry {
  nodes: SerializedNode[]
  edges: SerializedEdge[]
  timestamp: number
  description?: string
}

export const NODE_TYPES: {
  type: WorkflowNodeType
  label: string
  icon: string
  color: string
  description: string
  category: 'business' | 'basic' | 'control' | 'advanced'
}[] = [
  { type: 'quote', label: '报价', icon: '💰', color: '#1677ff', description: '报价被接受时自动完成', category: 'business' },
  { type: 'contract', label: '合同', icon: '📝', color: '#722ED1', description: '合同生效时自动完成', category: 'business' },
  { type: 'procurement', label: '采购', icon: '🛒', color: '#fa8c16', description: '采购审批通过时自动完成', category: 'business' },
  { type: 'delivery', label: '发货', icon: '🚚', color: '#13C2C2', description: '发货/物流阶段（手动完成）', category: 'business' },
  { type: 'payment', label: '回款', icon: '💳', color: '#52c41a', description: '回款确认（手动完成）', category: 'business' },
  { type: 'settlement', label: '结项', icon: '🏆', color: '#eb2f96', description: '结项审批通过时自动完成', category: 'business' },
  { type: 'custom', label: '自定义', icon: '📌', color: '#909399', description: '自定义任务（手动完成）', category: 'business' },
  { type: 'start', label: '开始', icon: '▶', color: '#52c41a', description: '流程起点', category: 'basic' },
  { type: 'end', label: '结束', icon: '⏹', color: '#f5222d', description: '流程终点', category: 'basic' },
  { type: 'approval', label: '审批', icon: '✅', color: '#52c41a', description: '需要审批确认', category: 'basic' },
  { type: 'notification', label: '通知', icon: '🔔', color: '#faad14', description: '发送通知提醒', category: 'basic' },
  { type: 'condition', label: '条件分支', icon: '◇', color: '#909399', description: '表达式求值后路由', category: 'control' },
  { type: 'parallel_gateway', label: '并行网关', icon: '⫘', color: '#722ED1', description: 'Fork/Join 并行执行', category: 'control' },
  { type: 'timer', label: '定时器', icon: '⏱', color: '#13C2C2', description: '延时后自动推进', category: 'advanced' },
]

export const NODE_COLOR_MAP: Record<WorkflowNodeType, string> = {
  start: '#52c41a', end: '#f5222d', approval: '#52c41a',
  notification: '#faad14', condition: '#909399',
  parallel_gateway: '#722ED1', timer: '#13C2C2',
  quote: '#1677ff', contract: '#722ED1', procurement: '#fa8c16',
  delivery: '#13C2C2', payment: '#52c41a', settlement: '#eb2f96', custom: '#909399',
}

export const BUSINESS_NODE_TYPES = ['quote', 'contract', 'procurement', 'delivery', 'payment', 'settlement', 'custom'] as const

export const BUSINESS_NODE_TRIGGERS: Record<string, { entity: string; status: string } | null> = {
  quote: { entity: 'quote', status: 'ACCEPTED' },
  contract: { entity: 'contract', status: 'EFFECTIVE' },
  procurement: { entity: 'procurement', status: 'APPROVED' },
  delivery: null,
  payment: null,
  settlement: { entity: 'settlement', status: 'APPROVED' },
  custom: null,
}

export const CONDITION_VARIABLES = [
  { name: 'amount', label: '订单金额', type: 'number' },
  { name: 'project_type', label: '项目类型', type: 'string' },
  { name: 'status', label: '订单状态', type: 'string' },
  { name: 'customer_name', label: '客户名称', type: 'string' },
  { name: 'currency', label: '币种', type: 'string' },
  { name: 'days_elapsed', label: '已用天数', type: 'number' },
]

export const CONDITION_OPERATORS = [
  { value: '>', label: '大于' },
  { value: '<', label: '小于' },
  { value: '>=', label: '大于等于' },
  { value: '<=', label: '小于等于' },
  { value: '==', label: '等于' },
  { value: '!=', label: '不等于' },
]

export const KEYBOARD_SHORTCUTS = [
  { key: 'Ctrl+Z', description: '撤销' },
  { key: 'Ctrl+Shift+Z', description: '重做' },
  { key: 'Delete', description: '删除选中' },
  { key: 'Ctrl+S', description: '保存' },
]
