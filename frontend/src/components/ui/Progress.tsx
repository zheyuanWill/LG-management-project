import { cn } from '@/lib/utils'

interface ProgressProps {
  value: number
  max?: number
  className?: string
  indicatorClassName?: string
  variant?: 'default' | 'success' | 'warning' | 'destructive'
}

export function Progress({
  value,
  max = 100,
  className,
  indicatorClassName,
  variant = 'default',
}: ProgressProps) {
  const percentage = Math.min((value / max) * 100, 100)

  const variantStyles = {
    default: 'bg-primary',
    success: 'bg-secondary',
    warning: 'bg-accent',
    destructive: 'bg-destructive',
  }

  return (
    <div
      className={cn(
        'relative h-2 w-full overflow-hidden rounded-full bg-muted',
        className
      )}
    >
      <div
        className={cn(
          'h-full w-full flex-1 transition-all',
          variantStyles[variant],
          indicatorClassName
        )}
        style={{ transform: `translateX(-${100 - percentage}%)` }}
      />
    </div>
  )
}