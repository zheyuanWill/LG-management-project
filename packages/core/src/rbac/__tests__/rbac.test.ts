import { describe, it, expect } from 'vitest'
import { hasPermission, getPermissions, Resource, Action } from '../index'
import { UserRole } from '../../domain/user'

describe('hasPermission', () => {
  it('OWNER has all permissions', () => {
    expect(hasPermission(UserRole.OWNER, Resource.ORDER, Action.CREATE)).toBe(true)
    expect(hasPermission(UserRole.OWNER, Resource.COST, Action.VIEW_PROFIT)).toBe(true)
  })

  it('PM can create orders', () => {
    expect(hasPermission(UserRole.PM, Resource.ORDER, Action.CREATE)).toBe(true)
  })

  it('PROC can create procurement', () => {
    expect(hasPermission(UserRole.PROC, Resource.PROCUREMENT, Action.CREATE)).toBe(true)
  })

  it('FIN can read payments', () => {
    expect(hasPermission(UserRole.FIN, Resource.PAYMENT, Action.READ)).toBe(true)
  })

  it('OPS can read inventory', () => {
    expect(hasPermission(UserRole.OPS, Resource.INVENTORY, Action.READ)).toBe(true)
  })
})

describe('getPermissions', () => {
  it('returns permissions for a role', () => {
    const perms = getPermissions(UserRole.OWNER)
    expect(perms.length).toBeGreaterThan(0)
    expect(perms).toContain('order:create')
  })

  it('returns different permissions for different roles', () => {
    const ownerPerms = getPermissions(UserRole.OWNER)
    const opsPerms = getPermissions(UserRole.OPS)
    expect(ownerPerms.length).toBeGreaterThan(opsPerms.length)
  })
})
