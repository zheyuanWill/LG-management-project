/**
 * Order Domain Types
 */
export enum ProjectType {
  TECHNICAL_SERVICE = 'TECHNICAL_SERVICE',
  SUPERVISION = 'SUPERVISION',
  SPARE_PARTS = 'SPARE_PARTS',
  IMPORT_EXPORT_AGENT = 'IMPORT_EXPORT_AGENT',
  BROKERAGE = 'BROKERAGE',
  AGENCY_FEE = 'AGENCY_FEE'
}

export enum OrderStatus {
  INQUIRY = 'INQUIRY',
  DRAFT = 'DRAFT',
  IN_PROGRESS = 'IN_PROGRESS',
  COMPLETED = 'COMPLETED',
  CANCELLED = 'CANCELLED'
}

export enum QuoteStatus {
  DRAFT = 'DRAFT',
  SENT = 'SENT',
  FEEDBACK = 'FEEDBACK',
  ACCEPTED = 'ACCEPTED',
  REJECTED = 'REJECTED'
}

export const projectTypeLabels: Record<ProjectType, string> = {
  [ProjectType.TECHNICAL_SERVICE]: '技术服务',
  [ProjectType.SUPERVISION]: '监理',
  [ProjectType.SPARE_PARTS]: '备件',
  [ProjectType.IMPORT_EXPORT_AGENT]: '进出口代理',
  [ProjectType.BROKERAGE]: '经纪',
  [ProjectType.AGENCY_FEE]: '代理费'
}

export const orderStatusLabels: Record<OrderStatus, string> = {
  [OrderStatus.INQUIRY]: '询价中',
  [OrderStatus.DRAFT]: '草稿',
  [OrderStatus.IN_PROGRESS]: '进行中',
  [OrderStatus.COMPLETED]: '已完成',
  [OrderStatus.CANCELLED]: '已取消'
}

export const quoteStatusLabels: Record<QuoteStatus, string> = {
  [QuoteStatus.DRAFT]: '草稿',
  [QuoteStatus.SENT]: '已发送',
  [QuoteStatus.FEEDBACK]: '已反馈',
  [QuoteStatus.ACCEPTED]: '已接受',
  [QuoteStatus.REJECTED]: '已拒绝'
}

// Order status transitions
export const orderStatusTransitions: Record<OrderStatus, OrderStatus[]> = {
  [OrderStatus.INQUIRY]: [OrderStatus.DRAFT, OrderStatus.CANCELLED],
  [OrderStatus.DRAFT]: [OrderStatus.IN_PROGRESS, OrderStatus.CANCELLED],
  [OrderStatus.IN_PROGRESS]: [OrderStatus.COMPLETED, OrderStatus.CANCELLED],
  [OrderStatus.COMPLETED]: [],
  [OrderStatus.CANCELLED]: []
}
