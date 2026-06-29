/**
 * API Endpoints
 */
import { http } from './http'
import type {
  PageResponse,
  Customer,
  Vessel,
  Order,
  OrderLineItem,
  Quote,
  Contract,
  PaymentPlan,
  Procurement,
  Product,
  Supplier,
  SupplierCategory,
  SupplierCategoryTree,
  TrackingNode,
  Settlement,
  FileAttachment,
  FileObjectType,
  InquiryRiskAssessment,
  InquiryRecord,
  SupplierComparison,
  ContractReview,
  ProjectChange,
  QualityInspection,
  ProjectAcceptance,
  ProjectClosure,
  Complaint,
  SatisfactionSurvey,
  SupplierAdmission,
  SupplierEvaluation,
  ChangeLogEntry,
  KnowledgeDocument,
} from './types'

// ---------------------------------------------------------------------------
// Typed request payloads (replacing `any`)
// ---------------------------------------------------------------------------

export interface OrderLineItemCreate {
  product_id?: number
  product_name: string
  specification?: string
  unit: string
  quantity: number
  unit_price: number
  notes?: string
}

export interface PaymentPlanCreate {
  phase: string
  percentage: number
  planned_amount: number
  planned_date: string
  notes?: string
}

export interface ReceiveItem {
  line_item_id: number
  received_quantity: number
}

export interface DisbursementCreate {
  amount: number
  currency?: string
  payment_date: string
  payment_method?: string
  notes?: string
}

export interface TrackingNodeCreate {
  order_id: number
  name: string
  sort_order?: number
  assignee_id?: number
  planned_date?: string
  notes?: string
}

export interface TrackingNodeUpdate {
  name?: string
  sort_order?: number
  assignee_id?: number
  planned_date?: string
  notes?: string
}

export interface TrackingTemplateCreate {
  project_type: string
  name: string
  nodes: Array<{ name: string; sort_order: number; default_days?: number }>
}

export interface SupplierQuoteCreate {
  supplier_id: number
  product_id: number
  unit_price: number
  currency?: string
  min_quantity?: number
  lead_time_days?: number
  valid_until?: string
  notes?: string
}

export interface BatchCreate {
  product_id: number
  quantity: number
  unit_cost: number
  batch_no?: string
  procurement_id?: number
  notes?: string
}

export interface CostItemCreate {
  order_id: number
  settlement_id?: number
  category_id: number
  description: string
  amount: number
  currency?: string
  amount_cny: number
  tax_rate?: number
  tax_amount?: number
  invoice_no?: string
  invoice_date?: string
  notes?: string
}

// Customer
export const customerApi = {
  list: (params?: { keyword?: string; page?: number; size?: number }) =>
    http.get<PageResponse<Customer>>('/customers', params),

  get: (id: number) =>
    http.get<Customer>(`/customers/${id}`),

  create: (data: Partial<Customer>) =>
    http.post<Customer>('/customers', data),

  update: (id: number, data: Partial<Customer>) =>
    http.put<Customer>(`/customers/${id}`, data),

  delete: (id: number) =>
    http.delete(`/customers/${id}`),

  listVessels: (customerId: number) =>
    http.get<Vessel[]>(`/customers/${customerId}/vessels`),

  createVessel: (data: Partial<Vessel>) =>
    http.post<Vessel>('/customers/vessels', data),
}

// Order
export const orderApi = {
  list: (params?: {
    keyword?: string;
    status?: string;
    project_type?: string;
    customer_id?: number;
    page?: number;
    size?: number
  }) =>
    http.get<PageResponse<Order>>('/orders', params),

  get: (id: number) =>
    http.get<Order>(`/orders/${id}`),

  create: (data: Partial<Order>) =>
    http.post<Order>('/orders', data),

  update: (id: number, data: Partial<Order>) =>
    http.put<Order>(`/orders/${id}`, data),

  updateStatus: (id: number, status: string) =>
    http.put<Order>(`/orders/${id}/status`, { status }),

  addLineItem: (orderId: number, data: OrderLineItemCreate) =>
    http.post<OrderLineItem>(`/orders/${orderId}/line-items`, data),

  deleteLineItem: (orderId: number, itemId: number) =>
    http.delete(`/orders/${orderId}/line-items/${itemId}`),
}

