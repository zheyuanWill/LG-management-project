/**
 * RBAC - Role-Based Access Control
 */
import { UserRole } from '../domain/user'

// Re-export UserRole for convenience
export { UserRole }

/**
 * Resource enums - aligned with backend (services/api/app/core/rbac.py)
 */
export enum Resource {
  ORDER = 'order',
  QUOTE = 'quote',
  CONTRACT = 'contract',
  PROCUREMENT = 'procurement',
  SUPPLIER = 'supplier',
  PRODUCT = 'product',
  INVENTORY = 'inventory',
  TRACKING = 'tracking',
  SETTLEMENT = 'settlement',
  COST = 'cost',
  REPORT = 'report',
  USER = 'user',
  FILE = 'file',
}

/**
 * Action enums - aligned with backend
 */
export enum Action {
  CREATE = 'create',
  READ = 'read',
  UPDATE = 'update',
  DELETE = 'delete',
  APPROVE = 'approve',
  EXPORT = 'export',
  VIEW_COST = 'view_cost',
  VIEW_PROFIT = 'view_profit',
}

export type Permission =
  | 'order:create' | 'order:read' | 'order:update' | 'order:delete' | 'order:export'
  | 'quote:create' | 'quote:read' | 'quote:update' | 'quote:approve' | 'quote:export'
  | 'contract:create' | 'contract:read' | 'contract:update' | 'contract:delete' | 'contract:approve' | 'contract:export'
  | 'procurement:create' | 'procurement:read' | 'procurement:update' | 'procurement:approve' | 'procurement:view_cost'
  | 'supplier:create' | 'supplier:read' | 'supplier:update' | 'supplier:delete' | 'supplier:view_cost'
  | 'product:create' | 'product:read' | 'product:update' | 'product:delete'
  | 'inventory:create' | 'inventory:read' | 'inventory:update' | 'inventory:delete'
  | 'tracking:create' | 'tracking:read' | 'tracking:update' | 'tracking:delete'
  | 'settlement:create' | 'settlement:read' | 'settlement:update' | 'settlement:approve' | 'settlement:export' | 'settlement:view_cost' | 'settlement:view_profit'
  | 'cost:create' | 'cost:read' | 'cost:update' | 'cost:export' | 'cost:view_cost' | 'cost:view_profit'
  | 'report:read' | 'report:export' | 'report:view_cost' | 'report:view_profit'
  | 'user:create' | 'user:read' | 'user:update' | 'user:delete'
  | 'file:create' | 'file:read' | 'file:update' | 'file:delete'

