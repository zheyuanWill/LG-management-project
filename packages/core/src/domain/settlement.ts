/**
 * Settlement Domain Types
 */
export enum SettlementStatus {
  DRAFT = 'DRAFT',
  PENDING_APPROVAL = 'PENDING_APPROVAL',
  APPROVING = 'APPROVING',
  APPROVED = 'APPROVED',
  REJECTED = 'REJECTED',
  COMPLETED = 'COMPLETED'
}

export const settlementStatusLabels: Record<SettlementStatus, string> = {
  [SettlementStatus.DRAFT]: '草稿',
  [SettlementStatus.PENDING_APPROVAL]: '待审批',
  [SettlementStatus.APPROVING]: '审批中',
  [SettlementStatus.APPROVED]: '已审批',
  [SettlementStatus.REJECTED]: '已拒绝',
  [SettlementStatus.COMPLETED]: '已完成'
}

export const settlementStatusColors: Record<SettlementStatus, string> = {
  [SettlementStatus.DRAFT]: '#909399',
  [SettlementStatus.PENDING_APPROVAL]: '#e6a23c',
  [SettlementStatus.APPROVING]: '#409eff',
  [SettlementStatus.APPROVED]: '#67c23a',
  [SettlementStatus.REJECTED]: '#f56c6c',
  [SettlementStatus.COMPLETED]: '#909399'
}
