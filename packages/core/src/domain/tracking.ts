/**
 * Tracking Domain Types
 */
export enum NodeStatus {
  PENDING = 'PENDING',
  IN_PROGRESS = 'IN_PROGRESS',
  COMPLETED = 'COMPLETED',
  OVERDUE = 'OVERDUE',
  SKIPPED = 'SKIPPED'
}

export const nodeStatusLabels: Record<NodeStatus, string> = {
  [NodeStatus.PENDING]: '待处理',
  [NodeStatus.IN_PROGRESS]: '进行中',
  [NodeStatus.COMPLETED]: '已完成',
  [NodeStatus.OVERDUE]: '已逾期',
  [NodeStatus.SKIPPED]: '已跳过'
}

export const nodeStatusColors: Record<NodeStatus, string> = {
  [NodeStatus.PENDING]: '#909399',
  [NodeStatus.IN_PROGRESS]: '#e6a23c',
  [NodeStatus.COMPLETED]: '#67c23a',
  [NodeStatus.OVERDUE]: '#f56c6c',
  [NodeStatus.SKIPPED]: '#909399'
}