// Quote
export const quoteApi = {
  list: (params?: { order_id?: number; status?: string; page?: number; size?: number }) =>
    http.get<PageResponse<Quote>>('/quotes', params),

  get: (id: number) =>
    http.get<Quote>(`/quotes/${id}`),

  create: (data: Partial<Quote>) =>
    http.post<Quote>('/quotes', data),

  updateStatus: (id: number, status: string, feedback?: string) =>
    http.put<Quote>(`/quotes/${id}/status`, { status, feedback }),

  duplicate: (id: number) =>
    http.post<Quote>(`/quotes/${id}/duplicate`),
}

// Contract
export const contractApi = {
  list: (params?: { keyword?: string; status?: string; customer_id?: number; order_id?: number; page?: number; size?: number }) =>
    http.get<PageResponse<Contract>>('/contracts', params),

  get: (id: number) =>
    http.get<Contract>(`/contracts/${id}`),

  create: (data: Partial<Contract>) =>
    http.post<Contract>('/contracts', data),

  update: (id: number, data: Partial<Contract>) =>
    http.put<Contract>(`/contracts/${id}`, data),

  updateStatus: (id: number, status: string) =>
    http.put<Contract>(`/contracts/${id}/status`, { status }),

  listPayments: (contractId: number) =>
    http.get<PaymentPlan[]>(`/contracts/${contractId}/payments`),

  createPayment: (contractId: number, data: PaymentPlanCreate) =>
    http.post<PaymentPlan>(`/contracts/${contractId}/payments`, data),
}

// Procurement
export const procurementApi = {
  list: (params?: { keyword?: string; status?: string; supplier_id?: number; order_id?: number; page?: number; size?: number }) =>
    http.get<PageResponse<Procurement>>('/procurements', params),

  get: (id: number) =>
    http.get<Procurement>(`/procurements/${id}`),

  create: (data: Partial<Procurement>) =>
    http.post<Procurement>('/procurements', data),

  update: (id: number, data: Partial<Procurement>) =>
    http.put<Procurement>(`/procurements/${id}`, data),

  submit: (id: number) =>
    http.post<Procurement>(`/procurements/${id}/submit`),

  approve: (id: number, approved: boolean, notes?: string) =>
    http.post<Procurement>(`/procurements/${id}/approve`, { approved, notes }),

  markOrdered: (id: number) =>
    http.post<Procurement>(`/procurements/${id}/order`),

  receive: (id: number, items: ReceiveItem[], notes?: string) =>
    http.post<Procurement>(`/procurements/${id}/receive`, { items, notes }),

  listDisbursements: (procurementId: number) =>
    http.get(`/procurements/${procurementId}/disbursements`),

  createDisbursement: (procurementId: number, data: DisbursementCreate) =>
    http.post(`/procurements/${procurementId}/disbursements`, data),
}

// Product
export const productApi = {
  list: (params?: { keyword?: string; category?: string; page?: number; size?: number }) =>
    http.get<PageResponse<Product>>('/products', params),

  get: (id: number) =>
    http.get<Product>(`/products/${id}`),

  create: (data: Partial<Product>) =>
    http.post<Product>('/products', data),

  update: (id: number, data: Partial<Product>) =>
    http.put<Product>(`/products/${id}`, data),

  delete: (id: number) =>
    http.delete(`/products/${id}`),
}

// Supplier
export const supplierApi = {
  list: (params?: { keyword?: string; type?: string; is_preferred?: boolean; category_id?: number; page?: number; size?: number }) =>
    http.get<PageResponse<Supplier>>('/suppliers', params),

  get: (id: number) =>
    http.get<Supplier>(`/suppliers/${id}`),

  create: (data: Partial<Supplier> & { category_ids?: number[] }) =>
    http.post<Supplier>('/suppliers', data),

  update: (id: number, data: Partial<Supplier> & { category_ids?: number[] }) =>
    http.put<Supplier>(`/suppliers/${id}`, data),

  delete: (id: number) =>
    http.delete(`/suppliers/${id}`),

  listQuotes: (supplierId: number) =>
    http.get(`/suppliers/${supplierId}/quotes`),

  createQuote: (data: SupplierQuoteCreate) =>
    http.post('/suppliers/quotes', data),
}

