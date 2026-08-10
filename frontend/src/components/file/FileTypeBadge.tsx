import { cn } from '@/lib/utils'

export type FileType =
  | 'contract'
  | 'receipt'
  | 'wechat_screenshot'
  | 'survey'
  | 'certificate'
  | 'other'

interface FileTypeBadgeProps {
  type: FileType | string
  className?: string
}

const typeConfig: Record<string, { label: string; className: string }> = {
  contract: {
    label: '合同',
    className: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 border-blue-200 dark:border-blue-800',
  },
  receipt: {
    label: '签收单',
    className: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 border-green-200 dark:border-green-800',
  },
  wechat_screenshot: {
    label: '微信截图',
    className: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800',
  },
  survey: {
    label: '调研报告',
    className: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400 border-amber-200 dark:border-amber-800',
  },
  certificate: {
    label: '证书',
    className: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400 border-purple-200 dark:border-purple-800',
  },
  other: {
    label: '其他',
    className: 'bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-400 border-gray-200 dark:border-gray-800',
  },
}

export default function FileTypeBadge({ type, className }: FileTypeBadgeProps) {
  const config = typeConfig[type] || typeConfig.other

  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold',
        config.className,
        className
      )}
    >
      {config.label}
    </span>
  )
}