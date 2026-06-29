import { Tag } from 'antd'

type PresetColor = 'default' | 'success' | 'processing' | 'error' | 'warning'

interface StatusBadgeProps {
  label: string
  color?: PresetColor
  colorMap?: Record<string, PresetColor>
  status?: string
}

export function StatusBadge({ label, color, colorMap, status }: StatusBadgeProps) {
  const resolved = color ?? (status && colorMap ? colorMap[status] : undefined) ?? 'default'
  return <Tag color={resolved}>{label}</Tag>
}
