import type { ReactNode } from 'react'

export interface MenuItemDef {
  key: string
  icon: ReactNode
  label: string
  roles?: string[]
  children?: MenuItemDef[]
  hidden?: boolean
}
