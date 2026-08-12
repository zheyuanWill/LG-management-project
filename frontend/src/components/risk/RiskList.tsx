import { useState, Fragment } from 'react'
import { ChevronDown, ChevronUp, Sparkles, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { RiskEvent } from '@/types'
import { RISK_LEVEL_LABELS } from '@/lib/constants'
import { formatDate } from '@/lib/utils'
import RiskDetail from './RiskDetail'
import { useApiPost } from '@/hooks/useApi'
import { toast } from '@/components/ui/Toast'

interface RiskListProps {
  risks: RiskEvent[]
  projectId: string
}

export default function RiskList({ risks, projectId }: RiskListProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [analyzingAll, setAnalyzingAll] = useState(false)

  const batchAnalyze = useApiPost<{ task_id: string; project_id: number; status: string }>(
    `/risks/projects/${projectId}/risks/ai-detect`
  )

  const handleBatchAnalyze = async () => {
    setAnalyzingAll(true)
    try {
      await batchAnalyze.mutateAsync({})
      toast.success({
        title: '已提交风险检测',
        description: '规则引擎正在分析项目数据,请稍后刷新查看结果',
      })
    } catch {
      toast.error({ title: '提交失败', description: '请稍后重试' })
    } finally {
      setAnalyzingAll(false)
    }
  }

  const handleResolved = () => {
    setExpandedId(null)
  }

  if (risks.length === 0) {
    return (
      <div className="py-12 text-center text-muted-foreground">
        <p>暂无风险记录</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">风险事件 ({risks.length})</h3>
        <button
          onClick={handleBatchAnalyze}
          disabled={analyzingAll || batchAnalyze.isPending}
          className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50"
        >
          {analyzingAll || batchAnalyze.isPending ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              分析中
            </>
          ) : (
            <>
              <Sparkles className="h-4 w-4" />
              自动检测风险
            </>
          )}
        </button>
      </div>

      <div className="rounded-lg border border-border overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-muted/50">
              <th className="h-10 px-4 text-left font-medium text-muted-foreground w-1/3">
                摘要
              </th>
              <th className="h-10 px-4 text-left font-medium text-muted-foreground w-24">
                等级
              </th>
              <th className="h-10 px-4 text-left font-medium text-muted-foreground w-40">
                创建时间
              </th>
              <th className="h-10 px-4 text-left font-medium text-muted-foreground w-24">
                状态
              </th>
              <th className="h-10 px-4 w-10" />
            </tr>
          </thead>
          <tbody>
            {risks.map((risk) => (
              <Fragment key={risk.id}>
                <tr
                  key={risk.id}
                  onClick={() =>
                    setExpandedId(expandedId === risk.id ? null : risk.id)
                  }
                  className={cn(
                    'border-b border-border cursor-pointer transition-colors hover:bg-muted/30',
                    expandedId === risk.id && 'bg-muted/50'
                  )}
                >
                  <td className="p-4">
                    <div className="font-medium">{risk.title}</div>
                    <div className="text-xs text-muted-foreground mt-0.5">
                      {risk.detail}
                    </div>
                  </td>
                  <td className="p-4">
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
                  </td>
                  <td className="p-4 text-muted-foreground">
                    {formatDate(risk.created_at)}
                  </td>
                  <td className="p-4">
                    {risk.resolved ? (
                      <span className="inline-flex items-center rounded px-2 py-0.5 text-xs bg-secondary text-secondary-foreground">
                        已处理
                      </span>
                    ) : (
                      <span className="inline-flex items-center rounded px-2 py-0.5 text-xs bg-accent/20 text-accent">
                        待处理
                      </span>
                    )}
                  </td>
                  <td className="p-4">
                    {expandedId === risk.id ? (
                      <ChevronUp className="h-4 w-4 text-muted-foreground" />
                    ) : (
                      <ChevronDown className="h-4 w-4 text-muted-foreground" />
                    )}
                  </td>
                </tr>
                {expandedId === risk.id && (
                  <tr className="border-b border-border">
                    <td colSpan={5} className="p-0">
                      <RiskDetail risk={risk} onResolved={handleResolved} />
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}