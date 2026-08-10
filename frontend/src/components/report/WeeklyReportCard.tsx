import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Calendar, Sparkles, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { WeeklyReport } from '@/types'
import { formatDate } from '@/lib/utils'

interface WeeklyReportCardProps {
  report: WeeklyReport
}

export default function WeeklyReportCard({ report }: WeeklyReportCardProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <Calendar className="h-5 w-5 text-primary" />
          周报 ({formatDate(report.week_start)} ~ {formatDate(report.week_end)})
        </CardTitle>
        <Badge variant="secondary">
          进度 {report.progress_total}%
        </Badge>
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

        {report.key_events.length > 0 && (
          <div className="space-y-2">
            <div className="text-sm font-semibold">关键事件</div>
            <ul className="space-y-1">
              {report.key_events.map((event, index) => (
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