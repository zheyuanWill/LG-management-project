/**
 * User Domain Types
 */
export interface User {
  id: number
  username: string
  email: string
  real_name: string
  role: UserRole
  is_active: boolean
  created_at: string
  updated_at: string
}

export enum UserRole {
  GENERAL_MANAGER = 'GENERAL_MANAGER',
  SUPERVISOR = 'SUPERVISOR',
  GENERAL_AFFAIRS = 'GENERAL_AFFAIRS',
  FINANCE = 'FINANCE',
  SOFTWARE_ENGINEER = 'SOFTWARE_ENGINEER',
  // Backward compatibility
  OWNER = 'OWNER',
  PM = 'PM',
  PROC = 'PROC',
  FIN = 'FIN',
  OPS = 'OPS'
}

export const roleLabels: Record<UserRole, string> = {
  [UserRole.GENERAL_MANAGER]: '总经理',
  [UserRole.SUPERVISOR]: '监修岗',
  [UserRole.GENERAL_AFFAIRS]: '总务',
  [UserRole.FINANCE]: '财务岗',
  [UserRole.SOFTWARE_ENGINEER]: '软件工程师',
  // Backward compatibility
  [UserRole.OWNER]: '总经理',
  [UserRole.PM]: '监修岗',
  [UserRole.PROC]: '总务',
  [UserRole.FIN]: '财务岗',
  [UserRole.OPS]: '总务'
}

// Alias for backward compatibility
export const UserRoleLabels = roleLabels
