import { useState } from 'react'
import { AlertTriangle, ChevronDown, ChevronUp, ShieldCheck } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { RiskEvent } from '@/types'
import { RISK_LEVEL_LABELS } from '@/lib/constants'
import { formatDate } from '@/lib/utils'

interface RiskTickerProps {
  risks?: RiskEvent[]
  projectId?: string
}

export default function RiskTicker({ risks = [] }: RiskTickerProps) {
  const [expanded, setExpanded] = useState(false)

  const criticalCount = risks.filter((r) => r.level === 'critical' && !r.resolved).length
  const warningCount = risks.filter((r) => r.level === 'warning' && !r.resolved).length
  const infoCount = risks.filter((r) => r.level === 'info' && !r.resolved).length

  const hasRisks = criticalCount > 0 || warningCount > 0 || infoCount > 0

  if (!hasRisks) {
    return (
      <div className="flex items-center gap-2 rounded-lg border border-secondary/30 bg-secondary/10 px-4 py-2 text-secondary">
        <ShieldCheck className="h-4 w-4" />
        <span className="text-sm font-medium">暂无风险提醒</span>
      </div>
    )
  }

  return (
    <div
      className={cn(
        'rounded-lg border overflow-hidden transition-all',
        criticalCount > 0
          ? 'border-destructive/50 bg-destructive/10'
          : 'border-accent/50 bg-accent/10'
      )}
    >
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-between px-4 py-3"
      >
        <div className="flex items-center gap-2">
          <AlertTriangle
            className={cn(
              'h-4 w-4',
              criticalCount > 0 ? 'text-destructive' : 'text-accent'
            )}
          />
          <span className="text-sm font-medium">
            {criticalCount > 0 && (
              <span className="text-destructive">
                严重 {criticalCount} 项
                {warningCount > 0 && ' · '}
              </span>
            )}
            {warningCount > 0 && (
              <span className="text-accent">
                警告 {warningCount} 项
                {infoCount > 0 && ' · '}
              </span>
            )}
            {infoCount > 0 && (
              <span className="text-muted-foreground">提示 {infoCount} 项</span>
            )}
          </span>
        </div>
        {expanded ? (
          <ChevronUp className="h-4 w-4 text-muted-foreground" />
        ) : (
          <ChevronDown className="h-4 w-4 text-muted-foreground" />
        )}
      </button>

      {expanded && (
        <div className="border-t border-border px-4 py-3 space-y-2">
          {risks
            .filter((r) => !r.resolved)
            .map((risk) => (
              <div
                key={risk.id}
                className={cn(
                  'flex items-start gap-3 rounded-md p-3 text-sm',
                  risk.level === 'critical'
                    ? 'bg-destructive/10 text-destructive'
                    : risk.level === 'warning'
                      ? 'bg-accent/10 text-accent'
                      : 'bg-surface-muted text-muted-foreground'
                )}
              >
                <span
                  className={cn(
                    'mt-0.5 inline-flex h-5 items-center rounded px-1.5 text-xs font-medium',
                    risk.level === 'critical'
                      ? 'bg-destructive text-destructive-foreground'
                      : risk.level === 'warning'
                        ? 'bg-accent text-accent-foreground'
                        : 'bg-surface text-foreground'
                  )}
                >
                  {RISK_LEVEL_LABELS[risk.level]}
                </span>
                <div className="flex-1">
                  <p className="font-medium">{risk.title}</p>
                  <p className="mt-1 text-sm opacity-80">{risk.message}</p>
                  <p className="mt-1 text-xs opacity-60">
                    {formatDate(risk.created_at)}
                  </p>
                </div>
              </div>
            ))}
        </div>
      )}
    </div>
  )
}