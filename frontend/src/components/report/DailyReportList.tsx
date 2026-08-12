import { useState, useMemo } from 'react'
import { Filter, Plus, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { DatePicker } from '@/components/ui/DatePicker'
import DailyReportCard from './DailyReportCard'
import { useApiPost } from '@/hooks/useApi'
import { toast } from '@/components/ui/Toast'
import type { DailyReport } from '@/types'

interface DailyReportListProps {
  projectId: string
  reports: DailyReport[]
  onReportsChange?: () => void
}

export default function DailyReportList({
  projectId,
  reports,
  onReportsChange,
}: DailyReportListProps) {
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [showFilters, setShowFilters] = useState(false)

  const generateMutation = useApiPost<DailyReport>(
    `/reports/projects/${projectId}/daily-reports/generate`
  )

  const sortedReports = useMemo(() => {
    let result = [...reports]
    if (startDate) {
      result = result.filter((r) => r.date >= startDate)
    }
    if (endDate) {
      result = result.filter((r) => r.date <= endDate)
    }
    return result.sort((a, b) => (a.date > b.date ? -1 : 1))
  }, [reports, startDate, endDate])

  const handleGenerate = async () => {
    try {
      const today = new Date().toISOString().split('T')[0]
      await generateMutation.mutateAsync({ date: today })
      toast.success({ title: '日报生成成功' })
      onReportsChange?.()
    } catch {
      toast.error({ title: '生成失败', description: '请稍后重试' })
    }
  }

  const handleResetFilters = () => {
    setStartDate('')
    setEndDate('')
  }

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
        <Button
          onClick={handleGenerate}
          disabled={generateMutation.isPending}
        >
          {generateMutation.isPending ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              生成中
            </>
          ) : (
            <>
              <Plus className="h-4 w-4" />
              生成日报
            </>
          )}
        </Button>
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
            <Button variant="ghost" size="sm" onClick={handleResetFilters}>
              重置筛选
            </Button>
          </div>
        </div>
      )}

      {sortedReports.length === 0 ? (
        <div className="py-16 text-center text-muted-foreground">
          <p className="mb-2">暂无日报数据</p>
          <p className="text-sm">点击"生成日报"创建今日日报</p>
        </div>
      ) : (
        <div className="space-y-4">
          {sortedReports.map((report) => (
            <DailyReportCard
              key={report.id}
              report={report}
              onUpdate={onReportsChange}
            />
          ))}
        </div>
      )}
    </div>
  )
}