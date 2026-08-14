import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Calendar, Sparkles, ChevronRight, Download } from 'lucide-react'
import type { WeeklyReport } from '@/types'
import { formatDate } from '@/lib/utils'
import { useApiDelete } from '@/hooks/useApi'
import DeleteConfirm from '@/components/common/DeleteConfirm'

interface WeeklyReportCardProps {
  report: WeeklyReport
  onDeleted?: () => void
}

export default function WeeklyReportCard({ report, onDeleted }: WeeklyReportCardProps) {
  const deleteMutation = useApiDelete<void>(`/reports/weekly-reports`)
  const handleDownload = () => {
    const start = report.week_start ?? report.week_start_date
    const end = report.week_end ?? report.week_end_date
    const parts = [`# 监修周报 — ${formatDate(start)} ~ ${formatDate(end)}`, '']
    parts.push('## 本周总结', report.summary || '暂无本周总结', '')
    if (report.key_events && report.key_events.length > 0) {
      parts.push('## 关键事件')
      for (const ev of report.key_events) parts.push(`- ${ev}`)
      parts.push('')
    }
    parts.push('## 下周计划', report.next_week_plan || '暂无下周计划', '')
    const blob = new Blob([parts.join('\n')], { type: 'text/markdown;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `监修周报-${start}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <Calendar className="h-5 w-5 text-primary" />
          周报 ({formatDate(report.week_start ?? report.week_start_date)} ~ {formatDate(report.week_end ?? report.week_end_date)})
        </CardTitle>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={handleDownload}>
            <Download className="h-4 w-4" />
            下载
          </Button>
          <DeleteConfirm
            resourceName="周报"
            description="删除后该周报将无法恢复。"
            mutation={deleteMutation}
            id={String(report.id)}
            onDeleted={() => onDeleted?.()}
          />
          <Badge variant="secondary">
            进度 {report.progress_total}%
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm font-semibold">
            <Sparkles className="h-4 w-4 text-accent" />
            本周总结
          </div>
          <p className="text-sm leading-relaxed text-foreground/90 whitespace-pre-wrap">
            {report.summary || '暂无本周总结'}
          </p>
        </div>

        {(report.key_events ?? []).length > 0 && (
          <div className="space-y-2">
            <div className="text-sm font-semibold">关键事件</div>
            <ul className="space-y-1">
              {(report.key_events ?? []).map((event, index) => (
                <li
                  key={index}
                  className="flex items-start gap-2 text-sm"
                >
                  <ChevronRight className="h-4 w-4 mt-0.5 text-muted-foreground shrink-0" />
                  <span>{event}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm font-semibold">
            <Sparkles className="h-4 w-4 text-primary" />
            下周计划
          </div>
          <p className="text-sm leading-relaxed text-foreground/90 whitespace-pre-wrap">
            {report.next_week_plan || '暂无下周计划'}
          </p>
        </div>

        <div className="text-xs text-muted-foreground pt-2 border-t border-border/50">
          生成于 {formatDate(report.created_at)}
        </div>
      </CardContent>
    </Card>
  )
}