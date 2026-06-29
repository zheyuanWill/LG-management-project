import {
  OrderStatus,
  orderStatusLabels,
  ProjectType,
  projectTypeLabels,
  ContractStatus,
  contractStatusLabels,
  ProcurementStatus,
  procurementStatusLabels,
  SettlementStatus,
  settlementStatusLabels,
  NodeStatus,
  nodeStatusLabels,
} from '@lg/core'
import type { SelectOption } from '@/types'

export const orderStatusOptions: SelectOption[] = Object.entries(orderStatusLabels).map(
  ([value, label]) => ({ value, label })
)

export const projectTypeOptions: SelectOption[] = Object.entries(projectTypeLabels).map(
  ([value, label]) => ({ value, label })
)

export const contractStatusOptions: SelectOption[] = Object.entries(contractStatusLabels).map(
  ([value, label]) => ({ value, label })
)

export const procurementStatusOptions: SelectOption[] = Object.entries(procurementStatusLabels).map(
  ([value, label]) => ({ value, label })
)

export const settlementStatusOptions: SelectOption[] = Object.entries(settlementStatusLabels).map(
  ([value, label]) => ({ value, label })
)

export const nodeStatusOptions: SelectOption[] = Object.entries(nodeStatusLabels).map(
  ([value, label]) => ({ value, label })
)

type PresetStatusColorType = 'default' | 'success' | 'processing' | 'error' | 'warning'

export const orderStatusColors: Record<string, PresetStatusColorType> = {
  [OrderStatus.DRAFT]: 'default',
  [OrderStatus.IN_PROGRESS]: 'processing',
  [OrderStatus.COMPLETED]: 'success',
  [OrderStatus.CANCELLED]: 'error',
}

export const contractStatusColors: Record<string, PresetStatusColorType> = {
  [ContractStatus.DRAFT]: 'default',
  [ContractStatus.PENDING_APPROVAL]: 'warning',
  [ContractStatus.EFFECTIVE]: 'success',
  [ContractStatus.EXECUTING]: 'processing',
  [ContractStatus.COMPLETED]: 'success',
  [ContractStatus.TERMINATED]: 'error',
}

export const procurementStatusColors: Record<string, PresetStatusColorType> = {
  [ProcurementStatus.DRAFT]: 'default',
  [ProcurementStatus.PENDING_APPROVAL]: 'warning',
  [ProcurementStatus.APPROVED]: 'success',
  [ProcurementStatus.ORDERED]: 'processing',
  [ProcurementStatus.PARTIAL_RECEIVED]: 'warning',
  [ProcurementStatus.RECEIVED]: 'success',
  [ProcurementStatus.CANCELLED]: 'error',
}

export const nodeStatusTagColors: Record<string, PresetStatusColorType> = {
  [NodeStatus.PENDING]: 'default',
  [NodeStatus.IN_PROGRESS]: 'processing',
  [NodeStatus.COMPLETED]: 'success',
  [NodeStatus.OVERDUE]: 'error',
  [NodeStatus.SKIPPED]: 'warning',
}

export const currencyOptions: SelectOption[] = [
  { value: 'CNY', label: '人民币 (CNY)' },
  { value: 'USD', label: '美元 (USD)' },
  { value: 'EUR', label: '欧元 (EUR)' },
  { value: 'JPY', label: '日元 (JPY)' },
  { value: 'HKD', label: '港币 (HKD)' },
]