// Supplier Categories
export const supplierCategoryApi = {
  tree: () =>
    http.get<SupplierCategoryTree[]>('/supplier-categories/tree'),

  list: (params?: { level?: number; parent_id?: number }) =>
    http.get<SupplierCategory[]>('/supplier-categories', params),

  create: (data: { name: string; code: string; level: number; parent_id?: number; sort_order?: number; description?: string }) =>
    http.post<SupplierCategory>('/supplier-categories', data),

  update: (id: number, data: { name?: string; sort_order?: number; description?: string }) =>
    http.put<SupplierCategory>(`/supplier-categories/${id}`, data),

  delete: (id: number) =>
    http.delete(`/supplier-categories/${id}`),
}

// Inventory
export const inventoryApi = {
  listBatches: (params?: { product_id?: number; keyword?: string; page?: number; size?: number }) =>
    http.get('/inventory/batches', params),

  createBatch: (data: BatchCreate) =>
    http.post('/inventory/batches', data),

  listMovements: (params?: { product_id?: number; batch_id?: number; type?: string; page?: number; size?: number }) =>
    http.get('/inventory/movements', params),

  reserve: (data: { batch_id: number; order_id: number; quantity: number; notes?: string }) =>
    http.post('/inventory/reserve', data),

  release: (reservationId: number) =>
    http.post(`/inventory/release/${reservationId}`),

  outbound: (batchId: number, quantity: number, orderId: number) =>
    http.post('/inventory/outbound', { batch_id: batchId, quantity, order_id: orderId }),

  summary: (keyword?: string) =>
    http.get('/inventory/summary', { keyword }),
}

// Tracking
export const trackingApi = {
  listTemplates: (projectType?: string) =>
    http.get('/tracking/templates', { project_type: projectType }),

  createTemplate: (data: TrackingTemplateCreate) =>
    http.post('/tracking/templates', data),

  listNodes: (params?: { order_id?: number; status?: string; assignee_id?: number; page?: number; size?: number }) =>
    http.get<PageResponse<TrackingNode>>('/tracking/nodes', params),

  getNode: (id: number) =>
    http.get<TrackingNode>(`/tracking/nodes/${id}`),

  createNode: (data: TrackingNodeCreate) =>
    http.post<TrackingNode>('/tracking/nodes', data),

  updateNode: (id: number, data: TrackingNodeUpdate) =>
    http.put<TrackingNode>(`/tracking/nodes/${id}`, data),

  updateNodeStatus: (id: number, status: string, actualDate?: string, notes?: string) =>
    http.put<TrackingNode>(`/tracking/nodes/${id}/status`, { status, actual_date: actualDate, notes }),

  initFromTemplate: (orderId: number, projectType: string, startDate?: string) =>
    http.post<TrackingNode[]>('/tracking/init-from-template', { order_id: orderId, project_type: projectType, start_date: startDate }),
}

// Settlement
export const settlementApi = {
  list: (params?: { keyword?: string; status?: string; page?: number; size?: number }) =>
    http.get<PageResponse<Settlement>>('/settlements', params),

  get: (id: number) =>
    http.get<Settlement>(`/settlements/${id}`),

  create: (data: { order_id: number; contract_id?: number; notes?: string }) =>
    http.post<Settlement>('/settlements', data),

  submit: (id: number) =>
    http.post<Settlement>(`/settlements/${id}/submit`),

  approve: (id: number, approved: boolean, rejectReason?: string) =>
    http.post<Settlement>(`/settlements/${id}/approve`, { approved, reject_reason: rejectReason }),

  listCosts: (params?: { order_id?: number; settlement_id?: number; category_id?: number; page?: number; size?: number }) =>
    http.get('/settlements/costs', params),

  createCost: (data: CostItemCreate) =>
    http.post('/settlements/costs', data),

  listCategories: () =>
    http.get('/settlements/categories'),

  listExchangeRates: (fromCurrency?: string, toCurrency?: string) =>
    http.get('/settlements/exchange-rates', { from_currency: fromCurrency, to_currency: toCurrency }),

  getOrderSummary: (orderId: number) =>
    http.get(`/settlements/order-summary/${orderId}`),
}

