import { useNavigate } from '@tanstack/react-router'
import { Ship, Calendar, Hash, ChevronRight } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Progress } from '@/components/ui/Progress'
import { cn } from '@/lib/utils'
import { useApiDelete } from '@/hooks/useApi'
import { useQueryClient } from '@tanstack/react-query'
import type { Project } from '@/types'
import { PROJECT_STATUS_LABELS } from '@/lib/constants'
import { formatDate } from '@/lib/utils'
import DeleteConfirm from '@/components/common/DeleteConfirm'

interface ProjectCardProps {
  project: Project
}

const STATUS_BADGE_VARIANTS: Record<string, 'default' | 'secondary' | 'destructive'> = {
  active: 'default',
  completed: 'secondary',
  cancelled: 'destructive',
}

export default function ProjectCard({ project }: ProjectCardProps) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const deleteProject = useApiDelete<Project>('/projects')

  const handleClick = () => {
    navigate({ to: '/supervision/$id', params: { id: project.id } })
  }

  return (
    <Card
      onClick={handleClick}
      className={cn(
        'cursor-pointer transition-all hover:shadow-md hover:-translate-y-0.5',
        'border-border hover:border-primary/50'
      )}
    >
      <CardContent className="p-5 space-y-4">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3">
            <div className="rounded-lg bg-primary/10 p-2.5">
              <Ship className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h3 className="font-semibold text-lg leading-tight">
                {project.ship_name}
              </h3>
              {project.imo && (
                <p className="text-xs text-muted-foreground mt-0.5">
                  IMO: {project.imo}
                </p>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={STATUS_BADGE_VARIANTS[project.status] || 'default'}>
              {PROJECT_STATUS_LABELS[project.status]}
            </Badge>
            <DeleteConfirm
              resourceName="项目"
              description={`将删除（软取消）「${project.ship_name}」项目及其下所有任务、日报、周报、风险等数据。此操作不可撤销。`}
              mutation={deleteProject}
              id={String(project.id)}
              onDeleted={() => {
                queryClient.invalidateQueries({ queryKey: ['/projects'] })
              }}
            />
          </div>
        </div>

        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Hash className="h-4 w-4" />
          <span>{project.project_no}</span>
        </div>

        <div className="flex items-center justify-between text-xs text-muted-foreground pt-2 border-t border-border/50">
          <div className="flex items-center gap-1">
            <Calendar className="h-3.5 w-3.5" />
            <span>计划完工: {project.planned_completion_date ? formatDate(project.planned_completion_date) : '-'}</span>
          </div>
          <ChevronRight className="h-4 w-4" />
        </div>
      </CardContent>
    </Card>
  )
}