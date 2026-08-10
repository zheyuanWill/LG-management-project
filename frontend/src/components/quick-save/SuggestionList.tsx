import { Check, RefreshCw, Trash2, Ship, Hash } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { cn } from '@/lib/utils'

interface SuggestedProject {
  id: string
  name: string
  project_no: string
  confidence: number
}

interface AISuggestion {
  summary: string
  projects: SuggestedProject[]
}

interface SuggestionListProps {
  suggestion: AISuggestion
  onConfirm: (projectId: string) => void
  onChangeProject: () => void
  onDelete: () => void
}

export default function SuggestionList({
  suggestion,
  onConfirm,
  onChangeProject,
  onDelete,
}: SuggestionListProps) {
  return (
    <div className="space-y-4">
      <div className="rounded-lg bg-primary/5 p-4 space-y-2">
        <p className="text-sm font-medium">AI 识别摘要</p>
        <p className="text-sm text-muted-foreground">{suggestion.summary}</p>
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <p className="text-sm font-medium">匹配的项目</p>
          {suggestion.projects.length > 1 && (
            <Button variant="ghost" size="sm" onClick={onChangeProject}>
              <RefreshCw className="h-3 w-3" />
              换项目
            </Button>
          )}
        </div>

        {suggestion.projects.length === 0 ? (
          <div className="py-8 text-center text-muted-foreground">
            <p className="text-sm">暂无匹配项目,请手动选择</p>
          </div>
        ) : (
          <div className="space-y-2">
            {suggestion.projects.map((project, index) => (
              <Card
                key={project.id}
                className={cn(
                  'transition-all cursor-pointer',
                  index === 0 && 'ring-2 ring-primary ring-offset-2'
                )}
              >
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="rounded-lg bg-primary/10 p-2 shrink-0">
                        <Ship className="h-4 w-4 text-primary" />
                      </div>
                      <div className="min-w-0">
                        <p className="font-medium text-sm truncate">{project.name}</p>
                        <p className="text-xs text-muted-foreground flex items-center gap-1 mt-0.5">
                          <Hash className="h-3 w-3" />
                          {project.project_no}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <Badge
                        variant={project.confidence >= 0.8 ? 'success' : 'secondary'}
                        className="text-xs"
                      >
                        {(project.confidence * 100).toFixed(0)}%
                      </Badge>
                      {index === 0 && (
                        <Badge variant="default" className="text-xs">
                          最佳匹配
                        </Badge>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      <div className="flex items-center justify-between pt-4 border-t">
        <Button variant="destructive" size="sm" onClick={onDelete}>
          <Trash2 className="h-4 w-4" />
          删除
        </Button>
        <div className="flex items-center gap-2">
          {suggestion.projects.length > 0 && (
            <Button onClick={() => onConfirm(suggestion.projects[0].id)} size="sm">
              <Check className="h-4 w-4" />
              确认关联
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}