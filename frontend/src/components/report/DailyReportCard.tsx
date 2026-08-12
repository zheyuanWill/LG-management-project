import { useState } from 'react'
import { Card, CardContent, CardHeader } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Calendar, CheckCircle, Edit3, AlertTriangle, Sparkles } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { DailyReport, DailyReportItem } from '@/types'
import { formatDate } from '@/lib/utils'
import ReportEditor from './ReportEditor'
import { useApiPost } from '@/hooks/useApi'
import { toast } from '@/components/ui/Toast'

interface DailyReportCardProps {
  report: DailyReport
  onUpdate?: () => void
}

export default function DailyReportCard({ report, onUpdate }: DailyReportCardProps) {
  const [showEditor, setShowEditor] = useState(false)

  const confirmMutation = useApiPost<void>(`/daily-reports/${report.id}/confirm`)

  const handleSave = (_values: Record<string, string>) => {
    toast.success({ title: '保存成功' })
    onUpdate?.()
  }

  const handleConfirm = async () => {
    if (!confirm('确认提交日报？提交后将无法修改。')) return
    try {
      await confirmMutation.mutateAsync({ confirmed: true })
      toast.success({ title: '日报已确认提交' })
      onUpdate?.()
    } catch {
      toast.error({ title: '提交失败' })
    }
  }

  const completedItems = report.completed_items || []

  return (
    <Card className={cn(report.confirmed && 'border-secondary/50')}>
      <CardHeader className="flex flex-row items-center justify-between pb-4">
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-primary/10 p-2">
            <Calendar className="h-4 w-4 text-primary" />
          </div>
          <div>
            <h3 className="font-semibold">{formatDate(report.report_date)}</h3>
            <p className="text-xs text-muted-foreground">
              完成 {completedItems.length} 项任务
            </p>
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
        {completedItems.length > 0 && (
          <div className="space-y-3">
            <div className="text-sm font-semibold">已完成事项</div>
            <div className="space-y-2">
              {completedItems.map((item: DailyReportItem, index: number) => (
                <div
                  key={index}
                  className="rounded-md border border-border p-3 space-y-2"
                >
                  <div className="font-medium text-sm">{item.task_title}</div>
                  {item.content && (
                    <p className="text-sm text-muted-foreground">{item.content}</p>
                  )}
                  {item.photos && item.photos.length > 0 && (
                    <div className="flex gap-2">
                      {item.photos.slice(0, 2).map((photo) => (
                        <img
                          key={photo.id}
                          src={photo.thumbnail_url || photo.url}
                          alt={photo.caption || '现场照片'}
                          className="w-20 h-20 object-cover rounded-md border border-border"
                        />
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {!showEditor ? (
          <>
            {report.tomorrow_plan && (
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm font-semibold">
                  <Sparkles className="h-4 w-4 text-accent" />
                  明日计划
                </div>
                <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                  {report.tomorrow_plan}
                </p>
              </div>
            )}

            {report.risk_alert && (
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm font-semibold">
                  <AlertTriangle className="h-4 w-4 text-accent" />
                  风险提醒
                </div>
                <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                  {report.risk_alert}
                </p>
              </div>
            )}

            <div className="flex items-center justify-between pt-4 border-t border-border/50">
              <span className="text-xs text-muted-foreground">
                生成于 {formatDate(report.created_at)}
              </span>
              <div className="flex gap-2">
                {!report.confirmed && (
                  <>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setShowEditor(true)}
                    >
                      <Edit3 className="h-4 w-4" />
                      编辑
                    </Button>
                    <Button size="sm" onClick={handleConfirm}>
                      <CheckCircle className="h-4 w-4" />
                      确认提交
                    </Button>
                  </>
                )}
              </div>
            </div>
          </>
        ) : (
          <ReportEditor
            title="编辑日报"
            fields={[
              {
                name: 'tomorrow_plan',
                label: '明日计划',
                value: report.tomorrow_plan || '',
                placeholder: '输入明日计划...',
              },
              {
                name: 'risk_alert',
                label: '风险提醒',
                value: report.risk_alert || '',
                placeholder: '输入风险提醒...',
              },
            ]}
            onSave={(values) => {
              handleSave(values)
              setShowEditor(false)
            }}
          />
        )}
      </CardContent>
    </Card>
  )
}