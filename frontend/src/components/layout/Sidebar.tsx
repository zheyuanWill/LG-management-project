import { useState } from 'react'
import { Link, useNavigate } from '@tanstack/react-router'
import {
  LayoutDashboard,
  Ship,
  FileText,
  Wrench,
  Package,
  StickyNote,
  BookOpen,
  Users,
  FolderOpen,
  ChevronLeft,
  ChevronRight,
  LogOut,
  Building2,
} from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'
import { cn } from '@/lib/utils'

const navigation = [
  { name: '首页', href: '/dashboard', icon: LayoutDashboard },
  {
    name: '业务管理',
    icon: Building2,
    children: [
      { name: '监修', href: '/supervision', icon: Ship },
      { name: '买卖经纪', href: '/brokerage-sale', icon: FileText },
      { name: '修船经纪', href: '/brokerage-repair', icon: Wrench },
      { name: '备件供应', href: '/spare-parts', icon: Package },
    ],
  },
  { name: '随手存', href: '/quick-save', icon: StickyNote },
  { name: 'RAG 知识库', href: '/knowledge', icon: BookOpen },
  { name: '客户名录', href: '/customers', icon: Users },
  { name: '文件中心', href: '/files', icon: FolderOpen },
]

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false)
  const { user, logout, isAuthenticated } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate({ to: '/login' })
  }

  return (
    <aside
      className={cn(
        'flex h-screen flex-col shrink-0 border-r border-border bg-surface transition-all duration-300',
        collapsed ? 'w-16' : 'w-64'
      )}
    >
      <div className="flex h-16 items-center justify-between border-b border-border px-4">
        <div className={cn('flex items-center gap-2', collapsed && 'justify-center w-full')}>
          {!collapsed && (
            <div className="flex flex-col">
              <span className="text-base font-bold text-primary">LG 船舶管理</span>
              <span className="text-xs text-muted-foreground">ERP System</span>
            </div>
          )}
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-white">
            <Ship className="h-5 w-5" />
          </div>
        </div>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto p-3">
        {navigation.map((item) => {
          if ('children' in item) {
            return (
              <div key={item.name} className="space-y-1">
                {!collapsed && (
                  <p className="px-3 pt-3 pb-1 text-xs font-semibold uppercase text-muted-foreground">
                    {item.name}
                  </p>
                )}
                {item.children.map((child) => (
                  <Link
                    key={child.href}
                    to={child.href}
                    className={cn(
                      'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                      collapsed && 'justify-center px-2'
                    )}
                    activeProps={{ className: 'bg-primary text-primary-foreground' }}
                    inactiveProps={{ className: 'text-foreground hover:bg-surface-muted' }}
                  >
                    <child.icon className="h-5 w-5 shrink-0" />
                    {!collapsed && <span>{child.name}</span>}
                  </Link>
                ))}
              </div>
            )
          }

          return (
            <Link
              key={item.href}
              to={item.href}
              className={cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                collapsed && 'justify-center px-2'
              )}
              activeProps={{ className: 'bg-primary text-primary-foreground' }}
              inactiveProps={{ className: 'text-foreground hover:bg-surface-muted' }}
            >
              <item.icon className="h-5 w-5 shrink-0" />
              {!collapsed && <span>{item.name}</span>}
            </Link>
          )
        })}
      </nav>

      <div className="border-t border-border p-3">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="mb-2 flex w-full items-center justify-center rounded-lg p-2 text-muted-foreground hover:bg-surface-muted hover:text-foreground transition-colors"
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </button>

        {isAuthenticated && (
          <div
            className={cn(
              'flex items-center gap-3 rounded-lg p-2',
              collapsed && 'justify-center'
            )}
          >
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-sm font-medium text-white">
              {user?.display_name?.[0]?.toUpperCase() || 'U'}
            </div>
            {!collapsed && (
              <div className="flex-1 min-w-0">
                <p className="truncate text-sm font-medium">{user?.display_name}</p>
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-1 text-xs text-muted-foreground hover:text-destructive transition-colors"
                >
                  <LogOut className="h-3 w-3" />
                  退出
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </aside>
  )
}