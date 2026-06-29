import { createFileRoute, redirect, Outlet } from '@tanstack/react-router'
import { MainLayout } from '@/components/layout/MainLayout'

export const Route = createFileRoute('/_authenticated')({
  beforeLoad: ({ context }) => {
    if (!context.auth.token || !context.auth.user) {
      throw redirect({ to: '/login', search: { redirect: window.location.pathname } })
    }
  },
  component: AuthenticatedLayout,
})

function AuthenticatedLayout() {
  return (
    <MainLayout>
      <Outlet />
    </MainLayout>
  )
}
