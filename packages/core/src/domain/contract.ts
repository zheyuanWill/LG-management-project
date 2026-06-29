/**
 * Contract Domain Types
 */
export enum ContractStatus {
  DRAFT = 'DRAFT',
  PENDING_APPROVAL = 'PENDING_APPROVAL',
  EFFECTIVE = 'EFFECTIVE',
  EXECUTING = 'EXECUTING',
  COMPLETED = 'COMPLETED',
  TERMINATED = 'TERMINATED'
}

export const contractStatusLabels: Record<ContractStatus, string> = {
  [ContractStatus.DRAFT]: '草稿',
  [ContractStatus.PENDING_APPROVAL]: '待审批',
  [ContractStatus.EFFECTIVE]: '已生效',
  [ContractStatus.EXECUTING]: '执行中',
  [ContractStatus.COMPLETED]: '已完成',
  [ContractStatus.TERMINATED]: '已终止'
}

export const contractStatusColors: Record<ContractStatus, string> = {
  [ContractStatus.DRAFT]: '#909399',
  [ContractStatus.PENDING_APPROVAL]: '#e6a23c',
  [ContractStatus.EFFECTIVE]: '#409eff',
  [ContractStatus.EXECUTING]: '#67c23a',
  [ContractStatus.COMPLETED]: '#909399',
  [ContractStatus.TERMINATED]: '#f56c6c'
}