// File
export const fileApi = {
  upload: (file: File, objectType: FileObjectType, objectId: number, notes?: string) =>
    http.upload<FileAttachment>('/files/upload', file, { object_type: objectType, object_id: objectId, notes }),

  getPresignedUrl: (filename: string, contentType: string, objectType: FileObjectType, objectId: number) =>
    http.post<{ upload_url: string; file_key: string }>('/files/presigned-url', {
      filename,
      content_type: contentType,
      object_type: objectType,
      object_id: objectId
    }),

  confirmUpload: (fileKey: string, originalName: string, mimeType: string, size: number, objectType: FileObjectType, objectId: number) =>
    http.post<FileAttachment>('/files/confirm-upload', {
      file_key: fileKey,
      original_name: originalName,
      mime_type: mimeType,
      size,
      object_type: objectType,
      object_id: objectId
    }),

  list: (objectType: FileObjectType, objectId: number) =>
    http.get<FileAttachment[]>('/files', { object_type: objectType, object_id: objectId }),

  get: (id: number) =>
    http.get<FileAttachment>(`/files/${id}`),

  delete: (id: number) =>
    http.delete(`/files/${id}`),

  offlineSync: (files: Array<{ file_data: string; file_name: string; mime_type: string; object_type: string; object_id: number }>) =>
    http.post<{ success: string[]; failed: Array<{ file_name: string; error: string }> }>('/files/offline-sync', { files }),
}

// User Management
export interface UserListParams {
  keyword?: string
  role?: string
  is_active?: boolean
  page?: number
  size?: number
  [key: string]: unknown
}

export interface UserCreateData {
  username: string
  password: string
  email?: string
  real_name?: string
  role: string
}

export interface UserUpdateData {
  email?: string
  real_name?: string
  role?: string
  is_active?: boolean
}

export interface UserResponse {
  id: number
  username: string
  email?: string
  real_name?: string
  role: string
  is_active: boolean
  created_at: string
  updated_at?: string
}

export const userApi = {
  list: (params?: UserListParams) =>
    http.get<PageResponse<UserResponse>>('/users', params),

  get: (id: number) =>
    http.get<UserResponse>(`/users/${id}`),

  create: (data: UserCreateData) =>
    http.post<UserResponse>('/users', data),

  update: (id: number, data: UserUpdateData) =>
    http.put<UserResponse>(`/users/${id}`, data),

  updatePassword: (id: number, newPassword: string) =>
    http.patch<UserResponse>(`/users/${id}/password`, { new_password: newPassword }),

  delete: (id: number) =>
    http.delete(`/users/${id}`),
}

// Notification
export type NotificationType = 'APPROVAL' | 'OVERDUE' | 'PAYMENT' | 'SYSTEM' | 'INFO'

export interface Notification {
  id: number
  user_id: number
  type: NotificationType
  title: string
  content: string
  is_read: boolean
  read_at?: string
  related_type?: string
  related_id?: number
  created_at: string
}

export interface NotificationListParams {
  type?: NotificationType
  is_read?: boolean
  page?: number
  size?: number
  [key: string]: unknown
}

export const notificationApi = {
  list: (params?: NotificationListParams) =>
    http.get<PageResponse<Notification>>('/notifications', params),

  getUnreadCount: () =>
    http.get<{ count: number }>('/notifications/unread-count'),

  markAsRead: (id: number) =>
    http.put<Notification>(`/notifications/${id}/read`),

  markAllAsRead: () =>
    http.put<{ message: string }>('/notifications/read-all'),

  delete: (id: number) =>
    http.delete(`/notifications/${id}`),
}


// ---------------------------------------------------------------------------
// Workflow API
// ---------------------------------------------------------------------------

export interface WorkflowTemplate {
  id: number
  name: string
  description?: string
  project_type?: string
  definition: {
    nodes: Array<{
      id: string
      type: string
      position: { x: number; y: number }
      data: Record<string, unknown>
    }>
    edges: Array<{
      id: string
      source: string
      target: string
      source_handle?: string
      target_handle?: string
      label?: string
    }>
  }
  is_active: boolean
  version: number
  created_by?: number
  creator_name?: string
  created_at: string
  updated_at: string
}

export interface WorkflowTemplateListItem {
  id: number
  name: string
  description?: string
  project_type?: string
  is_active: boolean
  version: number
  node_count: number
  edge_count: number
  creator_name?: string
  created_at: string
  updated_at: string
}

