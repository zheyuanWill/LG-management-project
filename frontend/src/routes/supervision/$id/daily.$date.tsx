import { useState, useMemo } from 'react'
import { useParams, useNavigate } from '@tanstack/react-router'
import { ArrowLeft, Calendar, Loader2, Sparkles, AlertTriangle, CheckCircle } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { useApiGet, useApiPost, useApiPatch } from '@/hooks/useApi'
import { toast } from '@/components/ui/Toast'
import { formatDate } from '@/lib/utils'
import type { DailyReport } from '@/types'

export default function DailyReportPage() {
  const { id, date } = useParams({ strict: false }) as { id: string; date: string }
  const navigate = useNavigate()

  const [tomorrowPlan, setTomorrowPlan] = useState('')
  const [riskReminders, setRiskReminders] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const { data: project, isLoading: projectLoading } = useApiGet<any>(`/projects/${id}`)
  const { data: dailyReport } = useApiGet<DailyReport>(
    `/reports/daily-reports/${date}`
  )
  const { data: tasks } = useApiGet<any[]>(`/tasks/projects/${id}/tasks`)

  const generateMutation = useApiPost<DailyReport>(
    `/reports/projects/${id}/daily-reports/generate`
  )
  const saveMutation = useApiPatch<void>(`/reports/daily-reports/${date}`)
  const confirmMutation = useApiPost<void>(`/reports/daily-reports/${date}/confirm`)

  const completedTasks = useMemo(() => {
    if (!tasks) return []
    return tasks.filter((t: any) => t.status === 'completed')
  }, [tasks])

  const handleGenerate = async () => {
    try {
      const result = await generateMutation.mutateAsync({ date })
      if (result.tomorrow_plan) setTomorrowPlan(result.tomorrow_plan)
      if (result.risk_alert) setRiskReminders(result.risk_alert)
      toast.success({ title: 'AI 日报生成成功' })
    } catch {
      toast.error({ title: '生成失败', description: '请稍后重试' })
    }
  }

  const handleSubmit = async () => {
    setSubmitting(true)
    try {
      if (!dailyReport?.confirmed) {
        await saveMutation.mutateAsync({
          tomorrow_plan: tomorrowPlan,
          risk_alert: riskReminders,
        })
      }
      await confirmMutation.mutateAsync({ confirmed: true })
      toast.success({ title: '日报已确认提交' })
      navigate({ to: '/supervision/$id', params: { id } })
    } catch {
      toast.error({ title: '提交失败' })
    } finally {
      setSubmitting(false)
    }
  }

  if (projectLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate({ to: '/supervision/$id', params: { id } })}
          >
            <ArrowLeft className="h-4 w-4" />
            返回
          </Button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold">
                {(project?.ship_name) || '监修项目'}
              </h1>
              <Badge variant="secondary">日报</Badge>
            </div>
            <div className="flex items-center gap-2 mt-1 text-sm text-muted-foreground">
              <Calendar className="h-4 w-4" />
              <span>{formatDate(dailyReport?.report_date || date)}</span>
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={handleGenerate}
            disabled={generateMutation.isPending}
          >
            <Sparkles className="h-4 w-4" />
            {generateMutation.isPending ? '生成中...' : 'AI 生成日报'}
          </Button>
          <Button onClick={handleSubmit} disabled={submitting}>
            <CheckCircle className="h-4 w-4" />
            {submitting ? '提交中...' : '确认提交'}
          </Button>
        </div>
      </div>

      {dailyReport?.confirmed && (
        <div className="flex items-center gap-2 rounded-lg border border-secondary/30 bg-secondary/10 px-4 py-3 text-secondary">
          <CheckCircle className="h-5 w-5" />
          <span className="text-sm font-medium">日报已确认提交</span>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardContent className="p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">已完成事项</h2>
              <span className="text-sm text-muted-foreground">
                {completedTasks.length} 项已完成
              </span>
            </div>

            {completedTasks.length === 0 ? (
              <div className="py-8 text-center text-muted-foreground">
                <p className="text-sm">今日暂无已完成任务</p>
              </div>
            ) : (
              <div className="space-y-3">
                {completedTasks.map((task: any) => (
                  <div
                    key={task.id}
                    className="rounded-lg border border-border p-4 space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-sm">{task.name}</span>
                      <Badge variant="secondary">已完成</Badge>
                    </div>
                    {task.description && (
                      <p className="text-xs text-muted-foreground">
                        {task.description}
                      </p>
                    )}
                    {task.updated_at && (
                      <p className="text-xs text-muted-foreground">
                        更新时间: {formatDate(task.updated_at)}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card>
            <CardContent className="p-6 space-y-4">
              <div className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-accent" />
                <h2 className="text-lg font-semibold">明日计划</h2>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">计划内容</label>
                <textarea
                  value={tomorrowPlan}
                  onChange={(e) => setTomorrowPlan(e.target.value)}
                  rows={6}
                  placeholder="AI 将根据项目进度和计划自动生成明日建议,您也可以手动编辑..."
                  className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 resize-none"
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6 space-y-4">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-accent" />
                <h2 className="text-lg font-semibold">风险提醒</h2>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">风险描述</label>
                <textarea
                  value={riskReminders}
                  onChange={(e) => setRiskReminders(e.target.value)}
                  rows={6}
                  placeholder="AI 将自动分析潜在风险并生成提醒,您也可以手动编辑..."
                  className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 resize-none"
                />
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      <Card className="border-primary/30 bg-primary/5">
        <CardContent className="p-6 flex items-center justify-between">
          <div>
            <h3 className="font-semibold">确认提交日报</h3>
            <p className="text-sm text-muted-foreground mt-1">
              提交后日报内容将锁定,如需修改请谨慎操作
            </p>
          </div>
          <Button
            size="lg"
            onClick={handleSubmit}
            disabled={submitting || dailyReport?.confirmed}
          >
            <CheckCircle className="h-5 w-5" />
            {submitting ? '提交中...' : '确认提交'}
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}