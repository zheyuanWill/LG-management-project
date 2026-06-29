/**
 * File Domain Types
 */
export enum FileObjectType {
  ORDER = 'ORDER',
  QUOTE = 'QUOTE',
  CONTRACT = 'CONTRACT',
  PROCUREMENT = 'PROCUREMENT',
  TRACKING_NODE = 'TRACKING_NODE',
  SETTLEMENT = 'SETTLEMENT',
  INVOICE = 'INVOICE',
  BILL_OF_LADING = 'BILL_OF_LADING',
  ACCEPTANCE = 'ACCEPTANCE',
  PHOTO = 'PHOTO',
  RISK_ASSESSMENT = 'RISK_ASSESSMENT',
  CONTRACT_REVIEW = 'CONTRACT_REVIEW',
  QUALITY_INSPECTION = 'QUALITY_INSPECTION',
  PROJECT_CHANGE = 'PROJECT_CHANGE',
  PROJECT_CLOSURE = 'PROJECT_CLOSURE',
  COMPLAINT = 'COMPLAINT',
  SUPPLIER_ADMISSION = 'SUPPLIER_ADMISSION',
  KNOWLEDGE = 'KNOWLEDGE',
  OTHER = 'OTHER'
}

export const fileObjectTypeLabels: Record<FileObjectType, string> = {
  [FileObjectType.ORDER]: '订单',
  [FileObjectType.QUOTE]: '报价',
  [FileObjectType.CONTRACT]: '合同',
  [FileObjectType.PROCUREMENT]: '采购单',
  [FileObjectType.TRACKING_NODE]: '跟单节点',
  [FileObjectType.SETTLEMENT]: '结项',
  [FileObjectType.INVOICE]: '发票',
  [FileObjectType.BILL_OF_LADING]: '提单',
  [FileObjectType.ACCEPTANCE]: '验收单',
  [FileObjectType.PHOTO]: '现场照片',
  [FileObjectType.RISK_ASSESSMENT]: '风险评估',
  [FileObjectType.CONTRACT_REVIEW]: '合同评审',
  [FileObjectType.QUALITY_INSPECTION]: '质检报告',
  [FileObjectType.PROJECT_CHANGE]: '项目变更',
  [FileObjectType.PROJECT_CLOSURE]: '项目关闭',
  [FileObjectType.COMPLAINT]: '投诉处理',
  [FileObjectType.SUPPLIER_ADMISSION]: '供应商准入',
  [FileObjectType.KNOWLEDGE]: '知识库',
  [FileObjectType.OTHER]: '其他'
}

export const allowedFileTypes = [
  'image/jpeg',
  'image/png',
  'image/gif',
  'image/webp',
  'application/pdf',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.ms-excel',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
]

export const maxFileSize = 50 * 1024 * 1024 // 50MB
