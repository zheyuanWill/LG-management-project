import { useState, useEffect, useRef } from 'react'
import { Calendar, Sparkles, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import WeeklyReportCard from './WeeklyReportCard'
import apiClient from '@/lib/api'
import { toast } from '@/components/ui/Toast'
import { useQueryClient } from '@tanstack/react-query'

interface WeeklyReportListProps {
  projectId: string
  reports: any[]
  onReportsChange?: () => void
}

const POLL_INTERVAL = 2000
const MAX_POLLS = 30

export default function WeeklyReportList({
  projectId,
  reports,
  onReportsChange,
}: WeeklyReportListProps) {
  const [generating, setGenerating] = useState(false)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const queryClient = useQueryClient()

  const stopPolling = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
  }

  useEffect(() => stopPolling, [])

  const refreshList = () => {
    queryClient.invalidateQueries({
      queryKey: [`/reports/projects/${projectId}/weekly-reports`],
    })
    onReportsChange?.()
  }

  const handleGenerate = async () => {
    if (generating) return
    setGenerating(true)
    const prevIds = new Set((reports || []).map((r) => r.id))

    try {
      await apiClient.post(`/reports/projects/${projectId}/weekly-reports/generate`, {})
      toast.success({
        title: '已提交周报生成',
        description: 'AI 正在汇总本周已确认日报,请稍候',
      })

      let polls = 0
      timerRef.current = setInterval(async () => {
        polls += 1
        try {
          const res = await apiClient.get(
            `/reports/projects/${projectId}/weekly-reports/latest`
          )
          const latest = res.data
          if (latest && latest.id != null && !prevIds.has(latest.id)) {
            stopPolling()
            setGenerating(false)
            refreshList()
            toast.success({ title: '周报已生成' })
            return
          }
        } catch {
          // ignore transient poll errors, keep trying
        }
        if (polls >= MAX_POLLS) {
          stopPolling()
          setGenerating(false)
          toast.warning({
            title: '生成超时',
            description: '周报仍在后台生成,请稍后手动刷新',
          })
        }
      }, POLL_INTERVAL)
    } catch {
      setGenerating(false)
      toast.error({ title: '提交失败', description: '请稍后重试' })
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <Calendar className="h-5 w-5 text-primary" />
          周报
        </h3>
        <Button onClick={handleGenerate} disabled={generating}>
          {generating ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              AI 生成中
            </>
          ) : (
            <>
              <Sparkles className="h-4 w-4" />
              生成周报
            </>
          )}
        </Button>
      </div>

      {reports.length === 0 ? (
        <div className="py-12 text-center text-muted-foreground">
          <p>暂无周报数据</p>
          <p className="text-sm mt-1">点击“生成周报”,由 AI 基于本周已确认日报汇总</p>
        </div>
      ) : (
        reports.map((report) => (
          <WeeklyReportCard key={report.id} report={report} onDeleted={refreshList} />
        ))
      )}
    </div>
  )
}
