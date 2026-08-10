import { useState } from 'react'
import { useParams, useNavigate } from '@tanstack/react-router'
import { ArrowLeft, Edit3, Loader2 } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Progress } from '@/components/ui/Progress'
import RiskTicker from '@/components/layout/RiskTicker'
import ProjectTabs from '@/components/project/ProjectTabs'
import ProjectForm from '@/components/project/ProjectForm'
import { useApiGet } from '@/hooks/useApi'
import { PROJECT_STATUS_LABELS } from '@/lib/constants'
import { formatDate } from '@/lib/utils'

export default function SupervisionDetail() {
  const { id } = useParams({ strict: false }) as { id: string }
  const navigate = useNavigate()
  const [showEditForm, setShowEditForm] = useState(false)
  const [dataVersion, setDataVersion] = useState(0)

  const { data: project, isLoading } = useApiGet<any>(`/projects/${id}`)
  const { data: tasks } = useApiGet<any[]>(`/projects/${id}/tasks`)
  const { data: dailyReports } = useApiGet<any[]>(`/projects/${id}/daily-reports`)
  const { data: weeklyReports } = useApiGet<any[]>(`/projects/${id}/weekly-reports`)
  const { data: risks } = useApiGet<any[]>(`/projects/${id}/risks`)

  const handleDataChange = () => {
    setDataVersion((v) => v + 1)
  }

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
                {project.vessel_name || project.name}
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
        <Button variant="outline" onClick={() => setShowEditForm(true)}>
          <Edit3 className="h-4 w-4" />
          编辑项目
        </Button>
      </div>

      {risks && risks.length > 0 && (
        <RiskTicker risks={risks} projectId={id} />
      )}

      <div className="grid gap-4 md:grid-cols-4">
        <Card className="md:col-span-3">
          <CardContent className="p-5">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-muted-foreground">项目进度</span>
              <span className="text-lg font-bold">{project.progress}%</span>
            </div>
            <Progress value={project.progress} />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5 space-y-3">
            <div>
              <p className="text-xs text-muted-foreground">船东</p>
              <p className="text-sm font-medium">{project.customer_name || '-'}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">计划完工</p>
              <p className="text-sm font-medium">
                {project.planned_end_date ? formatDate(project.planned_end_date) : '-'}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">创建时间</p>
              <p className="text-sm font-medium">{formatDate(project.created_at)}</p>
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