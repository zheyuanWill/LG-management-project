import { useState } from 'react'
import { useLocation } from '@tanstack/react-router'
import { Bell, ChevronDown, Search, User, Settings, LogOut } from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'
import { cn } from '@/lib/utils'

const breadcrumbMap: Record<string, string> = {
  '/dashboard': '首页',
  '/supervision': '监修',
  '/brokerage/sale': '买卖经纪',
  '/brokerage/repair': '修船经纪',
  '/spare-parts': '备件供应',
  '/quick-save': '随手存',
  '/knowledge': 'RAG 知识库',
  '/customers': '客户名录',
  '/files': '文件中心',
}

export default function TopBar() {
  const location = useLocation()
  const { user, logout } = useAuth()
  const [showMenu, setShowMenu] = useState(false)

  const pathSegments = location.pathname.split('/').filter(Boolean)
  const breadcrumbs: string[] = []
  let currentPath = ''

  for (const segment of pathSegments) {
    currentPath += `/${segment}`
    breadcrumbs.push(breadcrumbMap[currentPath] || segment)
  }

  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-border bg-surface px-6">
      <div className="flex items-center gap-2 text-sm">
        <span className="text-muted-foreground">LG 船舶管理</span>
        {breadcrumbs.map((crumb, index) => (
          <span key={index} className="flex items-center gap-2">
            <span className="text-muted-foreground">/</span>
            <span
              className={
                index === breadcrumbs.length - 1
                  ? 'font-medium text-foreground'
                  : 'text-muted-foreground'
              }
            >
              {crumb}
            </span>
          </span>
        ))}
      </div>

      <div className="flex items-center gap-3">
        <button className="flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground hover:bg-surface-muted hover:text-foreground transition-colors">
          <Search className="h-4 w-4" />
        </button>

        <button className="relative flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground hover:bg-surface-muted hover:text-foreground transition-colors">
          <Bell className="h-4 w-4" />
          <span className="absolute right-1.5 top-1.5 flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-destructive opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-destructive" />
          </span>
        </button>

        <div className="relative">
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="flex items-center gap-2 rounded-lg px-2 py-1.5 hover:bg-surface-muted transition-colors"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-sm font-medium text-white">
              {user?.full_name?.[0]?.toUpperCase() || 'U'}
            </div>
            <div className="text-left hidden sm:block">
              <p className="text-sm font-medium">{user?.full_name}</p>
              <p className="text-xs text-muted-foreground">{user?.role}</p>
            </div>
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          </button>

          {showMenu && (
            <>
              <div
                className="fixed inset-0 z-40"
                onClick={() => setShowMenu(false)}
              />
              <div
                className={cn(
                  'absolute right-0 z-50 mt-2 w-48 rounded-lg border border-border bg-surface shadow-lg animate-fade-in'
                )}
              >
                <div className="border-b border-border p-3">
                  <p className="text-sm font-medium">{user?.full_name}</p>
                  <p className="text-xs text-muted-foreground">{user?.email}</p>
                </div>
                <div className="p-1">
                  <button className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm hover:bg-surface-muted transition-colors">
                    <User className="h-4 w-4" />
                    个人资料
                  </button>
                  <button className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm hover:bg-surface-muted transition-colors">
                    <Settings className="h-4 w-4" />
                    设置
                  </button>
                  <button
                    onClick={() => {
                      logout()
                      window.location.href = '/login'
                    }}
                    className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm text-destructive hover:bg-destructive/10 transition-colors"
                  >
                    <LogOut className="h-4 w-4" />
                    退出登录
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  )
}