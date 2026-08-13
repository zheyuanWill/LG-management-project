import { useState, useMemo, useEffect } from 'react'
import { useParams, useNavigate } from '@tanstack/react-router'
import { ArrowLeft, Calendar, Loader2, Sparkles, AlertTriangle, CheckCircle } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { useApiGet, useApiPost } from '@/hooks/useApi'
import { toast } from '@/components/ui/Toast'
import { formatDate } from '@/lib/utils'
import MarkdownView from '@/components/common/MarkdownView'

interface DailyReportData {
  id?: number
  report_date: string
  today_work?: string | null
  tomorrow_plan?: string | null
  risk_alert?: string | null
  confirmed: boolean
  created_at?: string
}

interface ProposalData {
  report_date: string
  today_work: string
  tomorrow_candidates: string[]
  risk_alert: string
  existing_report_id: number | null
}

export default function DailyReportPage() {
  const { id, date } = useParams({ strict: false }) as { id: string; date: string }
  const navigate = useNavigate()

  const [tomorrowPlan, setTomorrowPlan] = useState('')
  const [riskReminders, setRiskReminders] = useState('')
  const [todayWork, setTodayWork] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const { data: project, isLoading: projectLoading } = useApiGet<any>(`/projects/${id}`)
  // Fetch daily reports for this project, filtered by date
  const { data: dailyReports } = useApiGet<DailyReportData[]>(
    `/reports/projects/${id}/daily-reports`,
    { params: { start_date: date, end_date: date } }
  )
  const { data: tasks } = useApiGet<any[]>(`/tasks/projects/${id}/tasks`)

  // Find the report matching this date
  const dailyReport = useMemo(() => {
    if (!dailyReports || dailyReports.length === 0) return null
    return dailyReports.find((r) => r.report_date === date) || null
  }, [dailyReports, date])

  // Sync state from existing report
  useEffect(() => {
    if (dailyReport) {
      if (dailyReport.tomorrow_plan) setTomorrowPlan(dailyReport.tomorrow_plan)
      if (dailyReport.risk_alert) setRiskReminders(dailyReport.risk_alert)
      if (dailyReport.today_work) setTodayWork(dailyReport.today_work)
    }
  }, [dailyReport])

  // Use propose (synchronous AI draft) instead of async generate
  const proposeMutation = useApiPost<ProposalData>(
    `/reports/projects/${id}/daily-reports/propose`
  )
  const finalizeMutation = useApiPost<DailyReportData>(
    `/reports/projects/${id}/daily-reports/finalize`
  )

  const completedTasks = useMemo(() => {
    if (!tasks) return []
    return tasks.filter((t: any) => t.status === 'completed')
  }, [tasks])

  const handleGenerate = async () => {
    try {
      const result = await proposeMutation.mutateAsync({})
      if (result.tomorrow_candidates?.length) {
        setTomorrowPlan(result.tomorrow_candidates.map((c: string) => `- ${c}`).join('\n'))
      }
      if (result.risk_alert) setRiskReminders(result.risk_alert)
      if (result.today_work) setTodayWork(result.today_work)
      toast.success({ title: 'AI 日报生成成功' })
    } catch {
      toast.error({ title: '生成失败', description: '请稍后重试' })
    }
  }

  const handleSubmit = async () => {
    setSubmitting(true)
    try {
      // Parse tomorrow_plan text back to items
      const items = tomorrowPlan
        .split('\n')
        .map((l) => l.replace(/^[-*]\s*/, '').trim())
        .filter(Boolean)

      await finalizeMutation.mutateAsync({
        report_date: date,
        today_work: todayWork,
        tomorrow_items: items,
        risk_alert: riskReminders,
        confirmed: true,
      })
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
              <span>{formatDate(date)}</span>
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={handleGenerate}
            disabled={proposeMutation.isPending}
          >
            <Sparkles className="h-4 w-4" />
            {proposeMutation.isPending ? '生成中...' : 'AI 生成日报'}
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
        {/* 已完成事项 + 今日工作 */}
        <Card>
          <CardContent className="p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">今日工作</h2>
              <span className="text-sm text-muted-foreground">
                {completedTasks.length} 项已完成
              </span>
            </div>

            {todayWork ? (
              <div className="rounded-md border border-border bg-muted/30 p-3">
                <MarkdownView content={todayWork} />
              </div>
            ) : completedTasks.length === 0 ? (
              <div className="py-8 text-center text-muted-foreground">
                <p className="text-sm">今日暂无任务更新记录</p>
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
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <div className="space-y-6">
          {/* 明日计划 */}
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

          {/* 风险提醒 */}
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
