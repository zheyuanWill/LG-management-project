import { useState } from 'react'
import { Check, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { RiskEvent } from '@/types'
import { RISK_LEVEL_LABELS } from '@/lib/constants'
import { formatDate } from '@/lib/utils'
import { useApiPatch } from '@/hooks/useApi'
import { toast } from '@/components/ui/Toast'

interface RiskDetailProps {
  risk: RiskEvent
  onResolved?: (riskId: string) => void
}

export default function RiskDetail({ risk, onResolved }: RiskDetailProps) {
  const [aiAnalysis, setAiAnalysis] = useState<string | null>(null)
  const [analyzing, setAnalyzing] = useState(false)

  const resolveMutation = useApiPatch<void>(`/risks/${risk.id}`)

  const handleResolve = async () => {
    try {
      await resolveMutation.mutateAsync({ resolved: true })
      toast.success({ title: '风险已处理' })
      onResolved?.(risk.id)
    } catch {
      toast.error({ title: '操作失败', description: '请稍后重试' })
    }
  }

  const handleAnalyze = async () => {
    setAnalyzing(true)
    try {
      const response = await fetch(`/api/v1/risks/${risk.id}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })
      if (response.ok) {
        const data = await response.json()
        setAiAnalysis(data.data?.result ?? 'AI 分析完成，但未返回详细内容。')
      } else {
        setAiAnalysis('AI 分析服务暂时不可用。')
      }
    } catch {
      setAiAnalysis('网络错误，无法获取 AI 分析结果。')
    } finally {
      setAnalyzing(false)
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
                risk.level === 'critical'
                  ? 'bg-destructive text-destructive-foreground'
                  : risk.level === 'warning'
                    ? 'bg-accent text-accent-foreground'
                    : 'bg-surface text-foreground'
              )}
            >
              {RISK_LEVEL_LABELS[risk.level]}
            </span>
            <span className="font-semibold text-base">{risk.title}</span>
            {risk.resolved && (
              <span className="inline-flex items-center gap-1 rounded px-2 py-0.5 text-xs bg-secondary text-secondary-foreground">
                <Check className="h-3 w-3" />
                已处理
              </span>
            )}
          </div>
          <p className="text-sm text-muted-foreground">{risk.message}</p>
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            <span>创建于 {formatDate(risk.created_at)}</span>
            {risk.resolved_at && <span>处理于 {formatDate(risk.resolved_at)}</span>}
            <span>分类: {risk.category}</span>
          </div>
        </div>
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

      <div className="border-t border-border pt-4">
        {!aiAnalysis && !analyzing ? (
          <button
            onClick={handleAnalyze}
            className="inline-flex items-center gap-2 rounded-md border border-border px-3 py-2 text-sm hover:bg-accent hover:text-accent-foreground transition-colors"
          >
            运行 AI 分析
          </button>
        ) : analyzing ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            正在进行 AI 智能分析...
          </div>
        ) : (
          <div className="space-y-2">
            <h4 className="text-sm font-semibold">AI 分析详情</h4>
            <p className="text-sm leading-relaxed whitespace-pre-wrap">{aiAnalysis}</p>
          </div>
        )}
      </div>
    </div>
  )
}