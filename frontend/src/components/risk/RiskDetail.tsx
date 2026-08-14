import { Check } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { RiskEvent } from '@/types'
import { RISK_LEVEL_LABELS } from '@/lib/constants'
import { formatDate } from '@/lib/utils'
import { useApiDelete, useApiPatch } from '@/hooks/useApi'
import { toast } from '@/components/ui/Toast'
import DeleteConfirm from '@/components/common/DeleteConfirm'

interface RiskDetailProps {
  risk: RiskEvent
  onResolved?: (riskId: string) => void
  onDeleted?: () => void
}

export default function RiskDetail({ risk, onResolved, onDeleted }: RiskDetailProps) {
  const resolveMutation = useApiPatch<void>(`/risks/${risk.id}`)
  const deleteMutation = useApiDelete<void>(`/risks`)

  const handleResolve = async () => {
    try {
      // Backend RiskResolveRequest now honours `resolved`; previously this body
      // was silently ignored, so "标记已处理" did nothing.
      await resolveMutation.mutateAsync({ resolved: true })
      toast.success({ title: '风险已处理' })
      onResolved?.(risk.id)
    } catch {
      toast.error({ title: '操作失败', description: '请稍后重试' })
    }
  }

  return (
    <div className="space-y-4 p-4 bg-surface-muted rounded-lg">
      <div className="flex items-start justify-between">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span
              className={cn(
                'inline-flex h-5 items-center rounded px-2 text-xs font-medium',
                risk.risk_level === 'critical'
                  ? 'bg-destructive text-destructive-foreground'
                  : risk.risk_level === 'warning'
                    ? 'bg-accent text-accent-foreground'
                    : 'bg-surface text-foreground'
              )}
            >
              {RISK_LEVEL_LABELS[risk.risk_level]}
            </span>
            <span className="font-semibold text-base">{risk.title}</span>
            {risk.resolved && (
              <span className="inline-flex items-center gap-1 rounded px-2 py-0.5 text-xs bg-secondary text-secondary-foreground">
                <Check className="h-3 w-3" />
                已处理
              </span>
            )}
          </div>
          <p className="text-sm text-muted-foreground whitespace-pre-wrap">
            {risk.detail || '暂无详细分析内容。'}
          </p>
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            <span>创建于 {formatDate(risk.created_at)}</span>
            {risk.resolved_at && <span>处理于 {formatDate(risk.resolved_at)}</span>}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <DeleteConfirm
            resourceName="风险事件"
            description="删除后该风险记录将无法恢复。"
            mutation={deleteMutation}
            id={String(risk.id)}
            onDeleted={() => onDeleted?.()}
          />
          {!risk.resolved && (
            <button
              onClick={handleResolve}
              disabled={resolveMutation.isPending}
              className="inline-flex items-center gap-1 rounded-md bg-secondary px-3 py-1.5 text-sm font-medium text-secondary-foreground hover:bg-secondary/90 transition-colors disabled:opacity-50"
            >
              <Check className="h-4 w-4" />
              标记已处理
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
