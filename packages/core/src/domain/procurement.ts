/**
 * Procurement Domain Types
 */
export enum ProcurementStatus {
  DRAFT = 'DRAFT',
  PENDING_APPROVAL = 'PENDING_APPROVAL',
  APPROVED = 'APPROVED',
  ORDERED = 'ORDERED',
  PARTIAL_RECEIVED = 'PARTIAL_RECEIVED',
  RECEIVED = 'RECEIVED',
  CANCELLED = 'CANCELLED'
}

export const procurementStatusLabels: Record<ProcurementStatus, string> = {
  [ProcurementStatus.DRAFT]: '草稿',
  [ProcurementStatus.PENDING_APPROVAL]: '待审批',
  [ProcurementStatus.APPROVED]: '已审批',
  [ProcurementStatus.ORDERED]: '已下单',
  [ProcurementStatus.PARTIAL_RECEIVED]: '部分收货',
  [ProcurementStatus.RECEIVED]: '已收货',
  [ProcurementStatus.CANCELLED]: '已取消'
}

export enum SupplierType {
  GOODS = 'GOODS',
  SERVICE = 'SERVICE'
}

export const supplierTypeLabels: Record<SupplierType, string> = {
  [SupplierType.GOODS]: '货物供应商',
  [SupplierType.SERVICE]: '服务供应商'
}
