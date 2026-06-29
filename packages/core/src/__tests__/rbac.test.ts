import { describe, it, expect } from 'vitest'
import { hasPermission, getPermissions, Resource, Action } from '../rbac'
import { UserRole } from '../domain/user'

describe('RBAC', () => {
  it('OWNER has all permissions', () => {
    expect(hasPermission(UserRole.OWNER, Resource.ORDER, Action.CREATE)).toBe(true)
    expect(hasPermission(UserRole.OWNER, Resource.ORDER, Action.DELETE)).toBe(true)
    expect(hasPermission(UserRole.OWNER, Resource.COST, Action.VIEW_PROFIT)).toBe(true)
  })

  it('PM can manage orders', () => {
    expect(hasPermission(UserRole.PM, Resource.ORDER, Action.CREATE)).toBe(true)
    expect(hasPermission(UserRole.PM, Resource.ORDER, Action.READ)).toBe(true)
  })

  it('PROC can manage procurement', () => {
    expect(hasPermission(UserRole.PROC, Resource.PROCUREMENT, Action.CREATE)).toBe(true)
  })

  it('FIN can view cost', () => {
    expect(hasPermission(UserRole.FIN, Resource.COST, Action.VIEW_COST)).toBe(true)
  })

  it('getPermissions returns array', () => {
    const perms = getPermissions(UserRole.OWNER)
    expect(Array.isArray(perms)).toBe(true)
    expect(perms.length).toBeGreaterThan(0)
  })
})
