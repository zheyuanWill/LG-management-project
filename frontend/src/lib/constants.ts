export const PROJECT_TYPE = {
  SUPERVISION: 'supervision',
  BROKERAGE_SALE: 'brokerage_sale',
  BROKERAGE_REPAIR: 'brokerage_repair',
  SPARE_PARTS: 'spare_parts',
} as const

export const PROJECT_TYPE_LABELS: Record<string, string> = {
  supervision: '监修',
  brokerage_sale: '买卖经纪',
  brokerage_repair: '修船经纪',
  spare_parts: '备件供应',
}

export const PROJECT_STATUS = {
  ACTIVE: 'active',
  COMPLETED: 'completed',
  CANCELLED: 'cancelled',
} as const

export const PROJECT_STATUS_LABELS: Record<string, string> = {
  active: '进行中',
  completed: '已完成',
  cancelled: '已取消',
}

export const TASK_STATUS = {
  NOT_STARTED: 'not_started',
  IN_PROGRESS: 'in_progress',
  COMPLETED: 'completed',
  PAUSED: 'paused',
} as const

export const TASK_STATUS_LABELS: Record<string, string> = {
  not_started: '未开始',
  in_progress: '进行中',
  completed: '已完成',
  paused: '已暂停',
}

export const RISK_LEVEL = {
  INFO: 'info',
  WARNING: 'warning',
  CRITICAL: 'critical',
} as const

export const RISK_LEVEL_LABELS: Record<string, string> = {
  info: '提示',
  warning: '警告',
  critical: '严重',
}

export const LOGISTICS_NODE_TYPE = {
  ORDERED: 'ordered',
  SUPPLIER_SHIPPED: 'supplier_shipped',
  IN_TRANSIT: 'in_transit',
  ARRIVED: 'arrived',
  WAREHOUSED: 'warehoused',
  SENT_TO_OWNER: 'sent_to_owner',
  HK_SIGNED: 'hk_signed',
  SETTLED: 'settled',
} as const

export const LOGISTICS_NODE_LABELS: Record<string, string> = {
  ordered: '已下单',
  supplier_shipped: '供应商发货',
  in_transit: '运输中',
  arrived: '到港',
  warehoused: '入库',
  sent_to_owner: '发给船东',
  hk_signed: '香港签收',
  settled: '结算完成',
}

export const FILE_TYPE = {
  CONTRACT: 'contract',
  RECEIPT: 'receipt',
  WECHAT_SCREENSHOT: 'wechat_screenshot',
  SURVEY: 'survey',
  CERTIFICATE: 'certificate',
  INVOICE: 'invoice',
  PHOTO: 'photo',
  OTHER: 'other',
} as const

export const FILE_TYPE_LABELS: Record<string, string> = {
  contract: '合同',
  receipt: '签收单',
  wechat_screenshot: '微信截图',
  survey: '调研报告',
  certificate: '验收单',
  invoice: '发票',
  photo: '照片',
  other: '其他',
}

export const DATE_FORMAT = 'YYYY-MM-DD'
export const DATE_TIME_FORMAT = 'YYYY-MM-DD HH:mm:ss'