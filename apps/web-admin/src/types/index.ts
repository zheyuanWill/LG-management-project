export interface SelectOption {
  value: string
  label: string
}

export interface TableColumn<T = unknown> {
  title: string
  dataIndex: keyof T | string
  key?: string
  width?: number
  fixed?: 'left' | 'right'
  render?: (value: unknown, record: T, index: number) => React.ReactNode
}

export interface RouteMetaInfo {
  title: string
  icon?: string
  hidden?: boolean
  roles?: string[]
}
