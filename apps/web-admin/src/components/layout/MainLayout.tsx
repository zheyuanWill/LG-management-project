import { useState, useMemo, useEffect, type ReactNode } from 'react'
import { useNavigate, useMatches } from '@tanstack/react-router'
import {
  Layout, Menu, Breadcrumb, Avatar, Dropdown, Button, Modal, message, theme, Tooltip,
} from 'antd'
import {
  MenuFoldOutlined, MenuUnfoldOutlined, SunOutlined, MoonOutlined,
  LogoutOutlined,
} from '@ant-design/icons'
import type { MenuProps } from 'antd'
import { useAuthStore } from '@lg/react-hooks'
import { useThemeStore } from '@/stores/themeStore'
import { AIChatDrawer } from '@/components/ai-chat/AIChatDrawer'
import { activeMenuItems } from './menu/activeMenu'
import type { MenuItemDef } from './menu/types'

const { Sider, Header, Content } = Layout
const allMenuItems: MenuItemDef[] = activeMenuItems

const roleLabels: Record<string, string> = {
  OWNER: '管理层',
  PM: '项目经理',
  PROC: '采购',
  FIN: '财务',
  OPS: '运营',
}

export function MainLayout({ children }: { children: ReactNode }) {
  const [collapsed, setCollapsed] = useState(false)
  const navigate = useNavigate()
  const matches = useMatches()
  const { token: themeToken } = theme.useToken()

  const user = useAuthStore((s) => s.user)
  const logout = useAuthStore((s) => s.logout)
  const { isDark, toggle: toggleTheme } = useThemeStore()

  const { selectedKey, activeGroupKey } = useMemo(() => {
    const lastMatch = matches[matches.length - 1]
    if (!lastMatch) return { selectedKey: '/dashboard', activeGroupKey: '' }
    const path = lastMatch.pathname
    for (const item of allMenuItems) {
      if (!item.children && path.startsWith(item.key)) {
        return { selectedKey: item.key, activeGroupKey: '' }
      }
      if (item.children) {
        const child = item.children.find((c) => path.startsWith(c.key))
        if (child) return { selectedKey: child.key, activeGroupKey: item.key }
      }
    }
    return { selectedKey: '/dashboard', activeGroupKey: '' }
  }, [matches])

  const [openKeys, setOpenKeys] = useState<string[]>([])

  useEffect(() => {
    if (activeGroupKey) {
      setOpenKeys((prev) => prev.includes(activeGroupKey) ? prev : [...prev, activeGroupKey])
    }
  }, [activeGroupKey])

  const menuItems: MenuProps['items'] = useMemo(() => {
    return allMenuItems
      .filter((item) => !item.hidden)
      .map((item) => {
        if (item.children) {
          const filteredChildren = item.children
            .filter((child) => {
              if (child.hidden) return false
              if (!child.roles) return true
              return user?.role && child.roles.includes(user.role)
            })
            .map((child) => ({ key: child.key, icon: child.icon, label: child.label }))
          if (filteredChildren.length === 0) return null
          return { key: item.key, icon: item.icon, label: item.label, children: filteredChildren }
        }
        if (item.roles && !(user?.role && item.roles.includes(user.role))) return null
        return { key: item.key, icon: item.icon, label: item.label }
      })
      .filter(Boolean) as MenuProps['items']
  }, [user?.role])

  const breadcrumbItems = useMemo(() => {
    const items: { title: string }[] = [{ title: '首页' }]
    for (const item of allMenuItems) {
      if (!item.children && selectedKey === item.key && item.key !== '/dashboard') {
        items.push({ title: item.label })
        break
      }
      if (item.children) {
        const child = item.children.find((c) => selectedKey === c.key)
        if (child) {
          items.push({ title: item.label })
          items.push({ title: child.label })
          break
        }
      }
    }
    return items
  }, [selectedKey])

  const handleMenuClick: MenuProps['onClick'] = ({ key }) => {
    navigate({ to: key })
  }

  const handleLogout = () => {
    Modal.confirm({
      title: '确定要退出登录吗？',
      onOk: async () => {
        await logout()
        message.success('已退出登录')
        navigate({ to: '/login' })
      },
    })
  }

  const dropdownItems: MenuProps['items'] = [
    { key: 'profile', label: '个人设置' },
    { type: 'divider' },
    { key: 'logout', label: '退出登录', icon: <LogoutOutlined />, danger: true },
  ]

  const handleDropdown: MenuProps['onClick'] = ({ key }) => {
    if (key === 'logout') handleLogout()
    if (key === 'profile') message.info('个人设置功能开发中...')
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        width={220}
        style={{ background: '#001529' }}
      >
        <div style={{
          height: 60,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#fff',
          fontSize: collapsed ? 16 : 18,
          fontWeight: 700,
          borderBottom: '1px solid rgba(255,255,255,0.1)',
        }}>
          {collapsed ? 'LG' : 'LG Management'}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[selectedKey]}
          openKeys={openKeys}
          onOpenChange={setOpenKeys}
          items={menuItems}
          onClick={handleMenuClick}
          style={{ flex: 1, overflowY: 'auto' }}
        />
      </Sider>

      <Layout>
        <Header style={{
          background: themeToken.colorBgContainer,
          padding: '0 20px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
          height: 60,
          lineHeight: '60px',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setCollapsed(!collapsed)}
            />
            <Breadcrumb items={breadcrumbItems.map((b) => ({ title: b.title }))} />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <Tooltip title={isDark ? '切换亮色' : '切换暗色'}>
              <Button
                type="text"
                icon={isDark ? <SunOutlined /> : <MoonOutlined />}
                onClick={toggleTheme}
              />
            </Tooltip>
            <Dropdown menu={{ items: dropdownItems, onClick: handleDropdown }} placement="bottomRight">
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
                <Avatar size={32} style={{ background: themeToken.colorPrimary }}>
                  {user?.realName?.charAt(0) ?? user?.username?.charAt(0) ?? 'U'}
                </Avatar>
                <span>{user?.realName ?? user?.username}</span>
                <span style={{ fontSize: 12, color: themeToken.colorTextSecondary }}>
                  ({roleLabels[user?.role ?? ''] ?? user?.role})
                </span>
              </div>
            </Dropdown>
          </div>
        </Header>

        <Content style={{
          padding: 20,
          overflow: 'auto',
          background: themeToken.colorBgLayout,
        }}>
          {children}
        </Content>
      </Layout>

      <AIChatDrawer baseUrl="" />
    </Layout>
  )
}
