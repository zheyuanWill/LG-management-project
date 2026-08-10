import { ReactNode, useState } from 'react'
import { cn } from '@/lib/utils'

interface TabsProps {
  tabs: {
    value: string
    label: string
    content: ReactNode
    icon?: ReactNode
  }[]
  defaultValue?: string
  className?: string
  onChange?: (value: string) => void
}

export function Tabs({
  tabs,
  defaultValue,
  className,
  onChange,
}: TabsProps) {
  const [active, setActive] = useState(defaultValue || tabs[0]?.value)

  const handleChange = (value: string) => {
    setActive(value)
    onChange?.(value)
  }

  return (
    <div className={cn('w-full', className)}>
      <div className="inline-flex h-10 items-center justify-start rounded-lg bg-muted p-1 text-muted-foreground">
        {tabs.map((tab) => (
          <button
            key={tab.value}
            onClick={() => handleChange(tab.value)}
            className={cn(
              'inline-flex items-center gap-2 whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-medium transition-all',
              active === tab.value
                ? 'bg-background text-foreground shadow-sm'
                : 'hover:text-foreground'
            )}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>
      <div className="mt-4">
        {tabs.find((t) => t.value === active)?.content}
      </div>
    </div>
  )
}

interface TabsListProps {
  children: ReactNode
  className?: string
}

export function TabsList({ children, className }: TabsListProps) {
  return (
    <div
      className={cn(
        'inline-flex h-10 items-center justify-start rounded-lg bg-muted p-1 text-muted-foreground',
        className
      )}
    >
      {children}
    </div>
  )
}

interface TabsTriggerProps {
  value: string
  active: boolean
  onClick: () => void
  children: ReactNode
  className?: string
}

export function TabsTrigger({
  active,
  onClick,
  children,
  className,
}: TabsTriggerProps) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'inline-flex items-center whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-medium transition-all',
        active
          ? 'bg-background text-foreground shadow-sm'
          : 'hover:text-foreground',
        className
      )}
    >
      {children}
    </button>
  )
}

interface TabsContentProps {
  value: string
  active: boolean
  children: ReactNode
  className?: string
}

export function TabsContent({ active, children, className }: TabsContentProps) {
  if (!active) return null
  return <div className={cn('mt-4', className)}>{children}</div>
}