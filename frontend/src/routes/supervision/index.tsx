import { useState, useMemo } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { Plus, Search, Ship, Calendar } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import ProjectCard from '@/components/project/ProjectCard'
import ProjectForm from '@/components/project/ProjectForm'
import { useApiGet } from '@/hooks/useApi'
import type { Project } from '@/types'
import { formatDate } from '@/lib/utils'

const statusFilters = [
  { value: 'all', label: '全部' },
  { value: 'active', label: '进行中' },
  { value: 'completed', label: '已完成' },
]

export default function SupervisionIndex() {
  const [statusFilter, setStatusFilter] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [showForm, setShowForm] = useState(false)

  const { data: projects, isLoading } = useApiGet<Project[]>('/projects', {
    params: { type: 'supervision' },
  })

  const filteredProjects = useMemo(() => {
    let result = projects || []
    if (statusFilter !== 'all') {
      result = result.filter((p) => p.status === statusFilter)
    }
    if (searchQuery.trim()) {
      const query = searchQuery.trim().toLowerCase()
      result = result.filter(
        (p) =>
          (p.ship_name).toLowerCase().includes(query) ||
          p.project_no.toLowerCase().includes(query) ||
          (p.imo && p.imo.toLowerCase().includes(query))
      )
    }
    return result
  }, [projects, statusFilter, searchQuery])

  const activeCount = (projects || []).filter((p) => p.status === 'active').length
  const completedCount = (projects || []).filter((p) => p.status === 'completed').length

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">监修项目管理</h1>
          <p className="text-muted-foreground mt-1">
            管理船舶监修项目,跟踪进度和风险
          </p>
        </div>
        <Button onClick={() => setShowForm(true)} size="lg">
          <Plus className="h-5 w-5" />
          新建项目
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">项目总数</p>
                <p className="mt-2 text-2xl font-bold">{projects?.length ?? 0}</p>
              </div>
              <div className="rounded-lg bg-primary/10 p-3">
                <Ship className="h-5 w-5 text-primary" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">进行中</p>
                <p className="mt-2 text-2xl font-bold text-primary">{activeCount}</p>
              </div>
              <div className="rounded-lg bg-primary/10 p-3">
                <Calendar className="h-5 w-5 text-primary" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">已完成</p>
                <p className="mt-2 text-2xl font-bold text-secondary">{completedCount}</p>
              </div>
              <div className="rounded-lg bg-secondary/10 p-3">
                <Ship className="h-5 w-5 text-secondary" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">状态:</span>
          <div className="flex items-center gap-1 rounded-lg border border-border bg-muted p-1">
            {statusFilters.map((filter) => (
              <button
                key={filter.value}
                onClick={() => setStatusFilter(filter.value)}
                className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                  statusFilter === filter.value
                    ? 'bg-background shadow-sm text-foreground font-medium'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                {filter.label}
              </button>
            ))}
          </div>
        </div>

        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="搜索船名或项目编号..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      {isLoading ? (
        <div className="py-16 text-center text-muted-foreground">
          <p>加载中...</p>
        </div>
      ) : filteredProjects.length === 0 ? (
        <div className="py-16 text-center text-muted-foreground">
          <Ship className="mx-auto h-12 w-12 opacity-50 mb-3" />
          <p className="text-lg">暂无监修项目</p>
          <p className="text-sm mt-1">点击"新建项目"创建第一个监修项目</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredProjects.map((project) => (
            <ProjectCard key={project.id} project={project} />
          ))}
        </div>
      )}

      <ProjectForm
        open={showForm}
        onOpenChange={setShowForm}
        onSaved={() => {
          setShowForm(false)
        }}
      />
    </div>
  )
}