export interface WorkflowInstance {
  id: number
  template_id: number
  order_id?: number
  name: string
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'CANCELLED'
  current_node_id?: string
  node_states: Record<string, {
    status: string
    label: string
    nodeType: string
    startedAt?: string
    completedAt?: string
    assignee?: string
    notes?: string
    config?: Record<string, unknown>
    condition_result?: boolean
    timer_fires_at?: string
  }>
  started_at?: string
  completed_at?: string
  template_name?: string
  order_no?: string
  definition?: WorkflowTemplate['definition']
  audit_logs?: WorkflowAuditLog[]
  created_at: string
  updated_at: string
}

// Validation types
export interface WorkflowValidationError {
  type: 'error' | 'warning'
  message: string
  node_ids: string[]
  edge_ids: string[]
}

export interface WorkflowValidationResult {
  valid: boolean
  errors: WorkflowValidationError[]
  warnings: WorkflowValidationError[]
}

// Condition evaluation
export interface ConditionEvaluateResult {
  result: boolean
  expression: string
  context: Record<string, unknown>
  error?: string
}

// Audit log
export interface WorkflowAuditLog {
  id: number
  instance_id: number
  node_id?: string
  action: string
  old_status?: string
  new_status?: string
  operator_id?: number
  operator_name?: string
  details?: Record<string, unknown>
  created_at: string
}

export interface WorkflowTemplateListParams {
  project_type?: string
  is_active?: boolean
  page?: number
  size?: number
  [key: string]: unknown
}

export const workflowApi = {
  // Templates
  listTemplates: (params?: WorkflowTemplateListParams) =>
    http.get<PageResponse<WorkflowTemplateListItem>>('/workflows/templates', params),

  getTemplate: (id: number) =>
    http.get<WorkflowTemplate>(`/workflows/templates/${id}`),

  createTemplate: (data: { name: string; description?: string; project_type?: string; definition: Record<string, unknown> }) =>
    http.post<WorkflowTemplate>('/workflows/templates', data),

  updateTemplate: (id: number, data: Partial<{ name: string; description: string; project_type: string; definition: Record<string, unknown>; is_active: boolean }>) =>
    http.put<WorkflowTemplate>(`/workflows/templates/${id}`, data),

  deleteTemplate: (id: number) =>
    http.delete(`/workflows/templates/${id}`),

  // Validation & Condition evaluation
  validateDefinition: (definition: Record<string, unknown>) =>
    http.post<WorkflowValidationResult>('/workflows/validate', { definition }),

  evaluateCondition: (expression: string, context: Record<string, unknown> = {}) =>
    http.post<ConditionEvaluateResult>('/workflows/evaluate-condition', { expression, context }),

  // Instances
  listInstances: (params?: { order_id?: number; template_id?: number; status?: string; page?: number; size?: number }) =>
    http.get<PageResponse<WorkflowInstance>>('/workflows/instances', params),

  getInstance: (id: number) =>
    http.get<WorkflowInstance>(`/workflows/instances/${id}`),

  createInstance: (data: { template_id: number; order_id?: number; name?: string }) =>
    http.post<WorkflowInstance>('/workflows/instances', data),

  advanceNode: (instanceId: number, data: { node_id: string; status: string; notes?: string }) =>
    http.put<WorkflowInstance>(`/workflows/instances/${instanceId}/advance`, data),

  // Audit logs
  getAuditLogs: (instanceId: number, params?: { page?: number; size?: number }) =>
    http.get<PageResponse<WorkflowAuditLog>>(`/workflows/instances/${instanceId}/audit-logs`, params),
}

// ---------------------------------------------------------------------------
// Dashboard API
// ---------------------------------------------------------------------------

export interface DashboardStats {
  active_orders: number
  monthly_revenue: number
  pending_approval: number
  overdue_nodes: number
  revenue_trend: number
}

export interface OrderStatusDistribution {
  status: string
  label: string
  count: number
}

export interface RevenueTrendItem {
  month: string
  key: string
  revenue: number
}

export interface CompletionRate {
  total: number
  completed: number
  rate: number
}

export interface ActivityItem {
  id: string
  text: string
  time: string | null
  type: string
  color: string
}

