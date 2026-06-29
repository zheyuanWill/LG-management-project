/**
 * API Client Package
 */
export * from './types'
export * from './storage'
export { http, configureHttp } from './http'
export type { HttpTransport, TransportRequest, TransportResponse } from './http'

// Export all APIs
export {
  customerApi,
  orderApi,
  quoteApi,
  contractApi,
  procurementApi,
  productApi,
  supplierApi,
  supplierCategoryApi,
  inventoryApi,
  trackingApi,
  settlementApi,
  fileApi,
  userApi,
  notificationApi,
  workflowApi,
  dashboardApi,
  type UserListParams,
  type UserCreateData,
  type UserUpdateData,
  type UserResponse,
  type Notification,
  type NotificationType,
  type NotificationListParams,
  type WorkflowTemplate,
  type WorkflowTemplateListItem,
  type WorkflowInstance,
  type WorkflowTemplateListParams,
  type WorkflowValidationError,
  type WorkflowValidationResult,
  type ConditionEvaluateResult,
  type WorkflowAuditLog,
  type DashboardStats,
  type OrderStatusDistribution,
  type RevenueTrendItem,
  type CompletionRate,
  type ActivityItem,
  type FunnelItem,
  type SupplyChainFlowData,
  type OrderLineItemCreate,
  type PaymentPlanCreate,
  type TrackingNodeCreate,
  type TrackingNodeUpdate,
} from './api'

// Export authApi from auth.ts (with token management)
export { authApi } from './auth'
