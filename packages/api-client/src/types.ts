/**
 * API Types
 *
 * Re-exports domain enums from @lg/core to maintain a single source of truth.
 * Only API-specific types (request/response shapes) are defined here.
 */

// Re-export domain enums from @lg/core (single source of truth)
export {
  UserRole,
  ProjectType,
  OrderStatus,
  QuoteStatus,
  ContractStatus,
  ProcurementStatus,
  SupplierType,
  NodeStatus,
  SettlementStatus,
  FileObjectType,
} from '@lg/core'

export { Currency } from '@lg/core'

// ---------------------------------------------------------------------------
// Common API response types
// ---------------------------------------------------------------------------

export interface ApiResponse<T> {
  data: T
  message?: string
}

export interface PageResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
}

// ---------------------------------------------------------------------------
// Auth types
// ---------------------------------------------------------------------------

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  accessToken: string
  refreshToken: string
  tokenType: string
  expiresIn: number
  user: {
    id: number
    username: string
    realName?: string
    role: string
    avatar?: string
  }
}

export interface CurrentUser {
  id: number
  username: string
  fullName?: string
  role: string
  avatar?: string
  isActive: boolean
  isSuperuser: boolean
  createdAt: string
  updatedAt: string
}

// ---------------------------------------------------------------------------
// Domain entity types (API response shapes — snake_case from backend)
// ---------------------------------------------------------------------------

