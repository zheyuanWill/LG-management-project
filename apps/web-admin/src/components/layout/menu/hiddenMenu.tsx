import {
  CopyOutlined,
  FlagOutlined,
  CheckCircleOutlined,
  BarChartOutlined,
  BellOutlined,
  UserOutlined,
  ShareAltOutlined,
  ApiOutlined,
  RobotOutlined,
  SettingOutlined,
  AccountBookOutlined,
  SafetyCertificateOutlined,
  CustomerServiceOutlined,
  BookOutlined,
  InboxOutlined,
} from '@ant-design/icons'

import type { MenuItemDef } from './types'

export const hiddenMenuItems: MenuItemDef[] = [
  {
    key: 'grp-project-hidden',
    icon: <SettingOutlined />,
    label: '暂存项目模块',
    children: [
      { key: '/contracts', icon: <CopyOutlined />, label: '合同管理' },
      { key: '/tracking', icon: <FlagOutlined />, label: '跟单进度（旧）' },
    ],
  },
  {
    key: 'grp-quality-hidden',
    icon: <SafetyCertificateOutlined />,
    label: '暂存质量与售后',
    children: [
      { key: '/quality', icon: <SafetyCertificateOutlined />, label: '质量管理' },
      { key: '/after-sales', icon: <CustomerServiceOutlined />, label: '售后服务' },
    ],
  },
  {
    key: 'grp-finance-hidden',
    icon: <AccountBookOutlined />,
    label: '暂存财务',
    children: [
      { key: '/cost', icon: <BarChartOutlined />, label: '成本核算' },
      { key: '/settlement', icon: <CheckCircleOutlined />, label: '结项管理' },
    ],
  },
  {
    key: 'grp-system-hidden',
    icon: <SettingOutlined />,
    label: '暂存系统模块',
    children: [
      { key: '/messages', icon: <BellOutlined />, label: '消息中心' },
      { key: '/inventory', icon: <InboxOutlined />, label: '库存管理' },
      { key: '/users', icon: <UserOutlined />, label: '用户管理', roles: ['OWNER'] },
      { key: '/workflow', icon: <ShareAltOutlined />, label: '工作流编排', roles: ['OWNER', 'PM'] },
      { key: '/integration', icon: <ApiOutlined />, label: '集成管理', roles: ['OWNER'] },
      { key: '/ai-assistant', icon: <RobotOutlined />, label: 'AI 助手' },
      { key: '/knowledge', icon: <BookOutlined />, label: '知识库' },
    ],
  },
]
