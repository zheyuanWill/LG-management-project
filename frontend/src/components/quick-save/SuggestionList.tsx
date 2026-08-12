import { useState } from 'react'
import { Check, RefreshCw, Trash2, Ship, Hash, Search, Loader2 } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Input } from '@/components/ui/Input'
import { cn } from '@/lib/utils'
import { stripMarkdown } from '@/lib/utils'
import apiClient from '@/lib/api'
import { toast } from '@/components/ui/Toast'

export interface SuggestionItem {
  id: number
  project_no: string
  ship_name: string
  type?: string
  match_score?: number
}

export interface QuickSaveResponse {
  id: number
  content_type: 'text' | 'image'
  content_text?: string | null
  file_key?: string | null
  recognized_text?: string | null
  suggested_project_id?: number | null
  confirmed_project_id?: number | null
  status: string
  created_at: string
}

interface SuggestionListProps {
  save: QuickSaveResponse
  suggestions: SuggestionItem[]
  onConfirm: (projectId: number) => Promise<void>
  onDelete: () => void
}

export default function SuggestionList({
  save,
  suggestions,
  onConfirm,
  onDelete,
}: SuggestionListProps) {
  const [showProjectPicker, setShowProjectPicker] = useState(false)
  const [projects, setProjects] = useState<any[]>([])
  const [search, setSearch] = useState('')
  const [loadingProjects, setLoadingProjects] = useState(false)
  const [busyProjectId, setBusyProjectId] = useState<number | null>(null)

  const loadProjects = async () => {
    setLoadingProjects(true)
    try {
      const res = await apiClient.get('/projects', { params: { status: 'active' } })
      const data = res.data as any
      const list = Array.isArray(data)
        ? data
        : Array.isArray(data?.items)
          ? data.items
          : Array.isArray(data?.projects)
            ? data.projects
            : []
      setProjects(list)
    } catch {
      toast.error({ title: '项目列表加载失败', description: '请稍后重试', duration: 4000 })
    } finally {
      setLoadingProjects(false)
    }
  }

  const handleChangeProject = () => {
    const next = !showProjectPicker
    setShowProjectPicker(next)
    if (next && projects.length === 0) {
      loadProjects()
    }
  }

  const confirm = async (projectId: number) => {
    setBusyProjectId(projectId)
    try {
      await onConfirm(projectId)
    } finally {
      setBusyProjectId(null)
    }
  }

  const filteredProjects = projects.filter((p) =>
    `${p.ship_name ?? ''} ${p.project_no ?? ''}`.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="space-y-4">
      <div className="rounded-lg bg-primary/5 p-4 space-y-2">
        <p className="text-sm font-medium">AI 识别摘要</p>
        {save.recognized_text ? (
          <p className="text-sm text-muted-foreground whitespace-pre-wrap">{stripMarkdown(save.recognized_text)}</p>
        ) : (
          <p className="text-sm text-muted-foreground">
            未能自动识别文字 (AI 暂不可用)。已保存为待处理,请手动选择关联项目。
          </p>
        )}
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <p className="text-sm font-medium">匹配的项目</p>
          <Button variant="ghost" size="sm" onClick={handleChangeProject}>
            <RefreshCw className={cn('h-3 w-3', showProjectPicker && 'animate-spin')} />
            换项目
          </Button>
        </div>

        {showProjectPicker ? (
          <div className="space-y-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                className="pl-9"
                placeholder="搜索船舶名称或项目编号"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            {loadingProjects ? (
              <div className="py-6 text-center text-sm text-muted-foreground flex items-center justify-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                加载项目中...
              </div>
            ) : filteredProjects.length === 0 ? (
              <div className="py-6 text-center text-sm text-muted-foreground">未找到匹配的项目</div>
            ) : (
              <div className="max-h-60 overflow-y-auto space-y-2">
                {filteredProjects.map((project) => (
                  <Card key={project.id} className="transition-all cursor-pointer hover:ring-2 hover:ring-primary/40">
                    <CardContent
                      className="p-3"
                      onClick={() => confirm(project.id)}
                    >
                      <div className="flex items-center justify-between gap-3">
                        <div className="flex items-center gap-3 min-w-0">
                          <div className="rounded-lg bg-primary/10 p-2 shrink-0">
                            <Ship className="h-4 w-4 text-primary" />
                          </div>
                          <div className="min-w-0">
                            <p className="font-medium text-sm truncate">{project.ship_name}</p>
                            <p className="text-xs text-muted-foreground flex items-center gap-1 mt-0.5">
                              <Hash className="h-3 w-3" />
                              {project.project_no}
                            </p>
                          </div>
                        </div>
                        {busyProjectId === project.id ? (
                          <Loader2 className="h-4 w-4 animate-spin shrink-0" />
                        ) : (
                          <Check className="h-4 w-4 text-primary shrink-0" />
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        ) : suggestions.length === 0 ? (
          <div className="py-8 text-center text-muted-foreground">
            <p className="text-sm">暂无自动匹配项目,请点击"换项目"手动选择</p>
          </div>
        ) : (
          <div className="space-y-2">
            {suggestions.map((project, index) => (
              <Card
                key={project.id}
                className={cn(
                  'transition-all cursor-pointer',
                  index === 0 && 'ring-2 ring-primary ring-offset-2'
                )}
                onClick={() => confirm(project.id)}
              >
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="rounded-lg bg-primary/10 p-2 shrink-0">
                        <Ship className="h-4 w-4 text-primary" />
                      </div>
                      <div className="min-w-0">
                        <p className="font-medium text-sm truncate">{project.ship_name}</p>
                        <p className="text-xs text-muted-foreground flex items-center gap-1 mt-0.5">
                          <Hash className="h-3 w-3" />
                          {project.project_no}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      {typeof project.match_score === 'number' && (
                        <Badge variant={project.match_score >= 2 ? 'success' : 'secondary'} className="text-xs">
                          匹配 {project.match_score}
                        </Badge>
                      )}
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
          {!showProjectPicker && suggestions.length > 0 && (
            <Button onClick={() => confirm(suggestions[0].id)} size="sm" disabled={busyProjectId !== null}>
              {busyProjectId !== null ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Check className="h-4 w-4" />
              )}
              确认关联
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}
