import { lazy, Suspense } from 'react'
import { ListTodo, FileText, Calendar, AlertTriangle, CheckCircle, Loader2 } from 'lucide-react'
import { Tabs } from '@/components/ui/Tabs'
import type { Project } from '@/types'

const TaskList = lazy(() => import('@/components/task/TaskList'))
const DailyReportList = lazy(() => import('@/components/report/DailyReportList'))
const WeeklyReportCard = lazy(() => import('@/components/report/WeeklyReportCard'))
const RiskList = lazy(() => import('@/components/risk/RiskList'))
const ProjectCompletion = lazy(() => import('@/components/project/ProjectCompletion'))

const LoadingFallback = () => (
  <div className="flex items-center justify-center py-12">
    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
    <span className="ml-2 text-sm text-muted-foreground">加载中...</span>
  </div>
)

interface ProjectTabsProps {
  project: Project
  tasks: import('@/types').Task[]
  dailyReports: import('@/types').DailyReport[]
  weeklyReports: import('@/types').WeeklyReport[]
  risks: import('@/types').RiskEvent[]
  onDataChange?: () => void
}

export default function ProjectTabs({
  project,
  tasks,
  dailyReports,
  weeklyReports,
  risks,
  onDataChange,
}: ProjectTabsProps) {
  const tabs = [
    {
      value: 'tasks',
      label: '任务管理',
      icon: <ListTodo className="h-4 w-4" />,
      content: (
        <Suspense fallback={<LoadingFallback />}>
          <TaskList projectId={project.id} tasks={tasks} onTasksChange={onDataChange} />
        </Suspense>
      ),
    },
    {
      value: 'daily-reports',
      label: '日报',
      icon: <FileText className="h-4 w-4" />,
      content: (
        <Suspense fallback={<LoadingFallback />}>
          <DailyReportList projectId={project.id} reports={dailyReports} onReportsChange={onDataChange} />
        </Suspense>
      ),
    },
    {
      value: 'weekly-reports',
      label: '周报',
      icon: <Calendar className="h-4 w-4" />,
      content: (
        <Suspense fallback={<LoadingFallback />}>
          <div className="space-y-4">
            {weeklyReports.length === 0 ? (
              <div className="py-12 text-center text-muted-foreground">
                暂无周报数据
              </div>
            ) : (
              weeklyReports.map((report) => (
                <WeeklyReportCard key={report.id} report={report} />
              ))
            )}
          </div>
        </Suspense>
      ),
    },
    {
      value: 'risks',
      label: '风险历史',
      icon: <AlertTriangle className="h-4 w-4" />,
      content: (
        <Suspense fallback={<LoadingFallback />}>
          <RiskList risks={risks} projectId={project.id} />
        </Suspense>
      ),
    },
    {
      value: 'completion',
      label: '完工资料',
      icon: <CheckCircle className="h-4 w-4" />,
      content: (
        <Suspense fallback={<LoadingFallback />}>
          <ProjectCompletion project={project} onStatusChange={onDataChange} />
        </Suspense>
      ),
    },
  ]

  return <Tabs tabs={tabs} defaultValue="tasks" />
}