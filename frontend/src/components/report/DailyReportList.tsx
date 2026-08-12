import { useState } from 'react'
import { Filter, Plus, Loader2, Sparkles, Trash2, CheckCircle2 } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { DatePicker } from '@/components/ui/DatePicker'
import { Input } from '@/components/ui/Input'
import DailyReportCard from './DailyReportCard'
import { useApiPost } from '@/hooks/useApi'
import { toast } from '@/components/ui/Toast'
import type { DailyReport } from '@/types'
import { cn } from '@/lib/utils'

interface Proposal {
  report_date: string
  today_work: string
  tomorrow_candidates: string[]
  risk_alert: string
  existing_report_id: number | null
}

interface DailyReportListProps {
  projectId: string
  reports: DailyReport[]
  onReportsChange?: () => void
}

function parsePlanItems(plan?: string | null): string[] {
  if (!plan) return []
  return plan
    .split('\n')
    .map((l) => l.replace(/^[-*]\s*/, '').trim())
    .filter(Boolean)
}

export default function DailyReportList({
  projectId,
  reports,
  onReportsChange,
}: DailyReportListProps) {
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [showFilters, setShowFilters] = useState(false)

  const [composing, setComposing] = useState(false)
  const [proposal, setProposal] = useState<Proposal | null>(null)
  const [todayWork, setTodayWork] = useState('')
  const [riskAlert, setRiskAlert] = useState('')
  const [selected, setSelected] = useState<string[]>([])
  const [custom, setCustom] = useState<string[]>([])
  const [customInput, setCustomInput] = useState('')

  const proposeMutation = useApiPost<Proposal>(
    `/reports/projects/${projectId}/daily-reports/propose`
  )
  const finalizeMutation = useApiPost<DailyReport>(
    `/reports/projects/${projectId}/daily-reports/finalize`
  )

  const startCompose = async () => {
    try {
      const data = await proposeMutation.mutateAsync({})
      setProposal(data)
      setTodayWork(data.today_work || '')
      setRiskAlert(data.risk_alert || '')
      setSelected(data.tomorrow_candidates || [])
      setCustom([])
      setCustomInput('')
      setComposing(true)
    } catch {
      toast.error({ title: '生成失败', description: '请稍后重试' })
    }
  }

  const startEdit = (report: DailyReport) => {
    const items = report.tomorrow_candidates || parsePlanItems(report.tomorrow_plan)
    setProposal({
      report_date: report.report_date,
      today_work: report.today_work || '',
      tomorrow_candidates: items,
      risk_alert: report.risk_alert || '',
      existing_report_id: report.id,
    })
    setTodayWork(report.today_work || '')
    setRiskAlert(report.risk_alert || '')
    setSelected(items)
    setCustom([])
    setCustomInput('')
    setComposing(true)
  }

  const toggleSelect = (item: string) => {
    setSelected((prev) =>
      prev.includes(item) ? prev.filter((x) => x !== item) : [...prev, item]
    )
  }

  const addCustom = () => {
    const v = customInput.trim()
    if (!v) return
    setCustom((prev) => [...prev, v])
    setCustomInput('')
  }

  const removeCustom = (idx: number) => {
    setCustom((prev) => prev.filter((_, i) => i !== idx))
  }

  const finalItems = [...selected, ...custom]

  const handleFinalize = async (confirmed: boolean) => {
    if (!proposal) return
    try {
      await finalizeMutation.mutateAsync({
        report_date: proposal.report_date,
        today_work: todayWork,
        tomorrow_items: finalItems,
        risk_alert: riskAlert,
        confirmed,
      })
      toast.success({ title: confirmed ? '日报已确认提交' : '日报已保存草稿' })
      setComposing(false)
      setProposal(null)
      onReportsChange?.()
    } catch {
      toast.error({ title: '保存失败', description: '请稍后重试' })
    }
  }

  const cancelCompose = () => {
    setComposing(false)
    setProposal(null)
  }

  const sortedReports = [...(reports || [])].sort((a, b) =>
    a.report_date < b.report_date ? 1 : -1
  )
  const filtered = sortedReports.filter((r) => {
    if (startDate && r.report_date < startDate) return false
    if (endDate && r.report_date > endDate) return false
    return true
  })

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="inline-flex items-center gap-2 rounded-md border border-border px-3 py-2 text-sm hover:bg-accent transition-colors"
        >
          <Filter className="h-4 w-4" />
          筛选
          {(startDate || endDate) && (
            <span className="ml-1 rounded-full bg-primary px-2 py-0.5 text-xs text-primary-foreground">
              已筛选
            </span>
          )}
        </button>
        {!composing && (
          <Button onClick={startCompose} disabled={proposeMutation.isPending}>
            {proposeMutation.isPending ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                AI 生成中
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" />
                生成日报
              </>
            )}
          </Button>
        )}
      </div>

      {showFilters && (
        <div className="rounded-lg border border-border p-4 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <DatePicker
              label="开始日期"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
            />
            <DatePicker
              label="结束日期"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
            />
          </div>
          <div className="flex justify-end">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setStartDate('')
                setEndDate('')
              }}
            >
              重置筛选
            </Button>
          </div>
        </div>
      )}

      {composing && proposal && (
        <div className="rounded-xl border-2 border-primary/40 bg-primary/5 p-5 space-y-5">
          <div className="flex items-center gap-2 text-sm font-semibold text-primary">
            <Sparkles className="h-4 w-4" />
            AI 日报草稿 · {proposal.report_date}
            {proposal.existing_report_id && (
              <span className="text-xs text-muted-foreground font-normal">
                （编辑已有日报）
              </span>
            )}
          </div>

          {/* 今天干了什么 */}
          <div className="space-y-2">
            <label className="text-sm font-medium">今天干了什么（可编辑）</label>
            <textarea
              value={todayWork}
              onChange={(e) => setTodayWork(e.target.value)}
              rows={4}
              className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm resize-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />
          </div>

          {/* 明天要干什么：human-in-the-loop */}
          <div className="space-y-2">
            <label className="text-sm font-medium">明天要干什么（勾选确认 / 可自增）</label>
            {proposal.tomorrow_candidates.length === 0 && selected.length === 0 && (
              <p className="text-xs text-muted-foreground">AI 暂未提出候选计划，可在下方自行添加。</p>
            )}
            <div className="space-y-1">
              {selected.map((item) => (
                <label
                  key={item}
                  className="flex items-center gap-2 rounded-md border border-border bg-background px-3 py-2 text-sm cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked
                    onChange={() => toggleSelect(item)}
                    className="h-4 w-4"
                  />
                  <span>{item}</span>
                </label>
              ))}
              {custom.map((item, idx) => (
                <div
                  key={`c-${idx}`}
                  className="flex items-center gap-2 rounded-md border border-dashed border-primary/50 bg-background px-3 py-2 text-sm"
                >
                  <CheckCircle2 className="h-4 w-4 text-primary shrink-0" />
                  <span className="flex-1">{item}</span>
                  <button
                    onClick={() => removeCustom(idx)}
                    className="text-muted-foreground hover:text-destructive"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              ))}
            </div>
            <div className="flex gap-2">
              <Input
                placeholder="自行添加明日计划…"
                value={customInput}
                onChange={(e) => setCustomInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && addCustom()}
              />
              <Button variant="outline" size="sm" onClick={addCustom} disabled={!customInput.trim()}>
                <Plus className="h-4 w-4" />
                添加
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              共 {finalItems.length} 条将写入日报
            </p>
          </div>

          {/* 风险提示 */}
          <div className="space-y-2">
            <label className="text-sm font-medium">风险提示（可编辑）</label>
            <textarea
              value={riskAlert}
              onChange={(e) => setRiskAlert(e.target.value)}
              rows={3}
              className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm resize-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />
          </div>

          <div className="flex justify-end gap-2 pt-1">
            <Button variant="ghost" size="sm" onClick={cancelCompose}>
              取消
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleFinalize(false)}
              disabled={finalizeMutation.isPending}
            >
              保存草稿
            </Button>
            <Button
              size="sm"
              onClick={() => handleFinalize(true)}
              disabled={finalizeMutation.isPending || finalItems.length === 0}
            >
              {finalizeMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <CheckCircle2 className="h-4 w-4" />
              )}
              保存并确认
            </Button>
          </div>
        </div>
      )}

      {!composing && filtered.length === 0 ? (
        <div className="py-16 text-center text-muted-foreground">
          <p className="mb-2">暂无日报数据</p>
          <p className="text-sm">点击"生成日报"，由 AI 基于今日任务与修船知识库生成草稿</p>
        </div>
      ) : !composing ? (
        <div className="space-y-4">
          {filtered.map((report) => (
            <DailyReportCard
              key={report.id}
              report={report}
              onUpdate={onReportsChange}
              onEdit={startEdit}
            />
          ))}
        </div>
      ) : null}
    </div>
  )
}