export interface User {
  id: number
  username: string
  email: string
  real_name: string
  role: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Customer {
  id: number
  name: string
  code: string
  contact_person?: string
  contact_phone?: string
  contact_email?: string
  address?: string
  notes?: string
  created_at: string
  updated_at: string
}

export interface Vessel {
  id: number
  name: string
  imo_number?: string
  customer_id: number
  vessel_type?: string
  notes?: string
  created_at: string
  updated_at: string
}

export interface OrderLineItem {
  id: number
  order_id: number
  product_id?: number
  product_name: string
  specification?: string
  unit: string
  quantity: number
  unit_price: number
  amount: number
  notes?: string
}

export interface Order {
  id: number
  order_no: string
  inquiry_no?: string
  project_code?: string
  customer_id: number
  vessel_id?: number
  project_type: string
  status: string
  currency: string
  total_amount: number
  delivery_date?: string
  pm_id: number
  inquiry_source?: string
  risk_level?: string
  cancellation_reason?: string
  cancellation_category?: string
  notes?: string
  created_at: string
  updated_at: string
  customer_name?: string
  vessel_name?: string
  pm_name?: string
  line_items?: OrderLineItem[]
}

export interface QuoteLineItem {
  id: number
  quote_id: number
  product_id?: number
  product_name: string
  specification?: string
  unit: string
  quantity: number
  unit_price: number
  amount: number
  notes?: string
}

export interface Quote {
  id: number
  quote_no: string
  order_id: number
  version: number
  status: string
  currency: string
  total_amount: number
  valid_until?: string
  notes?: string
  feedback?: string
  created_at: string
  updated_at: string
  line_items?: QuoteLineItem[]
  order_no?: string
  customer_name?: string
}

export interface PaymentPlan {
  id: number
  contract_id: number
  phase: string
  percentage: number
  planned_amount: number
  planned_date: string
  actual_amount?: number
  actual_date?: string
  notes?: string
}

export interface Contract {
  id: number
  contract_no: string
  order_id: number
  quote_id?: number
  customer_id: number
  title: string
  status: string
  currency: string
  total_amount: number
  signed_date?: string
  effective_date?: string
  expiry_date?: string
  payment_terms?: string
  delivery_terms?: string
  warranty_period?: number
  warranty_end_date?: string
  contract_type?: string
  related_contract_id?: number
  notes?: string
  created_at: string
  updated_at: string
  payment_plans?: PaymentPlan[]
  order_no?: string
  customer_name?: string
}

// ---------------------------------------------------------------------------
// ISO 9001 Process Types
// ---------------------------------------------------------------------------

export interface InquiryRiskAssessment {
  id: number
  order_id: number
  customer_credit?: string
  project_feasibility?: string
  payment_risk?: string
  overall_risk?: string
  assessment_notes?: string
  assessor_id?: number
  approved_by?: number
  approved_at?: string
  status: string
  created_at: string
}

export interface InquiryRecord {
  id: number
  order_id: number
  supplier_id: number
  inquiry_method: string
  inquiry_time?: string
  deadline?: string
  responded: boolean
  response_time?: string
  notes?: string
  created_at: string
}

export interface SupplierComparison {
  id: number
  order_id: number
  title?: string
  selected_supplier_id?: number
  selection_reason?: string
  comparison_data?: Record<string, unknown>
  created_by?: number
  created_at: string
}

export interface ContractReview {
  id: number
  contract_id: number
  delivery_review?: string
  payment_review?: string
  technical_review?: string
  penalty_review?: string
  warranty_review?: string
  conclusion: string
  reviewers?: Record<string, unknown>
  review_date?: string
  created_at: string
}

export interface ProjectChange {
  id: number
  order_id: number
  change_no: string
  change_type: string
  description: string
  impact_analysis?: string
  customer_confirmation: boolean
  confirmation_date?: string
  status: string
  created_by?: number
  created_at: string
}

export interface QualityInspection {
  id: number
  order_id: number
  procurement_id?: number
  inspection_type: string
  inspection_date?: string
  result?: string
  inspector_id?: number
  findings?: string
  report_data?: Record<string, unknown>
  created_at: string
}

export interface ProjectAcceptance {
  id: number
  order_id: number
  acceptance_no: string
  acceptance_type: string
  acceptance_date?: string
  customer_confirmed: boolean
  confirmation_method?: string
  confirmation_date?: string
  notes?: string
  status: string
  created_at: string
}

export interface ProjectClosure {
  id: number
  order_id: number
  closure_no: string
  all_payments_settled: boolean
  all_receivables_collected: boolean
  documents_archived: boolean
  archive_location?: string
  lessons_learned?: string
  improvement_suggestions?: string
  closed_by?: number
  closed_at?: string
  approved_by?: number
  approved_at?: string
  status: string
  created_at: string
}

export interface Complaint {
  id: number
  complaint_no: string
  order_id?: number
  customer_id: number
  source: string
  content: string
  received_at: string
  responded_at?: string
  investigation?: string
  resolution?: string
  resolved_at?: string
  customer_feedback?: string
  handler_id?: number
  status: string
  period_no_complaint: boolean
  created_at: string
}

export interface SatisfactionSurvey {
  id: number
  survey_no: string
  customer_id: number
  year: number
  service_quality?: number
  response_speed?: number
  price_reasonability?: number
  communication?: number
  overall_satisfaction?: number
  comments?: string
  sent_at?: string
  responded_at?: string
  status: string
  created_at: string
}

export interface SupplierAdmission {
  id: number
  supplier_id: number
  business_license_verified: boolean
  industry_qualification_verified: boolean
  case_references?: string
  trial_evaluation?: string
  trial_result?: string
  approval_status: string
  approved_by?: number
  approved_at?: string
  notes?: string
  created_at: string
}

export interface SupplierEvaluation {
  id: number
  supplier_id: number
  year: number
  quality_score?: number
  delivery_score?: number
  price_score?: number
  service_score?: number
  total_score?: number
  level?: string
  evaluator_id?: number
  evaluation_date?: string
  notified_supplier: boolean
  notes?: string
  created_at: string
}

export interface ChangeLogEntry {
  id: number
  entity_type: string
  entity_id: number
  change_reason: string
  change_content?: Record<string, unknown>
  changed_by?: number
  version_before?: string
  version_after?: string
  created_at: string
}

export interface KnowledgeDocument {
  id: number
  title: string
  content?: string
  doc_type: string
  source_type?: string
  source_id?: number
  file_id?: number
  embedding_status: string
  tags?: Record<string, unknown>
  created_by?: number
  created_at: string
}

export interface Procurement {
  id: number
  procurement_no: string
  supplier_id: number
  order_id?: number
  status: string
  currency: string
  total_amount: number
  expected_date?: string
  created_by: number
  approved_by?: number
  approved_at?: string
  notes?: string
  created_at: string
  updated_at: string
  supplier_name?: string
  order_no?: string
}

export interface Product {
  id: number
  name: string
  code: string
  specification?: string
  unit: string
  brand?: string
  hs_code?: string
  tax_refund_rate?: number
  shelf_life?: number
  category?: string
  notes?: string
  created_at: string
  updated_at: string
}

export interface SupplierCategoryBrief {
  id: number
  name: string
  code: string
  level: number
  parent_id?: number
}

export interface SupplierCategory extends SupplierCategoryBrief {
  sort_order: number
  description?: string
  created_at: string
  updated_at: string
}

export interface SupplierCategoryTree extends SupplierCategory {
  children: SupplierCategoryTree[]
}

export interface Supplier {
  id: number
  name: string
  code: string
  type: string
  contact_person?: string
  contact_phone?: string
  contact_email?: string
  address?: string
  bank_account?: string
  bank_name?: string
  tax_id?: string
  is_preferred: boolean
  qualification_status?: string
  business_license?: string
  industry_qualification?: string
  admission_date?: string
  last_evaluation_date?: string
  evaluation_score?: number
  evaluation_level?: string
  categories?: SupplierCategoryBrief[]
  notes?: string
  created_at: string
  updated_at: string
}

export interface TrackingNode {
  id: number
  order_id: number
  template_id?: number
  name: string
  sort_order: number
  status: string
  assignee_id?: number
  planned_date?: string
  actual_date?: string
  notes?: string
  created_at: string
  updated_at: string
  assignee_name?: string
  order_no?: string
}

export interface Settlement {
  id: number
  settlement_no: string
  order_id: number
  contract_id?: number
  status: string
  total_revenue: number
  total_cost: number
  gross_profit: number
  gross_profit_rate: number
  total_received: number
  total_disbursed: number
  applicant_id: number
  apply_date: string
  approver_id?: number
  approve_date?: string
  notes?: string
  created_at: string
  updated_at: string
}

export interface FileAttachment {
  id: number
  file_name: string
  original_name: string
  file_key: string
  mime_type: string
  size: number
  object_type: string
  object_id: number
  uploader_id: number
  created_at: string
  updated_at: string
  url?: string
  uploader_name?: string
}
