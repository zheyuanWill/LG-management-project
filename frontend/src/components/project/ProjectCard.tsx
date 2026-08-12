import { useNavigate } from '@tanstack/react-router'
import { Ship, Calendar, Hash, ChevronRight, Building2, AlertTriangle } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { cn } from '@/lib/utils'
import type { Project } from '@/types'
import { PROJECT_STATUS_LABELS } from '@/lib/constants'
import { formatDate } from '@/lib/utils'

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
          <Badge variant={STATUS_BADGE_VARIANTS[project.status] || 'default'}>
            {PROJECT_STATUS_LABELS[project.status]}
          </Badge>
        </div>

        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Hash className="h-4 w-4" />
          <span>{project.project_no}</span>
        </div>

        {project.customer_name && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Building2 className="h-4 w-4 shrink-0" />
            <span className="truncate">{project.customer_name}</span>
            {project.customer_phone && (
              <span className="text-muted-foreground/70">{project.customer_phone}</span>
            )}
          </div>
        )}

        {(project.risk_summary || project.has_unconfirmed_report) && (
          <div className="flex flex-wrap items-center gap-2 text-xs">
            {project.risk_summary && (
              <span className="inline-flex items-center gap-1 rounded-full bg-muted px-2 py-0.5 text-muted-foreground">
                <AlertTriangle className="h-3 w-3" />
                {project.risk_summary}
              </span>
            )}
            {project.has_unconfirmed_report && (
              <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 text-amber-700">
                有待确认日报
              </span>
            )}
          </div>
        )}

        <div className="flex items-center justify-between text-xs text-muted-foreground pt-2 border-t border-border/50">
          <div className="flex items-center gap-1">
            <Calendar className="h-3.5 w-3.5" />
            <span>计划完工: {project.planned_completion_date ? formatDate(project.planned_completion_date) : '未设置'}</span>
          </div>
          <ChevronRight className="h-4 w-4" />
        </div>
      </CardContent>
    </Card>
  )
}