export interface FunnelItem {
  name: string
  value: number
}

export interface SupplyChainFlowData {
  nodes: Array<{ name: string }>
  links: Array<{ source: string; target: string; value: number }>
}

export const dashboardApi = {
  getStats: (params?: { date_from?: string; date_to?: string }) =>
    http.get<DashboardStats>('/dashboard/stats', params),

  getOrderStatusDistribution: () =>
    http.get<OrderStatusDistribution[]>('/dashboard/order-status-distribution'),

  getRevenueTrend: (months?: number) =>
    http.get<RevenueTrendItem[]>('/dashboard/revenue-trend', months ? { months } : undefined),

  getCompletionRate: () =>
    http.get<CompletionRate>('/dashboard/completion-rate'),

  getRecentActivities: (limit?: number) =>
    http.get<ActivityItem[]>('/dashboard/recent-activities', limit ? { limit } : undefined),

  getFunnel: () =>
    http.get<FunnelItem[]>('/dashboard/funnel'),

  getSupplyChainFlow: () =>
    http.get<SupplyChainFlowData>('/dashboard/supply-chain-flow'),
}


// ---------------------------------------------------------------------------
// ISO 9001 Process API
// ---------------------------------------------------------------------------

export const isoApi = {
  // Risk Assessments
  listRiskAssessments: (params?: { order_id?: number; page?: number; size?: number }) =>
    http.get<PageResponse<InquiryRiskAssessment>>('/iso/risk-assessments', params),
  createRiskAssessment: (data: Partial<InquiryRiskAssessment>) =>
    http.post<InquiryRiskAssessment>('/iso/risk-assessments', data),
  approveRiskAssessment: (id: number, approved: boolean) =>
    http.post<InquiryRiskAssessment>(`/iso/risk-assessments/${id}/approve`, { approved }),

  // Inquiry Records
  listInquiryRecords: (params?: { order_id?: number; supplier_id?: number; page?: number; size?: number }) =>
    http.get<PageResponse<InquiryRecord>>('/iso/inquiry-records', params),
  createInquiryRecord: (data: Partial<InquiryRecord>) =>
    http.post<InquiryRecord>('/iso/inquiry-records', data),
  updateInquiryRecord: (id: number, data: Partial<InquiryRecord>) =>
    http.put<InquiryRecord>(`/iso/inquiry-records/${id}`, data),

  // Supplier Comparisons
  listComparisons: (params?: { order_id?: number; page?: number; size?: number }) =>
    http.get<PageResponse<SupplierComparison>>('/iso/supplier-comparisons', params),
  createComparison: (data: Partial<SupplierComparison>) =>
    http.post<SupplierComparison>('/iso/supplier-comparisons', data),

  // Contract Reviews
  listContractReviews: (params?: { contract_id?: number; page?: number; size?: number }) =>
    http.get<PageResponse<ContractReview>>('/iso/contract-reviews', params),
  createContractReview: (data: Partial<ContractReview>) =>
    http.post<ContractReview>('/iso/contract-reviews', data),

  // Project Changes
  listProjectChanges: (params?: { order_id?: number; page?: number; size?: number }) =>
    http.get<PageResponse<ProjectChange>>('/iso/project-changes', params),
  createProjectChange: (data: { order_id: number; change_type: string; description: string; impact_analysis?: string }) =>
    http.post<ProjectChange>('/iso/project-changes', data),
  confirmProjectChange: (id: number, data: { customer_confirmation: boolean; confirmation_date?: string }) =>
    http.post<ProjectChange>(`/iso/project-changes/${id}/confirm`, data),

  // Quality Inspections
  listInspections: (params?: { order_id?: number; result?: string; page?: number; size?: number }) =>
    http.get<PageResponse<QualityInspection>>('/iso/quality-inspections', params),
  createInspection: (data: Partial<QualityInspection>) =>
    http.post<QualityInspection>('/iso/quality-inspections', data),

  // Project Acceptances
  listAcceptances: (params?: { order_id?: number; page?: number; size?: number }) =>
    http.get<PageResponse<ProjectAcceptance>>('/iso/project-acceptances', params),
  createAcceptance: (data: { order_id: number; acceptance_type: string; acceptance_date?: string; notes?: string }) =>
    http.post<ProjectAcceptance>('/iso/project-acceptances', data),
  confirmAcceptance: (id: number, data: { customer_confirmed: boolean; confirmation_method?: string; confirmation_date?: string }) =>
    http.post<ProjectAcceptance>(`/iso/project-acceptances/${id}/confirm`, data),

  // Project Closures
  listClosures: (params?: { status?: string; page?: number; size?: number }) =>
    http.get<PageResponse<ProjectClosure>>('/iso/project-closures', params),
  createClosure: (data: { order_id: number; lessons_learned?: string; improvement_suggestions?: string }) =>
    http.post<ProjectClosure>('/iso/project-closures', data),
  updateClosure: (id: number, data: Partial<ProjectClosure>) =>
    http.put<ProjectClosure>(`/iso/project-closures/${id}`, data),
  submitClosure: (id: number) =>
    http.post<ProjectClosure>(`/iso/project-closures/${id}/submit`),
  approveClosure: (id: number, approved: boolean) =>
    http.post<ProjectClosure>(`/iso/project-closures/${id}/approve`, { approved }),

  // Complaints
  listComplaints: (params?: { customer_id?: number; status?: string; page?: number; size?: number }) =>
    http.get<PageResponse<Complaint>>('/iso/complaints', params),
  createComplaint: (data: { customer_id: number; order_id?: number; source?: string; content: string; period_no_complaint?: boolean }) =>
    http.post<Complaint>('/iso/complaints', data),
  updateComplaint: (id: number, data: { investigation?: string; resolution?: string; customer_feedback?: string; status?: string }) =>
    http.put<Complaint>(`/iso/complaints/${id}`, data),

  // Satisfaction Surveys
  listSurveys: (params?: { customer_id?: number; year?: number; status?: string; page?: number; size?: number }) =>
    http.get<PageResponse<SatisfactionSurvey>>('/iso/satisfaction-surveys', params),
  createSurvey: (data: { customer_id: number; year: number }) =>
    http.post<SatisfactionSurvey>('/iso/satisfaction-surveys', data),
  sendSurvey: (id: number) =>
    http.post<SatisfactionSurvey>(`/iso/satisfaction-surveys/${id}/send`),
  respondSurvey: (id: number, data: Partial<SatisfactionSurvey>) =>
    http.post<SatisfactionSurvey>(`/iso/satisfaction-surveys/${id}/respond`, data),

  // Supplier Admissions
  listAdmissions: (params?: { supplier_id?: number; status?: string; page?: number; size?: number }) =>
    http.get<PageResponse<SupplierAdmission>>('/iso/supplier-admissions', params),
  createAdmission: (data: Partial<SupplierAdmission>) =>
    http.post<SupplierAdmission>('/iso/supplier-admissions', data),
  approveAdmission: (id: number, data: { approved: boolean; notes?: string }) =>
    http.post<SupplierAdmission>(`/iso/supplier-admissions/${id}/approve`, data),

  // Supplier Evaluations
  listEvaluations: (params?: { supplier_id?: number; year?: number; page?: number; size?: number }) =>
    http.get<PageResponse<SupplierEvaluation>>('/iso/supplier-evaluations', params),
  createEvaluation: (data: { supplier_id: number; year: number; quality_score?: number; delivery_score?: number; price_score?: number; service_score?: number; notes?: string }) =>
    http.post<SupplierEvaluation>('/iso/supplier-evaluations', data),

  // Change Logs
  listChangeLogs: (params?: { entity_type?: string; entity_id?: number; page?: number; size?: number }) =>
    http.get<PageResponse<ChangeLogEntry>>('/iso/change-logs', params),

  // Knowledge Base
  listKnowledge: (params?: { doc_type?: string; keyword?: string; page?: number; size?: number }) =>
    http.get<PageResponse<KnowledgeDocument>>('/iso/knowledge', params),
  createKnowledge: (data: { title: string; content: string; doc_type: string }) =>
    http.post<KnowledgeDocument>('/iso/knowledge', data),
  getKnowledge: (id: number) =>
    http.get<KnowledgeDocument>(`/iso/knowledge/${id}`),
  deleteKnowledge: (id: number) =>
    http.delete(`/iso/knowledge/${id}`),
}
