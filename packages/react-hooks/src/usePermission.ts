import { useCallback } from 'react'
import { useAuthStore } from './useAuth'
import {
  hasPermission,
  getVisibility,
  Resource,
  Action,
  type Permission,
  type UserRole,
} from '@lg/core'

export function usePermission() {
  const user = useAuthStore((s) => s.user)
  const userRole = user?.role as UserRole | undefined

  const can = useCallback(
    (resource: Resource, action: Action): boolean => {
      if (!userRole) return false
      return hasPermission(userRole, resource, action)
    },
    [userRole]
  )

  const canAccess = useCallback(
    (permission: Permission): boolean => {
      if (!userRole) return false
      return hasPermission(userRole, permission)
    },
    [userRole]
  )

  const isRole = useCallback(
    (...roles: string[]): boolean => {
      if (!userRole) return false
      return roles.includes(userRole)
    },
    [userRole]
  )

  const visibility = useCallback(
    (permission: Permission) => {
      if (!userRole) return 'hidden' as const
      return getVisibility(userRole, permission)
    },
    [userRole]
  )

  return { userRole, can, canAccess, isRole, visibility, Resource, Action }
}
