import { useState } from 'react'
import { Card, CardContent, CardHeader } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Calendar, CheckCircle, Edit3, AlertTriangle, Sparkles, Download } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { DailyReport } from '@/types'
import { formatDate } from '@/lib/utils'
import MarkdownView from '@/components/common/MarkdownView'
import { useApiDelete, useApiPost } from '@/hooks/useApi'
import { toast } from '@/components/ui/Toast'
import DeleteConfirm from '@/components/common/DeleteConfirm'

interface DailyReportCardProps {
  report: DailyReport
  onUpdate?: () => void
  onEdit?: (report: DailyReport) => void
}

/** 后端优先返回 today_work（Markdown）。若无，则用结构化 completed_items 兜底渲染。 */
function fallbackTodayWork(report: DailyReport): string {
  if (report.today_work) return report.today_work
  const items = report.completed_items || []
  if (!items.length) return '## 今日工作\n\n今日暂无任务更新记录。'
  const lines = ['## 今日工作', '']
  for (const it of items) {
    const name = it.task_name || it.task_title || '未命名任务'
    const remark = it.remark || it.content || '（无备注）'
    lines.push(`- **${name}**：${remark}`)
  }
  return lines.join('\n')
}

export default function DailyReportCard({ report, onUpdate, onEdit }: DailyReportCardProps) {
  const [showRawTomorrow, setShowRawTomorrow] = useState(false)

  const confirmMutation = useApiPost<void>(`/reports/daily-reports/${report.id}/confirm`)
  const deleteMutation = useApiDelete<void>(`/reports/daily-reports`)

  const handleConfirm = async () => {
    if (!confirm('确认提交日报？提交后内容将锁定为终版。')) return
    try {
      await confirmMutation.mutateAsync({ confirmed: true })
      toast.success({ title: '日报已确认提交' })
      onUpdate?.()
    } catch {
      toast.error({ title: '提交失败' })
    }
  }

  const todayWork = fallbackTodayWork(report)

  const handleDownload = () => {
    const parts = [`# 监修日报 — ${formatDate(report.report_date)}`, '']
    parts.push('## 今日工作', todayWork, '')
    if (report.tomorrow_plan) parts.push('## 明日计划', report.tomorrow_plan, '')
    if (report.risk_alert) parts.push('## 风险预警', report.risk_alert, '')
    const blob = new Blob([parts.join('\n')], { type: 'text/markdown;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `监修日报-${report.report_date}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <Card className={cn(report.confirmed && 'border-secondary/50')}>
      <CardHeader className="flex flex-row items-center justify-between pb-4">
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-primary/10 p-2">
            <Calendar className="h-4 w-4 text-primary" />
          </div>
          <div>
            <h3 className="font-semibold">{formatDate(report.report_date)}</h3>
            <p className="text-xs text-muted-foreground">日报</p>
          </div>
        </div>
        {report.confirmed ? (
          <Badge variant="secondary" className="gap-1">
            <CheckCircle className="h-3 w-3" />
            已确认
          </Badge>
        ) : (
          <Badge variant="warning">待确认</Badge>
        )}
      </CardHeader>

      <CardContent className="space-y-5">
        {/* 第一部分：今天干了什么 */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm font-semibold">
            <CheckCircle className="h-4 w-4 text-primary" />
            今天干了什么
          </div>
          <div className="rounded-md border border-border bg-muted/30 p-3">
            <MarkdownView content={todayWork} />
          </div>
        </div>

        {/* 第二部分：明天要干什么 */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <Sparkles className="h-4 w-4 text-accent" />
              明天要干什么
            </div>
            {report.tomorrow_plan && (
              <button
                className="text-xs text-muted-foreground hover:text-foreground"
                onClick={() => setShowRawTomorrow((v) => !v)}
              >
                {showRawTomorrow ? '预览' : '原文'}
              </button>
            )}
          </div>
          <div className="rounded-md border border-border bg-muted/30 p-3">
            {report.tomorrow_plan ? (
              showRawTomorrow ? (
                <pre className="whitespace-pre-wrap text-xs text-muted-foreground">
                  {report.tomorrow_plan}
                </pre>
              ) : (
                <MarkdownView content={report.tomorrow_plan} />
              )
            ) : (
              <p className="text-sm text-muted-foreground">暂无明日计划，点击「编辑」添加</p>
            )}
          </div>
        </div>

        {/* 风险提示 */}
        {report.risk_alert && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <AlertTriangle className="h-4 w-4 text-accent" />
              风险提示
            </div>
            <div className="rounded-md border border-border bg-muted/30 p-3">
              <MarkdownView content={report.risk_alert} />
            </div>
          </div>
        )}

        <div className="flex items-center justify-between pt-2 border-t border-border/50">
          <span className="text-xs text-muted-foreground">
            生成于 {formatDate(report.created_at)}
          </span>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={handleDownload}>
              <Download className="h-4 w-4" />
              下载
            </Button>
            <DeleteConfirm
              resourceName="日报"
              description="删除后该日报将无法恢复，且已确认提交的日报也会被删除。"
              mutation={deleteMutation}
              id={String(report.id)}
              onDeleted={() => onUpdate?.()}
            />
            {!report.confirmed && (
              <>
                {onEdit && (
                  <Button variant="outline" size="sm" onClick={() => onEdit(report)}>
                    <Edit3 className="h-4 w-4" />
                    编辑
                  </Button>
                )}
                <Button size="sm" onClick={handleConfirm}>
                  <CheckCircle className="h-4 w-4" />
                  确认提交
                </Button>
              </>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
