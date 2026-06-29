import {
  DashboardOutlined,
  FileTextOutlined,
  DollarOutlined,
  ShoppingCartOutlined,
  ShopOutlined,
  AppstoreOutlined,
  TeamOutlined,
  ProjectOutlined,
  LinkOutlined,
  ToolOutlined,
  CarOutlined,
  CalendarOutlined,
} from '@ant-design/icons'

import type { MenuItemDef } from './types'

export const activeMenuItems: MenuItemDef[] = [
  { key: '/dashboard', icon: <DashboardOutlined />, label: '工作台' },
  {
    key: 'grp-project', icon: <ProjectOutlined />, label: '项目管理',
    children: [
      { key: '/orders', icon: <FileTextOutlined />, label: '订单管理' },
      { key: '/quotes', icon: <DollarOutlined />, label: '报价管理' },
      { key: '/quotes/excel', icon: <FileTextOutlined />, label: '报价Excel' },
    ],
  },
  {
    key: 'grp-shiprepair', icon: <CarOutlined />, label: '修船监修',
    children: [
      { key: '/ship-repair/dashboard', icon: <DashboardOutlined />, label: '首页 Dashboard' },
      { key: '/ship-repair/projects', icon: <FileTextOutlined />, label: '项目 Projects' },
      { key: '/ship-repair/tasks', icon: <ToolOutlined />, label: '任务 Tasks' },
      { key: '/ship-repair/daily-logs', icon: <CalendarOutlined />, label: '监修记录 Daily Logs' },
    ],
  },
  {
    key: 'grp-supply', icon: <LinkOutlined />, label: '供应链',
    children: [
      { key: '/procurement', icon: <ShoppingCartOutlined />, label: '采购管理' },
      { key: '/suppliers', icon: <ShopOutlined />, label: '供应商' },
      { key: '/products', icon: <AppstoreOutlined />, label: '商品管理' },
    ],
  },
  {
    key: 'grp-data', icon: <TeamOutlined />, label: '基础数据',
    children: [
      { key: '/customers', icon: <TeamOutlined />, label: '客户/船舶' },
    ],
  },
]
