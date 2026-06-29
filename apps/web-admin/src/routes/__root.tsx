import { createRootRouteWithContext, Outlet } from '@tanstack/react-router'
import type { AuthState } from './-authContext'

export interface RouterContext {
  auth: AuthState
}

export const Route = createRootRouteWithContext<RouterContext>()({
  component: () => <Outlet />,
})
