export interface User {
  id: number
  username: string
  display_name: string
  full_name?: string
  email?: string
  phone?: string | null
  role: 'admin' | 'manager' | 'user'
  created_at: string
}

export interface UserLogin {
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export type ProjectType = 'supervision' | 'brokerage_sale' | 'brokerage_repair' | 'spare_parts'
export type ProjectStatus = 'active' | 'completed' | 'cancelled'

export interface Project {
  id: number
  project_no: string
  type: ProjectType
  status: ProjectStatus
  ship_name: string
  imo?: string
  owner_id?: number
  owner_name?: string
  planned_completion_date?: string
  actual_completion_date?: string
  remarks?: string
  created_at: string
  updated_at: string
  task_count?: number
  completed_task_count?: number
  risk_count?: number
  customer_name?: string | null
  customer_phone?: string | null
  risk_summary?: string | null
  has_unconfirmed_report?: boolean
}

export type TaskStatus = 'not_started' | 'in_progress' | 'completed' | 'paused'

export interface Task {
  id: number
  project_id: number
  name: string
  title?: string
  description?: string
  planned_end_date?: string
  due_date?: string
  status: TaskStatus
  sort_order: number
  created_at: string
  updated_at: string
}

export interface TaskDailyUpdate {
  id: number
  task_id: number
  update_date: string
  status?: TaskStatus
  remark?: string
  audio_duration?: number
  created_at: string
  photos?: TaskPhoto[]
}

export interface TaskPhoto {
  id: number
  storage_key: string
  url?: string
  thumbnail_url?: string
  caption?: string
  created_at: string
}

export interface Photo {
  id: string
  url: string
  thumbnail_url?: string
  caption?: string
  created_at: string
}

export interface ProjectCompletionFile {
  id: string
  type: 'completion' | 'acceptance'
  name: string
  url: string
  uploaded_at: string
}

export interface DailyReport {
  id: number
  project_id: number
  report_date: string
  date?: string
  completed_items: DailyReportItem[]
  completed_tasks?: number
  progress_total?: number
  tomorrow_plan?: string
  risk_alert?: string
  confirmed: boolean
  created_at: string
}

export interface DailyReportItem {
  task_id: number
  task_name: string
  task_title?: string
  remark?: string
  content?: string
  photos: TaskPhoto[]
}

export interface WeeklyReport {
  id: number
  project_id: number
  week_start_date: string
  week_start?: string
  week_end_date: string
  week_end?: string
  summary: string
  next_week_plan: string
  progress_total?: number
  key_events?: string[]
  confirmed: boolean
  created_at: string
}

export type RiskLevel = 'info' | 'warning' | 'critical'

export interface RiskEvent {
  id: number
  project_id: number
  title: string
  detail?: string
  level?: RiskLevel
  risk_level: RiskLevel
  message?: string
  category?: string
  resolved: boolean
  resolved_at?: string
  created_at: string
}

export type LogisticsNodeType =
  | 'ordered'
  | 'supplier_shipped'
  | 'in_transit'
  | 'arrived'
  | 'warehoused'
  | 'sent_to_owner'
  | 'hk_signed'
  | 'settled'

export interface LogisticsNode {
  id: number
  project_id: number
  node_type: LogisticsNodeType
  node_date: string
  tracking_no?: string
  remark?: string
  attachment_key?: string
  created_at: string
}

export type FileType =
  | 'contract'
  | 'receipt'
  | 'wechat_screenshot'
  | 'survey'
  | 'certificate'
  | 'invoice'
  | 'photo'
  | 'other'

export interface FileItem {
  id: number
  project_id?: number
  file_name: string
  name?: string
  file_type: FileType
  type?: FileType
  storage_key: string
  file_size?: number
  size?: number
  mime_type?: string
  download_url?: string
  url?: string
  created_at: string
}

export interface Customer {
  id: number
  name: string
  contact_person?: string
  phone?: string
  email?: string
  survey_conclusion?: 'viable' | 'cautious' | 'not_recommended'
  remarks?: string
  notes?: string
  created_at: string
  updated_at: string
}

export interface QuickSave {
  id: number
  content_type: 'text' | 'image'
  content_text?: string
  file_key?: string
  recognized_text?: string
  suggested_project_id?: number
  confirmed_project_id?: number
  status: 'pending' | 'confirmed' | 'discarded'
  created_at: string
}

export interface KnowledgeDocument {
  id: number
  title: string
  category?: string
  file_key: string
  created_at: string
}

export interface ApiResponse<T> {
  data: T
  message?: string
  code?: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}