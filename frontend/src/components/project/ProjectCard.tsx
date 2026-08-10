import { useNavigate, Link } from '@tanstack/react-router'
import { Ship, Calendar, Hash, ChevronRight } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Progress } from '@/components/ui/Progress'
import { cn } from '@/lib/utils'
import type { Project } from '@/types'
import { PROJECT_STATUS_LABELS } from '@/lib/constants'
import { formatDate } from '@/lib/utils'

interface ProjectCardProps {
  project: Project
  routePath?: string
}

const STATUS_BADGE_VARIANTS: Record<string, 'default' | 'secondary' | 'destructive'> = {
  active: 'default',
  completed: 'secondary',
  cancelled: 'destructive',
}

export default function ProjectCard({ project, routePath = '/supervision/$id' }: ProjectCardProps) {
  const navigate = useNavigate()
  const detailUrl = routePath.replace('$id', String(project.id))

  const progressVariant =
    (project.progress ?? 0) >= 100
      ? 'success'
      : (project.progress ?? 0) >= 50
        ? 'default'
        : (project.progress ?? 0) > 0
          ? 'warning'
          : 'default'

  return (
    <Link
      to={detailUrl as any}
      className={cn(
        'block cursor-pointer transition-all hover:shadow-md hover:-translate-y-0.5 rounded-lg border border-border bg-card text-card-foreground shadow-sm hover:border-primary/50'
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
          <Badge variant={STATUS_BADGE_VARIANTS[project.status] || 'default'}>
            {PROJECT_STATUS_LABELS[project.status]}
          </Badge>
        </div>

        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Hash className="h-4 w-4" />
          <span>{project.project_no}</span>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">进度</span>
            <span className="font-medium">{project.progress ?? 0}%</span>
          </div>
          <Progress value={project.progress ?? 0} variant={progressVariant} />
        </div>

        <div className="flex items-center justify-between text-xs text-muted-foreground pt-2 border-t border-border/50">
          <div className="flex items-center gap-1">
            <Calendar className="h-3.5 w-3.5" />
            <span>计划完工: {project.planned_completion_date ? formatDate(project.planned_completion_date) : '-'}</span>
          </div>
          <ChevronRight className="h-4 w-4" />
        </div>
      </CardContent>
    </Link>
  )
}