const rolePermissions: Record<UserRole, Permission[]> = {
  [UserRole.OWNER]: [
    'order:create', 'order:read', 'order:update', 'order:delete', 'order:export',
    'quote:create', 'quote:read', 'quote:update', 'quote:approve', 'quote:export',
    'contract:create', 'contract:read', 'contract:update', 'contract:delete', 'contract:approve', 'contract:export',
    'procurement:create', 'procurement:read', 'procurement:update', 'procurement:approve', 'procurement:view_cost',
    'supplier:create', 'supplier:read', 'supplier:update', 'supplier:delete', 'supplier:view_cost',
    'product:create', 'product:read', 'product:update', 'product:delete',
    'inventory:create', 'inventory:read', 'inventory:update', 'inventory:delete',
    'tracking:create', 'tracking:read', 'tracking:update', 'tracking:delete',
    'settlement:create', 'settlement:read', 'settlement:update', 'settlement:approve', 'settlement:export', 'settlement:view_cost', 'settlement:view_profit',
    'cost:create', 'cost:read', 'cost:update', 'cost:export', 'cost:view_cost', 'cost:view_profit',
    'report:read', 'report:export', 'report:view_cost', 'report:view_profit',
    'user:create', 'user:read', 'user:update', 'user:delete',
    'file:create', 'file:read', 'file:update', 'file:delete',
  ],
  [UserRole.GENERAL_MANAGER]: [
    'order:create', 'order:read', 'order:update', 'order:delete', 'order:export',
    'quote:create', 'quote:read', 'quote:update', 'quote:approve', 'quote:export',
    'contract:create', 'contract:read', 'contract:update', 'contract:delete', 'contract:approve', 'contract:export',
    'procurement:create', 'procurement:read', 'procurement:update', 'procurement:approve', 'procurement:view_cost',
    'supplier:create', 'supplier:read', 'supplier:update', 'supplier:delete', 'supplier:view_cost',
    'product:create', 'product:read', 'product:update', 'product:delete',
    'inventory:create', 'inventory:read', 'inventory:update', 'inventory:delete',
    'tracking:create', 'tracking:read', 'tracking:update', 'tracking:delete',
    'settlement:create', 'settlement:read', 'settlement:update', 'settlement:approve', 'settlement:export', 'settlement:view_cost', 'settlement:view_profit',
    'cost:create', 'cost:read', 'cost:update', 'cost:export', 'cost:view_cost', 'cost:view_profit',
    'report:read', 'report:export', 'report:view_cost', 'report:view_profit',
    'user:create', 'user:read', 'user:update', 'user:delete',
    'file:create', 'file:read', 'file:update', 'file:delete',
  ],
  [UserRole.SOFTWARE_ENGINEER]: [
    'order:create', 'order:read', 'order:update', 'order:delete', 'order:export',
    'quote:create', 'quote:read', 'quote:update', 'quote:approve', 'quote:export',
    'contract:create', 'contract:read', 'contract:update', 'contract:delete', 'contract:approve', 'contract:export',
    'procurement:create', 'procurement:read', 'procurement:update', 'procurement:approve', 'procurement:view_cost',
    'supplier:create', 'supplier:read', 'supplier:update', 'supplier:delete', 'supplier:view_cost',
    'product:create', 'product:read', 'product:update', 'product:delete',
    'inventory:create', 'inventory:read', 'inventory:update', 'inventory:delete',
    'tracking:create', 'tracking:read', 'tracking:update', 'tracking:delete',
    'settlement:create', 'settlement:read', 'settlement:update', 'settlement:approve', 'settlement:export', 'settlement:view_cost', 'settlement:view_profit',
    'cost:create', 'cost:read', 'cost:update', 'cost:export', 'cost:view_cost', 'cost:view_profit',
    'report:read', 'report:export', 'report:view_cost', 'report:view_profit',
    'user:create', 'user:read', 'user:update', 'user:delete',
    'file:create', 'file:read', 'file:update', 'file:delete',
  ],
  [UserRole.PM]: [
    'order:create', 'order:read', 'order:update', 'order:export',
    'quote:create', 'quote:read', 'quote:update', 'quote:export',
    'contract:read', 'contract:update',
    'procurement:read',
    'supplier:read',
    'product:read',
    'inventory:read',
    'tracking:create', 'tracking:read', 'tracking:update',
    'settlement:create', 'settlement:read',
    'cost:read',
    'report:read',
    'file:create', 'file:read',
  ],
  [UserRole.SUPERVISOR]: [
    'order:create', 'order:read', 'order:update', 'order:export',
    'quote:create', 'quote:read', 'quote:update', 'quote:export',
    'contract:read', 'contract:update',
    'procurement:read',
    'supplier:read',
    'product:read',
    'inventory:read',
    'tracking:create', 'tracking:read', 'tracking:update',
    'settlement:create', 'settlement:read',
    'cost:read',
    'report:read',
    'file:create', 'file:read',
  ],
  [UserRole.PROC]: [
    'order:read',
    'quote:read',
    'contract:read',
    'procurement:create', 'procurement:read', 'procurement:update', 'procurement:view_cost',
    'supplier:create', 'supplier:read', 'supplier:update', 'supplier:view_cost',
    'product:create', 'product:read', 'product:update',
    'inventory:create', 'inventory:read', 'inventory:update',
    'tracking:read', 'tracking:update',
    'cost:read', 'cost:view_cost',
    'file:create', 'file:read',
  ],
  [UserRole.GENERAL_AFFAIRS]: [
    'order:read',
    'quote:read',
    'contract:read',
    'procurement:create', 'procurement:read', 'procurement:update', 'procurement:view_cost',
    'supplier:create', 'supplier:read', 'supplier:update', 'supplier:view_cost',
    'product:create', 'product:read', 'product:update',
    'inventory:create', 'inventory:read', 'inventory:update',
    'tracking:read', 'tracking:update',
    'cost:read', 'cost:view_cost',
    'file:create', 'file:read',
  ],
  [UserRole.FIN]: [
    'order:read', 'order:export',
    'quote:read', 'quote:export',
    'contract:read', 'contract:update', 'contract:export',
    'procurement:read', 'procurement:view_cost',
    'supplier:read', 'supplier:view_cost',
    'product:read',
    'inventory:read',
    'tracking:read',
    'settlement:create', 'settlement:read', 'settlement:update', 'settlement:approve', 'settlement:export', 'settlement:view_cost', 'settlement:view_profit',
    'cost:create', 'cost:read', 'cost:update', 'cost:export', 'cost:view_cost', 'cost:view_profit',
    'report:read', 'report:export', 'report:view_cost', 'report:view_profit',
    'file:create', 'file:read',
  ],
  [UserRole.FINANCE]: [
    'order:read', 'order:export',
    'quote:read', 'quote:export',
    'contract:read', 'contract:update', 'contract:export',
    'procurement:read', 'procurement:view_cost',
    'supplier:read', 'supplier:view_cost',
    'product:read',
    'inventory:read',
    'tracking:read',
    'settlement:create', 'settlement:read', 'settlement:update', 'settlement:approve', 'settlement:export', 'settlement:view_cost', 'settlement:view_profit',
    'cost:create', 'cost:read', 'cost:update', 'cost:export', 'cost:view_cost', 'cost:view_profit',
    'report:read', 'report:export', 'report:view_cost', 'report:view_profit',
    'file:create', 'file:read',
  ],
  [UserRole.OPS]: [
    'order:read', 'order:export',
    'quote:read', 'quote:export',
    'contract:read', 'contract:export',
    'procurement:read',
    'supplier:read',
    'product:create', 'product:read', 'product:update',
    'inventory:create', 'inventory:read', 'inventory:update',
    'tracking:read',
    'cost:read',
    'report:read', 'report:export',
    'file:create', 'file:read',
  ],
}

/**
 * Check if role has permission
 * Supports both string permission and Resource/Action combination
 */
export function hasPermission(role: UserRole | string, resourceOrPermission: Resource | Permission, action?: Action): boolean {
  const userRole = typeof role === 'string' ? role as UserRole : role
  const permissions = rolePermissions[userRole]
  if (!permissions) return false
  
  // If action is provided, build permission string
  if (action !== undefined) {
    const permission = `${resourceOrPermission}:${action}` as Permission
    return permissions.includes(permission)
  }
  
  // Direct permission check
  return permissions.includes(resourceOrPermission as Permission)
}

export const getPermissions = (role: UserRole): Permission[] => {
  return rolePermissions[role] ?? []
}

/**
 * UI Visibility Strategy
 * Returns: 'visible' | 'hidden' | 'disabled'
 */
export const getVisibility = (role: UserRole, permission: Permission): 'visible' | 'hidden' | 'disabled' => {
  if (hasPermission(role, permission)) {
    return 'visible'
  }
  
  // Read permissions show as disabled, write permissions are hidden
  if (permission.includes(':read')) {
    return 'disabled'
  }
  
  return 'hidden'
}
