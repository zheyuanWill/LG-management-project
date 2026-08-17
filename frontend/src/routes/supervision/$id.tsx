import { useState, useEffect } from 'react'
import { useParams, useNavigate } from '@tanstack/react-router'
import { useQueryClient } from '@tanstack/react-query'
import { useApiDelete, useApiGet } from '@/hooks/useApi'
import { ArrowLeft, Edit3, Loader2 } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { toast } from '@/components/ui/Toast'
import RiskTicker from '@/components/layout/RiskTicker'
import ProjectTabs from '@/components/project/ProjectTabs'
import ProjectForm from '@/components/project/ProjectForm'
import DeleteConfirm from '@/components/common/DeleteConfirm'
import { wsClient } from '@/lib/websocket'
import { useAuthStore } from '@/hooks/useAuth'
import { PROJECT_STATUS_LABELS } from '@/lib/constants'
import { formatDate } from '@/lib/utils'

export default function SupervisionDetail() {
  const { id } = useParams({ strict: false }) as { id: string }
  const navigate = useNavigate()
  const [showEditForm, setShowEditForm] = useState(false)
  const queryClient = useQueryClient()

  const { data: project, isLoading } = useApiGet<any>(`/projects/${id}`)
  const { data: tasks } = useApiGet<any[]>(`/tasks/projects/${id}/tasks`)
  const { data: dailyReports } = useApiGet<any[]>(`/reports/projects/${id}/daily-reports`)
  const { data: weeklyReports } = useApiGet<any[]>(`/reports/projects/${id}/weekly-reports`)
  const { data: risks } = useApiGet<any[]>(`/risks/projects/${id}/risks`)
  const deleteProject = useApiDelete<any>('/projects')

  const handleDataChange = () => {
    // 详情页数据来自 react-query（useApiGet 以 url 为 queryKey）。
    // 子 Tab 写操作后统一使其失效，触发详情页（头部/统计卡/风险滚动条）重取，
    // 取代原先无副作用的 setDataVersion 状态变量。
    const keys = [
      `/projects/${id}`,
      `/tasks/projects/${id}/tasks`,
      `/reports/projects/${id}/daily-reports`,
      `/reports/projects/${id}/weekly-reports`,
      `/risks/projects/${id}/risks`,
      `/projects`,
    ]
    keys.forEach((k) => queryClient.invalidateQueries({ queryKey: [k] }))
  }

  // 实时推送：进入详情页即订阅该项目房间，收到「现场更新」事件时刷新并提示
  useEffect(() => {
    const token = useAuthStore.getState().token
    wsClient.connect(id, token || undefined)

    const handler = (data: unknown) => {
      const evt = data as { type?: string }
      if (evt?.type === 'daily_update_created') {
        handleDataChange()
        toast.success({ title: '现场更新', description: '有新的每日更新已提交，列表已刷新' })
      }
    }
    wsClient.on('daily_update_created', handler)

    return () => {
      wsClient.off('daily_update_created', handler)
      wsClient.disconnect()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        <span className="ml-3 text-muted-foreground">加载项目详情...</span>
      </div>
    )
  }

  if (!project) {
    return (
      <div className="py-24 text-center">
        <p className="text-lg text-muted-foreground">项目不存在</p>
        <Button variant="outline" onClick={() => navigate({ to: '/supervision' })} className="mt-4">
          返回列表
        </Button>
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
            onClick={() => navigate({ to: '/supervision' })}
          >
            <ArrowLeft className="h-4 w-4" />
            返回
          </Button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold">
                {project.ship_name}
              </h1>
              <Badge
                variant={
                  project.status === 'active'
                    ? 'default'
                    : project.status === 'completed'
                      ? 'secondary'
                      : 'destructive'
                }
              >
                {PROJECT_STATUS_LABELS[project.status]}
              </Badge>
            </div>
            <div className="flex items-center gap-2 mt-1 text-sm text-muted-foreground">
              <span>项目编号: {project.project_no}</span>
              {project.imo && <span>· IMO: {project.imo}</span>}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={() => setShowEditForm(true)}>
            <Edit3 className="h-4 w-4" />
            编辑项目
          </Button>
          <DeleteConfirm
            resourceName="项目"
            triggerVariant="button"
            description={`将删除（软取消）「${project.ship_name}」项目及其下所有任务、日报、周报、风险等数据。此操作不可撤销。`}
            mutation={deleteProject}
            id={String(project.id)}
            onDeleted={() => {
              navigate({ to: '/supervision' })
            }}
          />
        </div>
      </div>

      {risks && risks.length > 0 && (
        <RiskTicker risks={risks} projectId={id} />
      )}

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardContent className="p-5 space-y-3">
            <div>
              <p className="text-xs text-muted-foreground">船东</p>
              <p className="text-sm font-medium">{project.customer_name || '-'}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">计划完工</p>
              <p className="text-sm font-medium">
                {project.planned_completion_date ? formatDate(project.planned_completion_date) : '-'}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">创建时间</p>
              <p className="text-sm font-medium">{formatDate(project.created_at)}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5 space-y-3">
            <div>
              <p className="text-xs text-muted-foreground">备注</p>
              <p className="text-sm font-medium">{project.remarks || '-'}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">任务数</p>
              <p className="text-sm font-medium">{tasks?.length || 0}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">风险数</p>
              <p className="text-sm font-medium">{risks?.length || 0}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5 space-y-3">
            <div>
              <p className="text-xs text-muted-foreground">状态</p>
              <p className="text-sm font-medium">{PROJECT_STATUS_LABELS[project.status]}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">更新时间</p>
              <p className="text-sm font-medium">{formatDate(project.updated_at)}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardContent className="p-0">
          <div className="p-6">
            <ProjectTabs
              project={project}
              tasks={tasks || []}
              dailyReports={dailyReports || []}
              weeklyReports={weeklyReports || []}
              risks={risks || []}
              onDataChange={handleDataChange}
            />
          </div>
        </CardContent>
      </Card>

      <ProjectForm
        open={showEditForm}
        onOpenChange={setShowEditForm}
        project={project}
        onSaved={() => {
          setShowEditForm(false)
          handleDataChange()
        }}
      />
    </div>
  )
}