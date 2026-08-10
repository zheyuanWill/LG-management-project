import { useState } from 'react'
import { AlertTriangle, ChevronDown, ChevronUp, ShieldCheck, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { RiskEvent } from '@/types'
import { RISK_LEVEL_LABELS } from '@/lib/constants'
import { formatDate } from '@/lib/utils'
import { useApiPost } from '@/hooks/useApi'
import { toast } from '@/components/ui/Toast'

interface RiskBannerProps {
  risks: RiskEvent[]
  projectId: string
}

export default function RiskBanner({ risks, projectId }: RiskBannerProps) {
  const [expanded, setExpanded] = useState(false)
  const [analyzingId, setAnalyzingId] = useState<string | null>(null)

  const aiAnalysis = useApiPost<{ result: string }>(`/projects/${projectId}/risks/analyze`)

  const unresolvedRisks = risks.filter((r) => !r.resolved)
  const criticalCount = unresolvedRisks.filter((r) => r.level === 'critical').length
  const warningCount = unresolvedRisks.filter((r) => r.level === 'warning').length

  const hasRisks = unresolvedRisks.length > 0

  const handleAnalyze = async (riskId: string) => {
    setAnalyzingId(riskId)
    try {
      const result = await aiAnalysis.mutateAsync({ risk_id: riskId })
      toast.success({ title: 'AI 分析完成', description: result.result })
    } catch {
      toast.error({ title: '分析失败', description: '请稍后重试' })
    } finally {
      setAnalyzingId(null)
    }
  }

  if (!hasRisks) {
    return (
      <div className="flex items-center gap-2 rounded-lg border border-secondary/30 bg-secondary/10 px-4 py-3 text-secondary">
        <ShieldCheck className="h-5 w-5" />
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
        className="flex w-full items-center justify-between px-4 py-3 hover:opacity-80 transition-opacity"
      >
        <div className="flex items-center gap-3">
          <AlertTriangle
            className={cn(
              'h-5 w-5',
              criticalCount > 0 ? 'text-destructive' : 'text-accent'
            )}
          />
          <span className="text-sm font-medium">
            {criticalCount > 0 && (
              <span className="text-destructive font-semibold">
                严重 {criticalCount} 项
                {warningCount > 0 && ' · '}
              </span>
            )}
            {warningCount > 0 && (
              <span className="text-accent font-semibold">
                警告 {warningCount} 项
              </span>
            )}
            {criticalCount === 0 && warningCount === 0 && (
              <span className="text-muted-foreground">提示 {unresolvedRisks.length} 项</span>
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
        <div className="border-t border-border/50 px-4 py-3 space-y-3">
          {unresolvedRisks.map((risk) => (
            <div
              key={risk.id}
              className={cn(
                'rounded-md p-3 text-sm',
                risk.level === 'critical'
                  ? 'bg-destructive/10'
                  : risk.level === 'warning'
                    ? 'bg-accent/10'
                    : 'bg-surface-muted'
              )}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 space-y-1">
                  <div className="flex items-center gap-2">
                    <span
                      className={cn(
                        'inline-flex h-5 items-center rounded px-1.5 text-xs font-medium',
                        risk.level === 'critical'
                          ? 'bg-destructive text-destructive-foreground'
                          : risk.level === 'warning'
                            ? 'bg-accent text-accent-foreground'
                            : 'bg-surface text-foreground'
                      )}
                    >
                      {RISK_LEVEL_LABELS[risk.level]}
                    </span>
                    <span className="font-medium">{risk.title}</span>
                  </div>
                  <p className="text-sm opacity-80">{risk.message}</p>
                  <p className="text-xs opacity-60">{formatDate(risk.created_at)}</p>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    handleAnalyze(risk.id)
                  }}
                  disabled={analyzingId === risk.id}
                  className="shrink-0 rounded-md border border-border px-2 py-1 text-xs hover:bg-accent hover:text-accent-foreground transition-colors disabled:opacity-50"
                >
                  {analyzingId === risk.id ? (
                    <span className="flex items-center gap-1">
                      <Loader2 className="h-3 w-3 animate-spin" />
                      分析中
                    </span>
                  ) : (
                    'AI 分析'
                  )}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}